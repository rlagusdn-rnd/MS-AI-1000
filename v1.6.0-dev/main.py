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

from solapi import SolapiMessageService
from solapi.model import RequestMessage
from solapi.model.kakao.kakao_option import KakaoOption

import threading

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

scheduler = BackgroundScheduler()
auto_label_scheduler = BackgroundScheduler()

trigger = CronTrigger(minute=0) 
auto_label_trigger = CronTrigger(minute=0)  # 매 시간 00분마다 실행

ROOT = Path(__file__).resolve().parents[0]

current_video_stream = None
stream_lock = threading.Lock()


from typing import Dict
torch.multiprocessing.set_start_method('spawn', force=True)

process_list = []
labeler_process_list = []
active_camera_num = []
login_user_info = {}

camera_info_data = {}
camera_img_temp = {}

run_auto_labeling_flag = False
auto_train_flag = False
auto_labeling_mode_flag = False
auto_labeling_start_time = ""
auto_labeling_end_time = ""

client_ip_dict = {}

# 자동 라벨링 시간 체크 및 실행/종료
def check_auto_labeling_schedule():
    global labeler_process_list, run_auto_labeling_flag, auto_labeling_mode_flag
    global auto_labeling_start_time, auto_labeling_end_time
    
    # auto_labeling_mode_flag가 False이면 실행하지 않음
    if not auto_labeling_mode_flag:
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
        if not run_auto_labeling_flag and len(labeler_process_list) == 0:
            logger.info(f"Starting auto labeling at {current_hour:02d}:{current_minute:02d}")
            run_ms_labeler()
            run_auto_labeling_flag = True
    else:
        # 시간 범위 밖에 있으면 종료
        if run_auto_labeling_flag and len(labeler_process_list) > 0:
            logger.info(f"Stopping auto labeling at {current_hour:02d}:{current_minute:02d}")
            for process in labeler_process_list:
                process.terminate()
            labeler_process_list.clear()
            run_auto_labeling_flag = False

# lifespan 함수 정의 (FastAPI app 생성 전)
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    global scheduler, auto_label_scheduler
    global auto_labeling_mode_flag, auto_labeling_start_time, auto_labeling_end_time
    
    # 앱 시작 시 스케줄러 시작
    scheduler.start()
    auto_label_scheduler.start()
    
    # setting_info.json 로드 및 자동 라벨링 스케줄러 설정
    if os.path.exists(os.path.join(ROOT, "cache", "setting_info.json")):
        try:
            setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
            auto_labeling_mode_flag = setting_info["AI"]["AutoLabel"]
            auto_labeling_start_time = setting_info["AI"]["AutoLabel_StartTime"]
            auto_labeling_end_time = setting_info["AI"]["AutoLabel_EndTime"]
            
            logger.info(f"Server startup - Auto labeling mode: {auto_labeling_mode_flag}, Start: {auto_labeling_start_time}, End: {auto_labeling_end_time}")
            
            if auto_labeling_mode_flag:
                auto_label_scheduler.remove_all_jobs()
                # 매 시간 00분마다 자동 라벨링 시간 체크
                auto_label_scheduler.add_job(check_auto_labeling_schedule, auto_label_trigger)
                logger.info("Auto labeling scheduler registered")
                check_auto_labeling_schedule()
        except Exception as e:
            logger.error(f"Failed to load setting_info.json: {e}")
    
    yield
    
    # 앱 종료 시 스케줄러 중지
    scheduler.shutdown()
    auto_label_scheduler.shutdown()

# FastAPI app 생성 (lifespan 연결)
app = FastAPI(lifespan=lifespan)

TEST = 1

def stop_ms_ai():
    global process_list
    if len(process_list):
        for process in process_list:
            process.terminate()
        del process_list[0]

