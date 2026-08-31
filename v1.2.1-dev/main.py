import sys
import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth

from multiprocessing import Process

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import torch
from datetime import datetime

from back.ms_labeler_main import ms_labeler, train
from back.utils import send_NVR_empty

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import StreamingResponse
import threading

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
                   connect_camera_server,
                   check_alarm_video_history
                    )

import cv2
import numpy as np
import base64
import shutil

from aiortc import RTCPeerConnection
from turbojpeg import TurboJPEG

app = FastAPI()
scheduler = BackgroundScheduler()
trigger = CronTrigger(minute=0) 
scheduler.start()

ROOT = Path(__file__).resolve().parents[0]

current_video_stream = None
stream_lock = threading.Lock()


sys.path.append(str(ROOT / 'front'))  

from typing import Dict

process_list = []
labeler_process_list = []
active_camera_num = []
login_user_info = {}

alarm_info_data = {}
camera_info_data = {}
auto_labeling_flag = False
auto_train_flag = False
auto_labeling_mode_flag = False
camera_page_permission = True
conntect_user_num = 0

torch.multiprocessing.set_start_method('spawn', force=True)

def get_camera_list(ip, id , pw, reset_flag):
    global process_list, alarm_info_data, camera_info_data
    camera_dict = {}
    camera_info_ori = {}
    auth = HTTPBasicAuth(id, pw) # NVR에 대한 ID / PW
    camera_post = f'http://{ip}/api/cameras'
    try:
        r = requests.get(camera_post,auth=auth, timeout= 1)
    except:
        print("NVR 연결 실패")
        return camera_dict

    if len(ip)  == 0 or  len(id) == 0:
        print("NVR 연결 실패")
        return camera_dict

    if reset_flag == False :
        if str(r) == "<Response [200]>":
            camera_info_ori = r.json()

        camera_dict = load_crypography_json(os.path.join(os.getcwd(), "cache", "camera_info.json"))

        # for camera_name, camera_info in camera_dict.items():
        #     camera_info["AI"] = False

        # save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)


    else :
        if len(process_list):
            for process in process_list:
                process.terminate()

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

                camera_id = ""
                camera_pw = ""

                camera_dict[camera["name"]] = {"Name" : camera["name"],
                                                "Num" :camera["id"],
                                            "IP" : camera["address"],
                                            "ID" : camera_id,
                                            "PW" : camera_pw,
                                            "detect_info" : [],
                                            "AI" : False,
                                            "Conf" : 33,
                                            "detect_schedule" : {"0" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },
                                                                "1" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },

                                                                "2" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },

                                                                "3" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },

                                                                "4" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },

                                                                "5" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]
                                                                        },

                                                                "6" : {"Intrusion" : [[0,24]],
                                                                        "Fire" : [[0,24]],
                                                                        "Loitering" : [[0,24]],
                                                                        "Falldown" : [[0,24]],
                                                                        "Fight" : [[0,24]]}},
                                            "active_week_days" : [1,1,1,1,1,1,1]
                                            }
                
            save_crypography_json(os.path.join(os.getcwd(), "cache", "camera_info.json"), camera_dict)
            # except Exception as e:
            #     print(11111)
            #     current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #     tb = traceback.format_exc()
            #     print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
            #     return camera_dict
    # return camera_dict, camera_info_ori
    return camera_dict


@app.post("/get_ai_weight_list")
async def get_ai_weight_list(data: DictData):
    weight_path = os.path.join(os.getcwd(), "back", "weight", "yolo")
    weight_list = sorted(os.listdir(weight_path))
                
    return {"weight_list": weight_list}

@app.post("/login")
async def login(data: DictData):
    global conntect_user_num, login_user_info
    user_name = data.msg["id"]
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login {user_name}")
    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))

    os.makedirs(os.path.join(os.getcwd(), "..", "backup", login_info["NVR"]["IP"]), exist_ok=True)

    check_alarm_video_history(login_info["NVR"]["IP"], setting_info)

    if data.msg["id"] == "admin" and data.msg["password"] == login_info["USER"]["admin"]:
        conntect_user_num += 1
        return {"success": True, "data": login_info["NVR"], "user_info" : "admin"}
    
    if data.msg["id"] in login_info["USER"].keys():
        if login_info["USER"][data.msg["id"]] == data.msg["password"]:
            conntect_user_num += 1
            login_user_info[login_info["USER"][data.msg["id"]]] = False

            return {"success": True, "data": login_info["NVR"], "user_info" : data.msg["id"]}

    return {"success": False, "data": "Invalid ID and PW"}

