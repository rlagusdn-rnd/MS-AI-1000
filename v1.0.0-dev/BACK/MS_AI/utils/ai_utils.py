import sys
import os
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # yolov5 strongsort root directory
WEIGHTS = ROOT / 'weights'

if str(ROOT / 'yolo_tracking') not in sys.path:
    sys.path.append(str(ROOT / 'yolo_tracking'))  

if str(ROOT / 'MS_AI') not in sys.path:
    sys.path.append(str(ROOT / 'MS_AI'))  

from datetime import datetime

import time
import numpy as np
import cv2
import torch

from MS_AI.utils.detect_utils import resize_with_padding, plot_one_box, get_extand_box
from MS_AI.utils.util import build_cfg_path
from MS_AI.models.action_classcifition_model import Img_Feature_Extraction_Clip

from omegaconf import OmegaConf

class Har_System():
    def __init__(self, har_model, device, model_path, feature_type = 'clip', model_yml_path = "./", stack_size = 32):
        self.id_dict = {}
        self.stack_size = stack_size

        self.har_model = har_model
        self.device = device

        self.feature_type = feature_type
        # Load and patch the config
        args = OmegaConf.load(build_cfg_path(model_yml_path, feature_type))
        args.feature_type = feature_type
        args.batch_size = 1
        args.show_pred = True

        args.pred_texts = [
                            #'There is no person', 

                           'There is a moving person',                      #0 normal
                           'There is a standing person',                    #1
                           'There is a lying down person',                  #2 falldown
                           'There is a sitting person',                     

                            #"There is a person doesn't move", 
                            "There is a smoke rising",                      #3 fire
                            "There is something that shines brightly",      #4
                            "There is a campfire",                          #5
                            "There is flame and fire soaring",              #6

                            "A photo of a standing person",                 #7 normal
                            "A photo of a walking person",                  #8
                            "A photo of a bending person",                  #9
                            "A photo of a squats person",                   #10

                            "A photo of a man fighting a fire",             #11 fire
                            "A photo of flames an fires soaring",           #12
                            "A photo of a campfire",                        #13
                            # "A photo of a burning cooking pan",           
                            "A photo of a man doing a barbecue",            #14
                            ]

        self.pred_texts = args.pred_texts

        self.img_extraction_model = Img_Feature_Extraction_Clip(args, model_path = model_path, clip_classifiction_mode = True)


    def update(self, id, crop_img, is_person = True):
        if crop_img.shape[0] > 0 and crop_img.shape[1] > 0:
            img_resize = resize_with_padding(crop_img)
        
            feature_data, logits = self.img_extraction_model.forward(img_resize)

            logits_fire_top1 = int(np.argmax(logits[0][:7].cpu().numpy()))
            logits_arsonist_top1 = int(np.argmax(logits[0][7:].cpu().numpy()))
            logits_falldown_top1 = int(np.argmax(logits[0][:3].cpu().numpy()))

            if id not in self.id_dict.keys():
                self.id_dict[id] = {"feature_buffer" : [feature_data],
                                    "last_time" : time.time(),
                                    "status" : [0],
                                    "logit_fire" :[logits_fire_top1],
                                    "logit_arsonist" :[logits_arsonist_top1],
                                    "logit_falldown" :[logits_falldown_top1],
                                    }
            else:
                self.id_dict[id]["feature_buffer"].append(feature_data)
                self.id_dict[id]["last_time"] = time.time()
                self.id_dict[id]["logit_fire"].append(logits_fire_top1)
                self.id_dict[id]["logit_arsonist"].append(logits_arsonist_top1)
                self.id_dict[id]["logit_falldown"].append(logits_falldown_top1)


            if len(self.id_dict[id]["feature_buffer"]) == self.stack_size:
                input_data = torch.cat(self.id_dict[id]["feature_buffer"]).type(torch.FloatTensor).to(self.device)
                status = self.har_model(input_data.unsqueeze(0))
                cls = np.argmax(status.cpu())
                self.id_dict[id]["status"].append(int(cls))
                self.id_dict[id]["feature_buffer"].pop(0)
                self.status_update(id)

    def status_update(self, id):
        if id in self.id_dict.keys() and len(self.id_dict[id]["status"]) > 100:
            self.id_dict[id]["status"].pop(0)

    def reset_id(self):
        delete_list = []
        for id in self.id_dict.keys():
            if time.time() - self.id_dict[id]["last_time"] > 60:
                delete_list.append(id)

        for id in delete_list:
            del self.id_dict[id]


