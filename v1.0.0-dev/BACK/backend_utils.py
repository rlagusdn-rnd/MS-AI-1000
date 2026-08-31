import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
import time
import numpy as np

import unicodedata

import os
import pickle
import datetime

import copy
import datetime
import os
import time
import traceback


from Crypto.Cipher import AES
import base64
from Crypto import Random

class aes_cipher:
    def __init__( self ):
        self.key = b"msvision561686740056168674005612"

    def pad(self, s):
        BS = 16
        return s + (BS - len(s.encode('utf-8')) % BS) * chr(BS - len(s.encode('utf-8')) % BS)
    def unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def enc( self, raw ):
        raw = self.pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw.encode('utf-8') ) ).decode()

    def dec( self, enc ):
        enc = base64.b64decode(enc.encode())
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return self.unpad(cipher.decrypt( enc[16:] )).decode()



"""
일반적으로 사용하는 공통함수 
"""
is_debug = True

# region 프로그램 관련 함수


#endregion

# region COMMON function
def clone(obj):
    return copy.deepcopy(obj)

def trim(string):
    return string.strip()

def fmti(value):
    return "{:,}".format(value)

def fmt(value, precision):
    return str(round(value, precision))

def filename_just(path):
    return os.path.basename(os.path.splitext(path)[0])

def now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def duration(start):
    return round(time.time() - start, 2)

def cut(value):
    return round(value, 3)

def error(ex):
    print(":: ERR :: " + str(ex))
    if is_debug : print(traceback.format_exc())
    #exit(1)

def warn(ex):
    print(":: WARNING :: " + str(ex))
    if is_debug : print(traceback.format_exc())

def debug(msg):
    if is_debug : print('DEBUG : ', msg)

def nullto(param, default=''):
    if param is None or param == '':
        return default
    else:
        return param

def unique_time():
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')

def filename(path):
    return os.path.basename(path)

def filename_just(path):
    return os.path.basename(os.path.splitext(path)[0])

def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False
#endregion



def get_roi(roi_dict_list) -> dict : 
    roi_list_dict = {}

    if len(roi_dict_list) == 0:
        return {None : [np.NaN, np.NaN]}
    
    else: # ROI 딕셔너리를 넘파이 배열로 변환
        for i in range(len(roi_dict_list)):
            roi_list = []
            event_kind  = kor_uni_decoder(roi_dict_list[i]['event_kind'])
            roi_pnt = roi_dict_list[i]['pnts']

            for j in range(len(roi_pnt)):
                roi_list.append([roi_pnt[j]['x'], roi_pnt[j]['y']])
            
            if event_kind not in roi_list_dict.keys():
                roi_list_dict[event_kind] = [np.array(roi_list)]
            else:
                roi_list_dict[event_kind].append(np.array(roi_list))

    return roi_list_dict
    

def kor_uni_decoder(uniCode) -> str :
    korean_str = unicodedata.normalize('NFC', uniCode) # 유니코드를 한글 문자로 변환

    if korean_str == '침입':
        detect_type = 'Intrusion'
    elif korean_str == '배회':
        detect_type = 'Loitering'
    elif korean_str == '출입확인':
        detect_type = 'Entering'
    elif korean_str == '방화':
        detect_type = 'Fire'
    elif korean_str == '쓰러짐':
        detect_type = 'Falldown'
    elif korean_str == '투기':
        detect_type = 'Abandonment'
    elif korean_str == '싸움':
        detect_type = 'Fight'
    else : detect_type = 'none'

    return detect_type


"""               
self.camera_group_info_dict[int(input_json["data"]["no"])]["process_time"]["start"] = input_json["data"]["group"]["process_time"][0]["start"]
self.camera_group_info_dict[int(input_json["data"]["no"])]["process_time"]["end"] = input_json["data"]["group"]["process_time"][0]["end"]
self.camera_group_info_dict[int(input_json["data"]["no"])]["process_time"]["weekday"] = input_json["data"]["group"]["process_time"][0]["weekday"]
"""


