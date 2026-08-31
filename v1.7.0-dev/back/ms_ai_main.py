
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
                        camera_info_refresh, get_IOU, send_SERVER_ai_info, send_SERVER_ai_info_batch,
                        get_active_info, check_stop_person, send_ai_info_via_manager)

from ultralytics import YOLO
import boxmot
import cv2
# cv2.namedWindow("people_img", cv2.WINDOW_NORMAL)
# cv2.resizeWindow("people_img", 448, 448)

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging(logger_name="MS_AI_MAIN", log_file="MS_AI_MAIN.log")


KST = timezone(timedelta(hours=9))


TRASH_DETECT_TIME = time.time()

# 쓰레기 검출 비동기 요청 관리를 위한 전역 변수
TRASH_DETECTION_PENDING = {}  # {camera_name: {person_id: request_data}}
TRASH_DETECTION_RESULTS = {}  # {camera_name: {person_id: [alarms]}}

siglip_model = None
siglip_processor = None
siglip_text_embeddings = {}  # 텍스트 임베딩 캐시 (falldown, fight)

object_color_dict =  {
    0: "#669900",  # person
    1: "#fff200",  # bicycle
    2: "#4682B4",  # car
    3: "#FF8C00",  # motorcycle
    4: "#9370DB",  # bus
    5: "#48D1CC",  # truck
    6: "#FF1493"   # fire
}
# class Video_Buffer:
#     def __init__(self, pipe="video1", appsink_name="video_sink", resolution = (640, 480)):
#         self._frame = None
#         self.pipe = pipe
#         self.appsink_name = appsink_name
#         self.video_pipe = None
#         self.video_sink = None
#         # self.video_source = f'rtspsrc location=rtsp://{pipe} latency=10 buffer-mode=0 protocols=tcp'
#         self.video_source = f'rtspsrc location={pipe} latency=30'

#         self.video_codec = '! rtph264depay ! h264parse '  # 'application/x-rtp' 생략
#         # Try hardware decoding first, fallback to software if needed
#         try:
#             # First try NVIDIA hardware decoding
#             # self.video_decode = f'! nvh264dec ! videoscale ! video/x-raw,width=1280,height=720 ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
#             self.video_decode = f'! nvh264dec ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
            
#         except:
#             # Fallback to software decoding
#             self.video_decode = f'!decodebin ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
        
#         self.run()

#     def start_gst(self, config=None):
#         command = ' '.join(config)
#         self.video_pipe = Gst.parse_launch(command)
#         self.video_pipe.set_state(Gst.State.PLAYING)
#         self.video_sink = self.video_pipe.get_by_name(self.appsink_name)
        
#         if not self.video_sink:
#             print(f"Failed to get appsink named {self.appsink_name}")
#             return
        
#         self.video_sink.set_property("emit-signals", True)
#         self.video_sink.set_property("sync", False)

#     @staticmethod
#     def gst_to_opencv(sample):
#         buf = sample.get_buffer()
#         caps = sample.get_caps()
#         array = np.ndarray(
#             (
#                 caps.get_structure(0).get_value('height'),
#                 caps.get_structure(0).get_value('width'),
#                 3
#             ),
#             buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
#         return array

#     def read(self):
#         if self.frame_available():
#             return self.frame_available(), self._frame
#         else:
#             return self.frame_available(), np.zeros((640, 480, 3), dtype=np.uint8)

#     def frame_available(self):
#         return self._frame is not None

#     def run(self):
#         try:
#             self.start_gst(
#                 [
#                     self.video_source,
#                     self.video_codec,
#                     self.video_decode
#                 ]
#             )
#             if self.video_sink:
#                 self.video_sink.connect('new-sample', self.callback)

#             bus = self.video_pipe.get_bus()
#             bus.add_signal_watch()
#             bus.connect("message", self.on_message)
#         except Exception as e:
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             tb = traceback.format_exc()
#             logger.error(f"Error occurred at {current_time}: {e}\n{tb}")