def get_camera_info(camera_info, height, width, grid_size, camera_num) -> dict:
    """
    camera_dict['ip']           = 카메라 IP
    camera_dict['nvr_ip']           = 카메라 IP
    camera_dict['appsink_name'] = 카메라 appsink 이름 
    camera_dict["detect_id_dict"]  = 카메라가 검출한 ID와 시간(누적됨)  {'Intrusion': [{}], 'Loitering': [{}]}, 
    camera_dict["alarm_list"]   = NVR로 전송하기 위한 검출 기록 리스트(매번 초기화됨)
    camera_dict["bbox_list"]    = NVR로 전송하기 위한 검출 박스 리스트(매번 초기화됨)
    ------------------------------------------------
    camera_dict['detect_area']  = 검출 영역 
                                  detect_area':{'Loitering': [array([[1042,  261],
                                                                    [1105,  469],
                                                                    [1272,  481],
                                                                    [1276,  257]])]}
    ----------------entering일떄--------------------
    camera_dict["detect_check_dict"] = entering 일때 A영역과 B 영역 검출 확인을 위한 리스트
    'detect_id_dict': {'Entering': [{area_1}, {area_2}, {area_3}]}, 
        
    'detect_area': {'Entering': [array([[638, 657],   array([[390, 873],
                                [490, 829],                 [396, 955],
                                [452, 818],                 [640, 958],
                                [394, 866],                 [378, 874]])
                                [396, 954],
                                [640, 958]]), 

    """
    camera_dict = {}

    camera_dict['ip'] = camera_info['nvr_source'][0]
    camera_dict['appsink_name'] = camera_info['nvr_source'][1] #+ str(1)

    camera_dict['ip_source'] = camera_info['video_source'][0]

    detect_id_dict = {}

    detect_area = camera_info['ROI']

    for detect_class, value in detect_area.items():
        new_roi = []

        if detect_class != None:
            for i in range(len(value)):
                new_roi.append(rescale_roi(value[i], height, width, grid_size, camera_num))

        detect_area[detect_class] = new_roi
        
    for detect_class, roi in camera_info['ROI'].items():
        if detect_class == 'Entering':
            detect_id_dict[detect_class] = [{}, {}, {}]
        else:
            detect_id_dict[detect_class] = [{} for x in range(len(roi))]


    camera_dict["alarm_list"] = []
    camera_dict["bbox_list"] = []

    camera_dict["detect_id_dict"] = detect_id_dict
    camera_dict["detect_area"] = detect_area

    return camera_dict

def rescale_roi(roi_list, height, width, grid_size, camera_num):

    if len(roi_list) == 0:
        roi_list = np.array([[0,0],[width,0], [width,height], [0,height]])

    roi = np.array(roi_list)
    one_grid_size = (width - 1, height - 1)

    row = camera_num // grid_size
    col = camera_num % grid_size

    roi[:, 0] = roi[:, 0] * one_grid_size[0] + col * one_grid_size[0]
    roi[:, 1] = roi[:, 1] * one_grid_size[1] + row * one_grid_size[1]

    roi = roi.astype(int)

    return roi

def get_extand_box(xyxy):
    x1 = xyxy[0]
    x2 = xyxy[2]
    y1 = xyxy[1]
    y2 = xyxy[3]

    width = x2 - x1
    height = y2 - y1

    if width > height:
        width *= 1.5
        height *= 3

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    elif width < height :
        width *= 3
        height *= 1.5

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    elif width == height :
        width *= 1.5
        height *= 1.5

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    if y1 < 0: y1 = 0
    if x1 < 0: x1 = 0

    return x1, x2, y1, y2

