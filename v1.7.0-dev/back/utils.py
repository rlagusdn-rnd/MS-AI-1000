import os
import sys
import numpy as np
import threading
import queue
import torch
import random
import cv2
import requests
from requests.auth import HTTPBasicAuth
import time
from datetime import datetime
import traceback
import gc
from typing import List, Tuple, Union

# ============== Latest-Only Worker Pattern for AI Info Sender ==============
# 최신 데이터만 유지 (스택/큐 대신 단일 변수 사용)
_ai_info_latest_data = None  # (url, data) 튜플
_ai_info_data_lock = threading.Lock()
_ai_info_new_data_event = threading.Event()
_ai_info_worker_running = False
_ai_info_worker_lock = threading.Lock()

def _ai_info_sender_worker():
    """백그라운드에서 최신 데이터만 전송하는 워커 스레드"""
    global _ai_info_latest_data
    while True:
        try:
            # 새 데이터가 올 때까지 대기 (최대 1초)
            if _ai_info_new_data_event.wait(timeout=1.0):
                # 최신 데이터 가져오기 (락 사용)
                with _ai_info_data_lock:
                    if _ai_info_latest_data is None:
                        continue
                    url, data = _ai_info_latest_data
                    _ai_info_latest_data = None  # 데이터 클리어
                    _ai_info_new_data_event.clear()  # 이벤트 리셋
                
                # HTTP 전송 (락 밖에서 수행)
                try:
                    requests.put(url, json={"msg": data}, timeout=1.0)
                except requests.exceptions.RequestException:
                    pass  # 네트워크 오류 시 무시
        except Exception:
            pass

def start_ai_info_sender_worker():
    """AI Info 전송 워커 스레드 시작 (한 번만 호출됨)"""
    global _ai_info_worker_running
    with _ai_info_worker_lock:
        if not _ai_info_worker_running:
            _ai_info_worker_running = True
            worker_thread = threading.Thread(target=_ai_info_sender_worker, daemon=True)
            worker_thread.start()
# ========================================================================

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

def TF_detect_area(detect_info: Union[list, str], img_size):
    TF_detect_area_list = []
    if len(detect_info):
        if isinstance(detect_info[0], list): 
            for item in detect_info:
                # 새로운 리스트의 첫 번째 요소는 기존 문자열 그대로 유지
                label = item[0]
                coordinates = item[1:]

                # 좌표에 대한 변환 수행
                transformed_coordinates = [[int(x[0] * img_size[0]), int(x[1] * img_size[1])] for x in coordinates]
                
                # 변환된 좌표를 포함하는 새로운 리스트 생성
                TF_detect_area_list.append([label] + transformed_coordinates)

        elif isinstance(detect_info[0], str): 
            label = detect_info[0]
            coordinates = detect_info[1:]

            # 좌표에 대한 변환 수행
            transformed_coordinates = [[int(x[0] * img_size[0]), int(x[1] * img_size[1])] for x in coordinates]
            
            # 변환된 좌표를 포함하는 새로운 리스트 생성
            TF_detect_area_list.append([label] + transformed_coordinates)

    return TF_detect_area_list

def Eng2kor(eng):
    if eng == "Intrusion": return "침입"
    elif eng == "Loitering": return "배회"
    elif eng == "Falldown": return "쓰러짐"
    elif eng == "Fire": return "방화"
    elif eng == "Fight": return "싸움"
    elif eng == "Trash": return "무단투기"


def TF_bbox(bbox, ori_imsz=(640, 360), target_imsz=(1920, 1080)):
    # 원본 이미지와 목표 이미지의 크기 비율 계산
    width_ratio = target_imsz[0] / ori_imsz[0]
    height_ratio = target_imsz[1] / ori_imsz[1]
    
    # 변환된 바운딩 박스를 저장할 리스트 초기화
    TF_boxes = []
    
    # 각 바운딩 박스에 대해 좌표 변환 수행
    for box in bbox:
        if len(box) == 8:
            x1, y1, x2, y2, id, conf, cls, ind  = box  # 좌표 추출
            # 좌표를 int(새로운 이미지 크기에 맞게 조정
            new_x1 = int(x1 * width_ratio)
            new_y1 = int(y1 * height_ratio)
            new_x2 = int(x2 * width_ratio)
            new_y2 = int(y2 * height_ratio)
        
            # 변환된 좌표와 기존 정보를 합쳐 새로운 리스트 생성
            TF_boxes.append([new_x1, new_y1, new_x2, new_y2, id, conf, cls, ind])
        
        elif len(box) == 6:
            x1, y1, x2, y2, conf, cls, = box  # 좌표 추출

            # 좌표를 int(새로운 이미지 크기에 맞게 조정
            new_x1 = int(x1 * width_ratio)
            new_y1 = int(y1 * height_ratio)
            new_x2 = int(x2 * width_ratio)
            new_y2 = int(y2 * height_ratio)
            
            # 변환된 좌표와 기존 정보를 합쳐 새로운 리스트 생성
            TF_boxes.append([new_x1, new_y1, new_x2, new_y2, conf, cls])

        elif len(box) == 9:
                x1, y1, x2, y2, id, conf, cls, ind, status = box  # 좌표 추출
                # 좌표를 int(새로운 이미지 크기에 맞게 조정
                new_x1 = int(x1 * width_ratio)
                new_y1 = int(y1 * height_ratio)
                new_x2 = int(x2 * width_ratio)
                new_y2 = int(y2 * height_ratio)
            
                # 변환된 좌표와 기존 정보를 합쳐 새로운 리스트 생성
                TF_boxes.append([new_x1, new_y1, new_x2, new_y2, id, conf, cls, ind, status])
        
    return TF_boxes

