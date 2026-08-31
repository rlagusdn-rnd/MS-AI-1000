import sys
import os
from pathlib import Path
from click import pause
import requests
from requests.auth import HTTPBasicAuth

from back.ms_labeler_main import ms_labeler, train
from back.utils import send_NVR_empty
from back.ms_ai_main import ms_ai
from back.utils import Eng2kor
from back.ms_trash_back_tracking import process_backtracking_trash

import subprocess

from multiprocessing import Process
from multiprocessing.managers import BaseManager
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import torch
from datetime import datetime, timedelta

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.requests import Request

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging(logger_name="MAIN_SERVER", log_file="MAIN_SERVER.log")

from utils import (LoginData, 
                   CameraInfoData, 
                   Login_Chg_Data, 
                   MsgData,
                   Colors,
                   DictData,
                   VideoStreamTrack,
                   load_json,
                   save_json,
                   load_crypography_json,
                   save_crypography_json,
                   check_alarm_video_history,
                   get_init_camera_dict
                    )

import cv2
import numpy as np
import base64
import shutil
import json
import time

from aiortc import RTCPeerConnection
from turbojpeg import TurboJPEG

ms_ai_scheduler = BackgroundScheduler()
auto_label_scheduler = BackgroundScheduler()

trigger = CronTrigger(minute=0) 
auto_label_trigger = CronTrigger(minute=0)  # 매 시간 00분마다 실행

ROOT = Path(__file__).resolve().parents[0]


from typing import Dict
torch.multiprocessing.set_start_method('spawn', force=True)

process_list = []
labeling_process_list = []
camera_ai_info_data = {}
server_info_dict = {}
run_auto_labeling_flag = False
run_training_flag = False

# BaseManager를 이용한 프로세스 간 데이터 공유 클래스
class SharedAIData:
    """멀티프로세스 간 AI 분석 결과를 공유하기 위한 클래스"""
    def __init__(self):
        self._data = {}
    
    def set(self, data):
        """AI 분석 결과 데이터 설정 (자식 프로세스에서 호출)"""
        self._data = data
    
    def get(self):
        """AI 분석 결과 데이터 조회 (부모 프로세스에서 호출)"""
        return self._data
    
    def clear(self):
        """데이터 초기화"""
        self._data = {}

# BaseManager 관련 전역 변수
shared_data_manager = None
shared_data_instance = None
data_receiver_thread = None
data_receiver_running = False

def init_shared_data_manager():
    """BaseManager 초기화 및 시작"""
    global shared_data_manager, shared_data_instance
    
    # 기존 매니저가 있으면 종료
    if shared_data_manager is not None:
        try:
            shared_data_manager.shutdown()
        except:
            pass
    
    # BaseManager에 SharedAIData 클래스 등록
    BaseManager.register('SharedAIData', SharedAIData)
    shared_data_manager = BaseManager()
    shared_data_manager.start()
    
    # 공유 데이터 인스턴스 생성
    shared_data_instance = shared_data_manager.SharedAIData()
    logger.info("SharedAIData Manager 초기화 완료")
    
    return shared_data_instance