def get_grid_frame(frame_list, grid_size):
    
    if grid_size == 2:
        frame_12 = np.hstack((frame_list[0], frame_list[1]))
        frame_34 = np.hstack((frame_list[2], frame_list[3]))
        frame = np.vstack((frame_12, frame_34))

    elif grid_size == 4:
        frame_1234 = np.hstack((frame_list[0], frame_list[1], frame_list[2], frame_list[3]))
        frame_5678 = np.hstack((frame_list[4], frame_list[5], frame_list[6], frame_list[7]))
        frame_9101112 = np.hstack((frame_list[8], frame_list[9], frame_list[10], frame_list[11]))
        frame_13141516 = np.hstack((frame_list[12], frame_list[13], frame_list[14], frame_list[15]))
        frame_12345678 = np.vstack((frame_1234, frame_5678))
        frame_910111213141516 = np.vstack((frame_9101112, frame_13141516))
        frame = np.vstack((frame_12345678, frame_910111213141516))

    else:
        frame = frame_list[-1]

    return frame.copy()

def get_detection_point_multi_camera(bboxes, img_size, grid_size):
    width, height = img_size

    detection_center_point = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]

    detection_point_top = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.1)]
    detection_point_bottom = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.95)]
    detection_point_left = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.1), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]
    detection_point_right = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.9), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]

    row = detection_center_point[1] // height
    col = detection_center_point[0] // width

    camera_postion = (row * grid_size + col)

    return [detection_point_top, detection_point_bottom, detection_point_left, detection_point_right], camera_postion

def check_box_in_area_bottom_point(detection_point_list, PC_points):
    detection_point_top, detection_point_bottom, detection_point_left, detection_point_right  = detection_point_list

    detection_point_x = int(detection_point_bottom[0])
    detection_point_y = int(detection_point_bottom[1])

    if cv2.pointPolygonTest(PC_points, (detection_point_x, detection_point_y), False) == 1 :
        return True
    
    else : False

def check_box_in_area_center_point(detection_point_list, PC_points):
    detection_point_top, detection_point_bottom, detection_point_left, detection_point_right  = detection_point_list

    detection_point_x = int((detection_point_top[0] + detection_point_bottom[0])/2)
    detection_point_y = int((detection_point_top[1] + detection_point_bottom[1])/2)

    if cv2.pointPolygonTest(PC_points, (detection_point_x, detection_point_y), False) == 1 :
        return True
    
    else : False

def detect_loitering(camera_info, detect_id_dict, detect_area, detection_point_list, detect_time, id, debug = False):
    loit_check_id_dict = detect_id_dict
    Loit_points = detect_area

    # no_detect_id_list = camera_info['no_detect_list']
    # Loit_non_detect_area = camera_info["non_DA"]

    # if cv2.pointPolygonTest(Loit_non_detect_area, (bboxes[0], bboxes[1]), False) == 1 and \
    #     cv2.pointPolygonTest(Loit_non_detect_area, (bboxes[2], bboxes[3]), False) == 1 and \
    #     (id not in loit_check_id_dict) and (id not in no_detect_id_list):
    #     no_detect_id_list.append(id)

    # bbox의 detect point가 검출 영역에 들어갔을때 기록
    # if check_box_in_area_4_point(detection_point_list, Loit_points):    
    # if check_box_in_area_center_point(detection_point_list, Loit_points):    
    if check_box_in_area_bottom_point(detection_point_list, Loit_points):  
        # if (id not in loit_check_id_dict) and (id not in no_detect_id_list) : # and 
        if (id not in loit_check_id_dict) :
            loit_check_id_dict[id] = [detect_time, -1] # bbox id  = [detect frame, time]

        # try:
        if (detect_time - loit_check_id_dict[id][0]) > 10 and (loit_check_id_dict[id][1] == -1): # 검출 기준 시간 10초
            loit_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            # camera_info["alarm_list"].append(["loitering", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "0"])
            camera_info["alarm_list"].append(["loitering", time.time(), "yolo", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])

        # except: pass

        if debug and len(camera_info["alarm_list"]):
            print("-----Loitering detect-----")
            print(loit_check_id_dict)

    # return loit_check_id_dict, no_detect_id_list
    return loit_check_id_dict