def connect_camera_server(camera_info_dict, login_info, setting_info):
    """카메라 MS-AI 서버 연결 및 프로세스 시작"""
    global process_list
    process_list = []
    active_camera_num = []

    weight_name = setting_info["AI"]["Weight"]

    ai_enabled_cameras = {}
    now = datetime.now()
    day = str((now.weekday() + 1) % 7)

    # AI가 활성화된 카메라만 필터링
    for name, info in camera_info_dict.items():
        break_flag = False

        if info["AI"] and info["active_week_days"][int(day)] == 1 and len(info["detect_info"]):
            for detect_class, time_range in info["detect_schedule"][day].items():
                if break_flag == False:
                    for time_ in time_range:
                        if time_[0] <= now.hour <= time_[1] - 1:
                            ai_enabled_cameras[name] = info
                            break_flag = True
                            active_camera_num.append(name)
                            break

    camera_count = len(ai_enabled_cameras)

    if camera_count:
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

        # 각 그룹에 대한 프로세스 시작
        for group in camera_groups:
            p = Process(target=ms_ai, args=([group, login_info["NVR"], weight_name]))
            p.start()
            process_list.append(p)

    return process_list, active_camera_num


@app.post("/get_ai_weight_list")
async def get_ai_weight_list(data: DictData):
    """지능형 엔진 가중치 목록 조회"""
    weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo")
    weight_list = sorted(os.listdir(weight_path))
                
    return {"weight_list": weight_list}

@app.post("/login")
async def login(data: DictData):
    """로그인"""
    global login_user_info, client_ip_dict
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login {user_name}")
    user_name = data.msg["id"]
    client_ip = data.msg["client_ip"]
    client_local_ip = data.msg["client_local_ip"]


    logger.info(f"login ID: {user_name}, IP : {client_ip}@{client_local_ip}")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))

    os.makedirs(os.path.join(os.getcwd(), "..", "backup", login_info["NVR"]["IP"]), exist_ok=True)

    # check_alarm_video_history(login_info["NVR"]["IP"], setting_info)

    if data.msg["id"] == "admin" and data.msg["password"] == login_info["USER"]["admin"]:
        ip = f"{client_ip}@{client_local_ip}"
        client_ip_dict[ip] = time.time()
        return {"success": True, "data": login_info["NVR"], "user_info" : "admin"}
    
    if data.msg["id"] in login_info["USER"].keys():
        if login_info["USER"][data.msg["id"]] == data.msg["password"]:
            login_user_info[login_info["USER"][data.msg["id"]]] = False
            ip = f"{client_ip}@{client_local_ip}"
            client_ip_dict[ip] = time.time()

            return {"success": True, "data": login_info["NVR"], "user_info" : data.msg["id"]}

    return {"success": False, "data": "아이디와 비밀번호가 일치하지 않습니다"}

@app.post("/login_admin_page")
async def login_admin_page(data: MsgData):
    """관리자 페이지 로그인 인증"""
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login_admin_page")
    logger.info(f"login_admin_page")

    if data.msg == "0512":
        return {"msg": True}
    else:
        return {"msg": False}

@app.post("/login_info_chg")
async def login_chg(data: Login_Chg_Data):
    """사용자 정보 변경"""
    logger.info(f"login info change")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    if data.username in login_info["USER"].keys():
        if data.password == login_info["USER"][data.username]:
            if data.new_password == data.new_password2:
                login_info["USER"][data.username] = data.new_password
                save_crypography_json(os.path.join(ROOT, "cache", "login_info.json"), login_info)
                return {"success": True, "message": "아이디와 비밀번호가 변경되었습니다"}
            
            else: return {"success": False, "message": "새로운 비밀번호가 일치하지 않습니다"}
        else:
            return {"success": False, "message": "기존 비밀번호가 일치하지 않습니다"}

@app.post("/login_nvr")
async def login(data: DictData):
    """NVR 로그인"""
    try:
        logger.info(f"login NVR")

        nvr_ip = data.msg["ip"]
        nvr_id = data.msg["id"]
        nvr_pw = data.msg["pw"]

        auth = HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW
        camera_post = f'http://{nvr_ip}/api/cameras'
        # try:
        r = requests.get(camera_post,auth=auth, timeout= 1)
        if str(r) == "<Response [200]>":
            return {"success": True, "message": f"NVR 로그인 성공"}

        else:
            return {"success": False, "message": f"{r}"}

    except:
        return {"success": False, "message": "NVR 로그인 실패"}