@app.post("/login_admin_page")
async def login_admin_page(data: MsgData):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login_admin_page")

    if data.msg == "0512":
        return {"msg": True}
    else:
        return {"msg": False}

@app.post("/login_info_chg")
async def login_chg(data: Login_Chg_Data):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login info change")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    if data.username in login_info["USER"].keys():
        if data.password == login_info["USER"][data.username]:
            if data.new_password == data.new_password2:
                login_info["USER"][data.username] = data.new_password
                save_crypography_json(os.path.join(ROOT, "cache", "login_info.json"), login_info)
                return {"success": True, "message": "Change ID and PW"}
            
            else: return {"success": False, "message": "Invalid New Pw"}
        else:
            return {"success": False, "message": "Invalid ID and PW"}

@app.post("/login_nvr")
async def login(data: DictData):
    try:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : login NVR")

        nvr_ip = data.msg["ip"]
        nvr_id = data.msg["id"]
        nvr_pw = data.msg["pw"]

        auth = HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW
        camera_post = f'http://{nvr_ip}/api/cameras'
        # try:
        r = requests.get(camera_post,auth=auth, timeout= 1)
        if str(r) == "<Response [200]>":
            return {"success": True, "message": f"success login NVR"}

        else:
            return {"success": False, "message": f"{r}"}

    except:
        return {"success": False, "message": "error"}

@app.post("/load_info")
async def load_info(data: DictData):
    file_name = data.msg["file_name"]
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : load info {file_name}")

    file_info = load_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"))

    return {"success": True, "data": file_info}

@app.post("/save_info")
async def save_info(data: DictData):

    file_name = data.msg["file_name"]
    info = data.msg["info"]
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : save info {file_name}")

    save_crypography_json(os.path.join(ROOT, "cache", f"{file_name}.json"), info)

    return {"success": True}

@app.post("/load_camera_info")
async def camera_init(data : CameraInfoData):
    # print(f"load camera info")

    reset_flag = data.reset
    
    if reset_flag == False:
        reset_flag = False if "camera_info.json" in os.listdir(os.path.join(ROOT, "cache")) else True

    camera_dict = get_camera_list(ip=data.ip, id=data.id, pw=data.pw, reset_flag=reset_flag)

    if len(camera_dict):
        return {"success": True, "data": camera_dict}

    else:
        return {"success": False}

@app.put("/end_ms_labeler")
async def end_ms_labeler(data : MsgData):
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : end {data.msg}")

    if data.msg == "ms_labeling":
        auto_labeling_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()
    elif data.msg == "ms_train":
        auto_train_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()

    return True

@app.put("/pause_ms_labeler")
async def pause_ms_labeler(data : MsgData):
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : pause {data.msg}")

    if data.msg == "ms_labeling" and auto_labeling_flag == True:
        auto_labeling_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()

    elif data.msg == "ms_train" and auto_train_flag == True:
        auto_train_flag = False
        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()

    return True

@app.put("/start_ms_labeler")
async def start_ms_labeler(data : MsgData):
    global labeler_process_list, auto_labeling_flag, auto_train_flag


    if auto_train_flag == False and auto_labeling_flag == False:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms labeler")

        login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
        camera_list_path = os.path.join(os.getcwd(), ".." ,"backup", login_info["NVR"]["IP"])

        setting_info = load_crypography_json(os.path.join(ROOT, "cache", "setting_info.json"))
        weight_name = setting_info["AI"]["Weight"]
        zero_shot_flag = setting_info["AI"]["ZeroShot"]

        p = Process(target=ms_labeler, args=([camera_list_path, weight_name, zero_shot_flag]))
        p.start()

        labeler_process_list.append(p)

        auto_labeling_flag = True

    return {"success": auto_labeling_flag}

@app.post("/start_trainer")
async def start_ms_trainer(data : MsgData):
    global labeler_process_list, auto_labeling_flag, auto_train_flag

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms train")

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
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start ms-ai")
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
    global process_list, camera_info_data, alarm_info_data, active_camera_num

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

