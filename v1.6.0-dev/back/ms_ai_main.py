
import numpy as np

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)

import sys

import os
from pathlib import Path
import time
from datetime import datetime, timezone, timedelta
import traceback
import gc
from  PIL import Image
import requests
import threading
from queue import Queue
import base64

import torch
from back.HAR import Person_Info
from back.utils import (remove_out_of_BBox, TF_detect_area, \
                        get_bottom_point, get_center_point, send_alarm_NVR, send_NVR_empty,
                        camera_info_refresh, get_IOU, send_SERVER_ai_info, get_active_info,
                        check_stop_person, make_square_bbox, merge_boxes, video_save_buffer_update)

from ultralytics import YOLO
import boxmot
import cv2

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging(logger_name="MS_AI_MAIN", log_file="MS_AI_MAIN.log")

KST = timezone(timedelta(hours=9))

# COLOR = {
#     0: (0, 150, 95),     # Grass Green - person
#     1: (0, 242, 255),    # yellow - bicycle (변경)
#     2: (180, 130, 70),   # Steel Blue - car
#     3: (0, 140, 255),    # Dark Orange - motorcycle
#     4: (219, 112, 147),  # Medium Purple - bus
#     5: (204, 209, 72),   # Medium Turquoise - truck
#     6: (147, 20, 255)    # Deep Pink - fire
# }

TRASH_DETECT_TIME = time.time()

# 쓰레기 검출 비동기 요청 관리를 위한 전역 변수
TRASH_DETECTION_PENDING = {}  # {camera_name: {person_id: request_data}}
TRASH_DETECTION_RESULTS = {}  # {camera_name: {person_id: [alarms]}}

# SigLip 검출 비동기 요청 관리를 위한 전역 변수
SIGLIP_DETECTION_PENDING = {}  # {camera_name: {person_id: request_data}}
SIGLIP_DETECTION_RESULTS = {}  # {camera_name: {person_id: {"probs": [], "detect_type": ""}}}

COLOR =  {
    0: "#669900",  # person
    1: "#fff200",  # bicycle
    2: "#4682B4",  # car
    3: "#FF8C00",  # motorcycle
    4: "#9370DB",  # bus
    5: "#48D1CC",  # truck
    6: "#FF1493"   # fire
}
class Video_Buffer:
    def __init__(self, pipe="video1", appsink_name="video_sink", resolution = (640, 480)):
        self._frame = None
        self.pipe = pipe
        self.appsink_name = appsink_name
        self.video_pipe = None
        self.video_sink = None
        # self.video_source = f'rtspsrc location=rtsp://{pipe} latency=10 buffer-mode=0 protocols=tcp'
        self.video_source = f'rtspsrc location={pipe} latency=30'

        self.video_codec = '! rtph264depay ! h264parse '  # 'application/x-rtp' 생략
        # Try hardware decoding first, fallback to software if needed
        try:
            # First try NVIDIA hardware decoding
            # self.video_decode = f'! nvh264dec ! videoscale ! video/x-raw,width=1280,height=720 ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
            self.video_decode = f'! nvh264dec ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
            
        except:
            # Fallback to software decoding
            self.video_decode = f'!decodebin ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
        
        self.run()

    def start_gst(self, config=None):
        command = ' '.join(config)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name(self.appsink_name)
        
        if not self.video_sink:
            print(f"Failed to get appsink named {self.appsink_name}")
            return
        
        self.video_sink.set_property("emit-signals", True)
        self.video_sink.set_property("sync", False)

    @staticmethod
    def gst_to_opencv(sample):
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def read(self):
        if self.frame_available():
            return self.frame_available(), self._frame
        else:
            return self.frame_available(), np.zeros((640, 480, 3), dtype=np.uint8)

    def frame_available(self):
        return self._frame is not None

    def run(self):
        try:
            self.start_gst(
                [
                    self.video_source,
                    self.video_codec,
                    self.video_decode
                ]
            )
            if self.video_sink:
                self.video_sink.connect('new-sample', self.callback)

            bus = self.video_pipe.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_message)
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            logger.error(f"Error occurred at {current_time}: {e}\n{tb}")

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR or t == Gst.MessageType.EOS:
            self.video_pipe.set_state(Gst.State.NULL)
            self.run()

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame

        return Gst.FlowReturn.OK

    def release(self):
        self.video_pipe.set_state(Gst.State.NULL)