@app.post("/load_info")
async def load_info(data: DictData):
    """JSON 파일 로드"""
    file_name = data.msg["file_name"]
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : load info {file_name}")
    logger.info(f"load info {file_name}")

    file_info = load_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"))

    return {"success": True, "data": file_info}

@app.post("/save_info")
async def save_info(data: DictData):
    """JSON 파일 저장"""
    global auto_labeling_mode_flag, auto_labeling_start_time, auto_labeling_end_time

    file_name = data.msg["file_name"]
    info = data.msg["info"]
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : save info {file_name}")
    logger.info(f"save info {file_name}")


    save_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"), info)

    if file_name == "setting_info":
        auto_labeling_mode_flag = info["AI"]["AutoLabel"]
        auto_labeling_start_time = info["AI"]["AutoLabel_StartTime"]
        auto_labeling_end_time = info["AI"]["AutoLabel_EndTime"]

        if auto_labeling_mode_flag:
            auto_label_scheduler.remove_all_jobs()
            # 매 시간 00분마다 자동 라벨링 시간 체크
            auto_label_scheduler.add_job(check_auto_labeling_schedule, auto_label_trigger)

        else:
            auto_label_scheduler.remove_all_jobs()

    return {"success": True}

@app.post("/load_camera_info")
async def camera_init(data : CameraInfoData):
    """카메라 정보 camera_info.json 로드"""
    """NVR에 연결된 카메라 정보 조회"""
    global process_list, camera_info_data
    reset_flag = data.reset
    
    if reset_flag == False:
        reset_flag = False if "camera_info.json" in os.listdir(os.path.join(ROOT, "cache")) else True
    
    camera_dict = {}
    camera_info_ori = {}
    auth = HTTPBasicAuth(data.id, data.pw) # NVR에 대한 ID / PW
    camera_post = f'http://{data.ip}/api/cameras'
    try:
        r = requests.get(camera_post,auth=auth, timeout= 1)
    except:
        # print("NVR 연결 실패")
        logger.info(f"NVR 연결 실패")
        return camera_dict

    if len(data.ip)  == 0 or  len(data.id) == 0:
        # print("NVR 연결 실패")
        logger.info(f"NVR 연결 실패")

        return camera_dict

    if reset_flag == False :
        """카메라 정보 camera_info.json 로드"""
        if str(r) == "<Response [200]>":
            camera_info_ori = r.json()

        camera_dict = load_crypography_json(os.path.join(os.getcwd(), "cache", "camera_info.json"))

    else :
        """NVR에 연결된 카메라 정보 조회"""
        stop_ms_ai()
        pause_ms_labeler({"msg" : "ms_labeling"})

        process_list = []
        camera_info_data = {}

        if str(r) == "<Response [200]>":
            camera_info_ori = r.json()

            for camera in camera_info_ori["cameras"]:
                """
                {'id': 1, 'name': '카메라 1', 'address': '117.17.159.195', 
                'location': '', 'source': 1, 'channel': 1, 
                'connected': True, 'has_signal': True, 
                'has_ptz': True, 'streaming': True, 
                'http_url': 'http://117.17.159.195/', 
                'note': '', 'ptz_presets': [], 'ptz_tours': [], 
                'osd': [{'text': '', 'size': 10, 'color': '#ffffff', 'location': 'top-right'}]},
                """

                if len(camera["address"]) == 0 or camera["connected"] == False:
                    continue


                camera_dict[camera["name"]] = get_init_camera_dict(camera)
                
            save_crypography_json(os.path.join(os.getcwd(), "cache", "camera_info.json"), camera_dict)


    if len(camera_dict):
        return {"success": True, "data": camera_dict}

    else:
        return {"success": False}