#     def on_message(self, bus, message):
#         t = message.type
#         if t == Gst.MessageType.ERROR or t == Gst.MessageType.EOS:
#             self.video_pipe.set_state(Gst.State.NULL)
#             self.run()

#     def callback(self, sink):
#         sample = sink.emit('pull-sample')
#         new_frame = self.gst_to_opencv(sample)
#         self._frame = new_frame

#         return Gst.FlowReturn.OK

#     def release(self):
#         self.video_pipe.set_state(Gst.State.NULL)

class Video_Buffer:
    def __init__(self, pipe="video1", appsink_name="video_sink", resolution=(640, 480)):
        self._frame = None
        self.pipe = pipe
        self.appsink_name = appsink_name
        self.video_pipe = None
        self.video_sink = None
        
        # [수정 1] 타임아웃 설정을 위한 변수 추가
        self.last_frame_time = time.time()  # 마지막 프레임 수신 시간
        self.timeout_sec = 10.0             # 10초 동안 프레임 없으면 재접속
        self.resolution = resolution
        
        # rtspsrc에 drop-on-latency=true 추가 권장 (지연 시 프레임 드랍하여 최신성 유지)
        self.video_source = f'rtspsrc location={pipe} latency=30 drop-on-latency=true'

        self.video_codec = '! rtph264depay ! h264parse '
        
        # 디코딩 파이프라인 문자열 미리 생성
        # try:
            # NVIDIA 하드웨어 디코딩
        self.video_decode = f'! nvh264dec ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
        # except:
            # 소프트웨어 디코딩 폴백
            # self.video_decode = f'! decodebin ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
        
        self.run()

    def start_gst(self, config=None):
        command = ' '.join(config)
        logger.info(f"Starting GStreamer pipeline: {command}")
        
        try:
            self.video_pipe = Gst.parse_launch(command)
            self.video_pipe.set_state(Gst.State.PLAYING)
            self.video_sink = self.video_pipe.get_by_name(self.appsink_name)
            
            if not self.video_sink:
                logger.error(f"Failed to get appsink named {self.appsink_name}")
                return
            
            self.video_sink.set_property("emit-signals", True)
            self.video_sink.set_property("sync", False)
            
            # [수정 2] 파이프라인 시작 시 시간 초기화 (무한 재부팅 방지)
            self.last_frame_time = time.time()
            
        except Exception as e:
            logger.error(f"Failed to start GST: {e}")

    @staticmethod
    def gst_to_opencv(sample):
        buf = sample.get_buffer()
        caps = sample.get_caps()
        
        # 캡슐화된 구조체에서 너비/높이 가져오기 안전하게 처리
        structure = caps.get_structure(0)
        h = structure.get_value('height')
        w = structure.get_value('width')
        
        array = np.ndarray(
            (h, w, 3),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def read(self):
        # [수정 3] 프레임을 읽을 때마다 타임아웃 체크 수행
        self.check_watchdog()

        if self.frame_available():
            return True, self._frame
        else:
            return False, np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)

    def frame_available(self):
        return self._frame is not None

    # [수정 4] Watchdog 로직 구현
    def check_watchdog(self):
        current_time = time.time()
        elapsed = current_time - self.last_frame_time

        # 타임아웃 시간 초과 시 재시작
        if elapsed > self.timeout_sec:
            logger.warning(f"RTSP Stream Timeout ({elapsed:.1f}s > {self.timeout_sec}s). Restarting...")
            self.restart()

    def restart(self):
        # 안전하게 기존 파이프라인 해제 후 재시작
        self.release()
        time.sleep(1) # 리소스 정리 대기
        self.run()
        # 재시작 직후 타임아웃 걸리지 않도록 시간 갱신
        self.last_frame_time = time.time()

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

            if self.video_pipe:
                bus = self.video_pipe.get_bus()
                bus.add_signal_watch()
                bus.connect("message", self.on_message)
                
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            logger.error(f"Error occurred at {current_time}: {e}\n{tb}")

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"GStreamer Error: {err}, {debug}")
            self.restart()
        elif t == Gst.MessageType.EOS:
            logger.info("End of Stream")
            self.restart()

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame
        
        # [수정 5] 프레임이 정상적으로 들어오면 시간 갱신 (Heartbeat 역할)
        self.last_frame_time = time.time()

        return Gst.FlowReturn.OK

    def release(self):
        if self.video_pipe:
            self.video_pipe.set_state(Gst.State.NULL)
            self.video_pipe = None
        self._frame = None # 프레임 초기화

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
                for _, camera_info in camera_info_dict.items():
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