@app.put("/upload-ai-data")
async def upload_data(data: DictData):
    global camera_info_data, alarm_info_data, auto_labeling_mode_flag

    auto_label_exec_flag = 0
    for camera_name, camera_info in data.msg.items():
        camera_info_data[camera_name] = camera_info

        if camera_info["alarm"]:
            for alarm in camera_info["alarm"]:
                if camera_name in alarm_info_data.keys():
                    alarm_info_data[camera_name].append(alarm)
                    auto_label_exec_flag = 1

                else:
                    alarm_info_data[camera_name] = [alarm]
                    auto_label_exec_flag = 1

            if len(alarm_info_data[camera_name]) > 25 :
                alarm_info_data[camera_name].pop(0)
    
    if auto_label_exec_flag == 1 and auto_labeling_mode_flag :
        await start_ms_labeler({"msg" : ""})

    return {"message": "Data stored successfully"}

@app.get("/get-camera-info")
async def retrieve_data(data: MsgData):
    global camera_info_data
    camera_name = data.msg
    # 데이터 검색
    if camera_name in active_camera_num and camera_name in camera_info_data.keys():
        data = camera_info_data[camera_name]
        return { camera_name  : data}
    return {camera_name  : False}


@app.get("/get-search-info")
async def get_search_info(data: DictData):
    print("load search info")
    #{'before_day': '24.08.28', 'after_day': '24.08.28', 'time_start': '00.00.00', 'time_end': '23.59.00', 'camera_num': '*', 'search_detect_type': ['침입', '배회', '방화', '쓰러짐', '싸움']}
    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    alarm_save_path = os.path.join(ROOT, ".." , "backup", login_info["NVR"]["IP"])
    camera_list = os.listdir(alarm_save_path)

    alarm_list = []

    camera_num = data.msg["camera_num"]
    before_day = data.msg["before_day"]
    time_start = data.msg["time_start"]
    time_end = data.msg["time_end"]
    after_day = data.msg["after_day"]
    search_detect_type = data.msg["search_detect_type"]

    for camera_name in camera_list:
        if camera_num == "*":
            date_list = os.listdir(os.path.join(alarm_save_path, camera_name))

            for date in date_list:
                if datetime.strptime(before_day, "%y.%m.%d") <= datetime.strptime(date, "%y.%m.%d") <= datetime.strptime(after_day, "%y.%m.%d"):
                    video_list = os.listdir(os.path.join(alarm_save_path, camera_name, date, "videos"))
                    for video_name in video_list:
                        video_time, detect_type = video_name.split("_")[0], video_name.split("_")[1][:-4]
                        if (detect_type in search_detect_type) and datetime.strptime(time_start, "%H.%M.%S") <= datetime.strptime(video_time, "%H.%M.%S") <= datetime.strptime(time_end, "%H.%M.%S"):
                            alarm_list.append(os.path.join(camera_name, date, "videos", video_name))

        elif camera_num == camera_name.split("_")[-1]:
            date_list = os.listdir(os.path.join(alarm_save_path, camera_name))

            for date in date_list:
                if datetime.strptime(before_day, "%y.%m.%d") <= datetime.strptime(date, "%y.%m.%d") <= datetime.strptime(after_day, "%y.%m.%d"):
                    video_list = os.listdir(os.path.join(alarm_save_path, camera_name, date, "videos"))
                    for video_name in video_list:
                        video_time, detect_type = video_name.split("_")[0], video_name.split("_")[1][:-4]
                        if (detect_type in search_detect_type) and datetime.strptime(time_start, "%H.%M.%S") <= datetime.strptime(video_time, "%H.%M.%S") <= datetime.strptime(time_end, "%H.%M.%S"):
                            alarm_list.append(os.path.join(camera_name, date, "videos", video_name))


    return {"data"  : alarm_list}

# @app.post("/get-search-video")
# async def get_search_video(data: MsgData):
#     global current_video_stream

#     print("load video")

#     login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
#     nvr_ip = login_info["NVR"]["IP"]
#     video_name = data.msg

#     video_path = os.path.join(os.getcwd(), ".." ,"backup", nvr_ip, video_name)

#     with stream_lock:
#         if current_video_stream:
#             current_video_stream.stop_stream()
#             del current_video_stream
#             current_video_stream = None

#         current_video_stream = VideoStream()
#         current_video_stream.start_stream(video_path)

#     return StreamingResponse(current_video_stream.generate_frames(), media_type='multipart/x-mixed-replace; boundary=frame')