def detect_intrusion(camera_info, detect_id_dict, detect_area, detection_point_list, detect_time, id, debug = False):
    intr_check_id_dict = detect_id_dict

    # no_detect_id_list = camera_info['no_detect_list']
    # Intr_non_detect_area = camera_info["non_DA"]

    #     no_detect_id_list.append(id)

    # if check_box_in_area_4_point(detection_point_list, Intr_points):
    # if check_box_in_area_center_point(detection_point_list, Intr_points):
    if check_box_in_area_bottom_point(detection_point_list, detect_area):
        if (id not in intr_check_id_dict):
            intr_check_id_dict[id]  = [detect_time, -1]
        
        # try:
        if (detect_time - intr_check_id_dict[id][0]) > 1 and (intr_check_id_dict[id][1] == -1): # 검출 기준 시간 1초
            intr_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            camera_info["alarm_list"].append(["intrusion", time.time(), "yolo", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])
        # except: pass

        if debug and len(camera_info["alarm_list"]):
            print("-----detect_Intrusion-----")
            print(intr_check_id_dict)
            print(camera_info["alarm_list"])


    # return intr_check_id_dict, no_detect_id_list
    return intr_check_id_dict


def detect_people_count(camera_info, detect_A, detect_B, detect_C, detect_area_A, detect_area_B, detection_point_list, detect_time, id, debug = False):
    pc_id_list = detect_C
    pc_A_check_id_dict = detect_A
    pc_B_check_id_dict = detect_B
    PC_A_points = detect_area_A
    PC_B_points = detect_area_B

    # detect_A_flag = check_box_in_area_4_point(detection_point_list, PC_A_points)
    # detect_B_flag = check_box_in_area_4_point(detection_point_list, PC_B_points)
    # detect_A_flag = check_box_in_area_center_point(detection_point_list, PC_A_points)
    # detect_B_flag = check_box_in_area_center_point(detection_point_list, PC_B_points)
    detect_A_flag = check_box_in_area_bottom_point(detection_point_list, PC_A_points)
    detect_B_flag = check_box_in_area_bottom_point(detection_point_list, PC_B_points)

    if detect_A_flag or detect_B_flag:
        if (id not in pc_A_check_id_dict) and (id not in pc_B_check_id_dict): # 신규등록
            # if check_box_in_area_4_point(detection_point_list, PC_A_points):
            if check_box_in_area_bottom_point(detection_point_list, PC_A_points):
                pc_A_check_id_dict[id] = [detect_time, -1]

            else :
                pc_B_check_id_dict[id] = [detect_time, -1]


        if detect_B_flag and (id in pc_A_check_id_dict) and (pc_A_check_id_dict[id][1] == -1): # Income
            pc_id_list[id] = ['Enter', detect_time, datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
            # camera_info["alarm_list"].append(['enter' ,datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "0"])
            camera_info["alarm_list"].append(['enter' ,time.time(), "yolo", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])
            del pc_A_check_id_dict[id]

            if debug and len(camera_info["alarm_list"]):
                print("-----detect income-----")
                print(pc_id_list)

        if detect_A_flag and (id in pc_B_check_id_dict) and (pc_B_check_id_dict[id][1] == -1): # Outcome
            pc_id_list[id] = ['Exit', detect_time, datetime.now().strftime("%d/%m/%Y %H:%M:%S")]
            # camera_info["alarm_list"].append(['exit', datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "0"])
            camera_info["alarm_list"].append(['exit', time.time(), "yolo", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])

            if debug and len(camera_info["alarm_list"]):
                print("-----detect outcome-----")
                print(pc_id_list)


    return [pc_A_check_id_dict, pc_B_check_id_dict, pc_id_list]

def detect_fire(camera_info, detect_id_dict, detect_area, detection_point_list, detect_time, id, debug = False):
    fire_check_id_dict = detect_id_dict

    if check_box_in_area_center_point(detection_point_list, detect_area):
        if (id not in fire_check_id_dict):
            fire_check_id_dict[id]  = [detect_time, -1]

    if (detect_time - fire_check_id_dict[id][0]) > 5 and (fire_check_id_dict[id][1] == -1): # 검출 기준 시간 1초
            fire_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            camera_info["alarm_list"].append(["fire", time.time(), "yolo", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])

    if debug and len(camera_info["alarm_list"]):
            print("-----detect_Fire-----")
            print(fire_check_id_dict)

    return fire_check_id_dict

def detect_fight(camera_info, detect_id_dict, detect_area, detection_point_list, detect_time, crop_img, har_system, id, debug = False):
    fight_check_id_dict = detect_id_dict

    if check_box_in_area_bottom_point(detection_point_list, detect_area):
        har_system.update(id, crop_img)

        if len(har_system.id_dict[id]["status"]) > 10:
            elements, counts = np.unique(np.array(har_system.id_dict[id]["status"][-10:]), return_counts=True)
            ind = np.argmax(counts)
            max_count_cls = elements[ind]


            if max_count_cls == 2:
                if (id not in fight_check_id_dict):
                    fight_check_id_dict[id]  = [detect_time, -1]

                #만약 싸움이라면 싸움 알림 리스트에 추가와 검출 시간 기록
                elif (detect_time - fight_check_id_dict[id][0]) > 1 and (fight_check_id_dict[id][1] == -1): # 검출 기준 시간 1초
                        fight_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        camera_info["alarm_list"].append(["fight", time.time(), "har", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])
            if debug and len(camera_info["alarm_list"]):
                    print("-----detect_fight-----")
                    print(fight_check_id_dict)

    return fight_check_id_dict

def detect_falldown(camera_info, detect_id_dict, detect_area, detection_point_list, detect_time, crop_img, har_system, id, debug = False):
    falldown_check_id_dict = detect_id_dict
    # print(har_system.id_dict[id]["status"])

    if check_box_in_area_center_point(detection_point_list, detect_area):
        har_system.update(id, crop_img)
        #print(har_system.idict[id]["status"])

        if len(har_system.id_dict[id]["status"]) > 10:
            elements, counts = np.unique(np.array(har_system.id_dict[id]["status"][-10:]), return_counts=True)
            ind = np.argmax(counts)
            max_count_cls = elements[ind]
                
            if max_count_cls == 1:
                # if (id in falldown_check_id_dict.keys()):
                    # print((detect_time - falldown_check_id_dict[id][0]) > 1 and (falldown_check_id_dict[id][1] == -1))
                if (id not in falldown_check_id_dict):
                    falldown_check_id_dict[id]  = [detect_time, -1, "har"]

                #만약 쓰러짐이라면 쓰러짐 알림 리스트에 추가와 검출 시간 기록
                elif (detect_time - falldown_check_id_dict[id][0]) > 5 and (falldown_check_id_dict[id][1] == -1): # 검출 기준 시간 5초
                        falldown_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        camera_info["alarm_list"].append(["falldown", time.time(), "har", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])

            if debug and len(camera_info["alarm_list"]):
                    print("-----detect_falldown-----")
                    print(falldown_check_id_dict)
                    print(camera_info["alarm_list"])

    return falldown_check_id_dict

def detect_falldown_clip(camera_info, 
                         detect_id_dict, 
                         detect_area, 
                         detection_point_list, 
                         detect_time, 
                         har_system, 
                         id,
                         debug = False):
    
    falldown_check_id_dict = detect_id_dict
    # print(har_system.id_dict[id]["status"])

    if check_box_in_area_center_point(detection_point_list, detect_area):
        # har_system.update(id, crop_img)
        #print(har_system.idict[id]["status"])

        if len(har_system.id_dict[id]["logit_falldown"]) > 5:
            elements, counts = np.unique(np.array(har_system.id_dict[id]["logit_falldown"][-10:]), return_counts=True)
            ind = np.argmax(counts)
            max_count_cls = elements[ind]
                
            if max_count_cls == 2:
                # if (id in falldown_check_id_dict.keys()):
                    # print((detect_time - falldown_check_id_dict[id][0]) > 1 and (falldown_check_id_dict[id][1] == -1))
                if (id not in falldown_check_id_dict):
                    falldown_check_id_dict[id]  = [detect_time, -1, "clip"]

                #만약 쓰러짐이라면 쓰러짐 알림 리스트에 추가와 검출 시간 기록
                elif falldown_check_id_dict[id][2] == "clip" and (detect_time - falldown_check_id_dict[id][0]) > 5 and (falldown_check_id_dict[id][1] == -1): # 검출 기준 시간 5초
                        falldown_check_id_dict[id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        camera_info["alarm_list"].append(["falldown", time.time(), "clip", datetime.now().strftime("%Y/%m/%d %H:%M:%S")])

            if debug:
                    print("-----detect_clip_falldown-----")
                    print(falldown_check_id_dict)
                    print(camera_info["alarm_list"])

    return falldown_check_id_dict



def detect_action_yolo(camera_info_dict , 
                       tracking_outputs, 
                       non_person_boxes,
                       video_buffer_list, 
                       img , 
                       har_system, 
                       img_size, 
                       grid_size, 
                       stop_person_id_dict,
                       debug = False):
    # for i in range(len(tracking_outputs[0].boxes.data)):
        # data = tracking_outputs[0].boxes.data[i].cpu().numpy()
        # data = tracking_outputs

    # for (x1, y1, x2, y2, id, conf, cls, ind) in tracking_outputs:
    for (x1, y1, x2, y2, id, conf, cls, ind) in tracking_outputs:
        bboxes = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
        detection_point_list, box_loc_camera = get_detection_point_multi_camera(bboxes      = bboxes, 
                                                                                img_size    = img_size, 
                                                                                grid_size   = grid_size)
        id = int(id)
        cls = int(cls)
        conf = float(conf)

        camera_id = video_buffer_list[box_loc_camera][0]
        camera_info_dict[camera_id]["bbox_list"].append([cls, bboxes])

        if cls == 0:
            stop_person_id_dict = check_person_stop(stop_person_id_dict,
                                            id,
                                            bboxes,
                                            )
            
            

        for detect_type, detect_id_list in camera_info_dict[camera_id]["detect_id_dict"].items():
            if detect_type == "Loitering" and cls == 0:
                for i in range(len(detect_id_list)):

                    camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_loitering(camera_info = camera_info_dict[camera_id], 
                                                                                detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i], 
                                                                                detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i], 
                                                                                detection_point_list = detection_point_list, 
                                                                                detect_time = time.time(), 
                                                                                id = id, 
                                                                                debug = debug)

            elif detect_type == "Intrusion" and cls == 0:
                for i in range(len(detect_id_list)):

                    camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_intrusion(camera_info = camera_info_dict[camera_id], 
                                                                                detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i], 
                                                                                detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i], 
                                                                                detection_point_list = detection_point_list, 
                                                                                detect_time = time.time(), 
                                                                                id = id, 
                                                                                debug = debug)

            elif detect_type == "Entering" and cls == 0:
                for i in range(len(detect_id_list)):

                    camera_info_dict[camera_id]["detect_id_dict"][detect_type] = detect_people_count(camera_info = camera_info_dict[camera_id], 
                                                                                detect_A = camera_info_dict[camera_id]["detect_id_dict"][detect_type][0], 
                                                                                detect_B = camera_info_dict[camera_id]["detect_id_dict"][detect_type][1], 
                                                                                detect_C = camera_info_dict[camera_id]["detect_id_dict"][detect_type][2], 
                                                                                detect_area_A = camera_info_dict[camera_id]["detect_area"][detect_type][0], 
                                                                                detect_area_B = camera_info_dict[camera_id]["detect_area"][detect_type][1], 
                                                                                detection_point_list = detection_point_list, 
                                                                                detect_time = time.time(), 
                                                                                id = id, 
                                                                                debug = debug)
                    

            elif detect_type == "Fight" and cls == 0:
                for i in range(len(detect_id_list)):
                    x1, x2, y1, y2 = get_extand_box(bboxes)
                    crop_img = img[int(y1):int(y2), int(x1):int(x2)]

                    camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_fight(camera_info = camera_info_dict[camera_id],
                                                                            detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i],
                                                                            detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i],
                                                                            detection_point_list = detection_point_list,
                                                                            detect_time = time.time(), 
                                                                            crop_img = crop_img,
                                                                            har_system = har_system,
                                                                            id = id,
                                                                            debug = debug)

            elif detect_type == "Falldown" and cls == 0:
                for i in range(len(detect_id_list)):
                    x1, x2, y1, y2 = get_extand_box(bboxes)
                    crop_img = img[int(y1):int(y2), int(x1):int(x2)]

                    camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_falldown(camera_info = camera_info_dict[camera_id],
                                                                                                    detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i],
                                                                                                    detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i],
                                                                                                    detection_point_list = detection_point_list,
                                                                                                    detect_time = time.time(), 
                                                                                                    crop_img = crop_img,
                                                                                                    har_system = har_system,
                                                                                                    id = id,
                                                                                                    debug = debug)
                    
                    if id in stop_person_id_dict.keys() and stop_person_id_dict[id][2] > 30 :
                        camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_falldown_clip(camera_info = camera_info_dict[camera_id],
                                                                                                        detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i],
                                                                                                        detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i],
                                                                                                        detection_point_list = detection_point_list,
                                                                                                        detect_time = time.time(), 
                                                                                                        # crop_img = crop_img,
                                                                                                        har_system = har_system,
                                                                                                        id = id,
                                                                                                        debug = debug)

    for (x1, y1, x2, y2, conf, cls) in non_person_boxes:
        bboxes = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
        detection_point_list, box_loc_camera = get_detection_point_multi_camera(bboxes      = bboxes, 
                                                                                img_size    = img_size, 
                                                                                grid_size   = grid_size)
        id = 0
        cls = int(cls)
        conf = float(conf)

        camera_id = video_buffer_list[box_loc_camera][0]
        camera_info_dict[camera_id]["bbox_list"].append([cls, bboxes])

        for detect_type, detect_id_list in camera_info_dict[camera_id]["detect_id_dict"].items():
            if detect_type == "Fire" and cls == 1 :
                for i in range(len(detect_id_list)):

                    try:
                        camera_info_dict[camera_id]["detect_id_dict"][detect_type][i] = detect_fire(camera_info = camera_info_dict[camera_id],
                                                                            detect_id_dict = camera_info_dict[camera_id]["detect_id_dict"][detect_type][i],
                                                                            detect_area = camera_info_dict[camera_id]["detect_area"][detect_type][i],
                                                                            detection_point_list = detection_point_list,
                                                                            detect_time = time.time(), 
                                                                            id = id,
                                                                            debug = debug)
                        
                    except:
                        # print("fire error")
                        continue
                    

    return camera_info_dict, stop_person_id_dict




