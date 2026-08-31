import sys
import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

from back.ms_labeler_main import ms_labeler, train
from back.utils import send_NVR_empty
from back.ms_ai_main import ms_ai

import subprocess

from multiprocessing import Process

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import torch
from datetime import datetime

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.requests import Request

import threading

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

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

app = FastAPI()
scheduler = BackgroundScheduler()
trigger = CronTrigger(minute=0) 
scheduler.start()

ROOT = Path(__file__).resolve().parents[0]

current_video_stream = None
stream_lock = threading.Lock()


from typing import Dict

process_list = []
labeler_process_list = []
active_camera_num = []
login_user_info = {}

alarm_info_data = {}
camera_info_data = {}
camera_img_temp = {}
auto_labeling_flag = False
auto_train_flag = False
auto_labeling_mode_flag = False
camera_page_permission = True

client_ip_dict = {}

torch.multiprocessing.set_start_method('spawn', force=True)


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
    video_save_flag = setting_info["AI"]["AutoLabel"]


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
            p = Process(target=ms_ai, args=([group, login_info["NVR"], weight_name, video_save_flag]))
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
    global auto_labeling_mode_flag

    file_name = data.msg["file_name"]
    info = data.msg["info"]
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : save info {file_name}")
    logger.info(f"save info {file_name}")


    save_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"), info)

    if file_name == "setting_info":
        auto_labeling_mode_flag = info["AI"]["AutoLabel"]
    
    return {"success": True}

@app.post("/load_camera_info")
async def camera_init(data : CameraInfoData):
    """카메라 정보 camera_info.json 로드"""
    """NVR에 연결된 카메라 정보 조회"""
    global process_list, alarm_info_data, camera_info_data
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

        process_list = []
        alarm_info_data = {}
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
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : end {data.msg}")
    logger.info(f"end {data.msg}")

    if data.msg == "ms_labeling":
        auto_labeling_flag = False
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
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : pause {data.msg}")
    logger.info(f"pause {data.msg}")

    if data.msg == "ms_labeling" and auto_labeling_flag == True:
        auto_labeling_flag = False
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
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    if len(labeler_process_list) == 0 and auto_train_flag == False and auto_labeling_flag == False:
        
        run_ms_labeler()
        auto_labeling_flag = True

    return {"success": auto_labeling_flag}

def run_ms_labeler():
    global labeler_process_list, auto_labeling_flag, auto_train_flag

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

@app.post("/start_trainer")
async def start_ms_trainer(data : MsgData):
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms train")
    logger.info(f"start ms train")

    if auto_train_flag == False and auto_labeling_flag == False:
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
    global scheduler, auto_labeling_mode_flag
    # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms-ai")
    logger.info(f"start ms-ai")

    # Stop existing jobs
    scheduler.remove_all_jobs()

    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
    auto_labeling_mode_flag = setting_info["AI"]["AutoLabel"]
    # print(auto_labeling_mode_flag)

    run_ms_ai()

    # scheduler.add_job(run_ms_ai, 'interval', hours=12)
    scheduler.add_job(run_ms_ai, trigger)

    return {"success": True}
    
def run_ms_ai():
    global process_list, camera_info_data, alarm_info_data, active_camera_num, auto_labeling_flag

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
    alarm_info_data = {}
    camera_info_data.clear()
    camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))

    process_list, active_camera_num = connect_camera_server(camera_dict, login_info, setting_info)

    current_hour = int(datetime.now().hour)  # 시간만 추출
    if (current_hour >= 22 or current_hour < 6) and len(labeler_process_list) == 0 and auto_labeling_mode_flag :
    # if (current_hour >= 9 or current_hour < 6) and len(labeler_process_list) == 0 and auto_labeling_mode_flag :

        auto_labeling_flag = True
        run_ms_labeler()

@app.put("/upload-ai-data")
async def upload_data(data: DictData):
    global camera_info_data, alarm_info_data, auto_labeling_mode_flag

    # auto_label_exec_flag = 0
    for camera_name, camera_info in data.msg.items():
        camera_info_data[camera_name] = camera_info

        if camera_info["alarm"]:
            for alarm in camera_info["alarm"]:
                if camera_name in alarm_info_data.keys():
                    alarm_info_data[camera_name].append(alarm)
                    # auto_label_exec_flag = 1

                else:
                    alarm_info_data[camera_name] = [alarm]
                    # auto_label_exec_flag = 1

            if len(alarm_info_data[camera_name]) > 25 :
                alarm_info_data[camera_name].pop(0)
    
    # if auto_label_exec_flag == 1 and auto_labeling_mode_flag :
        # await start_ms_labeler({"msg" : ""})

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
    global process_list, alarm_info_data, camera_info_data
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

    return {"success" : True, "data" : camera_connect_status_dict}

@app.get("/get-autolabel-info")
async def get_auto_label_info(data: DictData):
    global auto_labeling_flag, auto_train_flag

    cmd = data.msg["cmd"]

    # print(f"load {cmd}")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))

    if data.msg["cmd"] == "get_label_info":
        label_info_dict = {"label_flag" : auto_labeling_flag,
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

@app.get("/get_camera_page_permission")
async def get_camera_page_permission(data: MsgData):
    global camera_page_permission

    if camera_page_permission:
        camera_page_permission = False
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : allow camera page permission")
        logger.info(f"카메라 페이지 접근 허용")
        return True

    else:
        # print("reject camera page permission")
        logger.info(f"카메라 페이지 접근 거절")


        # return False
        return True
    
@app.put("/return_camera_page_permission")
async def return_camera_page_permission(data: MsgData):
    global camera_page_permission

    if camera_page_permission == False:
        # print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : return camera page permission")
        logger.info(f"카메라 페이지 접근 허용")


        camera_page_permission = True

    return False

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    # 앱 시작 시 스케줄러 시작
    scheduler.start()
    yield
    # 앱 종료 시 스케줄러 중지
    scheduler.shutdown()

if __name__ == "__main__" :
    import sys
    import os
    from pathlib import Path   

    try:
        import uvicorn

        vlm_process = subprocess.Popen([sys.executable, "VLM_main.py"])  # VLM_main.py는 FastAPI 서버 코드 파일
        
        try:
            camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
        except Exception as e:
            logger.error(f"Failed to load camera_info.json: {e}")
            logger.info("Initializing with empty camera dictionary")
            camera_dict = {}
            
        for name, info in camera_dict.items():
            info["AI"] = False
            
        save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)

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


 