def check_point_in_area(point, detect_area_list):
    return cv2.pointPolygonTest(detect_area_list, point, False) == 1

def update_bbox_lists(cls, conf, person_conf_score, fire_conf_score, bbox, new_person_bbox, new_non_person_bbox):
    if cls == 0 and conf > person_conf_score:
        new_person_bbox.append(bbox)
    elif cls == 1 and conf > fire_conf_score:
        new_non_person_bbox.append(bbox)

def remove_out_of_BBox(camera_info_dict, bbox_bn, num_to_camera_name):
    try:
        bn_new_person_bbox = []
        bn_new_non_person_bbox = []

        for index, bbox in enumerate(bbox_bn):
            new_person_bbox = []
            new_non_person_bbox = []
            bbox_array = bbox.boxes.data.cpu().numpy().astype(float)
            camera_info = camera_info_dict[num_to_camera_name[index]]
            person_conf_score = camera_info["object_conf_score"][0]
            car_conf_score = camera_info["object_conf_score"][1]
            fire_conf_score = camera_info["object_conf_score"][2]

            for bbox_data in bbox_array:
                if len(bbox_data) != 6: continue

                x1, y1, x2, y2, conf, cls = list(map(int, bbox_data[:4])) + list(bbox_data[4:])

                if cls not in camera_info["detect_cls"]: continue

                if cls == 0 :
                    new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                else:
                    points = [(x1, y1), (x2, y1), (x1, y2), (x2, y2), ((x1 + x2) // 2, (y1 + y2) // 2)]
                    add_bbox_flag = False
                    for detect_info in camera_info["TF_ROI"]:
                        detect_area_list = np.array(detect_info[1:])
                        if add_bbox_flag == False:
                            for point in points:
                                if cv2.pointPolygonTest(detect_area_list, point, False) == 1 :
                                    if 0 < cls < 6 and conf > car_conf_score:
                                        new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                                        add_bbox_flag = True
                                        break
                                    elif cls == 6 and conf > fire_conf_score:
                                        new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                                        add_bbox_flag = True
                                        break

            bn_new_person_bbox.append(np.array(new_person_bbox) if new_person_bbox else np.zeros((0, 6)))
            bn_new_non_person_bbox.append(np.array(new_non_person_bbox) if new_non_person_bbox else np.zeros((0, 6)))

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        print("camera_info : ",camera_info["TF_ROI"])
        print("detect_area_list : ",detect_area_list)
        print("point : ",point)

    finally:
        return bn_new_person_bbox, bn_new_non_person_bbox

def draw_roi(points, image, color, thickness=1, is_closed=True):
    """ 이미지에 관심 영역(ROI)를 그립니다. """
    cv2.polylines(image, [np.int32(points)], is_closed, color, thickness)


def draw_detect_result(camera_info_dict, har_model, colors, names, ROI_color_dict):
    for camera_num, camera_info in camera_info_dict.items():
        #person bbox
        for (x1, y1, x2, y2, id, conf, cls, ind) in camera_info["person_bbox"]:
            xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            conf = conf
            id = id.astype('int')
            cls = cls.astype('int')

            label = f'{id} {names[cls]} {conf:.2f}'

            bbox_color = colors(int(cls))

            if camera_num in har_model.id_dict.keys() and id in har_model.id_dict[camera_num].keys() and len(har_model.id_dict[camera_num][id]["status"]) > 10:
                status_list, counts =  np.unique(np.array(har_model.id_dict[camera_num][id]["status"][-10:]), return_counts=True)
                status = status_list[np.argmax(counts)]
                if status == 1:
                    bbox_color = (0,75,150)
                    status = "falldown"

                #싸움 감지 기능 억제
                elif status == 2:
                    # color_cls = (60,20,220)
                    # status = "fight"
                    bbox_color = (0,150,95)
                    status = "normal"

                elif status == 0:
                    bbox_color = (0,150,95)
                    status = "normal"

                label += f" {status}"

            if camera_num in har_model.id_dict.keys() and id in har_model.id_dict[camera_num].keys() and len(har_model.id_dict[camera_num][id]["clip_falldown"]) > 10:
                status_list, counts =  np.unique(np.array(har_model.id_dict[camera_num][id]["clip_falldown"][-10:]), return_counts=True)
                status = status_list[np.argmax(counts)]

                if status == 1:
                    bbox_color = (0,75,150)
                    status = "falldown"

                #싸움 감지 기능 억제
                elif status == 2:
                    # color_cls = (60,20,220)
                    # status = "fight"
                    bbox_color = (0,150,95)
                    status = "normal"

                elif status == 0:
                    bbox_color = (0,150,95)
                    status = "normal"

                label += f" {status}"

            plot_one_box(xyxy, camera_info["img"], label=label, color=bbox_color, line_thickness=1) # 박스 그리기

        #non person bbox x1, y1, x2, y2, conf, cls
        for (x1, y1, x2, y2, conf, cls) in camera_info["non_person_bbox"]:
            xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            conf = conf
            cls = cls.astype('int')

            label = f'{names[cls]} {conf:.2f}'
            plot_one_box(xyxy, camera_info["img"], label=label, color=colors(int(cls)), line_thickness=1) # 박스 그리기

        #ROI
        for detect_info in camera_info["TF_ROI"]:
            draw_roi(points = detect_info[1:], 
                     image = camera_info["img"],
                     color = ROI_color_dict[detect_info[0]], 
                     thickness = 1, 
                     is_closed = True)

def plot_one_box(x, img, color=None, label=None, bbox=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    if bbox:
        cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

    return img

def get_bottom_point(bbox):
    x1, y1, x2, y2 = bbox
    return [int(x1 + (x2 - x1) * 0.5), int(y1 + (y2 - y1) * 0.95)]

def get_center_point(bbox):
    x1, y1, x2, y2 = bbox
    return [int(x1 + (x2 - x1) * 0.5), int(y1 + (y2 - y1) * 0.5)]

def get_detect_area_svg(svg_data, detect_info, ROI_color_dict):
    if len(detect_info):
        TF_detect_info= TF_detect_area(detect_info, img_size=(1920, 1080))

        for detect_area in TF_detect_info:
            roi_color = ROI_color_dict[detect_area[0]].copy()
            roi_color.reverse()
            color = tuple(roi_color)
            roi_list = detect_area[1:]

            svg_data += f"""<polygon style="fill-opacity:0;
                stroke:rgb{color};
                stroke-opacity:0.8;
                stroke-width:5.0"
                points=" """

            for x, y in roi_list:
                svg_data += "{},{} ".format(int(x),int(y))
        svg_data += ''' " /> \n'''
    return svg_data

def create_graphic_bbox_svg(x1, y1, x2, y2, label, color):
    """
    "그래픽" 스타일 (모서리 + 외곽선 텍스트)의 SVG 문자열을 생성합니다.
    """
    
    # --- 스타일 파라미터 ---
    stroke_width = 4.0   # 선 두께
    corner_length = 30  # 모서리 'L'자 라인의 길이
    font_size = 22
    font_padding = 10   # BBox와 텍스트 사이의 간격

    svg_data = ""
    
    # <g> 태그로 BBox와 텍스트를 그룹화합니다.
    svg_data += '<g> \n'

    # --- 1. 네 모서리 그리기 (<path> 사용) ---
    corner_style = f"fill:none; stroke:{color}; stroke-width:{stroke_width}; stroke-linecap:square;"

    # 상단-좌측
    svg_data += f'''  <path d="M {x1 + corner_length} {y1} L {x1} {y1} L {x1} {y1 + corner_length}"
          style="{corner_style}" /> \n'''
    # 상단-우측
    svg_data += f'''  <path d="M {x2 - corner_length} {y1} L {x2} {y1} L {x2} {y1 + corner_length}"
          style="{corner_style}" /> \n'''
    # 하단-좌측
    svg_data += f'''  <path d="M {x1 + corner_length} {y2} L {x1} {y2} L {x1} {y2 - corner_length}"
          style="{corner_style}" /> \n'''
    # 하단-우측
    svg_data += f'''  <path d="M {x2 - corner_length} {y2} L {x2} {y2} L {x2} {y2 - corner_length}"
          style="{corner_style}" /> \n'''

    # --- 2. 라벨 텍스트 그리기 (외곽선 효과) ---
    text_x = x1
    text_y = y1 - font_padding # BBox 상단에서 padding만큼 위에 표시
    
    font_style_base = f"font-family:monospace; font-size:{font_size}px; font-weight:bold;"
    
    # 2-1. 텍스트 외곽선 (배경색과 동일)
    svg_data += f'''  <text x="{text_x}" y="{text_y}"
          style="{font_style_base} stroke:{color}; stroke-width:5; stroke-linejoin:round; fill:{color};">
        {label}
    </text> \n'''
    
    # 2-2. 텍스트 본체 (흰색)
    svg_data += f'''  <text x="{text_x}" y="{text_y}"
          style="{font_style_base} fill:#FFFFFF;">
        {label}
    </text> \n'''
    
    svg_data += '</g> \n'
    
    return svg_data

def get_class_label(cls):
    """
    클래스 번호를 라벨 이름으로 변환합니다.
    """
    class_labels = {
        0: "PERSON",
        1: "BICYCLE",
        2: "CAR",
        3: "MOTORCYCLE",
        4: "BUS",
        5: "TRUCK",
        6: "FIRE",
        # 필요한 클래스를 추가하세요
    }
    return class_labels.get(cls, f"CLASS_{cls}")


def get_svg_bbox(svg_data, person_bbox, non_person_bbox, ori_imsz, target_imsz, object_color_dict):
    TF_person_bbox = TF_bbox(person_bbox, ori_imsz, target_imsz)
    TF_non_person_bbox = TF_bbox(non_person_bbox, ori_imsz, target_imsz)

    for bbox in TF_person_bbox + TF_non_person_bbox:

        if len(bbox) == 8: x1, y1, x2, y2, id, conf, cls, ind = bbox
        elif len(bbox) == 6: x1, y1, x2, y2, conf, cls, = bbox  
        if len(bbox) == 9: x1, y1, x2, y2, id, conf, cls, ind, status = bbox  # 좌표 추출

        color = object_color_dict[cls]
        label = get_class_label(cls)
        
        # 새로운 그래픽 스타일의 BBox 생성
        svg_data += create_graphic_bbox_svg(x1, y1, x2, y2, label, color)

    return svg_data

def get_detect_num(detect_type):
    detect_type_dict = {"Intrusion" : 2, "Loitering" : 1, "Falldown": 6, "Fire" : 4, "Fight" : 7, "Trash" : 5}
    return detect_type_dict[detect_type]

def send_alarm_NVR(nvr_ip, nvr_id, nvr_pw, camera_info, ROI_color_dict, object_color_dict):
    try:
        auth=HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW

        enevt_svg = "http://" + nvr_ip + "/api/events/svg" # 이벤트 주소
        event_post = "http://" + nvr_ip + "/api/events" # 이벤트 주소

        svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> \n'''.format(int(camera_info["camera_id"]) - 1)

        for detect_info in camera_info["ROI_ori"]:
            svg_data = get_detect_area_svg(svg_data, detect_info, ROI_color_dict)

        svg_data = get_svg_bbox(svg_data, 
                                camera_info["plot_person_bbox"], 
                                camera_info["non_person_bbox"], 
                                ori_imsz= (camera_info["img"].shape[1], camera_info["img"].shape[0]), 
                                target_imsz = (1920, 1080),
                                object_color_dict = object_color_dict)
        
        r = requests.put(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        if len(camera_info["alarm"]):
            data = {}
            headers = {"Content-Type": "application/json",}

            for alarm_info in camera_info["alarm"]:
                detect_type = alarm_info[0]
                detect_num = get_detect_num(detect_type)
                data = {"type": 70, "devices": [int(camera_info["camera_id"]) - 1], "micro_ai": {"type": detect_num, "object": 1}}
                r = requests.put(event_post, headers=headers, json=data, auth=auth)

    except Exception as e:
        # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # tb = traceback.format_exc()
        # print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        pass

def send_NVR_empty(nvr_ip, nvr_id, nvr_pw):
    auth=HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW

    enevt_svg = "http://" + nvr_ip + "/api/events/svg" # 이벤트 주소

    for num in range(0, 17):
        svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> \n'''.format(num)

        r = requests.put(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

def start_delayed_video_save(video_save_buffer, camera_name, alarm, nvr_ip):
        thread = threading.Thread(target=video_save, args=(video_save_buffer, camera_name, alarm, nvr_ip))
        thread.start()

def video_save(video_save_buffer, camera_name, alarm, nvr_ip):
    try:
        # detect_info_buffer = video_save_buffer[camera_name]["detect_info"]
        img_buffer_ori = video_save_buffer[camera_name]["img_ori_buffer"]

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # print(len(img_buffer_ori))

        # fps = len(img_buffer_ori) / 10
        fps = 30


        # date_time = datetime.strptime(alarm[2], "%d/%m/%Y %H:%M:%S")
        date_time = datetime.strptime(alarm[2], "%Y/%m/%d %H:%M:%S")

        new_date_time = date_time.strftime("%y.%m.%dT%H.%M.%S")

        new_date, new_time = new_date_time.split("T")[0], new_date_time.split("T")[1]

        # output_video_file_path = os.path.join(os.getcwd(),"..", "backup", nvr_ip, f"{camera_name}", new_date, "videos")
        output_video_ori_file_path = os.path.join(os.getcwd(), "..", "backup", nvr_ip, f"{camera_name}", new_date)

        # os.makedirs(output_video_file_path,exist_ok=True)
        os.makedirs(output_video_ori_file_path,exist_ok=True)

        # output_video_name = os.path.join(output_video_file_path, f"{new_time}_{Eng2kor(alarm[0])}.mp4") 
        # output_video_name = os.path.join(output_video_file_path, f"{new_time}_{Eng2kor(alarm[0])}.avi") 

        # output_video_ori_name = os.path.join(output_video_ori_file_path, f"{new_time}_{Eng2kor(alarm[0])}.mp4") 
        output_video_ori_name = os.path.join(output_video_ori_file_path, f"{new_time}_{Eng2kor(alarm[0])}.avi") 

        # writer = cv2.VideoWriter(output_video_name, fourcc, fps, (img_buffer_ori[0][0].shape[1], img_buffer_ori[0][0].shape[0]))
        # writer_ori = cv2.VideoWriter(output_video_ori_name, fourcc, fps, (img_buffer_ori[0][0].shape[1], img_buffer_ori[0][0].shape[0]))

        # writer = cv2.VideoWriter(output_video_name, fourcc, fps, (img_buffer_ori[0].shape[1], img_buffer_ori[0].shape[0]))
        writer_ori = cv2.VideoWriter(output_video_ori_name, fourcc, fps, (img_buffer_ori[0].shape[1], img_buffer_ori[0].shape[0]))


        # for detect_info, img_ori in zip(detect_info_buffer, img_buffer_ori):
        #     writer_ori.write(img_ori[0])
        #     img_plot = plot_detect_info(img = img_ori[0], detect_info = detect_info, roi_thickness = 2)
        #     writer.write(img_plot)
        try:
            for i in range(len(img_buffer_ori) - 1):
                # detect_info = detect_info_buffer[i]

                # img, t = img_buffer_ori[i]
                # img_next, t_next = img_buffer_ori[i+1]

                # t_delta = t_next - t

                img = img_buffer_ori[i]

                writer_ori.write(img)
                # img_plot = plot_detect_info(img = img.copy(), detect_info = detect_info, roi_thickness = 2, line_thickness = 2)
                # writer.write(img_plot)


                # if t_delta > 0.033:
                #     add_frame_num = int(t_delta//0.033) - 1

                #     for j in range(add_frame_num):
                #         writer_ori.write(img)
                #         img_plot = plot_detect_info(img = img.copy(), detect_info = detect_info, roi_thickness = 2)
                #         writer.write(img_plot)

        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
            pass

        # writer.release()
        writer_ori.release()

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        writer_ori.release()

def _process_camera_info(camera_info):
    """카메라 정보를 전송 가능한 형태로 변환하는 내부 함수"""
    person_bbox = camera_info["plot_person_bbox"]
    person_info = camera_info["person_info"]

    add_status_person_bbox = []
    for person_box in person_bbox:
        if len(person_box) == 8:
            x1, y1, x2, y2, id_, conf, cls, ind = person_box
            try:
                falldown_status = person_info.get_status(int(id_), detect_type = "falldown")
                fight_status = person_info.get_status(int(id_), detect_type = "fight")
                status = max(falldown_status, fight_status)
            except Exception as e:
                status = 0
            add_status_person_bbox.append([x1, y1, x2, y2, int(id_), round(float(conf), 2), cls, ind, int(status)])

    person_bbox = add_status_person_bbox.tolist() if isinstance(add_status_person_bbox, np.ndarray) else add_status_person_bbox
    non_person_bbox = camera_info["non_person_bbox"].tolist() if isinstance(camera_info["non_person_bbox"], np.ndarray) else camera_info["non_person_bbox"]
    ROI_ori = camera_info["ROI_ori"]

    return {
        "ROI_ori": ROI_ori,
        "person_bbox": person_bbox, 
        "non_person_bbox": non_person_bbox,
        "alarm": camera_info["alarm"]
    }


def send_SERVER_ai_info_batch(host, port, camera_info_dict, nvr_info_finder):
    """
    모든 카메라의 AI 분석 결과를 하나의 배치로 전송합니다.
    최신 데이터만 유지하여 항상 가장 최신 프레임 결과를 전송합니다.
    
    Args:
        host: 서버 호스트
        port: 서버 포트
        camera_info_dict: 카메라 정보 딕셔너리
        nvr_info_finder: (camera_name) -> (nvr_id, nvr_pw, nvr_ip) 함수
    """
    global _ai_info_latest_data
    
    # 워커 스레드가 시작되지 않았으면 시작
    start_ai_info_sender_worker()
    
    url = f"http://{host}:{port}/upload-ai-alarm"
    
    # 모든 카메라 데이터를 하나의 딕셔너리로 병합
    batch_data = {}
    
    for camera_name, camera_info in camera_info_dict.items():
        _, _, nvr_ip = nvr_info_finder(camera_info["name"])
        
        if nvr_ip is None:
            continue
            
        # NVR IP별로 그룹화
        if nvr_ip not in batch_data:
            batch_data[nvr_ip] = {}
        
        # 카메라 정보 처리 및 추가
        batch_data[nvr_ip][camera_info["name"]] = _process_camera_info(camera_info)
    
    # 최신 데이터로 덮어쓰기 (이전 데이터는 버려짐)
    with _ai_info_data_lock:
        _ai_info_latest_data = (url, batch_data)
        _ai_info_new_data_event.set()  # 워커에게 새 데이터 알림


def send_ai_info_via_manager(shared_data, camera_info_dict, nvr_info_finder):
    """
    BaseManager를 통해 AI 분석 결과를 공유합니다.
    공유 메모리 기반으로 HTTP나 파이프보다 빠른 실시간 데이터 전달을 수행합니다.
    
    Args:
        shared_data: BaseManager로 생성된 SharedAIData 인스턴스
        camera_info_dict: 카메라 정보 딕셔너리
        nvr_info_finder: (camera_name) -> (nvr_id, nvr_pw, nvr_ip) 함수
    """
    try:
        # 모든 카메라 데이터를 하나의 딕셔너리로 병합
        batch_data = {}
        
        for camera_name, camera_info in camera_info_dict.items():
            _, _, nvr_ip = nvr_info_finder(camera_info["name"])
            
            if nvr_ip is None:
                continue
                
            # NVR IP별로 그룹화
            if nvr_ip not in batch_data:
                batch_data[nvr_ip] = {}
            
            # 카메라 정보 처리 및 추가
            batch_data[nvr_ip][camera_info["name"]] = _process_camera_info(camera_info)
        
        # 공유 데이터 객체에 데이터 설정 (즉시 반영)
        if batch_data:
            shared_data.set(batch_data)
            
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"BaseManager 전송 에러 at {current_time}: {e}\n{tb}", file=sys.stderr)


def send_SERVER_ai_info(nvr_ip, host, port, camera_name, camera_info):
    """
    FastAPI 서버로 AI 분석 결과를 전송합니다.
    최신 데이터만 유지하여 항상 가장 최신 프레임 결과를 전송합니다.
    (이전 데이터는 덮어씌워짐 - 딜레이 없이 최신 상태 유지)
    
    Note: 배치 전송이 필요한 경우 send_SERVER_ai_info_batch() 사용을 권장합니다.
    """
    global _ai_info_latest_data
    
    # 워커 스레드가 시작되지 않았으면 시작
    start_ai_info_sender_worker()
    
    url = f"http://{host}:{port}/upload-ai-alarm"

    data = {nvr_ip : {}}
    data[nvr_ip][camera_name] = _process_camera_info(camera_info)

    # 최신 데이터로 덮어쓰기 (이전 데이터는 버려짐)
    with _ai_info_data_lock:
        _ai_info_latest_data = (url, data)
        _ai_info_new_data_event.set()  # 워커에게 새 데이터 알림



def camera_info_refresh(camera_info_dict):
    for _, camera_info in camera_info_dict.items():
        for detect_type in ["loit", "intr", "fall", "fire", "fight", "trash"]:
            expire_id = []
            for id, detect_info in camera_info[detect_type].items():
                if time.time() - detect_info[0] > 300:
                # if time.time() - detect_info[0] > 5:
                    expire_id.append(id)
            if expire_id:
                for id in expire_id:
                    del camera_info[detect_type][id]

        camera_info["alarm"] = []
    
    if len(expire_id) > 0:
        gc.collect()

    return camera_info_dict



def get_IOU(box1, box2):
    # box = (x1, y1, x2, y2)
    box1_area = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
    box2_area = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)

    # obtain x1, y1, x2, y2 of the intersection
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    # compute the width and height of the intersection
    w = max(0, x2 - x1 + 1)
    h = max(0, y2 - y1 + 1)

    inter = w * h
    iou = inter / (box1_area + box2_area - inter)
    return iou

def get_active_info(roi_ori:list, detect_schedule:dict) -> list:
    active_info:dict = {"Intrusion" : 0,                          
                    "Fire" : 0,                           
                    "Loitering" : 0,
                    "Falldown" : 0,
                    "Fight" : 0 ,
                    "Trash" : 0 
                    }
    
    active_roi_list:list = []
    
    now = datetime.now()
    # day =  str((now.weekday() + 1) % 7)
    day_names = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    day = day_names[(now.weekday() + 1) % 7]

    schedule_info:dict = detect_schedule[day]

    for detect_class, schedule in schedule_info.items():
        for time_range in schedule:
            if time_range[0] <= now.hour <= time_range[1] - 1:
                active_info[detect_class] = 1
                break
    for detect_info in roi_ori:
        detect_class = detect_info[0]
        detect_roi:list = detect_info[1:]

        if active_info[detect_class] == 1 and len(detect_roi) != 0:
            active_roi_list.append(detect_info)

        elif active_info[detect_class] == 1 and len(detect_roi) == 0:
            detect_class = [detect_info[0]]
            detect_roi = [[0.01, 0.01], [0.99, 0.01], [0.99, 0.99], [0.01, 0.99]]
            active_roi_list.append(detect_class + detect_roi)
        

    return active_info, active_roi_list

def check_stop_person(bbox, trejectory):
    start_pts = trejectory[0]
    end_pts = trejectory[-1]

    distance_pts = np.array(end_pts) - np.array(start_pts)

    stop_area = bbox
    #x1, y1, x2, y2,
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]

    if abs(distance_pts[0]) < w/3 and abs(distance_pts[1]) < h/3:
        return True
    
    else:
        return False
    
def make_square_bbox(bbox):
    x1, y1, x2, y2, id_, conf, label, _ = bbox
    width = x2 - x1
    height = y2 - y1
    max_side = max(width, height)
    
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    new_x1 = center_x - max_side / 2
    new_y1 = center_y - max_side / 2
    new_x2 = center_x + max_side / 2
    new_y2 = center_y + max_side / 2
    
    new_x1 = max(new_x1, 0)
    new_y1 = max(new_y1, 0)
    
    return [new_x1, new_y1, new_x2, new_y2, id_, conf, label, None]

def calculate_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_area = max(0, x2 - x1 + 1) * max(0, y2 - y1 + 1)

    box1_area = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
    box2_area = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)

    iou = intersection_area / float(box1_area + box2_area - intersection_area)

    return iou