def precompute_text_embeddings():
    """SigLip 모델의 텍스트 임베딩을 사전 계산하는 함수"""
    global siglip_model, siglip_processor, siglip_text_embeddings
    
    if siglip_model is None or siglip_processor is None:
        logger.error("SigLip 모델이 로드되지 않아 텍스트 임베딩 사전 계산 불가")
        return
    
    # Falldown 텍스트
    falldown_texts = [
                "a photo of person collapsed on floor",
                "a photo of person collapsed on ground",
                "a photo of a person crouched on the ground after falling",
                "a photo of a person crouched on the floor after falling",

                "a photo of person walking on ground", 
                "a photo of person walking on floor", 

                "a photo of person standing on floor", 
                "a photo of person standing on ground", 

                "a photo of person sitting on ground",
                "a photo of person sitting on floor",
                "a photo of person sitting in chair",
                "a photo of person sitting in wheelchair",
    ]
    
    # Fight 텍스트
    fight_texts = [
        "a photo of fighting people.",
        "a photo of talking people on street",
        "a photo of walking people on street", 
        "a photo of standing people on street"
    ]
    
    try:
        with torch.no_grad():
            # Falldown 텍스트 임베딩
            falldown_inputs = siglip_processor(text=falldown_texts, padding="max_length", return_tensors="pt")
            falldown_text_embeds = siglip_model.get_text_features(**falldown_inputs.to("cuda"))
            # L2 정규화 적용
            falldown_text_embeds = falldown_text_embeds / falldown_text_embeds.norm(p=2, dim=-1, keepdim=True)
            siglip_text_embeddings["falldown"] = {
                "texts": falldown_texts,
                "embeddings": falldown_text_embeds
            }
            
            # Fight 텍스트 임베딩
            fight_inputs = siglip_processor(text=fight_texts, padding="max_length", return_tensors="pt")
            fight_text_embeds = siglip_model.get_text_features(**fight_inputs.to("cuda"))
            # L2 정규화 적용
            fight_text_embeds = fight_text_embeds / fight_text_embeds.norm(p=2, dim=-1, keepdim=True)
            siglip_text_embeddings["fight"] = {
                "texts": fight_texts,
                "embeddings": fight_text_embeds
            }
        
        logger.info("SigLip 텍스트 임베딩 사전 계산 완료")
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"SigLip 텍스트 임베딩 사전 계산 실패: {e}\n{tb}")