def shared_data_receiver():
    """BaseManager를 통해 공유된 AI 분석 결과를 수신하는 백그라운드 스레드"""
    global camera_ai_info_data, shared_data_instance, data_receiver_running, server_info_dict
    
    while data_receiver_running:
        try:
            if shared_data_instance is None:
                time.sleep(0.01)
                continue
            
            # 공유 데이터에서 최신 데이터 가져오기
            data = shared_data_instance.get()
            
            if not data:
                time.sleep(0.001)
                continue
            
            # 수신된 데이터로 camera_ai_info_data 업데이트
            for nvr_ip, camera_alarm_info_dict in data.items():
                if nvr_ip not in camera_ai_info_data.keys():
                    camera_ai_info_data[nvr_ip] = {}
                
                for camera_name, camera_info in camera_alarm_info_dict.items():
                    # AI plot 데이터 갱신
                    camera_ai_info_data[nvr_ip][camera_name] = {
                        "alarm": [],
                        "detect_info": camera_info
                    }
                    
                    # GUI 알림 전송용
                    if nvr_ip in server_info_dict.get("NVR", {}):
                        nvr_id = server_info_dict["NVR"][nvr_ip]["id"]
                        nvr_pw = server_info_dict["NVR"][nvr_ip]["pw"]
                        
                        if camera_name in server_info_dict["NVR"][nvr_ip].get("cameras", {}):
                            camera_num = server_info_dict["NVR"][nvr_ip]["cameras"][camera_name]["id"]
                            
                            try:
                                auth = HTTPBasicAuth(nvr_id, nvr_pw)
                                event_info_post = f'http://{nvr_ip}/api/events?types=70&devices={camera_num-1}sort={0}&limit=3'
                                r = requests.get(event_info_post, auth=auth, timeout=1)
                                camera_ai_info_data[nvr_ip][camera_name]["alarm"] = r.json()
                            except Exception as e:
                                # logger.error(f"NVR 이벤트 조회 실패: {e}")
                                pass
                    
                    # 쓰레기 역추적을 위한 검출 정보 저장
                    for alarm in camera_info.get("alarm", []):
                        if alarm[0] == "Trash":
                            try:
                                admin_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
                                camera_info_temp = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
                                
                                # camera_name을 찾기 위해 NVR 정보에서 검색
                                found_camera_num = None
                                for nvr_ip_temp, nvr_cameras in camera_info_temp.items():
                                    if camera_name in nvr_cameras:
                                        found_camera_num = nvr_cameras[camera_name].get("Num")
                                        break
                                
                                if found_camera_num is None:
                                    continue
                                    
                                nvr_ip_trash = admin_info["NVR"]["IP"]
                                nvr_id_trash = admin_info["NVR"]["ID"]
                                nvr_pw_trash = admin_info["NVR"]["PW"]
                                
                                trash_object_bbox, detect_time, enroll_time = alarm[1], alarm[2], alarm[3]
                                
                                t_delta = abs((datetime.strptime(detect_time, "%Y-%m-%dT%H:%M:%S") - 
                                              datetime.strptime(enroll_time, "%Y-%m-%dT%H:%M:%S")).total_seconds())
                                
                                auth = HTTPBasicAuth(nvr_id_trash, nvr_pw_trash)
                                event_info_post = f'http://{nvr_ip_trash}/api/events?types=70&devices={found_camera_num-1}&sort={0}&total=true&limit=10'
                                
                                r = requests.get(event_info_post, auth=auth, timeout=1)
                                event_info_ori = r.json()
                                
                                event_info = event_info_ori["events"][0]
                                event_detect_time_dt = datetime.fromtimestamp(event_info["timestamp"])
                                event_enroll_time_dt = event_detect_time_dt - timedelta(seconds=t_delta)
                                
                                event_detect_time = event_detect_time_dt.strftime("%Y-%m-%dT%H:%M:%S")
                                event_enroll_time = event_enroll_time_dt.strftime("%Y-%m-%dT%H:%M:%S")
                                
                                save_dir = os.path.join(os.getcwd(), "..", "backup", "trash_data", "info")
                                if not os.path.exists(save_dir):
                                    os.makedirs(save_dir)
                                
                                save_detect_time = datetime.strptime(event_detect_time, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H-%M-%S")
                                file_path = os.path.join(save_dir, f"{camera_name.replace(' ', '_')}_{save_detect_time}.json")
                                
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    data_to_save = {"trash_object_bbox": trash_object_bbox, 
                                                  "detect_time": event_detect_time, 
                                                  "enroll_time": event_enroll_time}
                                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                            except Exception as e:
                                logger.error(f"쓰레기 역추적 데이터 저장 실패: {e}")
            
            time.sleep(0.001)  # CPU 사용량 감소를 위한 짧은 대기
                    
        except Exception as e:
            logger.error(f"공유 데이터 수신 스레드 에러: {e}")
            time.sleep(0.01)

def start_data_receiver():
    """공유 데이터 수신 스레드 시작"""
    global data_receiver_thread, data_receiver_running
    
    if not data_receiver_running:
        data_receiver_running = True
        data_receiver_thread = threading.Thread(target=shared_data_receiver, daemon=True)
        data_receiver_thread.start()
        logger.info("공유 데이터 수신 스레드 시작됨")

def stop_data_receiver():
    """공유 데이터 수신 스레드 및 매니저 중지"""
    global data_receiver_running, shared_data_manager, shared_data_instance
    
    data_receiver_running = False
    
    # 매니저 종료
    if shared_data_manager is not None:
        try:
            shared_data_manager.shutdown()
        except:
            pass
        shared_data_manager = None
        shared_data_instance = None

# 자동 라벨링 시간 체크 및 실행/종료
def check_auto_labeling_schedule():
    global labeling_process_list, run_auto_labeling_flag, run_training_flag

    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
    auto_labeling_mode_flag = setting_info["AI"]["auto_label"]
    auto_labeling_start_time = setting_info["AI"]["auto_label_start_time"]
    auto_labeling_end_time = setting_info["AI"]["auto_label_end_time"]

    nvr_info_dict = load_crypography_json(os.path.join(ROOT, "cache", "ai_server_info.json"))

    if not auto_labeling_mode_flag or run_auto_labeling_flag or run_training_flag:
        return

    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # 시작/종료 시간 파싱 (HH:MM 형식)
    try:
        start_hour, start_minute = map(int, auto_labeling_start_time.split(":"))
        end_hour, end_minute = map(int, auto_labeling_end_time.split(":"))
    except:
        logger.error(f"Invalid time format - Start: {auto_labeling_start_time}, End: {auto_labeling_end_time}")
        return
    
    # 현재 시간을 분 단위로 변환
    current_total_minutes = current_hour * 60 + current_minute
    start_total_minutes = start_hour * 60 + start_minute
    end_total_minutes = end_hour * 60 + end_minute
    
    # 시간 범위 안에 있는지 확인
    in_time_range = False
    
    if start_total_minutes <= end_total_minutes:
        # 자정을 넘지 않는 경우 (예: 09:00 ~ 18:00)
        in_time_range = start_total_minutes <= current_total_minutes < end_total_minutes
    else:
        # 자정을 넘는 경우 (예: 22:00 ~ 05:00)
        in_time_range = current_total_minutes >= start_total_minutes or current_total_minutes <= end_total_minutes
    
    logger.info(f"Auto labeling schedule check - Current: {current_hour:02d}:{current_minute:02d}, Start: {auto_labeling_start_time}, End: {auto_labeling_end_time}, In range: {in_time_range}")
    
    if in_time_range:
        # 시간 범위 안에 있으면 실행
        if not run_auto_labeling_flag and len(labeling_process_list) == 0:
            logger.info(f"Starting auto labeling at {current_hour:02d}:{current_minute:02d}")
            run_self_labeling(nvr_info_dict["NVR"])
            run_auto_labeling_flag = True
    else:
        # 시간 범위 밖에 있으면 종료
        if run_auto_labeling_flag and len(labeling_process_list) > 0:
            logger.info(f"Stopping auto labeling at {current_hour:02d}:{current_minute:02d}")
            for process in labeling_process_list:
                process.terminate()
            labeling_process_list.clear()
            run_auto_labeling_flag = False


# lifespan 함수 정의 (FastAPI app 생성 전)
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global ms_ai_scheduler, auto_label_scheduler
    global run_auto_labeling_flag
    
    # 앱 시작 시 스케줄러 시작
    ms_ai_scheduler.start()
    auto_label_scheduler.start()
    
    # setting_info.json 로드 및 자동 라벨링 스케줄러 설정
    if os.path.exists(os.path.join(ROOT, "cache", "setting_info.json")):
        try:
            setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
            auto_labeling_mode_flag = setting_info["AI"]["auto_label"]
            auto_labeling_start_time = setting_info["AI"]["auto_label_start_time"]
            auto_labeling_end_time = setting_info["AI"]["auto_label_end_time"]
            
            logger.info(f"Server startup - Auto labeling mode: {auto_labeling_mode_flag}, Start: {auto_labeling_start_time}, End: {auto_labeling_end_time}")
            
            auto_label_scheduler.remove_all_jobs()
            # 매 시간 00분마다 자동 라벨링 시간 체크
            auto_label_scheduler.add_job(check_auto_labeling_schedule, auto_label_trigger)
            logger.info("Auto labeling scheduler registered")
            check_auto_labeling_schedule()
        except Exception as e:
            logger.error(f"Failed to load setting_info.json: {e}")
    
    yield
    
    # 앱 종료 시 스케줄러 중지
    ms_ai_scheduler.shutdown()
    auto_label_scheduler.shutdown()

# FastAPI app 생성 (lifespan 연결)
app = FastAPI(lifespan=lifespan)

@app.get("/load-info") # 각종 info 파일 로드
async def load_info(data: DictData):
    """JSON 파일 로드"""
    file_name = data.msg["file_name"]
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : load info {file_name}")
    logger.info(f"load info {file_name}")

    file_info = load_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"))

    return {"success": True, "data": file_info}

@app.put("/save-info")
async def save_info(data: DictData):
    """JSON 파일 저장"""
    global auto_labeling_mode_flag, auto_labeling_start_time, auto_labeling_end_time

    file_name = data.msg["file_name"]
    info = data.msg["info"]
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : save info {file_name}")
    logger.info(f"save info {file_name}")


    save_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"), info)
    save_json(os.path.join(ROOT, "cache", f"{file_name}_ori.json"), info)


    if file_name == "setting_info":
        print(info)
        auto_labeling_mode_flag = info["AI"]["auto_label"]
        auto_labeling_start_time = info["AI"]["auto_label_start_time"]
        auto_labeling_end_time = info["AI"]["auto_label_end_time"]

        # if auto_labeling_mode_flag:
            # auto_label_scheduler.remove_all_jobs()
            # 매 시간 00분마다 자동 라벨링 시간 체크
            # auto_label_scheduler.add_job(check_auto_labeling_schedule, auto_label_trigger)

        # else:
            # auto_label_scheduler.remove_all_jobs()

    return {"success": True}

@app.get("/get-camera-info") # 지능형 서버에 할당된 카메라 정보 조회
async def get_camera_info():
    camera_info_data = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))

    if len(camera_info_data):
        return {"camera_info_dict" : camera_info_data}

    return {"camera_info_dict"  : camera_info_data}