@app.post("/get_camera_img")
async def get_camera_img(data : DictData):
    global camera_img_temp

    logger.info(f"get camera img")

    auth = HTTPBasicAuth(data.msg["id"], data.msg["pw"]) # NVR에 대한 ID / PW
    camera_post = f'http://{data.msg["ip"]}/api/cameras'

    try:
        r = requests.get(camera_post,auth=auth, timeout= 1)
    except:
        logger.info(f"NVR 연결 실패")
        return {"success": False}
    
    camera_info_ori = r.json()
    camera_img_temp = {}  # 초기화

    for camera in camera_info_ori["cameras"]:
        num = camera["id"]

        camera_img_url = f'http://{data.msg["ip"]}/live/video{num}.jpg'

        try:
            img = requests.get(camera_img_url,auth=auth, timeout= 5)
            # 이미지 데이터를 base64로 인코딩
            camera_img_temp[camera["name"]] = base64.b64encode(img.content).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to get image for camera {camera['name']}: {e}")
            camera_img_temp[camera["name"]] = ""

    return {"success": True, "data": camera_img_temp}

@app.put("/end_ms_labeler")
async def end_ms_labeler(data : MsgData):
    """MS-Labeler 종료"""
    global labeler_process_list, run_auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : end {data.msg}")
    logger.info(f"end {data.msg}")

    if data.msg == "ms_labeling":
        run_auto_labeling_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()
            del labeler_process_list[0]
    elif data.msg == "ms_train":
        auto_train_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()
            del labeler_process_list[0]

    return True

@app.put("/pause_ms_labeler")
async def pause_ms_labeler(data : MsgData):
    """MS-Labeler 일시 정지"""
    global labeler_process_list, run_auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : pause {data.msg}")
    logger.info(f"pause {data.msg}")

    if data.msg == "ms_labeling" and run_auto_labeling_flag == True:
        run_auto_labeling_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()
            del labeler_process_list[0]

    elif data.msg == "ms_train" and auto_train_flag == True:
        auto_train_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()
            del labeler_process_list[0]

    return True

@app.put("/start_ms_labeler")
async def start_ms_labeler(data : MsgData):
    """MS-Labeler 시작"""
    global labeler_process_list, run_auto_labeling_flag, auto_train_flag

    if len(labeler_process_list) == 0 and auto_train_flag == False and run_auto_labeling_flag == False:
        
        run_ms_labeler()
        run_auto_labeling_flag = True

    return {"success": run_auto_labeling_flag}

@app.post("/start_trainer")
async def start_ms_trainer(data : MsgData):
    global labeler_process_list, run_auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms train")
    logger.info(f"start ms train")

    if auto_train_flag == False and run_auto_labeling_flag == False:
        setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
        weight_name = setting_info["AI"]["Weight"]

        login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
        nvr_ip = login_info["NVR"]["IP"]

        p = Process(target=train, args=([nvr_ip, weight_name]))
        p.start()

        labeler_process_list.append(p)

        auto_train_flag = True

    return {"success": auto_train_flag}

@app.post("/run_ms_ai")
async def receive_run_ms_ai(data : MsgData):
    global scheduler, auto_labeling_start_time, auto_labeling_end_time
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms-ai")
    logger.info(f"start ms-ai")

    # Stop existing jobs
    scheduler.remove_all_jobs()

    run_ms_ai()

    # scheduler.add_job(run_ms_ai, 'interval', hours=12)
    scheduler.add_job(run_ms_ai, trigger)
    

    return {"success": True}
    
@app.put("/upload-ai-data")
async def upload_data(data: DictData):
    global camera_info_data, TEST
    # auto_label_exec_flag = 0
    for camera_name, camera_info in data.msg.items():
        camera_info_data[camera_name] = camera_info

        if camera_info["alarm"]:
            for alarm in camera_info["alarm"]:
                # 솔라피를 이용한 알림 전송
                send_alarm_to_solapi(camera_name, alarm)
                    
                # 쓰레기 역추적을 위한 검출 정보 저장
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

@app.get("/get-camera-info")
async def retrieve_data(data: MsgData):
    global camera_info_data
    camera_name = data.msg
    # 데이터 검색
    if camera_name in active_camera_num and camera_name in camera_info_data.keys():
        data = camera_info_data[camera_name]
        return { camera_name  : data}
    return {camera_name  : False}