def detect_siglip(person_img, embed_type="falldown"):
    """SigLip 모델로 이미지-텍스트 유사도를 분석하는 함수 (사전 계산된 텍스트 임베딩 사용)"""
    global siglip_model, siglip_processor, siglip_text_embeddings
    
    try:
        if siglip_model is None or siglip_processor is None:
            logger.error("SigLip 모델이 로드되지 않음")
            return None
        
        if embed_type not in siglip_text_embeddings:
            logger.error(f"사전 계산된 텍스트 임베딩을 찾을 수 없음: {embed_type}")
            return None
        
        # 이미지 유효성 검사
        if person_img is None:
            logger.error("SigLip 검출 실패 - person_img가 None입니다.")
            return None
        
        if not isinstance(person_img, np.ndarray):
            logger.error(f"SigLip 검출 실패 - person_img가 numpy array가 아닙니다. Type: {type(person_img)}")
            return None
        
        if person_img.size == 0:
            logger.error("SigLip 검출 실패 - person_img가 비어있습니다.")
            return None
        
        # OpenCV BGR을 PIL RGB로 변환
        img_rgb = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb.astype('uint8'), 'RGB')
        
        t0_siglip = time.time()
        # 이미지만 처리 (사전 계산된 텍스트 임베딩 사용)
        image_inputs = siglip_processor(images=pil_img, return_tensors="pt")
        
        # 사전 계산된 텍스트 임베딩 가져오기
        text_embeds = siglip_text_embeddings[embed_type]["embeddings"]
        
        with torch.no_grad():
            with torch.autocast("cuda"):
                # 이미지 임베딩 추출
                image_embeds = siglip_model.get_image_features(**image_inputs.to("cuda"))
                # L2 정규화 적용
                image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
                
                # 유사도 계산 (SigLip sigmoid 기반)
                logits_per_image = torch.matmul(image_embeds, text_embeds.T) * siglip_model.logit_scale.exp() + siglip_model.logit_bias
                probs = torch.sigmoid(logits_per_image)
        
        # 결과를 리스트로 변환
        probs_list = probs[0].cpu().tolist()
        # logger.info(f"SigLip 검출 완료 - 소요시간: {time.time() - t0_siglip:.2f}s")
        return probs_list
        
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"SigLip 검출 에러 at {current_time}: {e}\n{tb}")
        return None