@app.put("/save-camera-info") # 지능형 서버에 할당된 카메라 정보 갱신
async def save_camera_info(data: DictData):
    camera_info_data = data.msg

    save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_info_data)
    save_json(os.path.join(ROOT, "cache", "camera_info_ori.json"), camera_info_data)

    return {"success" : True}

@app.get("/get-ai-weight-list") # 지능형 서버에 저장된 객체 검출 신경망 가중치 리스트 전달
async def get_ai_weight_list():
    """지능형 엔진 가중치 목록 조회"""
    weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo")
    weight_list = sorted(os.listdir(weight_path))
                
    return {"weight_list": weight_list}

@app.post("/login-admin-page")
async def login_admin_page(data: MsgData):
    """관리자 페이지 로그인 인증"""
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login_admin_page")
    logger.info(f"login_admin_page")

    if data.msg == "0512":
        return {"msg": True}
    else:
        return {"msg": False}

#라벨링 윈도우 명령 엔드포인트
@app.get("/get-auto-label-info")
async def get_auto_label_info(data: DictData):
    global run_auto_labeling_flag, run_training_flag

    if data.msg["cmd"] == "get_label_info":
        label_info_dict = {"label_flag" : run_auto_labeling_flag,
                           "train_flag" : run_training_flag,
                            "label_data_info": {}}

        nvr_path = os.path.join(os.getcwd(), ".." , "backup", "dataset", "auto_labeled_data")
        if not os.path.exists(nvr_path):
            os.makedirs(nvr_path)
            
        nvr_list = sorted(os.listdir(nvr_path))

        for nvr_ip in nvr_list:
            camera_name_path = os.path.join(nvr_path, nvr_ip)
            camera_name_list = sorted(os.listdir(camera_name_path))

            for camera_name in camera_name_list:
                date_path = os.path.join(camera_name_path, camera_name)
                if os.path.exists(date_path):
                    label_info_dict["label_data_info"][camera_name] = {}
                    date_list = sorted(os.listdir(date_path))
                    for date in date_list:
                        event_path = os.path.join(date_path, date)
                        if os.path.exists(event_path):
                            event_list = sorted(os.listdir(event_path))
                            if len(event_list):
                                label_info_dict["label_data_info"][camera_name][date] = []
                                for event_name in event_list:
                                    label_info_dict["label_data_info"][camera_name][date].append(event_name)
        return label_info_dict

    elif data.msg["cmd"] == "get_label_data":
        print(data.msg)
        img_buffer = []
        label_buffer = []

        camera_name = data.msg["camera_name"]
        date_name = data.msg["date"]
        event_name = data.msg["event_name"]
        nvr_ip = data.msg["nvr_ip"]


        img_data_path = os.path.join(os.getcwd(),
                                     ".." ,
                                    "backup",
                                    "dataset",
                                    "auto_labeled_data",
                                    nvr_ip,
                                    camera_name,
                                    date_name,
                                    event_name,
                                    "images")

        label_data_path = os.path.join(os.getcwd(),
                                       ".." ,
                                        "backup",
                                        "dataset",
                                        "auto_labeled_data",
                                        nvr_ip,
                                        camera_name,
                                        date_name,
                                        event_name,
                                        "labels")

        img_list = sorted(os.listdir(img_data_path))

        for img_name in img_list:
            if img_name.split(".")[-1] == "png":
                img = cv2.imread(os.path.join(img_data_path, img_name), cv2.IMREAD_COLOR)
                img = cv2.resize(img, dsize=(1280, 720))
                _, img_encoded = cv2.imencode('.png', img)
                img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                img_buffer.append(img_base64)

            if img_name.split(".")[-1] == "jpg":
                img = cv2.imread(os.path.join(img_data_path, img_name), cv2.IMREAD_COLOR)
                img = cv2.resize(img, dsize=(1280, 720))
                _, img_encoded = cv2.imencode('.jpg', img)
                img_base64 = base64.b64encode(img_encoded).decode('utf-8')
                img_buffer.append(img_base64)

            if os.path.exists(os.path.join(label_data_path, img_name[:-4] + ".txt")):
                label_list = []
                with open(os.path.join(label_data_path, img_name[:-4] + ".txt"), 'r') as file:
                    object_num = 0
                    # color = Colors()
                    for line in file:
                        line = line.strip()
                        cls, xc, yc, w, h = line.split(" ")
                        # color = (tuple(np.random.randint(0, 255, size=3).tolist()))
                        label_list.append([int(cls), float(xc), float(yc), float(w), float(h)])
                        object_num += 1

                label_buffer.append(label_list)
            else:
                label_buffer.append([])

        return {"image" : img_buffer, "label" : label_buffer}

    elif data.msg["cmd"] == "del_label_data":

        for event_folder_name in data.msg["event_name"]:
            data_path = os.path.join(os.getcwd(),
                                    ".." ,
                                    "backup",
                                    "dataset",
                                    "auto_labeled_data",
                                    data.msg["nvr_ip"],
                                    data.msg["camera_name"],
                                    data.msg["date"],
                                    event_folder_name
                                    )

            shutil.rmtree(data_path)
        return {"msg" : True}

    elif data.msg["cmd"] == "save_label":
        camera_name = data.msg["camera_name"]
        date = data.msg["date"]
        event_name = data.msg["event_name"]

        label_data_path = os.path.join(os.getcwd(),
                                            ".." ,
                                            "backup",
                                            "dataset",
                                            "auto_labeled_data",
                                            data.msg["nvr_ip"],
                                            camera_name,
                                            date,
                                            event_name,
                                            "labels")
        for i, label_list in enumerate(data.msg["label_buffer"]):
            img_name = sorted(os.listdir(os.path.join(label_data_path, '..', 'images')))[i]
            label_file_path = os.path.join(label_data_path, img_name[:-4] + ".txt")
            with open(label_file_path, 'w') as file:
                for label in label_list:
                    cls, xc, yc, w, h = label
                    file.write(f"{cls} {np.round(xc,3)} {np.round(yc,3)} {np.round(w,3)} {np.round(h,3)}\n")
        
        
        if "완료" not in event_name.split("_"):
            os.rename(os.path.join(os.getcwd(),".." , "backup","dataset","auto_labeled_data",data.msg["nvr_ip"],camera_name,date,event_name), 
                        os.path.join(os.getcwd(),".." , "backup","dataset","auto_labeled_data",data.msg["nvr_ip"],camera_name,date,f"{event_name}_완료"))
            
        return {"msg" : True}