@app.get("/get-camera-connect_status")
async def get_camera_status(data: DictData):
    global process_list, camera_info_data
    camera_connect_status_dict = {}
    auth = HTTPBasicAuth(data.msg["id"], data.msg["pw"]) # NVR에 대한 ID / PW
    camera_post = f'http://{data.msg["ip"]}/api/cameras'
    try:
        r = requests.get(camera_post,auth=auth, timeout= 5)
    except:
        # print("NVR 연결 실패")
        logger.info(f"NVR 연결 실패 {camera_post}")
        return {"success" : False, "data" : camera_connect_status_dict}


    if str(r) == "<Response [200]>":
        camera_info_ori = r.json()

        for camera in camera_info_ori["cameras"]:
            """
            {'id': 1, 'name': '카메라 1', 'address': '117.17.159.195', 
            'location': '', 'source': 1, 'channel': 1, 
            'connected': True, 'has_signal': True, 
            'has_ptz': True, 'streaming': True, 
            'http_url': 'http://117.17.159.195/', 
            'note': '', 'ptz_presets': [], 'ptz_tours': [], 
            'osd': [{'text': '', 'size': 10, 'color': '#ffffff', 'location': 'top-right'}]},
            """

            camera_connect_status_dict[camera["name"]] = camera["connected"]

    alarm_info_data = {}

    event_info_post = f'http://{data.msg["ip"]}/api/events?types=70&sort={0}&limit=10'
    r = requests.get(event_info_post, auth=auth, timeout= 1)

    alarm_info_data = r.json()

    return {"success" : True, "data" : camera_connect_status_dict, "alarm_info_data" : alarm_info_data}