def merge_boxes(track, iou_threshold=0.5):
    original_boxes = track.copy()
    bbox = track.copy()
    new_boxes = []

    while True:
        merged = False
        for i in range(len(bbox)):
            for j in range(i + 1, len(bbox)):
                if bbox[i] is None or bbox[j] is None:
                    continue
                iou = calculate_iou(bbox[i], bbox[j])
                if iou >= iou_threshold:
                    x1 = min(bbox[i][0], bbox[j][0])
                    y1 = min(bbox[i][1], bbox[j][1])
                    x2 = max(bbox[i][2], bbox[j][2])
                    y2 = max(bbox[i][3], bbox[j][3])
                    conf = max(bbox[i][5], bbox[j][5])
                    label = bbox[i][6] if bbox[i][5] > bbox[j][5] else bbox[j][6]
                    # new_box = np.array([x1, y1, x2, y2, bbox[i][4] + bbox[j][4], conf, label])
                    new_box = [x1, y1, x2, y2, [bbox[i][4], bbox[j][4]], conf, label, bbox[i][7]]

                    # new_boxes.append(new_box)
                    new_boxes.append(make_square_bbox(new_box))
                    
                    bbox[i] = None
                    bbox[j] = None
                    merged = True
                    break
            if merged:
                break
        bbox = [box for box in bbox if box is not None]
        if not merged:
            break

    return np.array(original_boxes), new_boxes