@app.put("/run-ms-ai")
async def run_ms_ai_endpoint(data: DictData):
    global ms_ai_scheduler, auto_labeling_start_time, auto_labeling_end_time, server_info_dict
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms-ai")
    logger.info(f"start ms-ai")

    server_info_dict = data.msg["ai_server_info_dict"]

    # Stop existing jobs
    ms_ai_scheduler.remove_all_jobs()

    run_ms_ai(server_info_dict = server_info_dict)

    # scheduler.add_job(run_ms_ai, 'interval', hours=12, args=[server_info_dict])
    ms_ai_scheduler.add_job(run_ms_ai, trigger, args=[server_info_dict])
    
    return {"success": True}

def run_ms_ai(server_info_dict):
    global process_list, camera_ai_info_data, shared_data_instance

    ai_server_camera_info_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
    setting_info_dict = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))

    #기존 실행되던 지능형 프로세스 초기화
    if len(process_list):
        for process in process_list:
            process.terminate()
            del process

        for nvr_ip, nvr_info in server_info_dict["NVR"].items():
            send_NVR_empty(nvr_ip = nvr_ip, nvr_id = nvr_info["id"], nvr_pw = nvr_info["pw"])
    
    # 기존 공유 데이터 초기화
    stop_data_receiver()
            
    process_list = []
    camera_ai_info_data = {}
    
    weight_name = setting_info_dict["AI"]["weight"]

    ai_enabled_cameras = {}
    now = datetime.now()
    # weekday(): 0=Monday, 1=Tuesday, ..., 6=Sunday
    # (weekday() + 1) % 7: 0=Sunday, 1=Monday, ..., 6=Saturday
    day_names = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    day = day_names[(now.weekday() + 1) % 7]

    # AI가 활성화된 카메라만 필터링
    for nvr_ip, camera_info_dict in ai_server_camera_info_dict.items():
        for camera_name, camera_info in camera_info_dict.items():
            break_flag = False

            if camera_info["ai"] and len(camera_info["detect_info"]):
                for detect_class, time_range in camera_info["detect_schedule"][day].items():
                    if break_flag == False:
                        for time_ in time_range:
                            if time_[0] <= now.hour <= time_[1] - 1:
                                ai_enabled_cameras[camera_name] = camera_info
                                break_flag = True
                                break

    camera_count = len(ai_enabled_cameras)

    if camera_count:
        # BaseManager 초기화 및 공유 데이터 인스턴스 생성
        shared_data_instance = init_shared_data_manager()
        
        # 공유 데이터 수신 스레드 시작
        start_data_receiver()
        
        # 한 프로세서당 최대 4개의 카메라
        max_channels_per_process = 4

        # 필요한 프로세서 수 계산
        num_processes = (camera_count + max_channels_per_process - 1) // max_channels_per_process

        # 카메라 정보를 그룹으로 분할
        start = 0
        camera_groups = []
        for _ in range(num_processes):
            group = dict(list(ai_enabled_cameras.items())[start:start + max_channels_per_process])
            camera_groups.append(group)
            start += max_channels_per_process

        # 각 그룹에 대한 프로세스 시작 (공유 데이터 객체 전달)
        for group in camera_groups:
            p = Process(target=ms_ai, args=([group, server_info_dict["NVR"], weight_name, shared_data_instance]))
            p.start()
            process_list.append(p)