@app.get("/get-search-video")
async def get_search_video(data: MsgData):
    global current_video_stream

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : load alarm video")

    login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
    nvr_ip = login_info["NVR"]["IP"]
    video_name = data.msg

    video_path = os.path.join(os.getcwd(), ".." ,"backup", nvr_ip, video_name)

    pc = RTCPeerConnection()
    video_track = VideoStreamTrack(video_path)
    pc.addTrack(video_track)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    async def stream_video():
        jpeg = TurboJPEG()

        while True:
            frame = await video_track.recv()
            if frame is None:
                print("video_finish")
                break
            # ret, buffer = cv2.imencode(".jpg", frame)
            # yield (
                # b"--frame\r\n"
                # b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
            # )
            buffer = jpeg.encode(frame)	
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer + b"\r\n"
            )


    return StreamingResponse(
        stream_video(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

# @app.get("/get-search-video")
# async def stream_video(data: MsgData):
#     print("load video")

#     login_info = load_crypography_json(os.path.join(ROOT, "cache", "login_info.json"))
#     nvr_ip = login_info["NVR"]["IP"]
#     video_name = data.msg

#     video_path = os.path.join(os.getcwd(), ".." ,"backup", nvr_ip, video_name)

#     if not os.path.isfile(video_path):
#         raise HTTPException(status_code=404, detail="Video not found")

#     def video_stream():
#         with open(video_path, "rb") as video_file:
#             while chunk := video_file.read(1024):  # 1KB 단위로 읽기
#                 yield chunk
#         print("finish")
#     return StreamingResponse(video_stream(), media_type="video/mp4")

@app.get("/get-status-info")
async def get_status_info(data: MsgData):
    global alarm_info_data, conntect_user_num

    data = alarm_info_data.copy()
    alarm_info_data = {}

    return {"data" : data, "user_num" : conntect_user_num}

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
                        label_info_dict["label_data_info"][camera_name][date] = []
                        event_list = sorted(os.listdir(event_path))

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
                    color = Colors()
                    for line in file:
                        line = line.strip()
                        cls, xc, yc, w, h = line.split(" ")
                        # color = (tuple(np.random.randint(0, 255, size=3).tolist()))
                        label_list.append([int(cls), float(xc), float(yc), float(w), float(h), color(object_num)])
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
                    cls, xc, yc, w, h, _ = label
                    file.write(f"{cls} {np.round(xc,3)} {np.round(yc,3)} {np.round(w,3)} {np.round(h,3)}\n")
        
        
        if "done" not in event_name.split("_"):
            os.rename(os.path.join(os.getcwd(),".." , "backup","dataset",login_info["NVR"]["IP"],camera_name,date,event_name), 
                        os.path.join(os.getcwd(),".." , "backup","dataset",login_info["NVR"]["IP"],camera_name,date,f"{event_name}_done"))
            
        return {"msg" : True}

@app.get("/get_camera_page_permission")
async def get_camera_page_permission(data: MsgData):
    global camera_page_permission

    if camera_page_permission:
        camera_page_permission = False
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : allow camera page permission")
        return True

    else:
        print("reject camera page permission")

        # return False
        return True
    
@app.put("/return_camera_page_permission")
async def return_camera_page_permission(data: MsgData):
    global camera_page_permission

    if camera_page_permission == False:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : return camera page permission")

        camera_page_permission = True

    return False

@app.put("/logout")
async def logout(data : MsgData):
    global conntect_user_num
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : user logout")

    conntect_user_num -= 1

    if conntect_user_num < 0 : conntect_user_num = 0


@app.put("/exit")
async def exit_server(data : MsgData):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : exit")

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

            print("Server is shutting down...")
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
        
        camera_dict = load_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"))
        for name, info in camera_dict.items():
            info["AI"] = False
        save_crypography_json(os.path.join(ROOT, "cache", "camera_info.json"), camera_dict)

        # uvicorn.run(app, host="0.0.0.0", port=65432, log_level="warning")
        uvicorn.run(app, host="0.0.0.0", port=12345, log_level="warning")

        # uvicorn.run(app, host="0.0.0.0", port=65432)

        # main()
        # print("start server")

    finally:
        os.system("chmod -R 777 ../backup")

        if len(process_list):
            for process in process_list:
                process.terminate()

        if len(labeler_process_list):
            for process in labeler_process_list:
                process.terminate()