def plot_detect_info(img, detect_info, line_thickness = 3 , roi_thickness = 3, plot_bbox = True, plot_label = True):
    color = {
    0: (60, 20, 220),   # Crimson - person
    1: (113, 179, 60),  # Medium Sea Green - bicycle
    2: (180, 130, 70),  # Steel Blue - car
    3: (0, 140, 255),   # Dark Orange - motorcycle
    4: (219, 112, 147), # Medium Purple - bus
    5: (204, 209, 72),  # Medium Turquoise - truck
    6: (147, 20, 255),  # Deep Pink - fire
    }
    ROI_color_dict = {"Loitering": [53, 225, 225], "Intrusion": [35, 28, 255], "Fire": [33, 145, 237],
                                "Fight": [255, 0, 127], "Falldown": [230, 255, 121], "Trash": [0, 165, 255]}

    # names = { 0 : "person", 1 : "fire"}
    names = { 0 : "person", 1 : "bicycle", 2 : "car", 3 : "motorcycle", 4 : "bus", 5 : "truck", 6 : "fire"}

    plot_img = img

    person_bbox = TF_bbox(detect_info["person_bbox"], ori_imsz=(img.shape[1], img.shape[0]), target_imsz=(img.shape[1], img.shape[0]))
    non_person_bbox = TF_bbox(detect_info["non_person_bbox"], ori_imsz=(img.shape[1], img.shape[0]), target_imsz=(img.shape[1], img.shape[0]))
    for person_box in person_bbox:
        if len(person_box) == 9:
            x1, y1, x2, y2, id, conf, cls, ind, status = person_box
            xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            conf = conf
            id = int(id)
            cls = int(cls)

            if plot_label:
                label = f'{id} {names[cls]} {conf:.2f}'
            else:
                label = False

            if status == 1 :
                bbox_color = (0,75,150)

            elif status == 2 :
                bbox_color = (60,20,220)

            elif status == 0 :
                bbox_color = (0,150,95)

            else:
                # bbox_color = color(int(cls))
                bbox_color = color[int(cls)]


            plot_one_box(xyxy, plot_img, label=label, bbox = plot_bbox, color=bbox_color, line_thickness=line_thickness) # 박스 그리기

        elif len(person_box) == 8:
            x1, y1, x2, y2, id, conf, cls, ind = person_box
            xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            conf = conf
            id = int(id)
            cls = int(cls)

            if plot_label:
                label = f'{id} {names[cls]} {conf:.2f}'
            else:
                label = False

            bbox_color = color[int(cls)]

            plot_one_box(xyxy, plot_img, label=label, bbox = plot_bbox, color=bbox_color, line_thickness=line_thickness) # 박스 그리기

    for (x1, y1, x2, y2, conf, cls) in non_person_bbox: #fire bbox
        xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
        conf = conf
        cls = int(cls)

        # bbox_color = (4,19,190)
        bbox_color = color[int(cls)]
        
        if plot_label:
            label = f'{names[cls]} {conf:.2f}'
        else:
            label = False

        plot_one_box(xyxy, plot_img, label=label, bbox = plot_bbox, color=bbox_color, line_thickness=line_thickness) # 박스 그리기

    TF_roi_info = TF_detect_area(detect_info["ROI_ori"], img_size=(img.shape[1], img.shape[0]))
    for roi_info in TF_roi_info:
        draw_roi(points = roi_info[1:], 
                    image = plot_img,
                    color = ROI_color_dict[roi_info[0]], 
                    thickness = roi_thickness, 
                    is_closed = True)

    return plot_img