@app.post("/run-self-labeling")
async def start_ms_labeler(data : DictData):
    """MS-Labeler 시작"""
    global labeling_process_list, run_auto_labeling_flag, run_training_flag
    logger.info(f"start self labeling")
    nvr_info_dict = data.msg


    if len(labeling_process_list) == 0 and run_training_flag == False and run_auto_labeling_flag == False:
        
        run_self_labeling(nvr_info_dict)
        run_auto_labeling_flag = True

    return {"success": run_auto_labeling_flag}

#자가 학습 데이터 생성 모듈 시작
def run_self_labeling(nvr_info_dict):
    global labeling_process_list
    
    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
    weight_name = setting_info["AI"]["weight"]
    zero_shot_flag = setting_info["AI"]["zero_shot"]

    p = Process(target=ms_labeler, args=([nvr_info_dict, weight_name, zero_shot_flag]))
    p.start()

    labeling_process_list.append(p)

@app.put("/stop-self-labeling-training")
async def stop_self_labeling_training(data : MsgData):
    """MS-Labeler 및 학습 중지"""
    global labeling_process_list, run_auto_labeling_flag, run_training_flag

    logger.info(f"stop self labeling and training")

    if data.msg == "ms_labeling" :
        run_auto_labeling_flag = False
        if len(labeling_process_list):
            for process in labeling_process_list:
                process.terminate()
            del labeling_process_list[0]

            VLM_URL = "http://127.0.0.1:1206"

            response = requests.post(VLM_URL + "/unload-vlm-model",
                            json={"question" : [],
                            "data_type" : "",
                            "video_path" : ""})

            if response.status_code != 200:
                logger.error(f"Failed to unload VLM model: {response.status_code} {response.text}")

    elif data.msg == "ms_train" :
        run_training_flag = False
        if len(labeling_process_list):
            for process in labeling_process_list:
                process.terminate()
            del labeling_process_list[0]
            

    return True

