import os
import json
import requests
import shutil
from requests.auth import HTTPBasicAuth

from multiprocessing import Process

import json

from back.ms_ai_main import ms_ai
from pydantic import BaseModel
from datetime import datetime
from aiortc import MediaStreamTrack

from cryptography.fernet import Fernet
import cv2

KEY = "FBRBdZIbc_ULGN_qOlZjdMLDLPPzdRJ2Nb63kX3wuDI="

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

class Colors:
    # Ultralytics color palette https://ultralytics.com/
    def __init__(self):
        # hex = matplotlib.colors.TABLEAU_COLORS.values()
        hexs = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB',
                '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
        self.palette = [self.hex2rgb(f'#{c}') for c in hexs]
        self.n = len(self.palette)

    def __call__(self, i, bgr=False):
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):  # rgb order (PIL)
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))  

class VideoStreamTrack(MediaStreamTrack):
    def __init__(self, video_path):
        super().__init__()        
        self.kind = "video"
        self.cap = cv2.VideoCapture(video_path)

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return frame

class VideoStream:
    def __init__(self):
        self.cap = None
        self.active = False

    def start_stream(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.active = True

    def stop_stream(self):
        if self.cap:
            self.cap.release()
        self.active = False

    def generate_frames(self):
        while self.active:
            ret, frame = self.cap.read()
            if not ret or not self.active:
                break

            # frame = cv2.resize(frame, (0,0), fx = 0.7, fy = 0.7)
            frame = cv2.resize(frame, (0,0), fx = 1, fy = 1)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        self.stop_stream()


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


# def connect_camera_server(camera_info_dict, login_info, setting_info):
#     global process_list
#     process_list = []
#     active_camera_num = []

#     weight_name = setting_info["AI"]["Weight"]

#     ai_enabled_cameras = {}
#     now = datetime.now()
#     day = str((now.weekday() + 1) % 7)

#     # AI가 활성화된 카메라만 필터링
#     for name, info in camera_info_dict.items():
#         break_flag = False

#         if info["AI"] and info["active_week_days"][int(day)] == 1:
#             for detect_class, time_range in info["detect_schedule"][day].items():
#                 if break_flag == False:
#                     for time_ in time_range:
#                         if time_[0] <= now.hour <= time_[1] - 1:
#                             ai_enabled_cameras[name] = info
#                             break_flag = True
#                             active_camera_num.append(name)
#                             break

#     camera_count = len(ai_enabled_cameras)

#     if camera_count:
#         # 프로세스 수 결정 (최대 4개)
#         num_processes = min(4, camera_count)

#         # 각 프로세스에 할당될 카메라 수 계산
#         cameras_per_process = [camera_count // num_processes] * num_processes
#         for i in range(camera_count % num_processes):
#             cameras_per_process[i] += 1

#         # 카메라 정보를 그룹으로 분할
#         start = 0
#         camera_groups = []
#         for count in cameras_per_process:
#             group = dict(list(ai_enabled_cameras.items())[start:start + count])
#             camera_groups.append(group)
#             start += count

#         # 각 그룹에 대한 프로세스 시작
#         for group in camera_groups:
#             p = Process(target=ms_ai, args=([group, login_info["NVR"], weight_name, ]))
#             p.start()
#             process_list.append(p)

#     return process_list, active_camera_num

def connect_camera_server(camera_info_dict, login_info, setting_info):
    global process_list
    process_list = []
    active_camera_num = []

    weight_name = setting_info["AI"]["Weight"]
    video_save_flag = setting_info["VIDEO_SAVE"]["active"]


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


def check_alarm_video_history(nvr_ip : str, setting_info : dict):
    period = int(setting_info["VIDEO_SAVE"]["period"])
    date_format = "%y.%m.%d"
    today_date = datetime.today()

    alarm_video_path = os.path.join(os.getcwd(), "..", "backup", nvr_ip)
    camera_name_list : list = os.listdir(alarm_video_path)

    for camera_name in camera_name_list:
        if os.path.exists(os.path.join(alarm_video_path, camera_name)):
            date_list : list = os.listdir(os.path.join(alarm_video_path, camera_name))

            for date in date_list:
                start_date = datetime.strptime(date, date_format)
                if (today_date - start_date).days > period:
                    # os.remove(os.path.join(alarm_video_path, camera_name, date))
                    shutil.rmtree(os.path.join(alarm_video_path, camera_name, date))

def check_par_video_history(nvr_ip : str, setting_info : dict):
    period = int(setting_info["VIDEO_SAVE"]["period"])
    date_format = "%y-%m-%d"
    today_date = datetime.today()

    par_video_path = os.path.join(os.getcwd(), "..", "backup", "PAR", "done", nvr_ip)
    camera_name_list : list = os.listdir(par_video_path)

    for camera_name in camera_name_list:
        if os.path.exists(os.path.join(par_video_path, camera_name)):
            date_list : list = os.listdir(os.path.join(par_video_path, camera_name))

            for date in date_list:
                start_date = datetime.strptime(date, date_format)
                if (today_date - start_date).days > period:
                    # os.remove(os.path.join(alarm_video_path, camera_name, date))
                    shutil.rmtree(os.path.join(par_video_path, camera_name, date))

def get_init_camera_dict(camera):
    camera_id = ""
    camera_pw = ""
    
    return {"Name" : camera["name"],
            "Num" :camera["id"],
            "IP" : camera["address"],
            "ID" : camera_id,
            "PW" : camera_pw,
            "detect_info" : [],
            "AI" : False,
            "Cls" : [True, True, True, False],
            "Conf" : [33, 33, 33],
            "ParTime" : [0, 0],

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