@app.get("/get-autolabel-info")
async def get_auto_label_info(data: DictData):
    global run_auto_labeling_flag, auto_train_flag

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))

    if data.msg["cmd"] == "get_label_info":
        label_info_dict = {"label_flag" : run_auto_labeling_flag,
                           "train_flag" : auto_train_flag,
                            "label_data_info": {}}

        camera_name_path = os.path.join(os.getcwd(), ".." , "backup", "dataset", login_info["NVR"]["IP"])
        os.makedirs(camera_name_path, exist_ok=True)
        camera_name_list = os.listdir(camera_name_path)

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
        img_buffer = []
        label_buffer = []

        camera_name = data.msg["camera_name"]
        date_name = data.msg["date"]
        event_name = data.msg["event_name"]

        img_data_path = os.path.join(os.getcwd(),
                                     ".." ,
                                    "backup",
                                    "dataset",
                                    login_info["NVR"]["IP"],
                                    camera_name,
                                    date_name,
                                    event_name,
                                    "images")

        label_data_path = os.path.join(os.getcwd(),
                                       ".." ,
                                        "backup",
                                        "dataset",
                                        login_info["NVR"]["IP"],
                                        camera_name,
                                        date_name,
                                        event_name,
                                        "labels")

        img_list = sorted(os.listdir(img_data_path))

        for img_name in img_list:
            if img_name.split(".")[-1] == "png":
                img = cv2.imread(os.path.join(img_data_path, img_name), cv2.IMREAD_COLOR)
                _, img_encoded = cv2.imencode('.png', img)
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

    elif data.msg["cmd"] == "del_label":
        for event_folder_name in data.msg["event_name"]:
            data_path = os.path.join(os.getcwd(),
                                    ".." ,
                                    "backup",
                                    "dataset",
                                    login_info["NVR"]["IP"],
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
                                            login_info["NVR"]["IP"],
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
            os.rename(os.path.join(os.getcwd(),".." , "backup","dataset",login_info["NVR"]["IP"],camera_name,date,event_name), 
                        os.path.join(os.getcwd(),".." , "backup","dataset",login_info["NVR"]["IP"],camera_name,date,f"{event_name}_완료"))
            
        return {"msg" : True}


@app.get("/get-search-info")
async def get_search_info(data: DictData):
    # print("load search info")
    logger.info(f"load search info {data.msg}")

    #data => {'before_day': '24.08.28', 'after_day': '24.08.28', 'time_start': '00.00.00', 'time_end': '23.59.00', 'camera_num': '*', 'search_detect_type': ['침입', '배회', '방화', '쓰러짐', '싸움']}
    camera_name_list = data.msg["camera_name"]
    start_day = data.msg["start_day"]
    time_start = data.msg["time_start"]
    time_end = data.msg["time_end"]
    end_day = data.msg["end_day"]
    camera_num_list = data.msg["camera_num"]
    sort_type = data.msg["sort_type"]
    detect_type_list = data.msg["detect_type"]


    """
    types: event types (default: *, start from 0)
    devices : device numbers (default: *, start from 0)
    sort : sort type (default: 0, see below)
    since : YYYY-MM-DD or YYYY-MM-DDtHH:MM:SS format (default: NULL)
    until : YYYY-MM-DD or YYYY-MM-DDtHH:MM:SS format (default: NULL)
    limit : the maximum number of search result (default: 10, 1~1000)
    total : get the total number of events (default: false) (slower)
    offset : the offset of search result (default: 0)
    last : last rowid/timestamp of search result (default: NULL) (ex: rowid:12345678,timestamp:1531094400)
    Event types and device numbers can be described like 0,3-4,7.
    For example, you can request a search like:

    http://192.168.1.100/api/events?types=0,3-4,7&since=2020-01-01t00:00:00&until=2020-01-01t23:59:59&devices=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15&sort=0

    """
    camera_num_input = ""
    for camera_num in camera_num_list:
        camera_num_input += f"{int(camera_num) - 1},"

    detect_type_input = ""
    for detect_type in detect_type_list:
        detect_type_input += f"{detect_type},"

    auth = HTTPBasicAuth(data.msg["id"], data.msg["pw"]) # NVR에 대한 ID / PW
    event_info_post = f'http://{data.msg["ip"]}/api/events?types=70&since={start_day}t{time_start}&until={end_day}t{time_end}&devices={camera_num_input[:-1]}&sort={sort_type}&total=true&limit=1000&micro_ai_type={detect_type_input[:-1]}'
    r = requests.get(event_info_post, auth=auth, timeout= 1)

    event_info_ori = r.json()

    return {"data"  : event_info_ori}


@app.put("/logout")
async def logout(data : MsgData):
    global client_ip_dict
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : user logout")
    logger.info(f"user logout {data.msg}")

    del client_ip_dict[data.msg]

@app.put("/exit")
async def exit_server(data : MsgData):
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : exit")
    logger.info(f"exit")


    global process_list

    try:
        if len(process_list):
            for process in process_list:
                process.terminate()

        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()

        os.system("chmod -R 777 ./")

    finally:
            login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
            
            if len(login_info["NVR"]["IP"]):
                send_NVR_empty(nvr_ip = login_info["NVR"]["IP"], nvr_id = login_info["NVR"]["ID"], nvr_pw = login_info["NVR"]["PW"])

            # print("Server is shutting down")
            logger.info("Server is shutting down")
            os._exit(0)

@app.put("/request_backtracking_trash")
async def request_backtracking_trash(data: DictData):
    global camera_info_data
    camera_name = data.msg["camera_name"]
    camera_num = int(data.msg["camera_num"])
    detect_time = data.msg["detect_time"]
    nvr_info = data.msg["nvr_info"]
    
    logger.info(f"쓰레기 역추적 요청 전송 - 카메라: {camera_name}, 시간: {detect_time}")
    p = Process(target=process_backtracking_trash, args=([camera_name, camera_num, detect_time, nvr_info]))
    p.start()

    return {"msg" : True}

@app.get("/check_report_exists")
async def check_report_exists(data: DictData):
    camera_name = data.msg["camera_name"]
    detect_time = data.msg["detect_time"]
    print(os.getcwd(), ".." , "backup", "trash_data", "images", f"{camera_name}_{detect_time}")
    report_path = os.path.join(os.getcwd(), ".." , "backup", "trash_data", "images", f"{camera_name}_{detect_time}")
    return {"exists" : os.path.exists(report_path)}

@app.get("/download_report")
async def download_report(data: DictData):
    camera_name = data.msg["camera_name"]
    detect_time = data.msg["detect_time"]
    report_path = os.path.join(os.getcwd(), ".." , "backup", "trash_data", "images", f"{camera_name}_{detect_time}")

    if os.path.exists(report_path):
        image_buffer = []
        images_list = os.listdir(report_path)
        if len(images_list):
            for image_name in images_list:
                image_path = os.path.join(report_path, image_name)
                if os.path.exists(image_path):
                    image = cv2.imread(image_path)
                    _, image_encoded = cv2.imencode('.png', image)
                    image_base64 = base64.b64encode(image_encoded).decode('utf-8')
                    image_buffer.append(image_base64)
            return {"image" : image_buffer, "exists" : True}
        else:
            return {"image" : [], "exists" : False}
    else:
        return {"image" : [], "exists" : False}


#오토 라벨링 시작
def run_ms_labeler():
    global labeler_process_list

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms labeler")
    logger.info(f"start ms labeler")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    camera_list_path = os.path.join(os.getcwd(), ".." ,"backup", login_info["NVR"]["IP"])

    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
    weight_name = setting_info["AI"]["Weight"]
    zero_shot_flag = setting_info["AI"]["ZeroShot"]

    p = Process(target=ms_labeler, args=([camera_list_path, weight_name, zero_shot_flag]))
    p.start()

    labeler_process_list.append(p)

#지능형 알고리즘 시작
def run_ms_ai():
    global process_list, camera_info_data, active_camera_num

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))


    if len(process_list):
        for process in process_list:
            process.terminate()
            send_NVR_empty(nvr_ip = login_info["NVR"]["IP"], nvr_id = login_info["NVR"]["ID"], nvr_pw = login_info["NVR"]["PW"])
            camera_info_data.clear()
            del process
            
    process_list = []
    active_camera_num = []
    camera_info_data.clear()
    camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))

    process_list, active_camera_num = connect_camera_server(camera_dict, login_info, setting_info)