@app.get("/get-camera-ai-plot-data")
async def get_camera_ai_data(data: MsgData):
    global camera_ai_info_data
    find_camera_name = data.msg
    # 데이터 검색
    for nvr_ip, camera_info_dict in camera_ai_info_data.items():
        for camera_name, camera_info in camera_info_dict.items():
            if find_camera_name == camera_name:
                return {find_camera_name : camera_info["detect_info"]}
    return {find_camera_name : False}

@app.get("/get-ai-alarm-data")
async def get_ai_alarm_data():
    global camera_ai_info_data
    alarm_data = {}

    for nvr_ip, camera_info_dict in camera_ai_info_data.items():
        alarm_data[nvr_ip] = {}
        for camera_name, camera_info in camera_info_dict.items():
                alarm_data[nvr_ip][camera_name] = camera_info["alarm"]

    return alarm_data

@app.put("/upload-ai-alarm")
async def upload_ai_alarm_data(data: DictData):
    global camera_ai_info_data, server_info_dict
    # auto_label_exec_flag = 0

    for nvr_ip, camera_alarm_info_dict in data.msg.items():
        if nvr_ip not in camera_ai_info_data.keys():
                camera_ai_info_data[nvr_ip] = {}

        for camera_name, camera_info in camera_alarm_info_dict.items():
            #ai plot 데이터 갱신
            camera_ai_info_data[nvr_ip][camera_name] = {"alarm" : [], "detect_info" : camera_info}

            # GUI 알림 전송용 
            nvr_id = server_info_dict["NVR"][nvr_ip]["id"]
            nvr_pw = server_info_dict["NVR"][nvr_ip]["pw"]

            camera_num = server_info_dict["NVR"][nvr_ip]["cameras"][camera_name]["id"]

            auth = HTTPBasicAuth(nvr_id, nvr_pw)

            event_info_post = f'http://{nvr_ip}/api/events?types=70&devices={camera_num-1}sort={0}&limit=3'
            r = requests.get(event_info_post, auth=auth, timeout= 1)

            camera_ai_info_data[nvr_ip][camera_name]["alarm"] = r.json()

            # 쓰레기 역추적을 위한 검출 정보 저장
            for alarm in camera_info["alarm"]:
                if alarm[0] == "Trash":
                    admin_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
                    camera_info_temp = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
                    camera_num = camera_info_temp[camera_name]["Num"]
                    nvr_ip = admin_info["NVR"]["IP"]
                    nvr_id = admin_info["NVR"]["ID"]
                    nvr_pw = admin_info["NVR"]["PW"]

                    trash_object_bbox, detect_time, enroll_time = alarm[1], alarm[2], alarm[3]

                    # detect_time과 enroll_time 형식: "2025-10-30T12:01:05"
                    t_delta = abs((datetime.strptime(detect_time, "%Y-%m-%dT%H:%M:%S") - datetime.strptime(enroll_time, "%Y-%m-%dT%H:%M:%S")).total_seconds())

                    auth = HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW
                    event_info_post = f'http://{nvr_ip}/api/events?types=70&devices={camera_num-1}&sort={0}&total=true&limit=10'

                    r = requests.get(event_info_post, auth=auth, timeout= 1)
                    event_info_ori = r.json()
                    """event_info_ori =>
                        {'total': 2, 'offset': 0, 'limit': 10, 
                        'events': [
                                {'type': 70, 'timestamp': 1761121687, 'rowid': 151944, 'devices': [0], 'micro_ai': {'type': 2, 'object': 1, 'direction': 0}}, 
                                {'type': 70, 'timestamp': 1761121687, 'rowid': 151943, 'devices': [0], 'micro_ai': {'type': 2, 'object': 1, 'direction': 0}}, 
                    """
                    event_info = event_info_ori["events"][0]
                    event_detect_time_dt = datetime.fromtimestamp(event_info["timestamp"])
                    event_enroll_time_dt = event_detect_time_dt - timedelta(seconds=t_delta)
                    
                    event_detect_time = event_detect_time_dt.strftime("%Y-%m-%dT%H:%M:%S")
                    event_enroll_time = event_enroll_time_dt.strftime("%Y-%m-%dT%H:%M:%S")

                    save_dir = os.path.join(os.getcwd(), "..", "backup", "trash_data","info")
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)
                    # 파일 이름에 사용할 수 없는 문자(:) 제거 2025-10-30T10:36:27 -> 2025-10-30T10-36
                    save_detect_time = datetime.strptime(event_detect_time, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%dT%H-%M-%S")
                    file_path = os.path.join(save_dir, f"{camera_name.replace(' ', '_')}_{save_detect_time}.json")
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        data = {"trash_object_bbox": trash_object_bbox, "detect_time": event_detect_time, "enroll_time": event_enroll_time}
                        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"message": "데이터가 저장되었습니다"}