def check_person_stop(stop_person_id_dict,
                      id,
                      bboxes):
    
    if id in stop_person_id_dict.keys():
        if time.time() - stop_person_id_dict[id][1] < 10 :
            before_bboxs = stop_person_id_dict[id][0]
            iou = get_IOU(before_bboxs, bboxes)

            stop_person_id_dict[id][0] = bboxes.copy()
            stop_person_id_dict[id][1] = int(time.time())

            if iou > 0.98:
                stop_person_id_dict[id][2] += 1

    else:
        stop_person_id_dict[id] = [bboxes, int(time.time()), 0]

    return stop_person_id_dict

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


def reset_camera_info_detect_list(camera_info_list):
    for camera_id, camera_dict in camera_info_list.items():
        camera_info_list[camera_id]["alarm_list"] = []
        camera_info_list[camera_id]["bbox_list"] = []

    for camera_id, camera_info in camera_info_list.items():
        for detect_class, detect_list in camera_info["detect_id_dict"].items():
            if detect_class == "Entering":
                delete_list = []
                for k, v in detect_list[-1].items():
                    if v[1] > 0 and (time.time() - v[1]) > 60:
                        delete_list.append(k)

                for delete_key in delete_list:
                    try :
                        del camera_info_list[camera_id]["detect_id_dict"][detect_class][-1][delete_key]
                    except :
                        print(delete_list)
                        print(camera_info_list[camera_id]["detect_id_dict"][detect_class][-1])
            else:
                for i in range(len(detect_list)):
                    delete_list = []
                    for k, v in detect_list[i].items():
                        if v[0] > 0 and (time.time() - v[0]) > 10:
                            delete_list.append(k)

                    for delete_key in delete_list:
                        try :
                            del camera_info_list[camera_id]["detect_id_dict"][detect_class][i][delete_key]
                        except :
                            print(delete_list)
                            print(detect_list[i])
                            print(camera_info_list[camera_id]["detect_id_dict"][detect_class][i])

    return camera_info_list