def send_alarm_to_solapi(camera_name, alarm):
    # API 키와 API Secret을 설정합니다
    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
    if setting_info["SMS"]["active"] == 1:
        for phone_num, detect_type_dict in setting_info["SMS"]["USER"].items():
            for detect_type, detect_type_flag in detect_type_dict.items():
                if detect_type_flag == 1 and alarm[0] == detect_type:
                    detect_type_kor = Eng2kor(detect_type)
                    current_time = alarm[2]

                    message_service = SolapiMessageService(
                        api_key="NCSV30HGFAONWEPN", api_secret="KTNWYZVICVQ7XU5AFUZGNC8OQXT9AACT"
                    )

                    kakao_option = KakaoOption(
                        pf_id="KA01PF251028000707180RUlDmOmEIHl",#계정에 등록된 카카오 비즈니스 채널ID,
                        template_id="KA01TP251029053533686cVW9f2fory3", #계정에 등록된 카카오 알림톡 템플릿 ID
                        # 만약에 템플릿에 변수가 있다면 아래와 같이 설정합니다.
                        # 값은 반드시 문자열로 넣어주셔야 합니다!
                        variables={
                          "#{detect_type}": str(detect_type_kor),
                          "#{camare_name}": str(camera_name),
                          "#{current_time}": str(current_time)

                        }
                    )

                    message = RequestMessage(
                        from_="01084461617",  # 발신번호 (등록된 발신번호만 사용 가능) TODO : 회사 번호로 변경
                        to=phone_num,  # 수신번호
                        kakao_options=kakao_option,
                    )
                    try:
                        response = message_service.send(message)
                        logger.info(f"Kakao 발송 성공! {phone_num} {detect_type} {alarm}")
                    except Exception as e:
                        logger.error(f"Kakao 발송 실패: {str(e)}")



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
            
        for name, info in camera_dict.items():
            info["AI"] = False
            
        save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)
        logger.info("Starting server")
        uvicorn.run(app, host="0.0.0.0", port=65432, log_level="warning")

    finally:
        os.system("chmod -R 777 ../backup")
        vlm_process.terminate()
        vlm_process.wait()

        if len(process_list):
            for process in process_list:
                process.terminate()

        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()


 