# yolo 학습 엔드포인트
@app.post("/start-training")
async def start_training(data : MsgData):
    global labeling_process_list, run_auto_labeling_flag, run_training_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms train")
    logger.info(f"start ms train")

    if run_training_flag == False and run_auto_labeling_flag == False:
        setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
        weight_name = setting_info["AI"]["weight"]

        p = Process(target=train, args=([weight_name]))
        p.start()

        labeling_process_list.append(p)

        run_training_flag = True

    return {"success": run_training_flag}

@app.put("/exit") # 서버 종료
async def exit_server(data : MsgData):
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : exit")
    logger.info(f"exit")

    global process_list, camera_ai_info_data
    camera_ai_info_data = {}
    
    try:
        # 공유 데이터 수신 스레드 및 매니저 중지
        stop_data_receiver()
        
        if len(process_list):
            for process in process_list:
                process.terminate()

        # if len(labeler_process_list):
        #     for process in labeler_process_list:
        #         process.terminate()

        os.system("chmod -R 777 ./")

    finally:
            login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
            
            if len(login_info["NVR"]["IP"]):
                send_NVR_empty(nvr_ip = login_info["NVR"]["IP"], nvr_id = login_info["NVR"]["ID"], nvr_pw = login_info["NVR"]["PW"])

            # print("Server is shutting down")
            logger.info("Server is shutting down")
            os._exit(0)

if __name__ == "__main__" :
    import sys
    import os
    from pathlib import Path   

    try:
        import uvicorn

        vlm_process = subprocess.Popen([sys.executable, "AI_core_main.py"])  # AI_core_main.py는 FastAPI 서버 코드 파일
        
        try:
            camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
        except Exception as e:
            logger.error(f"Failed to load camera_info.json: {e}")
            logger.info("Initializing with empty camera dictionary")
            camera_dict = {}
            
        for nvr_ip, info in camera_dict.items():
            for camera_name, camera_info in info.items():
                camera_info["ai"] = False
            
        save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)
        logger.info("Starting server")
        uvicorn.run(app, host="0.0.0.0", port=65432, log_level="warning")

    finally:
        os.system("chmod -R 777 ../backup")
        vlm_process.terminate()
        vlm_process.wait()


 