def process_siglip_falldown_result(camera_info, person_id, probs, texts):
    """SigLip 쓰러짐 검출 결과를 처리하는 함수"""
    camera_name = camera_info["name"]

    # 검출 결과 상세 출력
    if True:
        print(f"person_id: {person_id}")
        for text, detection in zip(texts, probs):
            print(f"    - {text}: {detection*100:.2f}%")
    
    if len(probs) >= 4:
        # 조건1: probs[0] > 0.50 이고 나머지 모든 확률이 0.3 미만
        if np.max([probs[0], probs[1]]) > 0.85 and np.max([probs[2], probs[3]]) > 0.05 and all(p < 0.05 for p in probs[4:8]) and all(p < 0.25 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건1) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건2: 앉아있을 때 검출되는 경우
        elif np.max([probs[0], probs[1]]) > 0.80 and np.max([probs[2], probs[3]]) > 0.50 and all(p < 0.05 for p in probs[4:8]) and all(p < 0.45 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건2) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건3
        elif np.max([probs[0], probs[1]]) > 0.70 and np.max([probs[2], probs[3]]) > 0.10 and all(p < 0.04 for p in probs[4:8]) and all(p < 0.15 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건3) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건4
        elif np.max([probs[0], probs[1]]) > 0.50 and np.max([probs[2], probs[3]]) > 0.20 and all(p < 0.03 for p in probs[4:8]) and all(p < 0.05 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건4) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건5
        elif np.max([probs[0], probs[1]]) > 0.2 and np.max([probs[2], probs[3]]) > 0.15 and all(p < 0.01 for p in probs[4:8]) and all(p < 0.01 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건5) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건6 오검출 감소를 위한 억제
        # elif np.max([probs[0], probs[1]]) > 0.1 and all(p < 0.004 for p in probs[4:]):
        #     camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
        #     logger.info(f"쓰러짐 검출(조건6) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건7
        elif np.max([probs[0], probs[1]]) > 0.95 and np.max([probs[2], probs[3]]) > 0.90 and all(p < 0.60 for p in probs[8:]):
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건7) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        # 조건8
        elif np.max([probs[0], probs[1]]) > 0.99 and np.max([probs[2], probs[3]]) > 0.80:
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건8) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        elif np.max([probs[0], probs[1]]) > 0.70 and np.max([probs[2], probs[3]]) > 0.65:
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=1)
            logger.info(f"쓰러짐 검출(조건9) - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        else:
            camera_info["person_info"].update_status(person_id, detect_type="falldown", status=0)

def process_siglip_fight_result(camera_info, person_id, probs, texts):
    """SigLip 싸움 검출 결과를 처리하는 함수"""
    camera_name = camera_info["name"]
    
    if True:
        print(f"person_id: {person_id}")
        for text, detection in zip(texts, probs):
            print(f"    - {text}: {detection*100:.2f}%")
    

    if len(probs) >= 1:
        if probs[0] > 0.1:
            camera_info["person_info"].update_status(person_id, detect_type="fight", status=2)
            logger.info(f"싸움 검출 - 카메라: {camera_name}, ID: {person_id}, 확률: {np.round(probs, 2)}")
        else:
            camera_info["person_info"].update_status(person_id, detect_type="fight", status=0)

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
       쓰러짐 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상 일 경우 쓰러짐 검출 
       쓰러짐 알림 발생 기준 : 최근 쓰러짐 검출이 중 3회 이상 발생하고 5초 이상 지속될 경우 알림 발생
       """
    try:
        camera_name = camera_info["name"]
        
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            center_point = get_center_point(bbox)
            corner_points = [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]  # 좌상, 우상, 좌하, 우하
            detect_points = [center_point] + corner_points  # 중심점 + 모서리 4개

            if all(check_box_in_area(pt, detect_area) for pt in detect_points):
                if id_ in camera_info["person_info"].info.keys() :
                    trejectory = camera_info["person_info"].info[id_]["trejectory"]
                    if len(trejectory) > 30 and check_stop_person(bbox, trejectory) :
                        if time.time() - camera_info["person_info"].info[id_]["request_time"] > 1 :
                            person_img = camera_info["person_info"].info[id_]["img_crop"]
                            
                            # 이미지 유효성 검사
                            if person_img is None or not isinstance(person_img, np.ndarray) or person_img.size == 0:
                                logger.warning(f"쓰러짐 검출 - 유효하지 않은 이미지 (카메라: {camera_name}, ID: {id_})")
                                continue
                            
                            # 동기식 SigLip 분석 수행 (사전 계산된 텍스트 임베딩 사용)
                            # cv2.imshow("people_img", person_img)
                            # cv2.waitKey(1)
                            probs = detect_siglip(person_img, embed_type="falldown")
                            
                            if probs is not None:
                                # 결과 처리
                                camera_info["person_info"].info[id_]["request_time"] = time.time()
                                texts = siglip_text_embeddings["falldown"]["texts"]
                                process_siglip_falldown_result(camera_info, id_, probs, texts)
                            else:
                                camera_info["person_info"].update_status(id_, detect_type="falldown", status=0)

                    else:
                        camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 0)


        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 쓰러짐 알람 기록 알고리즘 : 최근 쓰러짐 감지 기록 10회 중 3회 이상일 경우 검출 시간 기록
            status = camera_info["person_info"].get_status(int(id_), detect_type = "falldown")

            if status == 1 :
                if id_ not in camera_info["fall"].keys():
                    camera_info["fall"][id_]  = [time.time(), -1]

                else:
                    if camera_info["fall"][id_][1] == -1 and time.time() - camera_info["fall"][id_][0] > 10 : # 검출 시간 기준 기준 초 이상 지속될 경우 쓰러짐 감지
                        camera_info["fall"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Falldown", id_, camera_info["fall"][id_][1]])
                        logger.info(f"쓰러짐 검출 - 카메라: {camera_name}, ID: {id_}, 검출 시간: {camera_info['fall'][id_][1]}")

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰러짐 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def detect_fight(camera_info, detect_area, person_bbox_list):
    """싸움 검출 시작 기준 : 사람의 bbox 하단 점이 검출 영역에 들어올 경우
       싸움 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상(30점)일 경우 싸움 검출 (동기식)
       싸움 알림 발생 기준 : 싸움 검출이 10회 중 5회 이상 발생하고 3초 이상 지속될 경우 알림 발생
    """
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
                    people_img = camera_info["person_info"].info[id_]["img_crop"]
                    
                    # 이미지 유효성 검사
                    if people_img is None or not isinstance(people_img, np.ndarray) or people_img.size == 0:
                        logger.warning(f"싸움 검출 - 유효하지 않은 이미지 (카메라: {camera_name}, ID: {id_})")
                        continue

                    # 동기식 SigLip 분석 수행 (사전 계산된 텍스트 임베딩 사용)
                    # cv2.imshow("people_img", people_img)
                    # cv2.waitKey(1)
                    probs = detect_siglip(people_img, embed_type="fight")
                    
                    if probs is not None:
                        # 결과 처리
                        texts = siglip_text_embeddings["fight"]["texts"]
                        process_siglip_fight_result(camera_info, id_, probs, texts)
                    else:
                        camera_info["person_info"].update_status(id_, detect_type="fight", status=0)

                else:
                    camera_info["person_info"].update_status(id_, detect_type = "fight", status = 0) #정상 상태 할당

        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 싸움 알람 기록 알고리즘
            status = camera_info["person_info"].get_status(int(id_), detect_type = "fight")

            if status == 2 :
                if id_ not in camera_info["fight"].keys():
                    camera_info["fight"][id_]  = [time.time(), -1]

                else:
                    if camera_info["fight"][id_][1] == -1 and time.time() - camera_info["fight"][id_][0] > 3 : # 검출 시간 기준 3초 이상 싸움이 지속될 경우 알림 발생
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

                    if iou > 0.1:
                        fire_check_flag = 1
                        detect_info[3] = bbox
                        

                        if detect_info[1] == -1 and time.time() - detect_info[0] > 30 and detect_info[4] > 30: # 최초 방화 검출 이후 30초 경과시 알람 발생
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
                    bbox_extend = extend_bbox(bbox, 1.5)
                    camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox_extend, 0]

            else:
                bbox_extend = extend_bbox(bbox, 1.5)
                camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox_extend, 0]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"방화 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_info

def extend_bbox(bbox, extend_ratio = 1.5):
    x1, y1, x2, y2 = bbox

    width = x2 - x1
    height = y2 - y1
    max_side = max(width, height) * extend_ratio  # Increase by 1.3 times
    
    # Calculate the center of the bounding box
    x1 = x1 - max_side / 2
    y1 = y1 - max_side / 2
    x2 = x2 + max_side / 2
    y2 = y2 + max_side / 2
    
    return [x1, y1, x2, y2]

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
    for _, camera_info in camera_info_dict.items():
        camera_info["plot_person_bbox"] = []
        for (x1, y1, x2, y2, id_, conf, cls, ind) in camera_info["person_bbox"]:


            if conf > camera_info["object_conf_score"][0] and cls == 0:
                camera_info["plot_person_bbox"].append([x1, y1, x2, y2, id_, conf, cls, ind])

    return camera_info_dict

def find_nvr_info(NVR_info_dict, camera_name):
    for nvr_ip, nvr_info in NVR_info_dict.items():
        if camera_name in nvr_info["cameras"].keys():
            return nvr_info["id"], nvr_info["pw"], nvr_ip
    return None, None, None

def ms_ai(camera_info_dict_ori, NVR_info, weight_name, shared_data=None):
    global siglip_model, siglip_processor
    
    camera_info_dict = {}
    start_time = time.time()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


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

    camera_name_to_num = {}
    num_to_camera_name = {}
    num = 0

    for camera_name, camera_info in camera_info_dict_ori.items():
        camera_name_to_num[camera_name] = num
        num_to_camera_name[num] = camera_name
        num += 1
        
        NVR_ID, NVR_PW, NVR_IP = find_nvr_info(NVR_info, camera_name)

        if len(camera_info["detect_info"]):        
            # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'
            # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'
            # pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'
            pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{camera_info["camera_id"]}'
            # pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/video{camera_info["camera_id"]}'


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
                                    new_track_thresh=0.01,        # 낮춘 값
                                    track_buffer=300,             # 늘린 값
                                    match_thresh=0.7,            # 낮춘 값
                                    proximity_thresh=0.4,        # 낮춘 값
                                    appearance_thresh=0.2,       # 낮춘 값
                                    cmc_method="ecc",
                                    frame_rate=30,
                                    fuse_first_associate=True,   # 변경된 값
                                    with_reid=True,)
            
            # tracker = boxmot.ByteTrack(track_thresh=camera_info["Conf"] / 100, 
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

            if camera_info["cls"][0]: detect_cls_list += [0]
            if camera_info["cls"][1]: detect_cls_list += [1,2,3,4,5]
            if camera_info["cls"][2]: detect_cls_list += [6]

            logger.info(f"camera_name: {camera_name}, active_roi: {[roi[0] for roi in active_roi]}, detect_cls_list: {detect_cls_list}")

            camera_info_dict[camera_name] = {"cap" : cap,
                                    "name" : camera_name,
                                    "camera_id" : camera_info["camera_id"],
                                    "detect_cls" : detect_cls_list,
                                    "object_conf_score" : np.array(camera_info["conf"]) / 100,
                                    "tracker" : tracker,
                                    "ROI_ori" : active_roi,                 # 정규화된 ROI 좌표 normalized(0 ~ 1) [detect class, [x1,y1], [xn,yn]]
                                    "TF_ROI" : TF_detect_info,              # [detect class, [x1,y1], [xn,yn]]
                                    "img" : np.zeros([480,640,3], dtype=np.uint8),  # Img
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

    # SigLip 모델 로드
    logger.info("Starting SigLip model loading...")

    try:
        from transformers import SiglipProcessor, SiglipModel, AutoModel
        siglip_model = SiglipModel.from_pretrained(
            str(os.getcwd()) + f"/../weights/SigLip_512",
            attn_implementation="flash_attention_2",
            torch_dtype=torch.float16,
            device_map="cuda",
        )

        siglip_model = torch.compile(siglip_model, mode="reduce-overhead")

        siglip_processor = SiglipProcessor.from_pretrained(str(os.getcwd()) + f"/../weights/SigLip_512")
        logger.info("SigLip 모델 로드 완료")
        
        # 텍스트 임베딩 사전 계산
        precompute_text_embeddings()
    except Exception as e:
        try:
            from transformers import SiglipProcessor, SiglipModel, AutoModel
            siglip_model = SiglipModel.from_pretrained(
                str(os.getcwd()) + f"/../weights/SigLip_512",
                torch_dtype=torch.float16,
                device_map="cuda",
            )

            siglip_model = torch.compile(siglip_model, mode="reduce-overhead")

            siglip_processor = SiglipProcessor.from_pretrained(str(os.getcwd()) + f"/../weights/SigLip_512")
            logger.info("SigLip 모델 로드 완료")
            
            # 텍스트 임베딩 사전 계산
            precompute_text_embeddings()

        except Exception as e:
            logger.error(f"SigLip 모델 로드 실패: {e}")
            siglip_model = None
            siglip_processor = None



    start_time = time.time()

    while len(camera_info_dict):
        # next_time = time.time()

        img_list = []
        camera_num_list = []
        t0 = time.time()

        for camera_name, camera_info in camera_info_dict.items():
            ret, img = camera_info["cap"].read()

            if ret:
                img_list.append(img)
                camera_num_list.append(camera_name_to_num[camera_name])
                camera_info_dict[camera_name]["img"] = img

            else:
                # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{camera_info["camera_id"]}'

                # logger.info(f"Attempting to reconnect to video stream: {pipe}")
                # cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                
                # time.sleep(0.5)
                # if cap.frame_available():
                    # camera_info_dict[camera_name]["cap"] = cap

                img_list.append(np.zeros([480,640,3], dtype=np.uint8))
                camera_num_list.append(camera_name_to_num[camera_name])
                camera_info_dict[camera_name]["img"] = img


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
                num_to_camera_name = num_to_camera_name
                )
            
            for index, bbox in enumerate(bn_person_boxes):
                try:
                    camera_info_dict[num_to_camera_name[camera_num_list[index]]]["person_bbox"] = camera_info_dict[num_to_camera_name[camera_num_list[index]]]["tracker"].update(bbox, img_list[index])
                    camera_info_dict[num_to_camera_name[camera_num_list[index]]]["non_person_bbox"] = bn_non_person_boxes[index]

                    """사람의 bbox정보, 이동 경로, 검출 시간 갱신"""
                    camera_info_dict[num_to_camera_name[camera_num_list[index]]]["person_info"].update_id(
                        img = img_list[index],
                        track_info = camera_info_dict[num_to_camera_name[camera_num_list[index]]]["person_bbox"]
                        )
                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tb = traceback.format_exc()
                    logger.error(f"사람 정보 갱신 실패 : {current_time}: {e}\n{tb}")

            for camera_name, camera_info in camera_info_dict.items():
                """지능형 알고리즘 실행"""
                camera_info = detect_action(
                    camera_info = camera_info,
                    )
                # print(camera_name)
                # print(camera_info[7])

            # t2 = time.time()

            # VLM 응답 확인 및 처리
            # check_vlm_responses(camera_info_dict)
            
            # 쓰레기 검출 비동기 요청 결과 확인 및 처리
            check_trash_detection_results(camera_info_dict)


            # print(f"total : {1/(time.time() - t0)}")
            # print(f"t1 : {1/(t1 - t0)}")


            camera_info_dict = update_plot_person_bbox(
                camera_info_dict = camera_info_dict, 
                )

            for _, camera_info in camera_info_dict.items():
                NVR_ID, NVR_PW, NVR_IP = find_nvr_info(NVR_info, camera_info["name"])
                send_alarm_NVR(
                    nvr_ip = NVR_IP,
                    nvr_id = NVR_ID, 
                    nvr_pw = NVR_PW, 
                    camera_info = camera_info,
                    ROI_color_dict = ROI_color_dict,
                    object_color_dict = object_color_dict
                    )
            
            t2 = time.time()
            # BaseManager를 통해 AI 분석 결과 전송 (공유 메모리 방식)
            send_ai_info_via_manager(
                shared_data = shared_data,
                camera_info_dict = camera_info_dict,
                nvr_info_finder = lambda name: find_nvr_info(NVR_info, name),
            )
            
            camera_info_dict = camera_info_refresh(
                camera_info_dict = camera_info_dict,
                )

            if time.time() - start_time > 600: #600초 마다 미활동 점유 메모리 초기화
                gc.collect()
                start_time = time.time()


            # print(f"fps : {1/(time.time() - t0)}")
            ### 평균 Fps 계산
            if not hasattr(ms_ai, "fps_accum"):
                ms_ai.fps_accum = 0.0
                ms_ai.fps_count = 0
            current_fps = 1 / (time.time() - t0)
            ms_ai.fps_accum += current_fps
            ms_ai.fps_count += 1
            if ms_ai.fps_count % 100 == 0:
                avg_fps = ms_ai.fps_accum / ms_ai.fps_count
                print(f"평균 FPS (최근 {ms_ai.fps_count}회): {avg_fps:.2f}")
                ms_ai.fps_accum = 0
                ms_ai.fps_count = 0

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

