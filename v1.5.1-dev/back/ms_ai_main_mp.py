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
import multiprocessing as mp
from multiprocessing import Process, Pipe

import torch
from back.HAR import Person_Info
from back.utils import (remove_out_of_BBox, TF_detect_area, \
                        get_bottom_point, get_center_point, send_alarm_NVR, send_NVR_empty,
                        camera_info_refresh, get_IOU, send_SERVER_ai_info, get_active_info,
                        check_stop_person, make_square_bbox, merge_boxes, video_save_buffer_update,
                        send_alarm_NVR_mp, send_SERVER_ai_info_mp, camera_info_refresh_mp)

from ultralytics import YOLO
import boxmot
import cv2


from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

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
            self.video_decode = f'! decodebin ! videoscale ! video/x-raw,width={resolution[0]},height={resolution[1]} ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=3 drop=true'
        
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

def check_box_in_area(point_list, area_list):
    if len(area_list) == 0: return False

    if cv2.pointPolygonTest(np.array(area_list), (point_list[0], point_list[1]), False) == 1 :
        return True
    
    else : return False


#침입
def detect_intrusion(camera_har_info, camera_name, detect_area, person_bbox_list):
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
                if id_ not in camera_har_info[camera_name]["intr"]:
                    camera_har_info[camera_name]["intr"][id_] = [time.time(), -1]

                else:
                    if camera_har_info[camera_name]["intr"][id_][1] == -1 and time.time() - camera_har_info[camera_name]["intr"][id_][0] >= 3 : # 검출 시간 기준 3초 이상 침입이 지속될 경우 알림 발생
                        camera_har_info[camera_name]["intr"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_har_info[camera_name]["alarm"].append(["Intrusion", id_, camera_har_info[camera_name]["intr"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"침입 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_har_info  

#배회
def detect_loitering(camera_har_info, camera_name, detect_area, person_bbox_list):
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
                if id_ not in camera_har_info[camera_name]["loit"].keys():
                    camera_har_info[camera_name]["loit"][id_] = [time.time(), -1]

                else:
                    if camera_har_info[camera_name]["loit"][id_][1] == -1 and time.time() - camera_har_info[camera_name]["loit"][id_][0] >= 10 : # 검출 시간 기준 10초 이상 배회가 지속될 경우 알림 발생
                        camera_har_info[camera_name]["loit"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_har_info[camera_name]["alarm"].append(["Loitering", id_, camera_har_info[camera_name]["loit"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"배회 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_har_info

def detect_falldown(camera_har_info, camera_name, detect_area, person_bbox_list, siglip_model, siglip_processor):
    """쓰러짐 검출 시작 기준 : 사람 이동 경로 점이(bbox의 중심점) 30개 이상 지속되고 이동 경로가 정지할 경우 판별 시작
       쓰러짐 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상(90점)일 경우 쓰러짐 검출
       쓰러짐 알림 발생 기준 : 쓰러짐 검출이 10회 중 5회 이상 발생하고 5초 이상 지속될 경우 VLM에 QnA 요청 후 답변이 yes일 경우 알림 발생
       """
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_center_point(bbox)

            if check_box_in_area(detect_point, detect_area):
                if id_ in camera_har_info[camera_name]["person_info"].info.keys():
                    trejectory = camera_har_info[camera_name]["person_info"].info[id_]["trejectory"]
                    if len(trejectory) > 30 and check_stop_person(bbox, trejectory):
                        new_x1, new_y1, new_x2, new_y2, id_, conf, label, _ = make_square_bbox([x1, y1, x2, y2, id_, conf, cls, ind])

                        person_img = camera_har_info[camera_name]["img"][int(new_y1) : int(new_y2), int(new_x1) : int(new_x2)]
                        pil_img = Image.fromarray(person_img.astype('uint8'), 'RGB')
                        texts = ["a photo of falldown person on ground.", 
                                "a photo of walking person on street", 
                                "a photo of riding person on street", 
                                "a photo of standing person on street", 
                                "a photo of sitting person on ground"]
                        
                        inputs = siglip_processor(text=texts, images=pil_img, padding="max_length", return_tensors="pt")

                        with torch.no_grad():
                            with torch.autocast("cuda"):
                                outputs = siglip_model(**inputs.to("cuda"))
                            
                                logits_per_image = outputs.logits_per_image
                                probs = torch.sigmoid(logits_per_image) # these are the probabilities
                            
                            # if probs[0][0] > 0.90 and (probs[0][1:] < 0.3).all():
                            if probs[0][0] > 0.50 and (probs[0][1:] < 0.3).all():
                            # if True:
                                camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "falldown", status = 1)

                            elif torch.argmax(probs) == 0 and (probs[0][1:] < 0.01).all():
                                camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "falldown", status = 1)
                            else:
                                camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "falldown", status = 0)
                    
                            del outputs
                            del probs

                    else:
                        camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "falldown", status = 0)


        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 쓰러짐 알람 기록 알고리즘 : 최근 쓰러짐 감지 기록 10회 중 5회 이상일 경우 검출 시간 기록
            status = camera_har_info[camera_name]["person_info"].get_status(int(id_), detect_type = "falldown")

            if status == 1 :
                if id_ not in camera_har_info[camera_name]["fall"].keys():
                    camera_har_info[camera_name]["fall"][id_]  = [time.time(), -1]

                else:
                    if camera_har_info[camera_name]["fall"][id_][1] == -1 and time.time() - camera_har_info[camera_name]["fall"][id_][0] > 5 : # 검출 시간 기준 5초 이상 쓰러짐이 지속될 경우 vlm QnA 시도
                        # VLM 비동기 처리로 변경 - 즉시 알람을 발생시키지 않고 VLM 결과를 기다림
                        response = camera_har_info[camera_name]["person_info"].run_har_vlm(id_, detect_type = "lying person or fallen person")
                        
                        # run_har_vlm이 비동기로 처리되므로 즉시 False가 반환됨
                        # 실제 VLM 결과는 나중에 check_vlm_results()를 통해 확인됨
                        if not response:  # VLM 처리가 시작됨
                            # 중복 VLM 요청 방지를 위해 검출 시간을 30초 후로 설정
                            camera_har_info[camera_name]["fall"][id_][0] = time.time() + 300

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰러짐 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_har_info

def detect_fight(camera_har_info, camera_name, detect_area, person_bbox_list, siglip_model, siglip_processor):
    """싸움 검출 시작 기준 : 사람의 bbox 하단 점이 검출 영역에 들어올 경우
       싸움 검출 기준 : 이미지와 텍스트의 유사도 점수가 일정 값 이상(90점)일 경우 싸움 검출
       싸움 알림 발생 기준 : 싸움 검출이 10회 중 5회 이상 발생하고 5초 이상 지속될 경우 VLM에 QnA 요청 후 답변이 yes일 경우 알림 발생
    """
    try:
        if len(person_bbox_list):
            for x1, y1, x2, y2, id_list, conf, label, _ in person_bbox_list:
                if x1 < 0 : x1 = 0
                if y1 < 0 : y1 = 0
                bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

                detect_point =  get_bottom_point(bbox)

                if check_box_in_area(detect_point, detect_area):
                    people_img = camera_har_info[camera_name]["img"][int(y1) : int(y2), int(x1) : int(x2)]
                    pil_img = Image.fromarray(people_img.astype('uint8'), 'RGB')

                    texts = ["a photo of fighting people.",
                            "a photo of talking people on street",
                            "a photo of walking people on street", 
                            "a photo of standing people on street"]
                    
                    inputs = siglip_processor(text=texts, images=pil_img, padding="max_length", return_tensors="pt")

                    with torch.no_grad():
                        with torch.autocast("cuda"):
                            outputs = siglip_model(**inputs.to("cuda"))
                        
                            logits_per_image = outputs.logits_per_image
                            probs = torch.sigmoid(logits_per_image) # these are the probabilities

                    if probs[0][0] > 0.3:
                        camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "fight", status = 2) #싸움 검출 상태 할당

                else:
                    camera_har_info[camera_name]["person_info"].update_status(id_, detect_type = "fight", status = 0) #정상 상태 할당

        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 싸움 알람 기록 알고리즘
            status = camera_har_info[camera_name]["person_info"].get_status(int(id_), detect_type = "fight")

            if status == 2 :
                if id_ not in camera_har_info[camera_name]["fight"].keys():
                    camera_har_info[camera_name]["fight"][id_]  = [time.time(), -1]

                else:
                    if camera_har_info[camera_name]["fight"][id_][1] == -1 and time.time() - camera_har_info[camera_name]["fight"][id_][0] > 3 : # 검출 시간 기준 3초 이상 싸움이 지속될 경우 VLM 처리 시작
                        # VLM 비동기 처리로 변경
                        response = camera_har_info[camera_name]["person_info"].run_har_vlm(id_, detect_type = "fight")
                        
                        # run_har_vlm이 비동기로 처리되므로 즉시 False가 반환됨
                        if not response:  # VLM 처리가 시작됨
                            # 중복 VLM 요청 방지를 위해 검출 시간을 30초 후로 설정
                            camera_har_info[camera_name]["fight"][id_][0] = time.time() + 120

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"싸움 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_har_info

def detect_fire(camera_har_info, camera_name, detect_area, bbox):
    """방화 검출 시작 기준 : 불꽃에 대한 bbox가 검출 영역에서 발생할 경우
       방화 검출 기준 : 불꽃에 대한 bbox가 5초 이상 지속되고 30번 연속으로 발생할 경우 방화 검출
       방화 알림 발생 기준 : VLM에 QnA 요청 후 답변이 yes일 경우 알림 발생
    """
    try:
        detect_point =  get_center_point(bbox)
        fire_check_flag = 0

        if check_box_in_area(detect_point, detect_area):
            if len(camera_har_info[camera_name]["fire"]):
                for id, detect_info in camera_har_info[camera_name]["fire"].items():
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
                            camera_har_info[camera_name]["alarm"].append(["Fire", id, detect_info[1]])

                        else:
                            detect_info[4] += 1
                
                if fire_check_flag == 0:
                    camera_har_info[camera_name]["fire"][len(camera_har_info[camera_name]["fire"])] = [time.time(), -1, time.time(), bbox, 0]

            else:
                camera_har_info[camera_name]["fire"][len(camera_har_info[camera_name]["fire"])] = [time.time(), -1, time.time(), bbox, 0]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"방화 검출 에러 발생 : {current_time}: {e}\n{tb}")

    finally:
        return camera_har_info

def detect_action_process(har_pipe_conn, camera_info_dict_ori, HOST):
    """HAR 전용 프로세스에서 실행되는 함수"""
    try:
        # HAR 전용 모델 로드
        active_HAR = False
        camera_har_info = {}
        start_time = time.time()
        
        # camera_har_info 초기화
        for camera_name, camera_info in camera_info_dict_ori.items():
            if len(camera_info["detect_info"]):
                active_roi = get_active_info(camera_info["detect_info"], camera_info["detect_schedule"])
                TF_detect_info = TF_detect_area(active_roi, img_size=(640, 480))
                
                camera_har_info[camera_name] = {
                    "img": np.zeros([480, 640, 3]),
                    "person_bbox": [],
                    "non_person_bbox": [],
                    "alarm": [],
                    "loit": {},
                    "intr": {},
                    "fall": {},
                    "fire": {},
                    "fight": {},
                    "person_info": Person_Info(host=HOST, camera_name=camera_name),
                    "TF_ROI": TF_detect_info,
                }
                
                for roi_list in TF_detect_info:
                    if roi_list[0] in ["Fight", "Falldown"]:
                        active_HAR = True

        # SigLip 모델 로드 (HAR 필요시)
        if active_HAR:
            from transformers import SiglipProcessor, SiglipModel
            siglip_model = SiglipModel.from_pretrained(str(os.getcwd()) + f"/back/weights/SigLip_512",
                                                        attn_implementation="flash_attention_2",
                                                        torch_dtype=torch.float16,
                                                        device_map="cuda",)
            siglip_processor = SiglipProcessor.from_pretrained(str(os.getcwd()) + f"/back/weights/SigLip_512")
        else:
            siglip_model = None
            siglip_processor = None

        logger.info("HAR 프로세스 시작됨")
        
        while True:
            try:
                # 메인 프로세스에서 데이터 수신
                if har_pipe_conn.poll():

                    try:
                        data = har_pipe_conn.recv()
                                    
                    except EOFError:
                        logger.info("HAR 프로세스 종료됨")
                        break
                    
                    if data is None:  # 종료 신호
                        break
                        
                    camera_name = data['camera_name']
                    img = data['img']
                    person_bbox = data['person_bbox']
                    non_person_bbox = data['non_person_bbox']
                    
                    # HAR 정보 업데이트
                    camera_har_info[camera_name]["img"] = img
                    camera_har_info[camera_name]["person_bbox"] = person_bbox
                    camera_har_info[camera_name]["non_person_bbox"] = non_person_bbox
                    
                    # Person_Info 업데이트
                    camera_har_info[camera_name]["person_info"].update_id(img=img, track_info=person_bbox)
                    
                    # HAR 알고리즘 실행
                    camera_har_info = detect_action_har(camera_har_info, camera_name, siglip_model, siglip_processor)
                    
                    # VLM 비동기 결과 확인 및 처리
                    completed_vlm_results = camera_har_info[camera_name]["person_info"].check_vlm_results()
                    for person_id, vlm_result in completed_vlm_results:
                        if vlm_result:  # VLM에서 검출 결과가 True인 경우
                            # 해당 person_id에 대한 알람 생성
                            current_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                            
                            # person_id가 어떤 검출 타입에 속하는지 확인
                            if person_id in camera_har_info[camera_name]["fall"]:
                                if camera_har_info[camera_name]["fall"][person_id][1] == -1:  # 아직 알람이 발생하지 않은 경우
                                    camera_har_info[camera_name]["fall"][person_id][1] = current_time
                                    camera_har_info[camera_name]["alarm"].append(["Falldown", person_id, current_time])
                                    logger.info(f"VLM 결과로 쓰러짐 알람 발생: 카메라 {camera_name}, ID {person_id}")
                            
                            elif person_id in camera_har_info[camera_name]["fight"]:
                                if camera_har_info[camera_name]["fight"][person_id][1] == -1:  # 아직 알람이 발생하지 않은 경우
                                    camera_har_info[camera_name]["fight"][person_id][1] = current_time
                                    camera_har_info[camera_name]["alarm"].append(["Fight", person_id, current_time])
                                    logger.info(f"VLM 결과로 싸움 알람 발생: 카메라 {camera_name}, ID {person_id}")
                    
                    # 알람 정보를 메인 프로세스로 전송
                    if camera_har_info[camera_name]["alarm"]:
                        har_pipe_conn.send({
                            'camera_name': camera_name,
                            'alarms': camera_har_info[camera_name]["alarm"].copy()
                        })
                        camera_har_info[camera_name]["alarm"].clear()
                        
                camera_har_info = camera_info_refresh(camera_har_info)
                time.sleep(0.001)  # CPU 사용률 조절
                
            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                tb = traceback.format_exc()
                logger.error(f"HAR 프로세스 내부 에러 : {current_time}: {e}\n{tb}")
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"HAR 프로세스 에러 : {current_time}: {e}\n{tb}")
    finally:
        logger.info("HAR 프로세스 종료됨")

def camera_info_refresh(camera_info_dict):
    """지능형 검출 정보 초기화 : 5분이 지난 정보는 삭제"""
    for camera_num, camera_info in camera_info_dict.items():
        for detect_type in ["loit", "intr", "fall", "fire", "fight"]:
            expire_id = []
            for id, detect_info in camera_info[detect_type].items():
                if time.time() - detect_info[0] > 300:
                    expire_id.append(id)
            if expire_id:
                for id in expire_id:
                    del camera_info[detect_type][id]

    return camera_info_dict

def detect_action_har(camera_har_info, camera_name, siglip_model, siglip_processor):
    """HAR 프로세스에서 실행되는 행동 인식 함수"""
    person_bbox_list = camera_har_info[camera_name]["person_bbox"]
    non_person_bbox_list = camera_har_info[camera_name]["non_person_bbox"]

    """사람 기준 지능형 알고리즘 실행"""
    for detect_info in camera_har_info[camera_name]["TF_ROI"]:
        detect_type = detect_info[0]
        detect_area = detect_info[1:]

        if detect_type == "Intrusion":
            camera_har_info = detect_intrusion(camera_har_info=camera_har_info,
                                            camera_name=camera_name,
                                            detect_area=detect_area,
                                            person_bbox_list=person_bbox_list)
            
        elif detect_type == "Loitering":
            camera_har_info = detect_loitering(camera_har_info=camera_har_info,
                                            camera_name=camera_name,
                                            detect_area=detect_area,
                                            person_bbox_list=person_bbox_list)
            
        elif detect_type == "Falldown":
            camera_har_info = detect_falldown(camera_har_info=camera_har_info,
                                            camera_name=camera_name,
                                            detect_area=detect_area,
                                            person_bbox_list=person_bbox_list,
                                            siglip_model=siglip_model,
                                            siglip_processor=siglip_processor)

        elif detect_type == "Fight":
            camera_har_info = detect_fight(camera_har_info=camera_har_info,
                                        camera_name=camera_name,
                                        detect_area=detect_area,
                                        person_bbox_list=person_bbox_list,
                                        siglip_model=siglip_model,
                                        siglip_processor=siglip_processor)

    for (x1, y1, x2, y2, conf, cls) in non_person_bbox_list:
        #방화
        if x1 < 0: x1 = 0
        if y1 < 0: y1 = 0

        if cls == 1:
            bbox = np.array([x1, y1, x2, y2], dtype="int")
            for detect_info in camera_har_info[camera_name]["TF_ROI"]:
                detect_type = detect_info[0]
                detect_area = detect_info[1:]

                if detect_type == "Fire":
                    camera_har_info = detect_fire(camera_har_info=camera_har_info,
                                                camera_name=camera_name,
                                                detect_area=detect_area,
                                                bbox=bbox)

    return camera_har_info

def ms_ai(camera_info_dict_ori, NVR_info, weight_name, video_save_flag):
    camera_info_dict = {}
    start_time = time.time()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    NVR_ID = NVR_info["ID"]
    NVR_PW = NVR_info["PW"]
    NVR_IP = NVR_info["IP"]

    video_save_buffer = {}

    HOST = "127.0.0.1"
    PORT = 65432

    ROI_color_dict = {"Loitering": [53, 225, 225], "Intrusion": [35, 28, 255], "Fire": [33, 145, 237],
                        "Fight": [255, 0, 127], "Falldown": [230, 255, 121]
                        }

    interval = 1.0 / 30

    # HAR 프로세스용 파이프 생성
    har_pipe_main, har_pipe_har = Pipe()
    
    # HAR 프로세스 시작
    har_process = Process(target=detect_action_process, args=(har_pipe_har, camera_info_dict_ori, HOST))
    har_process.start()
    
    # 알람 정보를 저장할 딕셔너리
    camera_alarms = {}

    for camera_name, camera_info in camera_info_dict_ori.items():
        num = camera_info["Num"]

        if len(camera_info["detect_info"]):        
            pipe = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'

            logger.info(f"Attempting to connect to video stream: {pipe}")
            
            cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                
            # cap = cv2.VideoCapture(pipe)

            disconnect_cnt = 0
            no_connect_cnt = 0 
            time.sleep(1)
            ret, frame = cap.read()

            while ret == False:
                ret, frame = cap.read()

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Try connect {pipe}")
                time.sleep(1)
                disconnect_cnt += 1

                if no_connect_cnt > 2:
                    logger.error(f"Failed to connect to {pipe} after multiple attempts")
                    break

                if disconnect_cnt > 60:
                    no_connect_cnt += 1
                    del cap
                    gc.collect()
                    
                    try:
                        cap = Video_Buffer(pipe=pipe)
                        time.sleep(5)
                    except Exception as e:
                        logger.error(f"Failed to reconnect to {pipe}: {e}")
                        break

            if ret == False:
                logger.error(f"Unable to establish connection to {pipe}, skipping camera")
                continue
                
            logger.info(f"Successfully connected to {pipe}")

            tracker = boxmot.BotSort(reid_weights=Path(os.getcwd() + "/back/weights/ReID/osnet_ain_x1_0_msmt17.pt"),
                                     device=device,
                                     half=True,
                                    per_class=False,
                                    track_high_thresh=0.4,
                                    track_low_thresh=0.05,
                                    new_track_thresh=0.5,
                                    track_buffer=300,
                                    match_thresh=0.7,
                                    proximity_thresh=0.4,
                                    appearance_thresh=0.2,
                                    cmc_method="ecc",
                                    frame_rate=30,
                                    fuse_first_associate=True,
                                    with_reid=True,)
            
            # tracker = boxmot.BYTETracker(track_thresh=camera_info["Conf"] / 100, 
            #                             match_thresh=0.8, 
            #                             track_buffer=150, 
            #                             frame_rate=30, 
            #                             per_class=False)   

            active_roi = get_active_info(camera_info["detect_info"], camera_info["detect_schedule"])

            TF_detect_info = TF_detect_area(active_roi, 
                                            img_size=(cap._frame.shape[1], cap._frame.shape[0])
                                            )

            detect_cls_list = []

            if camera_info["Cls"][0]: detect_cls_list += [0]
            if camera_info["Cls"][1]: detect_cls_list += [1,2,3,4,5]
            if camera_info["Cls"][2]: detect_cls_list += [6]

            camera_info_dict[num] = {"cap": cap,
                                    "name": camera_name,
                                    "detect_cls": detect_cls_list,
                                    "object_conf_score": np.array(camera_info["Conf"]) / 100,
                                    "tracker": tracker,
                                    "ROI_ori": active_roi,
                                    "TF_ROI": TF_detect_info,
                                    }

            # 알람 정보 초기화
            camera_alarms[camera_name] = []

            """라벨링 데이터 생성용 비디오 버퍼"""
            video_save_buffer[camera_name] = {"img_ori_buffer": []}

    conf_score = 0.05
    model_name = f"ms-ai_{weight_name[2:]}-M"
    yolo_model_path_dict = {0 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}1.engine",
                            1 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}1.engine",
                            2 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}2.engine",
                            3 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}3.engine",
                            4 : str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}4.engine"}
    
    
    # yolo_model_path = yolo_model_path_dict[len(camera_info_dict)]  # load a pretrained model (recommended for training)
    yolo_model_path = str(os.getcwd()) + f"/back/weights/yolo/{weight_name}/{model_name}.pt"

    model = YOLO(yolo_model_path, task="detect")

    try:
        while len(camera_info_dict):
            next_time = time.time()

            img_list = []
            camera_num_list = []
            t0 = time.time()

            for camera_num, camera_info in camera_info_dict.items():
                ret, img = camera_info["cap"].read()

                if ret:
                    img_list.append(img)
                    camera_num_list.append(camera_num)

                else:
                    pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{camera_num}'

                    logger.info(f"Attempting to reconnect to video stream: {pipe}")
                    cap = Video_Buffer(pipe=pipe, resolution=(640,480))
                    
                    time.sleep(0.5)
                    if cap.frame_available():
                        camera_info_dict[camera_num]["cap"] = cap

                    img_list.append(np.zeros([480,640,3]))

            if len(img_list):
                dets = model.predict(source=img_list, 
                                        imgsz=640, 
                                        conf=conf_score, 
                                        classes=[0, 1, 2, 3, 4, 5, 6], 
                                        half=True, 
                                        verbose=False)
                t1 = time.time()
                bn_person_boxes, bn_non_person_boxes = remove_out_of_BBox(camera_info_dict=camera_info_dict, 
                                                                        bbox_bn=dets,
                                                                        camera_num_list=camera_num_list
                                                                        )
                for index, bbox in enumerate(bn_person_boxes):
                    camera_num = camera_num_list[index]
                    camera_name = camera_info_dict[camera_num]["name"]
                    
                    person_bbox = camera_info_dict[camera_num]["tracker"].update(bbox, img_list[index])
                    non_person_bbox = bn_non_person_boxes[index]

                    # 메인 프로세스에서 최신 bbox 정보 저장 (NVR 통신용)
                    camera_info_dict[camera_num]["person_bbox"] = person_bbox
                    camera_info_dict[camera_num]["non_person_bbox"] = non_person_bbox
                    camera_info_dict[camera_num]["img"] = img_list[index]

                    # HAR 프로세스로 데이터 전송
                    har_data = {
                        'camera_name': camera_name,
                        'img': img_list[index],
                        'person_bbox': person_bbox,
                        'non_person_bbox': non_person_bbox
                    }
                    har_pipe_main.send(har_data)

                # HAR 프로세스에서 알람 정보 수신
                if har_pipe_main.poll():
                    alarm_data = har_pipe_main.recv()
                    camera_name = alarm_data['camera_name']
                    alarms = alarm_data['alarms']
                    camera_alarms[camera_name].extend(alarms)
                    logger.info(f"HAR 알람 수신: 카메라 {camera_name}, 알람 수: {len(alarms)}")

                t2 = time.time()


                # NVR 및 서버에 정보 전송 (알람 정보 포함)
                logger.debug(f"YOLO 처리 시간: {t1-t0:.3f}s, HAR 처리 시간: {t2-t1:.3f}s")
                
                send_alarm_NVR_mp(nvr_ip=NVR_IP,
                                nvr_id=NVR_ID, 
                                nvr_pw=NVR_PW, 
                                camera_info_dict=camera_info_dict,
                                camera_alarms=camera_alarms,
                                ROI_color_dict=ROI_color_dict,
                                object_color_dict=COLOR)

                send_SERVER_ai_info_mp(host=HOST,
                                     port=PORT,
                                     camera_info_dict=camera_info_dict,
                                     camera_alarms=camera_alarms,
                                     video_save_buffer=video_save_buffer,
                                     nvr_ip=NVR_IP,
                                     video_save_flag=video_save_flag)
                
                camera_info_dict, start_time = camera_info_refresh_mp(camera_info_dict, camera_alarms, start_time)

                next_time += interval
                sleep_time = next_time - time.time()

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_time = time.time()

    except KeyboardInterrupt:
        logger.info("프로그램 종료 중...")
    finally:
        # HAR 프로세스 종료
        har_pipe_main.send(None)
        har_pipe_main.close()
        har_process.terminate()
        # har_process.join()
        logger.info("HAR 프로세스 종료 완료")



def camera_info_refresh_mp(camera_info_dict, camera_alarms, start_time):
    """멀티프로세스 환경용 카메라 정보 갱신 함수"""
    try:
        current_time = time.time()
        
        # 1시간마다 알람 정보 초기화
        if current_time - start_time > 3600:
            for camera_name in camera_alarms.keys():
                camera_alarms[camera_name].clear()
            start_time = current_time
            logger.info("알람 정보 초기화 완료")
            
        return camera_info_dict, start_time
        
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"카메라 정보 갱신 에러 발생 : {current_time}: {e}\n{tb}")
        return camera_info_dict, start_time
