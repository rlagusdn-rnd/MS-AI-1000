import os
import sys

import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst
Gst.init(None)


import numpy as np
import torch
import random
import cv2
import requests
from requests.auth import HTTPBasicAuth
import time
from datetime import datetime
import traceback

class Video_Buffer:
    def __init__(self, pipe="video1", appsink_name="video_sink"):
        self._frame = None
        self.video_source = f'rtspsrc location=rtsp://{pipe} latency=100 buffer-mode=0 protocols=tcp'
        self.video_codec = '! application/x-rtp, encoding-name=(string)H264, payload=96 ! rtph264depay ! h264parse '
        self.video_decode = f'! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={appsink_name} emit-signals=true sync=false max-buffers=1 drop=true'
        
        self.video_pipe = None
        self.video_sink = None
        self.appsink_name = appsink_name
        self.run()

    def start_gst(self, config=None):
        if not config:
            config = [
                'videotestsrc ! decodebin',
                '! videoconvert ! video/x-raw,format=(string)BGR ! appsink name={self.appsink_name}'
            ]

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

    def get_frame(self):
        return self._frame

    def frame_available(self):
        return self._frame is not None

    def run(self):
        try:
            self.start_gst(
                [
                    self.video_source,
                    self.video_codec,
                    ' ! queue leaky=downstream max-size-buffers=10 ',
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
            print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

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

    def stop(self):
        self.video_pipe.set_state(Gst.State.NULL)

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

def TF_detect_area(detect_info, img_size):
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

def TF_bbox(bbox, ori_imsz=(640, 480), target_imsz=(1920, 1080)):
    # 원본 이미지와 목표 이미지의 크기 비율 계산
    width_ratio = target_imsz[0] / ori_imsz[0]
    height_ratio = target_imsz[1] / ori_imsz[1]
    
    # 변환된 바운딩 박스를 저장할 리스트 초기화
    TF_boxes = []
    
    # 각 바운딩 박스에 대해 좌표 변환 수행
    for box in bbox:
        if len(box) == 8:
            x1, y1, x2, y2, id, conf, cls, ind  = box  # 좌표 추출
        elif len(box) == 6:
            x1, y1, x2, y2, conf, cls, = box  # 좌표 추출

        # 좌표를 int(새로운 이미지 크기에 맞게 조정
        new_x1 = int(x1 * width_ratio)
        new_y1 = int(y1 * height_ratio)
        new_x2 = int(x2 * width_ratio)
        new_y2 = int(y2 * height_ratio)
        
        # 변환된 좌표와 기존 정보를 합쳐 새로운 리스트 생성
        TF_boxes.append([int(cls), new_x1, new_y1, new_x2 - new_x1, new_y2 - new_y1])
    
    return TF_boxes

def check_point_in_area(point, detect_area_list):
    return cv2.pointPolygonTest(detect_area_list, point, False) == 1

def update_bbox_lists(cls, conf, person_conf_score, fire_conf_score, bbox, new_person_bbox, new_non_person_bbox):
    if cls == 0 and conf > person_conf_score:
        new_person_bbox.append(bbox)
    elif cls == 1 and conf > fire_conf_score:
        new_non_person_bbox.append(bbox)

def remove_out_of_BBox(camera_info_dict, bbox_bn, camera_num_list, fire_conf_score = 0.05):
    try:
        bn_new_person_bbox = []
        bn_new_non_person_bbox = []

        for index, bbox in enumerate(bbox_bn):
            new_person_bbox = []
            new_non_person_bbox = []
            bbox_array = bbox.boxes.data.cpu().numpy().astype(float)
            camera_info = camera_info_dict[camera_num_list[index]]
            person_conf_score = camera_info["person_conf_score"]

            for bbox_data in bbox_array:
                if len(bbox_data) != 6:
                    continue
                add_bbox_flag = False

                x1, y1, x2, y2, conf, cls = list(map(int, bbox_data[:4])) + list(bbox_data[4:])
                points = [(x1, y1), (x2, y1), (x1, y2), (x2, y2), ((x1 + x2) // 2, (y1 + y2) // 2)]
                
                for detect_info in camera_info["TF_ROI"]:
                    if add_bbox_flag == False:
                        detect_area_list = np.array(detect_info[1:])
                        for point in points:
                            if cv2.pointPolygonTest(detect_area_list, point, False) == 1 :
                                if cls == 0 and conf > person_conf_score:
                                    new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                                elif cls == 1 and conf > fire_conf_score:
                                    new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                                add_bbox_flag = True
                                break

            # bn_new_person_bbox.append(np.array(new_person_bbox) if new_person_bbox else np.zeros((0, 6)))
            # bn_new_non_person_bbox.append(np.array(new_non_person_bbox) if new_non_person_bbox else np.zeros((0, 6)))
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

def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)

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

def get_svg_bbox(svg_data, person_bbox, non_person_bbox, ori_imsz, target_imsz):
    TF_person_bbox = TF_bbox(person_bbox, ori_imsz, target_imsz)
    TF_non_person_bbox = TF_bbox(non_person_bbox, ori_imsz, target_imsz)

    for bbox in TF_person_bbox + TF_non_person_bbox:
        cls = bbox[0]
        x1, y1, w, h = bbox[1:]

        if cls == 1 : color = "#8d0000"
        
        elif cls == 0 : color = "#0702a6"

        svg_data += '''<rect style="fill:{};
                        fill-opacity:0.1;
                        stroke:{};
                        stroke-opacity: 0.8;
                        stroke-width:5.0;" \n'''.format(color, color)
        svg_data += '''  x="{}" y="{}" width="{}" height="{}" /> \n'''.format(x1,y1,w,h)

    return svg_data

def get_detect_num(detect_type):
    detect_type_dict = {"Intrusion" : 2, "Loitering" : 1, "Falldown": 6, "Fire" : 4, "Fight" : 7}
    return detect_type_dict[detect_type]

def send_alarm_NVR(nvr_ip, nvr_id, nvr_pw, camera_info_dict, ROI_color_dict):
    auth=HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW

    enevt_svg = "http://" + nvr_ip + "/api/events/svg" # 이벤트 주소
    event_post = "http://" + nvr_ip + "/api/events" # 이벤트 주소

    for camera_num, camera_info in camera_info_dict.items():
        svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> \n'''.format(int(camera_num) - 1)

        for detect_info in camera_info["ROI_ori"]:
            svg_data = get_detect_area_svg(svg_data, detect_info, ROI_color_dict)

        svg_data = get_svg_bbox(svg_data, camera_info["person_bbox"], 
                                camera_info["non_person_bbox"], 
                                ori_imsz= (camera_info["img"].shape[1], camera_info["img"].shape[0]), 
                                target_imsz = (1920, 1080))
        
        r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        if len(camera_info["alarm"]):
            data = {}
            headers = {"Content-Type": "application/json",}

            for alarm_info in camera_info["alarm"]:
                detect_type = alarm_info[0]
                detect_num = get_detect_num(detect_type)
                data = {"type": 70, "devices": [int(camera_num) - 1], "micro_ai": {"type": detect_num, "object": 1}}
                r = requests.put(event_post, headers=headers, json=data, auth=auth)

            camera_info["alarm"] = []


def send_NVR_empty(nvr_ip, nvr_id, nvr_pw):
    auth=HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW

    enevt_svg = "http://" + nvr_ip + "/api/events/svg" # 이벤트 주소

    for num in range(0, 17):
        svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> \n'''.format(num)

        # for detect_info in camera_info["ROI_ori"]:
        #     svg_data = get_detect_area_svg(svg_data, [], ROI_color_dict)

        # svg_data = get_svg_bbox(svg_data, bbox_info)
        r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

def send_SERVER_camera_info(host, port, camera_info_dict, har_model):
    url = f"http://{host}:{port}/upload-data"
    url_alarm = f"http://{host}:{port}/upload-alarm"

    data = {}
    alarm_data = {}
    for camera_num, camera_info in camera_info_dict.items():
        person_bbox = camera_info["person_bbox"]
        add_status_person_bbox = []
        for person_box in person_bbox:
            if len(person_box) == 8:
                x1, y1, x2, y2, id, conf, cls, ind = person_box
                status_vit = -1
                status_clip = -1

                if camera_num in har_model.id_dict.keys() and id in har_model.id_dict[camera_num].keys() and len(har_model.id_dict[camera_num][id]["status"]) > 10:
                    status_list, counts = np.unique(np.array(har_model.id_dict[camera_num][id]["status"][-10:]), return_counts=True)
                    status_vit = status_list[np.argmax(counts)]

                if camera_num in har_model.id_dict.keys() and id in har_model.id_dict[camera_num].keys() and len(har_model.id_dict[camera_num][id]["clip_falldown"]) > 10:
                    status_list, counts =  np.unique(np.array(har_model.id_dict[camera_num][id]["clip_falldown"][-10:]), return_counts=True)
                    status_clip = status_list[np.argmax(counts)]

                add_status_person_bbox.append([x1, y1, x2, y2, id, conf, cls, ind, int(status_vit), int(status_clip)])
            person_bbox = add_status_person_bbox

        person_bbox = person_bbox.tolist() if isinstance(person_bbox, np.ndarray) else person_bbox
        non_person_bbox = camera_info["non_person_bbox"].tolist() if isinstance(camera_info["non_person_bbox"], np.ndarray) else camera_info["non_person_bbox"]
        ROI_ori = camera_info["ROI_ori"]

        data[camera_info["name"]] = {"ROI_ori": ROI_ori,
                             "person_bbox": person_bbox, 
                             "non_person_bbox" : non_person_bbox}

        for alarm_info in camera_info["alarm"] :
            alarm_data[camera_info["name"]] = alarm_info

    response = requests.post(url, json={"msg" : data})
    response = requests.post(url_alarm, json={"msg" : alarm_data})



def camera_info_refresh(camera_info_dict):
    for camera_num, camera_info in camera_info_dict.items():
        for detect_type in ["loit", "intr", "fall", "fall_clip", "fire"]:
            expire_id = []
            for id, detect_info in camera_info[detect_type].items():
                if time.time() - detect_info[2] > 300:
                # if time.time() - detect_info[0] > 5:
                    expire_id.append(id)
            if expire_id:
                for id in expire_id:
                    del camera_info[detect_type][id]

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

def get_active_info(roi_ori, detect_schedule):
    active_info = {"Intrusion" : 0,                          
                    "Fire" : 0,                           
                    "Loitering" : 0,
                    "Falldown" : 0 
                    }
    
    active_roi_list = []
    
    now = datetime.now()
    day =  str((now.weekday() + 1) % 7)

    schedule_info = detect_schedule[day]

    for detect_class, schedule in schedule_info.items():
        for time_range in schedule:
            if time_range[0] <= now.hour <= time_range[1]:
                active_info[detect_class] = 1
                break
    for detect_info in roi_ori:
        detect_class = detect_info[0]
        detect_roi = detect_info[1:]

        if active_info[detect_class] == 1 and len(detect_roi) != 0:
            active_roi_list.append(detect_info)

        elif active_info[detect_class] == 1 and len(detect_roi) == 0:
            detect_class = [detect_info[0]]
            detect_roi = [[0.01, 0.01], [0.99, 0.01], [0.99, 0.99], [0.01, 0.99]]
            active_roi_list.append(detect_class + detect_roi)
        

    return active_roi_list