def draw_detect_area_multi_camera(camera_info_dict, im0, track_boxes, non_person_boxes, colors, har_system, names, har_model_gen_flag = False, draw_box = False):
    color_DA = (255, 255, 0)
    color_Loit = (0, 255, 255)
    color_Intr = (255, 0, 255)
    color_Fire = (97, 150, 242)
    color_Fight = (255, 0, 127)
    color_Falldown = (102, 204, 0)

    color_pc_A = (0, 0, 255)
    color_pc_B = (255, 0, 0)

    thickness = 1
    isClosed = True

    for (x1, y1, x2, y2, id, conf, cls, ind) in track_boxes:
        xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
        conf = conf
        id = id.astype('int')
        cls = cls.astype('int')

        if har_model_gen_flag == True and cls == 0 and id in har_system.id_dict.keys():
            # status_id = har_system.id_dict[id]["status"][-1]
            elements, counts = np.unique(np.array(har_system.id_dict[id]["status"][-10:]), return_counts=True)
            ind = np.argmax(counts)
            max_count_cls = elements[ind]
            
            if max_count_cls == 1:
                color_cls = (0,75,150)
                status = "falldown"

            #싸움 감지 기능 억제
            elif max_count_cls == 2:
                # color_cls = (60,20,220)
                # status = "fight"
                color_cls = (0,150,95)
                status = "normal"

            elif max_count_cls == 0:
                color_cls = (0,150,95)
                status = "normal"

            label = None if False else f"{id} {names[cls]} {conf:.2f} {status}"

            elements, counts = np.unique(np.array(har_system.id_dict[id]["logit_falldown"][-10:]), return_counts=True)
            ind = np.argmax(counts)
            max_count_cls = elements[ind]
            
            if max_count_cls == 2:
                status_clip = " falldown"
                label += status_clip

            #싸움 감지 기능 억제
            else :
                # color_cls = (60,20,220)
                # status = "fight"
                status_clip = " normal"
                label += status_clip
            
            plot_one_box(xyxy, im0, label=label, color=color_cls, line_thickness=thickness) # 박스 그리기
        
        else :
            label = f'{id} {names[cls]} {conf:.2f}'
            plot_one_box(xyxy, im0, label=label, color=colors(int(cls)), line_thickness=thickness) # 박스 그리기


    for (x1, y1, x2, y2, conf, cls) in non_person_boxes:
        xyxy = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
        conf = conf
        cls = cls.astype('int')

        if cls == 1:
            label = f'{names[cls]} {conf:.2f}'
            plot_one_box(xyxy, im0, label=label, color=(60,20,220), line_thickness=thickness) # 박스 그리기


    for camera_id, camera_info in camera_info_dict.items():
        for detect_type, roi_list in camera_info["detect_area"].items():
            if detect_type == "Loitering":
                for i in range(len(roi_list)):
                    points = roi_list[i]
                    cv2.polylines(im0, [np.int32(points)], isClosed, color_Loit, thickness)

            elif detect_type == "Intrusion":
                for i in range(len(roi_list)):
                    points = roi_list[i]
                    cv2.polylines(im0, [np.int32(points)], isClosed, color_Intr, thickness)

            elif detect_type == "Entering":
                points_A = roi_list[0]
                points_B = roi_list[1]

                cv2.polylines(im0, [np.int32(points_A)], isClosed, color_pc_A, thickness)
                cv2.polylines(im0, [np.int32(points_B)], isClosed, color_pc_B, thickness)

            elif detect_type == "Fire":
                for i in range(len(roi_list)):
                    points = roi_list[i]
                    cv2.polylines(im0, [np.int32(points)], isClosed, color_Fire, thickness)


            elif detect_type == "Fight":
                for i in range(len(roi_list)):
                    points = roi_list[i]
                    cv2.polylines(im0, [np.int32(points)], isClosed, color_Fight, thickness)


            elif detect_type == "Falldown":
                for i in range(len(roi_list)):
                    points = roi_list[i]
                    cv2.polylines(im0, [np.int32(points)], isClosed, color_Falldown, thickness)

    return im0