def video_save_buffer_update(camera_name, camera_info, video_save_buffer):
    # video_save_buffer[camera_name]["detect_info"].append(detect_info.copy())
    # video_save_buffer[camera_name]["img_ori_buffer"].append([camera_info["img"].copy(), time.time()])
    video_save_buffer[camera_name]["img_ori_buffer"].append(camera_info["img"].copy())


    # for i in range(len(video_save_buffer[camera_name]["img_ori_buffer"])):
    #     if time.time() - video_save_buffer[camera_name]["img_ori_buffer"][i][1] < 10:
    #         del video_save_buffer[camera_name]["detect_info"][:i]
    #         del video_save_buffer[camera_name]["img_ori_buffer"][:i]
    #         break

    # if len(video_save_buffer[camera_name]["detect_info"]) > 300:
    #     del video_save_buffer[camera_name]["detect_info"][0]

    if len(video_save_buffer[camera_name]["img_ori_buffer"]) > 300:
        del video_save_buffer[camera_name]["img_ori_buffer"][0]

    # gc.collect()

    # cv2.imshow(f"{camera_num}",video_save_buffer[camera_num]["alarm_img_buffer"][-1])
    # cv2.imshow(f"{camera_num}_test",video_save_buffer[camera_num]["img_ori_buffer"][-1])

    # print(len(video_save_buffer[camera_num]["alarm_img_buffer"]))
    # cv2.waitKey(1)