def send_trash_detection_request(camera_name, detect_area, current_img, enroll_img, 
                                  enroll_time, enroll_bbox, fgmask_enroll, person_bbox_list, 
                                  non_person_bbox_list, person_id, fgmask):
    """쓰레기 검출 API로 비동기 요청을 보내는 함수"""
    try:
        # 이미지를 base64로 인코딩
        _, current_img_encoded = cv2.imencode('.jpg', current_img)
        current_img_b64 = base64.b64encode(current_img_encoded).decode('utf-8')
        
        _, enroll_img_encoded = cv2.imencode('.jpg', enroll_img)
        enroll_img_b64 = base64.b64encode(enroll_img_encoded).decode('utf-8')

        _, fgmask_enroll_encoded = cv2.imencode('.jpg', fgmask_enroll)
        fgmask_enroll_b64 = base64.b64encode(fgmask_enroll_encoded).decode('utf-8')

        _, fgmask_encoded = cv2.imencode('.jpg', fgmask)
        fgmask_b64 = base64.b64encode(fgmask_encoded).decode('utf-8')
        
        # 요청 데이터 생성
        request_data = {
            "camera_name": camera_name,
            "detect_area": detect_area,
            "current_img": current_img_b64,
            "enroll_img": enroll_img_b64,
            "enroll_time": enroll_time,
            "enroll_bbox": enroll_bbox,
            "person_bbox_list": person_bbox_list,
            "non_person_bbox_list": non_person_bbox_list,
            "person_id": person_id,
            "fgmask": fgmask_b64,
            "fgmask_enroll": fgmask_enroll_b64
        }
        
        # API 요청
        url = "http://127.0.0.1:1206/detect_trash"
        # logger.info(f"쓰레기 검출 API 요청 - 카메라: {camera_name}, Person ID: {person_id}")
        response = requests.post(url, json=request_data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status"):
                alarms = result.get("alarms", [])
                logger.info(f"쓰레기 검출 API 응답 성공 - 카메라: {camera_name}, 알람 수: {len(alarms)}")
                
                # 결과를 전역 딕셔너리에 저장
                if camera_name not in TRASH_DETECTION_RESULTS:
                    TRASH_DETECTION_RESULTS[camera_name] = {}
                TRASH_DETECTION_RESULTS[camera_name][person_id] = alarms
            else:
                logger.warning(f"쓰레기 검출 실패 - 카메라: {camera_name}, 에러: {result.get('error')}")
        else:
            logger.error(f"쓰레기 검출 API 요청 실패 - 상태 코드: {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.error(f"쓰레기 검출 API 요청 타임아웃 - 카메라: {camera_name}")
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰레기 검출 API 요청 에러 at {current_time}: {e}\n{tb}")
    finally:
        # pending 리스트에서 제거
        if camera_name in TRASH_DETECTION_PENDING:
            if person_id in TRASH_DETECTION_PENDING[camera_name]:
                del TRASH_DETECTION_PENDING[camera_name][person_id]

def check_trash_detection_results(camera_info_dict):
    """비동기 쓰레기 검출 결과를 확인하고 alarm에 추가하는 함수"""
    global TRASH_DETECTION_RESULTS
    
    try:
        for camera_name in list(TRASH_DETECTION_RESULTS.keys()):
            for person_id in list(TRASH_DETECTION_RESULTS[camera_name].keys()):
                alarms = TRASH_DETECTION_RESULTS[camera_name][person_id]
                
                # 해당 카메라의 camera_info 찾기
                for camera_num, camera_info in camera_info_dict.items():
                    if camera_info["name"] == camera_name:
                        # alarm 리스트에 추가
                        for alarm in alarms:
                            camera_info["alarm"].append(alarm)
                            logger.info(f"쓰레기 알람 추가 - 카메라: {camera_name}, bbox: {alarm[1]}")
                        break
                
                # 처리 완료된 결과 삭제
                del TRASH_DETECTION_RESULTS[camera_name][person_id]
            
            # 빈 딕셔너리 정리
            if len(TRASH_DETECTION_RESULTS[camera_name]) == 0:
                del TRASH_DETECTION_RESULTS[camera_name]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰레기 검출 결과 처리 에러 at {current_time}: {e}\n{tb}")

def send_siglip_detection_request(camera_name, person_img, texts, person_id, detect_type):
    """SigLip 검출 API로 비동기 요청을 보내는 함수"""
    global SIGLIP_DETECTION_PENDING, SIGLIP_DETECTION_RESULTS
    
    try:
        # 이미지 유효성 검사 추가
        if person_img is None:
            logger.error(f"SigLip 검출 API 요청 실패 - person_img가 None입니다. 카메라: {camera_name}, ID: {person_id}")
            return
        
        if not isinstance(person_img, np.ndarray):
            logger.error(f"SigLip 검출 API 요청 실패 - person_img가 numpy array가 아닙니다. Type: {type(person_img)}, 카메라: {camera_name}, ID: {person_id}")
            return
        
        if person_img.size == 0:
            logger.error(f"SigLip 검출 API 요청 실패 - person_img가 비어있습니다. 카메라: {camera_name}, ID: {person_id}")
            return
        
        # 이미지를 base64로 인코딩
        _, img_encoded = cv2.imencode('.jpg', person_img)
        img_b64 = base64.b64encode(img_encoded).decode('utf-8')
        
        # 요청 데이터 생성
        request_data = {
            "camera_name": camera_name,
            "person_id": person_id,
            "image": img_b64,
            "texts": texts,
            "detect_type": detect_type
        }
        
        # API 요청
        url = "http://127.0.0.1:1206/detect_siglip"
        logger.info(f"SigLip 검출 API 요청 - 카메라: {camera_name}, Person ID: {person_id}, Type: {detect_type}")
        response = requests.post(url, json=request_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status"):
                probs = result.get("probs", [])
                logger.info(f"SigLip 검출 API 응답 성공 - 카메라: {camera_name}, ID: {person_id}, '결과: {np.argmax(probs)}', '확률: {np.round(probs[np.argmax(probs)], 2)}'")
                
                # 결과를 전역 딕셔너리에 저장
                if camera_name not in SIGLIP_DETECTION_RESULTS:
                    SIGLIP_DETECTION_RESULTS[camera_name] = {}
                SIGLIP_DETECTION_RESULTS[camera_name][person_id] = {
                    "probs": probs,
                    "detect_type": detect_type
                }
            else:
                logger.warning(f"SigLip 검출 실패 - 카메라: {camera_name}, 에러: {result.get('error')}")
        else:
            logger.error(f"SigLip 검출 API 요청 실패 - 상태 코드: {response.status_code}")
            
    except requests.exceptions.Timeout:
        logger.error(f"SigLip 검출 API 요청 타임아웃 - 카메라: {camera_name} ID: {person_id}")
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"SigLip 검출 API 요청 에러 at {current_time}: {e}\n{tb}")
    finally:
        # pending 리스트에서 제거
        if camera_name in SIGLIP_DETECTION_PENDING:
            if person_id in SIGLIP_DETECTION_PENDING[camera_name]:
                del SIGLIP_DETECTION_PENDING[camera_name][person_id]

def check_siglip_detection_results(camera_info_dict):
    """비동기 SigLip 검출 결과를 확인하고 상태를 업데이트하는 함수"""
    global SIGLIP_DETECTION_RESULTS
    
    try:
        for camera_name in list(SIGLIP_DETECTION_RESULTS.keys()):
            for person_id in list(SIGLIP_DETECTION_RESULTS[camera_name].keys()):
                result_data = SIGLIP_DETECTION_RESULTS[camera_name][person_id]
                probs = result_data["probs"]
                detect_type = result_data["detect_type"]
                
                # 해당 카메라의 camera_info 찾기
                for camera_num, camera_info in camera_info_dict.items():
                    if camera_info["name"] == camera_name:
                        # detect_type에 따라 status 업데이트
                        if detect_type == "falldown":
                            # 쓰러짐 검출 로직
                            if len(probs) >= 5:
                            #     if probs[0] > 0.50 and all(p < 0.3 for p in probs[1:]):
                            #         camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                            #         logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {person_id}")
                            #     elif max(range(len(probs)), key=lambda i: probs[i]) == 0 and all(p < 0.01 for p in probs[1:]):
                            #         camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                            #         logger.info(f"쓰러짐 검출(argmax) - 카메라: {camera_name}, ID: {person_id}")
                            #     else:
                            #         camera_info["person_info"].update_status(person_id, detect_type="falldown", status=0)
                                if probs[0] > 0.80 and (probs[1] + probs[2]) > 0.15 and all(p < 0.2 for p in probs[3:6]):
                                    camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                                    logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {person_id}")
                                elif probs[0] > 0.70 and probs[1] + probs[2] > 0.15 and all(p < 0.1 for p in probs[3:6]):
                                    camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                                    logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {person_id}")
                                elif probs[0] > 0.50 and (probs[1] + probs[2]) > 0.15 and all(p < 0.05 for p in probs[3:6]):
                                    camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                                    logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {person_id}")
                                elif probs[0] > 0.2 and (probs[1] + probs[2]) > 0.15 and all(p < 0.01 for p in probs[3:6]):
                                    camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
                                    logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {person_id}")
                                else:
                                    camera_info["person_info"].update_status(person_id, detect_type="falldown", status=0)
                        elif detect_type == "fight":
                            # 싸움 검출 로직
                            if len(probs) >= 1:
                                if probs[0] > 0.3:
                                    camera_info["person_info"].update_status(person_id, detect_type="fight", status=2)
                                    logger.info(f"싸움 검출 - 카메라: {camera_name}, ID: {person_id}")
                                else:
                                    camera_info["person_info"].update_status(person_id, detect_type="fight", status=0)
                        
                        break
                
                # 처리 완료된 결과 삭제
                del SIGLIP_DETECTION_RESULTS[camera_name][person_id]
            
            # 빈 딕셔너리 정리
            if len(SIGLIP_DETECTION_RESULTS[camera_name]) == 0:
                del SIGLIP_DETECTION_RESULTS[camera_name]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"SigLip 검출 결과 처리 에러 at {current_time}: {e}\n{tb}")

def check_box_in_area(point_list, area_list):
    if len(area_list) == 0: return False

    if cv2.pointPolygonTest(np.array(area_list), (point_list[0], point_list[1]), False) == 1 :
        return True
    
    else : return False


#침입
def detect_intrusion(camera_info, detect_area, person_bbox_list):
    """침입 검출 기준 : 사람 검출(bbox의 아래 중심점)이 3초 이상 지속될 경우 알림 발생"""
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_bottom_point(bbox)
            if check_box_in_area(detect_point, detect_area):
                if id_ not in camera_info["intr"]:
                    camera_info["intr"][id_] = [time.time(), -1]

                else:
                    if camera_info["intr"][id_][1] == -1 and time.time() - camera_info["intr"][id_][0] >= 3 : # 검출 시간 기준 3초 이상 침입이 지속될 경우 알림 발생
                        camera_info["intr"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Intrusion", id_, camera_info["intr"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"침입 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info  
#배회
def detect_loitering(camera_info, detect_area, person_bbox_list):
    """배회 검출 기준 : 사람 검출(bbox의 아래 중심점)이 10초 이상 지속될 경우 알림 발생"""
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_bottom_point(bbox)
            if check_box_in_area(detect_point, detect_area):
                if id_ not in camera_info["loit"].keys():
                    camera_info["loit"][id_] = [time.time(), -1]

                else:
                    if camera_info["loit"][id_][1] == -1 and time.time() - camera_info["loit"][id_][0] >= 10 : # 검출 시간 기준 10초 이상 배회가 지속될 경우 알림 발생
                        camera_info["loit"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Loitering", id_, camera_info["loit"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"배회 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def detect_falldown(camera_info, detect_area, person_bbox_list):
    """쓰러짐 검출 시작 기준 : 사람 이동 경로 점이(bbox의 중심점) 30개 이상 지속되고 이동 경로가 정지할 경우 판별 시작
       쓰러짐 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상(50점)일 경우 쓰러짐 검출 (비동기 API 요청)
       쓰러짐 알림 발생 기준 : 쓰러짐 검출이 10회 중 5회 이상 발생하고 5초 이상 지속될 경우 알림 발생
       """
    global SIGLIP_DETECTION_PENDING
    
    try:
        camera_name = camera_info["name"]
        
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_center_point(bbox)

            if check_box_in_area(detect_point, detect_area):
                if id_ in camera_info["person_info"].info.keys():
                    trejectory = camera_info["person_info"].info[id_]["trejectory"]
                    if len(trejectory) > 30 and check_stop_person(bbox, trejectory) and time.time() - camera_info["person_info"].info[id_]["request_time"] > 1:
                        # new_x1, new_y1, new_x2, new_y2, id_, conf, label, _ = make_square_bbox([x1, y1, x2, y2, id_, conf, cls, ind])

                        # person_img = camera_info["img"][int(new_y1) : int(new_y2), int(new_x1) : int(new_x2)]
                        person_img = camera_info["person_info"].info[id_]["img_crop"]
                        
                        # 이미지 유효성 검사
                        if person_img is None or not isinstance(person_img, np.ndarray) or person_img.size == 0:
                            logger.warning(f"쓰러짐 검출 - 유효하지 않은 이미지 (카메라: {camera_name}, ID: {id_})")
                            continue
                        
                        # 중복 요청 방지
                        if camera_name in SIGLIP_DETECTION_PENDING:
                            if id_ in SIGLIP_DETECTION_PENDING[camera_name]:
                                # logger.info(f"(쓰러짐) Siglip 결과 대기 중 - 카메라: {camera_name} ID: {id_}")
                                # logger.info(f"응답 대기 목록 {SIGLIP_DETECTION_PENDING[camera_name]}")
                                continue
                        
                        # texts = ["a photo of falldown person on ground.", 
                        #         "a photo of walking person on street", 
                        #         "a photo of riding person on street", 
                        #         "a photo of standing person on street", 
                        #         "a photo of sitting person on ground"]
                        texts = [
                                    "a photo of person collapsed on floor",
                                    "a person collapsed on their hands and knees",
                                    "a person crouching on the floor after falling",

                                    "a photo of walking person on floor", 
                                    "a photo of standing person on floor", 
                                    "a photo of sitting person on floor",
                                ]
                        
                        # 요청 상태 등록
                        if camera_name not in SIGLIP_DETECTION_PENDING:
                            SIGLIP_DETECTION_PENDING[camera_name] = {}
                        SIGLIP_DETECTION_PENDING[camera_name][id_] = True
                        
                        # 비동기 API 요청 시작
                        thread = threading.Thread(
                            target=send_siglip_detection_request,
                            args=(camera_name, person_img, texts, id_, "falldown"),
                            daemon=True
                        )
                        thread.start()
                        camera_info["person_info"].info[id_]["request_time"] = time.time()

                    else:
                        camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 0)


        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 쓰러짐 알람 기록 알고리즘 : 최근 쓰러짐 감지 기록 10회 중 5회 이상일 경우 검출 시간 기록
            status = camera_info["person_info"].get_status(int(id_), detect_type = "falldown")

            if status == 1 :
                if id_ not in camera_info["fall"].keys():
                    camera_info["fall"][id_]  = [time.time(), -1]

                else:
                    if camera_info["fall"][id_][1] == -1 and time.time() - camera_info["fall"][id_][0] > 5 : # 검출 시간 기준 5초 이상 쓰러짐이 지속될 경우 vlm QnA 시도
                        # VLM 요청 시작 (비동기)
                        # camera_info["person_info"].run_har_vlm(id_, detect_type = "lying person or fallen person")
                        # camera_info["fall"][id_][1] = 0
                        camera_info["fall"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Falldown", id_, camera_info["fall"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰러짐 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def detect_fight(camera_info, detect_area, person_bbox_list):
    """싸움 검출 시작 기준 : 사람의 bbox 하단 점이 검출 영역에 들어올 경우
       싸움 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상(30점)일 경우 싸움 검출 (비동기 API 요청)
       싸움 알림 발생 기준 : 싸움 검출이 10회 중 5회 이상 발생하고 3초 이상 지속될 경우 알림 발생
    """
    global SIGLIP_DETECTION_PENDING
    
    try:
        camera_name = camera_info["name"]
        
        if len(person_bbox_list):
            for x1, y1, x2, y2, id_, conf, label, _ in person_bbox_list:
                if x1 < 0 : x1 = 0
                if y1 < 0 : y1 = 0
                bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
                id_ = int(id_)

                detect_point =  get_bottom_point(bbox)

                if check_box_in_area(detect_point, detect_area):
                    # people_img = camera_info["img"][int(y1) : int(y2), int(x1) : int(x2)]
                    people_img = camera_info["person_info"].info[id_]["img_crop"]
                    
                    # 이미지 유효성 검사
                    if people_img is None or not isinstance(people_img, np.ndarray) or people_img.size == 0:
                        logger.warning(f"싸움 검출 - 유효하지 않은 이미지 (카메라: {camera_name}, ID: {id_})")
                        logger.warning(f"people_img: {type(people_img)}")
                        logger.warning(f"people_img: {people_img}")
                        continue
                    
                    # 중복 요청 방지
                    if camera_name in SIGLIP_DETECTION_PENDING:
                        if id_ in SIGLIP_DETECTION_PENDING[camera_name]:
                            # logger.info(f"(싸움) Siglip 결과 대기 중 - 카메라: {camera_name} ID: {id_}")
                            # logger.info(f"응답 대기 목록 {SIGLIP_DETECTION_PENDING[camera_name]}")
                            continue

                    texts = ["a photo of fighting people.",
                            "a photo of talking people on street",
                            "a photo of walking people on street", 
                            "a photo of standing people on street"]
                    
                    # 요청 상태 등록
                    if camera_name not in SIGLIP_DETECTION_PENDING:
                        SIGLIP_DETECTION_PENDING[camera_name] = {}
                    SIGLIP_DETECTION_PENDING[camera_name][id_] = True
                    
                    # 비동기 API 요청 시작
                    thread = threading.Thread(
                        target=send_siglip_detection_request,
                        args=(camera_name, people_img, texts, id_, "fight"),
                        daemon=True
                    )
                    thread.start()

                else:
                    camera_info["person_info"].update_status(id_, detect_type = "fight", status = 0) #정상 상태 할당

        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 싸움 알람 기록 알고리즘
            status = camera_info["person_info"].get_status(int(id_), detect_type = "fight")

            if status == 2 :
                if id_ not in camera_info["fight"].keys():
                    camera_info["fight"][id_]  = [time.time(), -1]

                else:
                    if camera_info["fight"][id_][1] == -1 and time.time() - camera_info["fight"][id_][0] > 3 : # 검출 시간 기준 3초 이상 싸움이 지속될 경우 알림 발생
                        # VLM 요청 시작 (비동기)
                        # camera_info["person_info"].run_har_vlm(id_, detect_type = "fight")
                        camera_info["fight"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Fight", id_, camera_info["fight"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"싸움 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def detect_fire(camera_info, detect_area, bbox):
    """방화 검출 시작 기준 : 불꽃에 대한 bbox가 검출 영역에서 발생할 경우
       방화 검출 기준 : 불꽃에 대한 bbox가 5초 이상 지속되고 30번 연속으로 발생할 경우 방화 검출
       방화 알림 발생 기준 : VLM에 QnA 요청 후 답변이 yes일 경우 알림 발생
    """
    try:
        detect_point =  get_center_point(bbox)
        fire_check_flag = 0

        if check_box_in_area(detect_point, detect_area):
            if len(camera_info["fire"]):
                for id, detect_info in camera_info["fire"].items():
                    iou = get_IOU(bbox, detect_info[3])

                    if iou > 0.5:
                        fire_check_flag = 1
                        detect_info[3] = bbox
                        detect_info[2] = time.time()

                        if detect_info[1] == -1 and time.time() - detect_info[0] > 5 and detect_info[4] > 30: # 최초 방화 검출 이후 10초 경과시 알람 발생
                            # TODO : 영상 vlm 기반 방화 검출 알고리즘 구현 예정 - 불꽃 이미지 버퍼 구현 필요
                            # response = camera_info["person_info"].run_har_vlm(id)

                            # if response: # vlm QnA 답변이 yes일 경우 알림 발생
                            #     detect_info[1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                            #     camera_info["alarm"].append(["Fire", id, detect_info[1]])

                            detect_info[1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                            camera_info["alarm"].append(["Fire", id, detect_info[1]])

                        else:
                            detect_info[4] += 1
                
                if fire_check_flag == 0:
                    camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox, 0]

            else:
                camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox, 0]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"방화 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def _is_bbox_in_polygon(bbox, polygon):
    """사각 박스를 기준으로 가로는 점 3개, 세로는 점 5개를 생성하여 겹쳤는지 확인"""
    if len(polygon) == 0:
        return False
    
    x1, y1, x2, y2 = bbox
    # 3 x 위치 (가로)
    x_points = np.linspace(x1, x2, 3)
    # 5 y 위치 (세로)
    y_points = np.linspace(y1, y2, 5)
    bbox_points = []
    for ix in x_points:
        for iy in y_points:
            bbox_points.append((ix, iy))
    bbox_points = np.array(bbox_points, dtype=np.float32)
    
    polygon_array = np.array(polygon, dtype=np.int32)
    return any(cv2.pointPolygonTest(polygon_array, (int(pt[0]), int(pt[1])), False) >= 0 for pt in bbox_points)

def detect_trash(camera_info, detect_area, person_bbox_list, non_person_bbox_list):
    global TRASH_DETECT_TIME, TRASH_DETECTION_PENDING
    """쓰레기 투기 검출 (비동기 처리 버전)
       검출 시작 기준: 사람이 ROI 영역에 침입했다가 벗어날 때
       검출 기준: API 서버로 비동기 요청을 보내고 결과를 기다림
       알림 발생 기준: API 응답에서 쓰레기 객체가 검출된 경우
    """
    try:
        img = camera_info["img"]

        fgmask = camera_info["MOG2"].apply(img)
        fgmask = cv2.erode(fgmask, None, iterations=2)
        # cv2.imshow("fgmask", fgmask)

        # person_info 초기화 (camera_info["trash_person_info"]에 저장)
        if "trash_person_info" not in camera_info:
            camera_info["trash_person_info"] = {}
        
        person_info = camera_info["trash_person_info"]
        camera_name = camera_info["name"]
        
        # main_enroll_img_info 찾기 (현재 ROI에 있는 사람 중 가장 오래된 등록 이미지)
        main_enroll_img_info = []
        main_enroll_id = -1
        
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            
            id_ = int(id_)
            bbox = [x1, y1, x2, y2]
            
            # 사람이 ROI와 겹치는지 확인
            is_intrusion = _is_bbox_in_polygon(bbox, detect_area)
            
            if is_intrusion and id_ in person_info:
                if len(main_enroll_img_info) == 0 and person_info[id_]['enroll_info'][0] != -1:
                    main_enroll_img_info = person_info[id_]['enroll_info']
                    main_enroll_id = id_
                else:
                    if len(main_enroll_img_info) and main_enroll_img_info[0] < person_info[id_]['enroll_info'][0]:
                        main_enroll_img_info = person_info[id_]['enroll_info']
                        main_enroll_id = id_
        
        # tracked objects 처리
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0: x1 = 0
            if y1 < 0: y1 = 0
            
            id_ = int(id_)
            bbox = [x1, y1, x2, y2]
            
            # 사람에 대해 관심영역 침입확인
            is_intrusion = _is_bbox_in_polygon(bbox, detect_area)
            
            if id_ not in person_info:
                person_info[id_] = {
                    'bbox': bbox,
                    'miss_count': 0,
                    'before_intrusion': False,
                    'is_intrusion': [is_intrusion, time.time()],
                    'enroll_info': [-1, None, []],
                    'delete_flag': False
                }
            else:
                person_info[id_]['bbox'] = bbox
                person_info[id_]['miss_count'] = 0
                person_info[id_]['is_intrusion'] = [is_intrusion, time.time()]
                
                # 관심영역에 침입하는 순간 투기 비교 이미지 등록
                if person_info[id_]['before_intrusion'] == False and is_intrusion:
                    person_info[id_]['before_intrusion'] = is_intrusion
                    
                    # 현재 관심영역에 사람이 침입해 있는 경우 해당 사람의 등록 이미지를 상속받음
                    if len(main_enroll_img_info):
                        # logger.info(f"쓰레기 검출 - ID {id_}: 비교이미지 상속(id: {main_enroll_id})")
                        person_info[id_]['enroll_info'] = main_enroll_img_info
                    else:
                        # logger.info(f"쓰레기 검출 - ID {id_}: 비교이미지 신규 등록")
                        person_info[id_]['enroll_info'] = [time.time(), camera_info["img"], bbox, fgmask]
        
        # ROI에 아무도 없을 때 쓰레기 검출 (API로 비동기 요청)
        if len(main_enroll_img_info) == 0:
            for id_ in list(person_info.keys()):
                # 관심영역에 침입 후 현재 관심영역에서 벗어난 경우 투기 감지 알고리즘 동작
                if (person_info[id_]['is_intrusion'][0] == False and 
                    person_info[id_]['before_intrusion'] == True and 
                    person_info[id_]['delete_flag'] == False):

                    if person_info[id_]['is_intrusion'][1] - TRASH_DETECT_TIME < 1: 
                        continue
                    
                    # 중복 요청 방지: 이미 요청 중인지 확인
                    if camera_name in TRASH_DETECTION_PENDING:
                        if id_ in TRASH_DETECTION_PENDING[camera_name]:
                            continue
                    
                    TRASH_DETECT_TIME = time.time()
                    # logger.info(f"쓰레기 검출 - ID {id_}: API 요청 시작")
                    person_info[id_]['delete_flag'] = True
                    
                    # API 요청 데이터 준비
                    people_bbox_for_api = [[float(x1), float(y1), float(x2), float(y2)] for (x1, y1, x2, y2, _, _, _, _) in person_bbox_list]
                    non_people_bbox_for_api = [[float(x1), float(y1), float(x2), float(y2)] for (x1, y1, x2, y2, _, _) in non_person_bbox_list]
                    
                    # detect_area를 float 리스트로 변환
                    detect_area_list = [[float(x), float(y)] for [x, y] in detect_area]
                    
                    # 요청 상태 등록
                    if camera_name not in TRASH_DETECTION_PENDING:
                        TRASH_DETECTION_PENDING[camera_name] = {}
                    TRASH_DETECTION_PENDING[camera_name][id_] = True
                    
                    # 비동기 API 요청 시작 (별도 스레드에서 실행)
                    thread = threading.Thread(
                        target=send_trash_detection_request,
                        args=(
                            camera_name,
                            detect_area_list,
                            # camera_info["img"].copy(),
                            camera_info["img"],
                            person_info[id_]['enroll_info'][1],
                            person_info[id_]['enroll_info'][0], #enroll_time
                            person_info[id_]['enroll_info'][2],
                            person_info[id_]['enroll_info'][3],
                            people_bbox_for_api,
                            non_people_bbox_for_api,
                            int(id_),
                            fgmask,
                        ),
                        daemon=True
                    )
                    thread.start()
                    # logger.info(f"쓰레기 검출 API 비동기 요청 시작 - 카메라: {camera_name}, Person ID: {id_}")
        
        # person_info 관리 (오래된 정보 삭제)
        del_id = []
        for id_ in list(person_info.keys()):
            person_info[id_]['miss_count'] += 1
            if person_info[id_]['miss_count'] >= 300 or person_info[id_]['delete_flag']:
                del_id.append(id_)
        
        for id_ in del_id:
            # logger.info(f"쓰레기 검출 - ID {id_}: 정보 삭제")
            del person_info[id_]

        if len(del_id) > 0:
            gc.collect()

        camera_info["trash_person_info"] = person_info
        
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰레기 검출 에러 발생 : {current_time}: {e}\n{tb}")
    
    finally:
        return camera_info

def detect_action(camera_info):
    person_bbox_list = camera_info["person_bbox"]
    non_person_bbox_list = camera_info["non_person_bbox"]

    """사람 기준 지능형 알고리즘 실행"""
    for detect_info in camera_info["TF_ROI"]:
        detect_type = detect_info[0]
        detect_area = detect_info[1:]

        if detect_type == "Intrusion":
            camera_info = detect_intrusion(
                camera_info =  camera_info, 
                detect_area = detect_area,
                person_bbox_list = person_bbox_list,
                )
            
        elif detect_type == "Loitering" :
            camera_info = detect_loitering(
                camera_info =  camera_info, 
                detect_area = detect_area,
                person_bbox_list = person_bbox_list,
                )
            
        elif detect_type == "Falldown":
            camera_info = detect_falldown(
                camera_info =  camera_info, 
                detect_area = detect_area,
                person_bbox_list = person_bbox_list,
                )

        
        elif detect_type == "Fight":
            camera_info = detect_fight(
                camera_info =  camera_info, 
                detect_area = detect_area,
                person_bbox_list = person_bbox_list,
                )

        elif detect_type == "Trash":
            camera_info = detect_trash(
                camera_info = camera_info,
                detect_area = detect_area,
                person_bbox_list = person_bbox_list,
                non_person_bbox_list = non_person_bbox_list,
                )

    for (x1, y1, x2, y2, conf, cls) in non_person_bbox_list:
        #방화
        if x1 < 0 : x1 = 0
        if y1 < 0 : y1 = 0

        if cls == 6:
            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            for detect_info in camera_info["TF_ROI"]:
                detect_type = detect_info[0]
                detect_area = detect_info[1:]

                if detect_type == "Fire" :
                    camera_info = detect_fire(
                        camera_info =  camera_info, 
                        detect_area = detect_area,
                        bbox = bbox,
                        )

    return camera_info

def check_vlm_responses(camera_info_dict):
    """모든 카메라의 VLM 응답을 확인하고 결과를 처리하는 함수"""
    try:
        for camera_num, camera_info in camera_info_dict.items():
            person_info = camera_info["person_info"]
            
            # 대기 중인 VLM 요청 확인
            pending_requests = person_info.get_pending_vlm_requests()
            
            for id_ in list(pending_requests.keys()):
                result, status = person_info.check_vlm_response(id_)
                
                if status == "completed":
                    # VLM 응답이 완료된 경우 결과 처리
                    process_vlm_result(camera_info, id_, result)
                    logger.info(f"VLM 요청 완료: camera={camera_info['name']}, id={id_}")

                elif status == "error":
                    logger.warning(f"VLM 요청 에러: camera={camera_info['name']}, id={id_}")
                elif status == "timeout":
                    logger.warning(f"VLM 요청 타임아웃: camera={camera_info['name']}, id={id_}")
                    
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"VLM 응답 확인 중 에러 발생: {current_time}: {e}\n{tb}")

def process_vlm_result(camera_info, id_, result):
    """VLM 응답 결과를 처리하여 camera_info 업데이트"""
    try:
        camera_name = camera_info["name"]
        
        # fight 검출 결과 처리
        if id_ in camera_info["fight"] and camera_info["fight"][id_][1] == -1:
            if result:  # VLM 응답이 True인 경우
                camera_info["fight"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                camera_info["alarm"].append(["Fight", id_, camera_info["fight"][id_][1]])
                logger.info(f"싸움 알림 발생: camera={camera_name}, id={id_}")
            else:
                # VLM 응답이 False인 경우 60초 후 다시 검출 시도
                camera_info["fight"][id_][0] = time.time() + 60
                logger.info(f"VLM 싸움 검출 실패, 60초 후 재시도: camera={camera_name}, id={id_}")
        
        # falldown 검출 결과 처리
        elif id_ in camera_info["fall"] and camera_info["fall"][id_][1] == -1:
            if result:  # VLM 응답이 True인 경우
                camera_info["fall"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                camera_info["alarm"].append(["Falldown", id_, camera_info["fall"][id_][1]])
                logger.info(f"쓰러짐 알림 발생: camera={camera_name}, id={id_}")
            else:
                # VLM 응답이 False인 경우 30초 후 다시 검출 시도
                camera_info["fall"][id_][0] = time.time() + 30
                logger.info(f"VLM 쓰러짐 검출 실패, 60초 후 재시도: camera={camera_name}, id={id_}")
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"VLM 결과 처리 중 에러 발생: {current_time}: {e}\n{tb}")

def update_plot_person_bbox(camera_info_dict):
    for camera_num, camera_info in camera_info_dict.items():
        camera_info["plot_person_bbox"] = []
        for (x1, y1, x2, y2, id_, conf, cls, ind) in camera_info["person_bbox"]:
            if conf > camera_info["object_conf_score"][0] and cls == 0:
                camera_info["plot_person_bbox"].append([x1, y1, x2, y2, id_, conf, cls, ind])

    return camera_info_dict


def ms_ai(camera_info_dict_ori, NVR_info, weight_name):
    camera_info_dict = {}
    start_time = time.time()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    NVR_ID = NVR_info["ID"]
    NVR_PW = NVR_info["PW"]
    NVR_IP = NVR_info["IP"]

    HOST = "127.0.0.1"
    PORT = 65432

    ROI_color_dict = {"Loitering": [53, 225, 225], 
                        "Intrusion": [35, 28, 255], 
                        "Fire": [33, 145, 237],
                        "Fight": [255, 0, 127], 
                        "Falldown": [230, 255, 121], 
                        "Trash": [0, 165, 255]
                        }

    interval = 1.0 / 30

    for camera_name, camera_info in camera_info_dict_ori.items():
        num = camera_info["Num"]

        if len(camera_info["detect_info"]):        
            # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'
            # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'
            # pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'
            pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'

            logger.info(f"Attempting to connect to video stream: {pipe}")
            
            cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                
            # cap = cv2.VideoCapture(pipe)

            disconnect_cnt = 0
            no_connect_cnt = 0 
            time.sleep(1)
            ret, frame = cap.read()

            while ret == False :
                ret, frame = cap.read()

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Try connect {pipe}")
                time.sleep(1)
                disconnect_cnt += 1

                if no_connect_cnt > 2:
                    logger.error(f"Failed to connect to {pipe} after multiple attempts")
                    break

                if disconnect_cnt > 60 :
                    no_connect_cnt += 1
                    del cap
                    gc.collect()
                    
                    try:
                        cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                        time.sleep(5)
                    except Exception as e:
                        logger.error(f"Failed to reconnect to {pipe}: {e}")
                        break

            if ret == False:
                logger.error(f"Unable to establish connection to {pipe}, skipping camera")
                continue
                
            logger.info(f"Successfully connected to {pipe}")

            tracker = boxmot.BotSort(reid_weights = Path(os.getcwd() + "/../weights/ReID/osnet_ain_x1_0_msmt17.pt"),
                                     device = device,
                                     half=True,
                                    per_class=False,
                                    track_high_thresh=0.4,       # 낮춘 값
                                    track_low_thresh=0.05,       # 낮춘 값
                                    new_track_thresh=0.5,        # 낮춘 값
                                    track_buffer=300,             # 늘린 값
                                    match_thresh=0.7,            # 낮춘 값
                                    proximity_thresh=0.4,        # 낮춘 값
                                    appearance_thresh=0.2,       # 낮춘 값
                                    cmc_method="ecc",
                                    frame_rate=30,
                                    fuse_first_associate=True,   # 변경된 값
                                    with_reid=True,)
            
            # tracker = boxmot.BYTETracker(track_thresh=camera_info["Conf"] / 100, 
            #                             match_thresh=0.8, 
            #                             track_buffer=150, 
            #                             frame_rate=30, 
            #                             per_class=False)   

            active_detect_info, active_roi = get_active_info(camera_info["detect_info"], camera_info["detect_schedule"])

            TF_detect_info = TF_detect_area(
                detect_info = active_roi, 
                img_size  = (cap._frame.shape[1], cap._frame.shape[0])
                )

            detect_cls_list = []

            if camera_info["Cls"][0]: detect_cls_list += [0]
            if camera_info["Cls"][1]: detect_cls_list += [1,2,3,4,5]
            if camera_info["Cls"][2]: detect_cls_list += [6]

            logger.info(f"camera_name: {camera_name}, active_roi: {[roi[0] for roi in active_roi]}, detect_cls_list: {detect_cls_list}")

            camera_info_dict[num] = {"cap" : cap,
                                    "name" : camera_name,
                                    "detect_cls" : detect_cls_list,
                                    "object_conf_score" : np.array(camera_info["Conf"]) / 100,
                                    "tracker" : tracker,
                                    "ROI_ori" : active_roi,                 # 정규화된 ROI 좌표 normalized(0 ~ 1) [detect class, [x1,y1], [xn,yn]]
                                    "TF_ROI" : TF_detect_info,              # [detect class, [x1,y1], [xn,yn]]
                                    "img" : np.zeros([480,640,3]),          # Img
                                    "person_bbox" : [],                     # Person bbox list
                                    "plot_person_bbox" : [],                # Plot Person bbox list
                                    "non_person_bbox" : [],                 # non person bbox list
                                    "alarm" : [],                           # Detect Alarm
                                    "loit" : {},                            # 배회 검출정보 list 
                                    "intr" : {},                            # 침입 검출정보 list
                                    "fall" : {},                            # 쓰러짐 검출정보 list
                                    "fire" : {},                            # 방화 검출정보 list
                                    "fight" : {},                           # 싸움 검출정보 list
                                    "trash" : {},                           # 쓰레기 검출정보 list
                                    "person_info" : Person_Info(host = HOST,
                                                                camera_name = camera_name), 
                                    }
            if active_detect_info["Trash"] == 1:
                camera_info_dict[num]["MOG2"] = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

    conf_score = 0.05
    model_name = f"ms-ai_{weight_name[2:]}-M"
    yolo_model_path_dict = {0 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}1.engine",
                            1 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}1.engine",
                            2 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}2.engine",
                            3 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}3.engine",
                            4 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}4.engine"}
    
    
    # yolo_model_path = yolo_model_path_dict[len(camera_info_dict)]  # load a pretrained model (recommended for training)
    yolo_model_path = str(os.getcwd()) + f"/../weights/yolo/{weight_name}/{model_name}.pt"

    model = YOLO(yolo_model_path, task="detect")  # load a pretrained model (recommended for training)\

    start_time = time.time()

    while len(camera_info_dict):
        # next_time = time.time()

        img_list = []
        camera_num_list = []
        t0 = time.time()

        for camera_num, camera_info in camera_info_dict.items():
            ret, img = camera_info["cap"].read()

            if ret:
                img_list.append(img)
                camera_num_list.append(camera_num)
                camera_info_dict[camera_num]["img"] = img

            else:
                pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'

                logger.info(f"Attempting to reconnect to video stream: {pipe}")
                cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                
                time.sleep(0.5)
                if cap.frame_available():
                    camera_info_dict[camera_num]["cap"] = cap

                img_list.append(np.zeros([480,640,3]))


        if len(img_list):
            dets = model.predict(source=img_list, 
                                    imgsz = 640, 
                                    conf = 0.05, 
                                    classes = [0, 1, 2, 3, 4, 5, 6], 
                                    half = True, 
                                    verbose = False)
            t1 = time.time()
            bn_person_boxes, bn_non_person_boxes = remove_out_of_BBox(
                camera_info_dict = camera_info_dict, 
                bbox_bn= dets,
                camera_num_list = camera_num_list
                )
            
            for index, bbox in enumerate(bn_person_boxes):
                camera_info_dict[camera_num_list[index]]["person_bbox"] = camera_info_dict[camera_num_list[index]]["tracker"].update(bbox, img_list[index])
                camera_info_dict[camera_num_list[index]]["non_person_bbox"] = bn_non_person_boxes[index]

                try: 
                    """사람의 bbox정보, 이동 경로, 검출 시간 갱신"""
                    camera_info_dict[camera_num_list[index]]["person_info"].update_id(
                        img = img_list[index],
                        track_info = camera_info_dict[camera_num_list[index]]["person_bbox"]
                        )
                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tb = traceback.format_exc()
                    logger.error(f"사람 정보 갱신 실패 : {current_time}: {e}\n{tb}")

            for camera_num, camera_info in camera_info_dict.items():
                """지능형 알고리즘 실행"""
                camera_info = detect_action(
                    camera_info = camera_info,
                    )
                # print(camera_name)
                # print(camera_info[7])

            # VLM 응답 확인 및 처리
            # check_vlm_responses(camera_info_dict)
            
            # SigLip 검출 비동기 요청 결과 확인 및 처리
            check_siglip_detection_results(camera_info_dict)
            
            # 쓰레기 검출 비동기 요청 결과 확인 및 처리
            check_trash_detection_results(camera_info_dict)

            t2 = time.time()

            
            # print(f"total : {1/(time.time() - t0)}")
            # print(f"t1 : {1/(t1 - t0)}")
            # print(f"t2 : {1/(t2 - t1)}")

            camera_info_dict = update_plot_person_bbox(
                camera_info_dict = camera_info_dict, 
                )

            send_alarm_NVR(
                nvr_ip = NVR_IP,
                nvr_id = NVR_ID, 
                nvr_pw = NVR_PW, 
                camera_info_dict = camera_info_dict,
                ROI_color_dict = ROI_color_dict,
                object_color_dict = COLOR
                )

            send_SERVER_ai_info(
                host = HOST,
                port = PORT,
                camera_info_dict = camera_info_dict,
                nvr_ip = NVR_IP,
                )
            
            camera_info_dict = camera_info_refresh(
                camera_info_dict = camera_info_dict,
                )

            if time.time() - start_time > 60: #60초 마다 미활동 점유 메모리 초기화
                gc.collect()
                start_time = time.time()

            # print(f"fps : {1/(time.time() - t0)}")

            if time.time() - t0 > 1/30:
                continue
            else:
                try:
                    sleep_time = 1/30 - (time.time() - t0)
                    time.sleep(sleep_time)
                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tb = traceback.format_exc()
                    logger.error(f"시간 조정 실패 : {sleep_time}: {e}\n{tb}")
            # next_time += interval
            # sleep_time = next_time - time.time()

            # if sleep_time > 0:
            #     time.sleep(sleep_time)
            # else:
            #     # 작업이 예상 시간보다 오래 걸린 경우
            #     next_time = time.time()

