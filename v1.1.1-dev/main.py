import cv2
import numpy as np
import time
import sys
import os
from pathlib import Path
import json
import requests
from requests.auth import HTTPBasicAuth

from multiprocessing import Process

import socket
import json

import torch

from back.ms_ai_main import ms_ai
from back.utils.util import send_NVR_empty

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import math
from datetime import datetime

# NVR_IP = "117.17.159.2"
# NVR_IP = "117.17.159.143"

# NVR_ID = "admin"
# NVR_PW = "1234"
from cryptography.fernet import Fernet
KEY = "FBRBdZIbc_ULGN_qOlZjdMLDLPPzdRJ2Nb63kX3wuDI="

app = FastAPI()

ROOT = Path(__file__).resolve().parents[0]

sys.path.append(str(ROOT / 'front'))  

from front import run_GUI
from typing import Dict

process_list = []
active_camera_num = []
alarm_info_data = {}
camera_info_data = {}

p_front = Process(target=run_GUI.main)

torch.multiprocessing.set_start_method('spawn', force=True)

def load_json(info_filename):
    with open(info_filename, "r", encoding="UTF-8") as f:
        return json.load(f)

def save_json(info_filename_save_path, info):
    with open(info_filename_save_path, "w", encoding="UTF-8") as f:
        f.write(json.dumps(info, indent=4))

def load_crypography_json(info_filename):
    fernet = Fernet(KEY)
    with open(info_filename, "rb") as f:
        file = f.read()
        file_tran = fernet.decrypt(file)
        return json.loads(file_tran.decode())

def save_crypography_json(info_filename_save_path, info):
    fernet = Fernet(KEY)
    # 딕셔너리를 JSON 문자열로 변환
    json_data = json.dumps(info)
    # JSON 문자열을 바이트로 인코딩
    byte_data = json_data.encode('utf-8')

    with open(info_filename_save_path, "wb") as f:
        f.write(fernet.encrypt(byte_data))

def get_camera_list(ip, id , pw, reset_flag):
    global process_list, alarm_info_data, camera_info_data
    camera_dict = {}

    if len(ip)  == 0 or  len(id) == 0:
        print("NVR 연결 실패")
        return camera_dict

    if reset_flag == False :
        camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))

        for camera_name, camera_info in camera_dict.items():
            camera_info["AI"] = False

        save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)


    else :
        if len(process_list):
            for process in process_list:
                process.terminate()

        process_list = []
        alarm_info_data = {}
        camera_info_data = {}

        auth = HTTPBasicAuth(id, pw) # NVR에 대한 ID / PW
        camera_post = f'http://{ip}/api/cameras'
        try:
            r = requests.get(camera_post,auth=auth, timeout= 3)
            camera_info = r.json()

            for camera in camera_info["cameras"]:
                """
                {'id': 1, 'name': '카메라 1', 'address': '117.17.159.195', 
                'location': '', 'source': 1, 'channel': 1, 
                'connected': True, 'has_signal': True, 
                'has_ptz': True, 'streaming': True, 
                'http_url': 'http://117.17.159.195/', 
                'note': '', 'ptz_presets': [], 'ptz_tours': [], 
                'osd': [{'text': '', 'size': 10, 'color': '#ffffff', 'location': 'top-right'}]},
                """
                camera_id = ""
                camera_pw = ""

                camera_dict[camera["name"]] = {"Name" : camera["name"],
                                             "Num" :camera["id"],
                                            "IP" : camera["address"],
                                            "ID" : camera_id,
                                            "PW" : camera_pw,
                                            "detect_info" : [],
                                            "AI" : False,
                                            "Conf" : 50,
                                            "detect_schedule" : {"0" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},
                                                                "1" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},

                                                                "2" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},

                                                                "3" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},

                                                                "4" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},

                                                                "5" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []},

                                                                "6" : {"Intrusion" : [],
                                                                        "Fire" : [],
                                                                        "Loitering" : [],
                                                                        "Falldown" : []}},
                                            "active_week_days" : [1,1,1,1,1,1,1]
                                            }
                
            save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)
        except:
            print("NVR 연결 실패")
            return camera_dict
    return camera_dict