def make_group_dict(cameara_info_dict, group_info, path_info) -> dict:
    # 카메라 정보 딕셔너리를 그룹 정보 딕셔너리로 변환
    group_dict = {}
    index_cnt = 0
    for key, value in cameara_info_dict.items():
        group_name = value['group_name']

        if group_name in group_dict.keys():
            group_dict[group_name]["ID_list"].append(key)
        else:
            group_dict[group_name] = {"ID_list" : [key],\
                                    "AI_processing" : 0, \
                                    "snap_shot" : 0, \
                                    "record" : 0, \
                                    "video_save_path" : path_info["record"], \
                                    "img_save_path" : path_info["snapshot"], \
                                    "process_time" : {"start" : "00:00", "end" : "23:59","weekday" : [0,1,2,3,4,5,6]}, \
                                    "grid_size" : 1}

    # print("------------------------")
    # print(cameara_info_dict)
    # print("------------------------")
    # print(group_info)
    # print("------------------------")
    # print(group_dict)


    if len(group_dict):
        for group_name in group_dict.keys():

            if group_name != -1:
                group_dict[group_name]["AI_processing"] = group_info[index_cnt]["is_processing"]
                group_dict[group_name]["grid_size"] = group_info[index_cnt]["grid"]
                group_dict[group_name]["record"] = group_info[index_cnt]["is_recording"]
                if len(group_info[index_cnt]["process_time"]):
                    group_dict[group_name]["process_time"]["start"] = group_info[index_cnt]["process_time"][0]["start"]
                    group_dict[group_name]["process_time"]["end"] = group_info[index_cnt]["process_time"][0]["end"]
                    group_dict[group_name]["process_time"]["weekday"] = change_weekday(group_info[index_cnt]["process_time"][0]["weekday"])
                index_cnt += 1
            else:
                group_dict[group_name]["AI_processing"] = 0
                group_dict[group_name]["grid_size"] = 1


    return group_dict


def search_log_data(pickle_path, start, end, event_kind, target, order):
    """
    [[1687282074.7542226, 2, '침입', '0'],
    [1687282042.3066614, 2, '침입', '0'],
    [1687281985.19336, 2, '침입', '0'],
    [1687281912.2020948, 2, '침입', '0'],
    [1687281883.8457305, 2, '침입', '0'],
    [1687281843.715829, 2, '침입', '0'],
    [1687281842.814885, 2, '침입', '0'],
    [1687281669.8080804, 2, '침입', '0'],
    [1687281612.7147362, 2, '침입', '0'],
    [1687281605.736153, 2, '침입', '0'],
    [1687281602.7868292, 2, '침입', '0'],
    [1687281602.7868207, 2, '침입', '0'],
    [1687281553.8430648, 2, '침입', '0'],
    [1687281400.7954423, 2, '침입', '0'],
    [1687281281.9303348, 2, '침입', '0'],
    [1687280840.6179824, 2, '침입', '0'],
    [1687280727.864043, 2, '침입', '0'],
    [1687280712.528106, 2, '침입', '0'],
    [1687280712.5280962, 2, '침입', '0']]
    """
    log_data = pickle.load(open(pickle_path, 'rb'))

    search_data = []

    date_format = "%Y-%m-%d %H:%M:%S"

    # 문자열을 datetime 객체로 변환
    start_time = datetime.strptime(start, date_format).timestamp()
    end_time = datetime.strptime(end, date_format).timestamp()

    if event_kind == "침입":
        detect_type = "intrusion"
    elif event_kind == "배회":
        detect_type = "loitering"
    elif event_kind == "출입확인":
        # detect_type = "entering"
        detect_type = ["enter", "exit"]
    elif event_kind == "방화":
        detect_type = "fire"
    elif event_kind == "쓰러짐":
        detect_type = "falling"
    elif event_kind == "투기":
        detect_type = "abandonment"
    elif event_kind == "싸움":
        detect_type = "fighting"
    else : detect_type = "none"

    if event_kind == "출입확인":
        for camera_id, alarm_list in log_data.items():
            for alarm in alarm_list:
                if (alarm[0] in detect_type) and start_time <= alarm[1] <= end_time:
                    search_data.append([alarm[1], camera_id, event_kind, alarm[2]]) 

    else:
        for camera_id, alarm_list in log_data.items():
            for alarm in alarm_list:
                if alarm[0] == detect_type and start_time <= alarm[1] <= end_time:
                    search_data.append([alarm[1], camera_id, event_kind, alarm[2]])

    sorted_data = sorted(search_data, key=lambda x: x[0])

    if int(order) == -1:
        sorted_data = sorted_data[::-1]

    return sorted_data


def change_weekday(weekday: list) -> list:
    for i in range(len(weekday)):
        weekday[i] = weekday[i] - 1 if weekday[i] != 0 else 6

    return weekday

def check_time(process_time: dict) -> bool:
    # 현재 시간 구하기
    KST = datetime.timezone(timedelta(hours=9))

    now = datetime.datetime.now(KST)
    # print("now.weekday()", now.weekday() )
    # 요일에 따른 비교
    if now.weekday() not in process_time["weekday"]:
        return False
    
    # 시간 비교
    start = datetime.datetime.strptime(process_time["start"], "%H:%M")
    end = datetime.datetime.strptime(process_time["end"], "%H:%M")
    now_time = datetime.datetime.strptime(now.strftime('%H:%M'), '%H:%M')

    # print("start", start)
    # print("end", end)
    # print("now_time", now_time)
    
    if start <= end:
        return start <= now_time <= end
    else:
        return now_time >= start or now_time <= end