def connect_camera_server(camera_info_dict, login_info):
    global process_list
    process_list = []
    active_camera_num = []

    ai_enabled_cameras = {}
    now = datetime.now()
    day = str((now.weekday() + 1) % 7)

    # AI가 활성화된 카메라만 필터링
    for name, info in camera_info_dict.items():
        break_flag = False

        if info["AI"] and info["active_week_days"][int(day)] == 1:
            for detect_class, time_range in info["detect_schedule"][day].items():
                if break_flag == False:
                    for time_ in time_range:
                        if time_[0] <= now.hour <= time_[1]:
                            ai_enabled_cameras[name] = info
                            break_flag = True
                            print(f"active camera {name}")
                            active_camera_num.append(name)
                            break

    camera_count = len(ai_enabled_cameras)

    if camera_count:
        # 프로세스 수 결정 (최대 4개)
        num_processes = min(4, camera_count)

        # 각 프로세스에 할당될 카메라 수 계산
        cameras_per_process = [camera_count // num_processes] * num_processes
        for i in range(camera_count % num_processes):
            cameras_per_process[i] += 1

        # 카메라 정보를 그룹으로 분할
        start = 0
        camera_groups = []
        for count in cameras_per_process:
            group = dict(list(ai_enabled_cameras.items())[start:start + count])
            camera_groups.append(group)
            start += count

        # 각 그룹에 대한 프로세스 시작
        for group in camera_groups:
            p = Process(target=ms_ai, args=([group, ROOT, login_info["NVR"]]))
            p.start()
            process_list.append(p)

    return process_list, active_camera_num

# 로그인 정보 확인
class LoginData(BaseModel):
    username: str
    password: str

class CameraInfoData(BaseModel):
    ip: str
    id: str
    pw: str
    reset : bool

class Login_Chg_Data(BaseModel):
    username: str
    password: str
    new_password: str
    new_password2: str

class MsgData(BaseModel):
    msg : str


class DictData(BaseModel):
    msg: dict 


class AiMsgData(BaseModel):
    msg: dict 

@app.post("/login")
async def login(data: DictData):
    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    if data.msg["id"] == login_info["ms_ai"]["ID"] and data.msg["password"] == login_info["ms_ai"]["PW"]:
        return {"success": True, "data": login_info["NVR"], "user_info" : "user"}
    
    elif data.msg["id"] == "admin" and data.msg["password"] == "admin":
        return {"success": True, "data": login_info["NVR"], "user_info" : "admin"}

    else:
        return {"success": False, "data": "Invalid ID and PW"}

@app.post("/login_chg")
async def login_chg(data: Login_Chg_Data):
    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    if data.username == login_info["ms_ai"]["ID"] and data.password == login_info["ms_ai"]["PW"]:
        if data.new_password == data.new_password2:
            login_info["ms_ai"]["ID"] = data.username
            login_info["ms_ai"]["PW"] = data.new_password
            save_crypography_json(os.path.join(ROOT, "cache", "login_info.json"), login_info)
            return {"success": True, "message": "Change ID and PW"}
        else: return {"success": False, "message": "Invalid New Pw"}
    else:

        return {"success": False, "message": "Invalid ID and PW"}

@app.post("/load_info")
async def load_info(data: DictData):
    file_name = data.msg["file_name"]

    file_info = load_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"))

    return {"success": True, "data": file_info}

@app.post("/save_info")
async def save_info(data: DictData):
    file_name = data.msg["file_name"]
    info = data.msg["info"]

    save_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"), info)

    return {"success": True}

@app.post("/camera_init")
async def camera_init(data : CameraInfoData):
    # try:
    #     reset_flag = data.reset
    #     if reset_flag == False:
    #         reset_flag = False if "camera_info.json" in os.listdir("cache") else True

    #     camera_dict = get_camera_list(ip=data.ip, id=data.id, pw=data.pw, reset_flag=reset_flag)

    #     print(camera_dict)

    #     if len(camera_dict):
    #         return {"success": True, "data": camera_dict}

    #     else:
    #         return {"success": False}

    # except:
    #     return {"success": False}

    reset_flag = data.reset
    if reset_flag == False:
        reset_flag = False if "camera_info.json" in os.listdir(os.path.join(ROOT, "cache")) else True

    camera_dict = get_camera_list(ip=data.ip, id=data.id, pw=data.pw, reset_flag=reset_flag)

    if len(camera_dict):
        return {"success": True, "data": camera_dict}

    else:
        return {"success": False}

@app.post("/run_ms_ai")
async def camera_info(data : MsgData):
    global process_list, camera_info_data, alarm_info_data, active_camera_num

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))

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

    process_list, active_camera_num = connect_camera_server(camera_dict, login_info)
    
    return {"success": True}

@app.post("/upload-data")
async def upload_data(data: AiMsgData):
    global camera_info_data
    for camera_name, camera_info in data.msg.items():
        camera_info_data[camera_name] = camera_info
    return {"message": "Data stored successfully"}

@app.get("/get-camera-info")
async def retrieve_data(data: MsgData):
    global camera_info_data
    camera_num = data.msg
    # 데이터 검색
    if camera_num in active_camera_num and camera_num in camera_info_data.keys():
        data = camera_info_data[camera_num].copy()
        return { camera_num  : data}
    return {camera_num  : False}

@app.post("/upload-alarm")
async def upload_data(data: AiMsgData):
    global alarm_info_data
    for camera_num, alarm_info in data.msg.items():
        if camera_num in alarm_info_data.keys():
            alarm_info_data[camera_num].append(alarm_info)

            if len(alarm_info_data) > 25 :
                alarm_info_data.pop(0)

        else:
            alarm_info_data[camera_num] = [alarm_info]

    return {"message": "Data stored successfully"}

@app.get("/get-alarm-info")
async def retrieve_data(data: MsgData):
    global alarm_info_data

    data = alarm_info_data.copy()
    alarm_info_data = {}

    return {"data" : data}

@app.put("/exit")
async def exit_server(data : MsgData):
    global process_list, p_front

    try:
        p_front.terminate()

        if len(process_list):
            for process in process_list:
                process.terminate()

    finally:
            login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
            
            if len(login_info["NVR"]["IP"]):
                send_NVR_empty(nvr_ip = login_info["NVR"]["IP"], nvr_id = login_info["NVR"]["ID"], nvr_pw = login_info["NVR"]["PW"])

            print("Server is shutting down...")
            os._exit(0)

if __name__ == "__main__" :
    import sys
    import os
    from pathlib import Path

    try:
        p_front.start()
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=65432, log_level="warning")
        # main()
        print("start front")

    finally:
        p_front.terminate()

        os.system("chmod -R 777 ./backup")

        if len(process_list):
            for process in process_list:
                process.terminate()

