import torch
import numpy as np
import os
from pathlib import Path
import sys

from back.utils import (Video_Buffer, remove_out_of_BBox, TF_detect_area, \
                        get_bottom_point, get_center_point, send_alarm_NVR, send_NVR_empty,
                        camera_info_refresh, get_IOU, send_SERVER_ai_info, get_active_info,
                        check_stop_person, make_square_bbox, merge_boxes, video_save_buffer_update)

from ultralytics import YOLO
import boxmot
import time
from datetime import datetime, timezone, timedelta
import traceback
import gc

from back.HAR import Person_Info
from  PIL import Image
import cv2

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

KST = timezone(timedelta(hours=9))

# COLOR = {
#     0: (60, 20, 220),   # Crimson - person
#     1: (113, 179, 60),  # Medium Sea Green - bicycle
#     2: (180, 130, 70),  # Steel Blue - car
#     3: (0, 140, 255),   # Dark Orange - motorcycle
#     4: (219, 112, 147), # Medium Purple - bus
#     5: (204, 209, 72),  # Medium Turquoise - truck
#     6: (147, 20, 255)   # Deep Pink - fire
# }

COLOR =  {
    0: "#DC143C",  # Crimson - person
    1: "#3CB371",  # Medium Sea Green - bicycle
    2: "#4682B4",  # Steel Blue - car
    3: "#FF8C00",  # Dark Orange - motorcycle
    4: "#9370DB",  # Medium Purple - bus
    5: "#48D1CC",  # Medium Turquoise - truck
    6: "#FF1493"   # Deep Pink - fire
}


def check_box_in_area(point_list, area_list):
    if len(area_list) == 0: return False

    if cv2.pointPolygonTest(np.array(area_list), (point_list[0], point_list[1]), False) == 1 :
        return True
    
    else : return False


#침입
def detect_intrusion(camera_info, detect_area, person_bbox_list):
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_bottom_point(bbox)
            if check_box_in_area(detect_point, detect_area):
                if id_ not in camera_info["intr"]:
                    # camera_info["intr"][id_] = [time.time(), -1, time.time()]
                    camera_info["intr"][id_] = [time.time(), -1]


                else:
                    # camera_info["intr"][id_][2] = time.time()
                    if camera_info["intr"][id_][1] == -1 and time.time() - camera_info["intr"][id_][0] > 3 : # 검출 시간 기준 3초 이상 침입이 지속될 경우 알림 발생
                        camera_info["intr"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Intrusion", id_, camera_info["intr"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

    finally:
        return camera_info
    
#배회
def detect_loitering(camera_info, detect_area, person_bbox_list):
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_bottom_point(bbox)
            if check_box_in_area(detect_point, detect_area):
                if id_ not in camera_info["loit"].keys():
                    camera_info["loit"][id_] = [time.time(), -1, time.time()]
                    camera_info["loit"][id_] = [time.time(), -1]


                else:
                    # camera_info["loit"][id_][2] = time.time()
                    if camera_info["loit"][id_][1] == -1 and time.time() - camera_info["loit"][id_][0] > 10 : # 검출 시간 기준 10초 이상 배회가 지속될 경우 알림 발생
                        camera_info["loit"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Loitering", id_, camera_info["loit"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

    finally:
        return camera_info

def detect_falldown(camera_info, detect_area, person_bbox_list, siglip_model, siglip_processor):
    try:
        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list:
            if x1 < 0 : x1 = 0
            if y1 < 0 : y1 = 0

            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

            id_ = int(id_)
            cls = int(cls)
            conf = float(conf)

            detect_point =  get_center_point(bbox)

            if check_box_in_area(detect_point, detect_area):
                if id_ in camera_info["person_info"].info.keys():
                    trejectory = camera_info["person_info"].info[id_]["trejectory"]
                    if len(trejectory) > 30 and check_stop_person(bbox, trejectory):
                        new_x1, new_y1, new_x2, new_y2, id_, conf, label, _ = make_square_bbox([x1, y1, x2, y2, id_, conf, cls, ind])

                        person_img = camera_info["img"][int(new_y1) : int(new_y2), int(new_x1) : int(new_x2)]
                        pil_img = Image.fromarray(person_img.astype('uint8'), 'RGB')
                        texts = ["a photo of falldown person on ground.", 
                                "a photo of walking person on street", 
                                "a photo of riding person on street", 
                                "a photo of standing person on street", 
                                "a photo of sitting person on ground"]
                        
                        inputs = siglip_processor(text=texts, images=pil_img, padding="max_length", return_tensors="pt")

                        # with torch.no_grad():
                        #     outputs = siglip_model(**inputs.to("cuda"))
                        #     logits_per_image = outputs.logits_per_image
                        #     probs = torch.sigmoid(logits_per_image) # these are the probabilities

                        with torch.no_grad():
                            with torch.autocast("cuda"):
                                outputs = siglip_model(**inputs.to("cuda"))
                            
                                logits_per_image = outputs.logits_per_image
                                probs = torch.sigmoid(logits_per_image) # these are the probabilities
                            
                            if probs[0][0] > 0.90 and (probs[0][1:] < 0.3).all():
                                camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 1)

                            elif torch.argmax(probs) == 0 and (probs[0][1:] < 0.01).all():
                                camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 1)
                            else:
                                camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 0)
                    
                            del outputs
                            del probs

                    else:
                        camera_info["person_info"].update_status(id_, detect_type = "falldown", status = 0)


        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 쓰러짐 알람 기록 알고리즘 : 최근 쓰러짐 감지 기록 10회 중 5회 이상일 경우 검출 시간 기록
            status = camera_info["person_info"].get_status(int(id_), detect_type = "falldown")

            if status == 1 :
                if id_ not in camera_info["fall"].keys():
                    # camera_info["fall"][id_]  = [time.time(), -1, time.time()]
                    camera_info["fall"][id_]  = [time.time(), -1]

                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"{current_time} : {id_} falldown detect")
                    print(camera_info["person_info"].info[id_]["falldown"])

                else:
                    # camera_info["fall"][id_][2] = time.time()
                    if camera_info["fall"][id_][1] == -1 and time.time() - camera_info["fall"][id_][0] > 5 : # 검출 시간 기준 5초 이상 쓰러짐이 지속될 경우 알림 발생
                        camera_info["fall"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Falldown", id_, camera_info["fall"][id_][1]])
                        
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        print(f"{current_time} : {id_} falldown alarm")
                        print(camera_info["person_info"].info[id_]["falldown"])

                        

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        # print(bbox)
        # print(camera_info["person_bbox"])
        # print(camera_info["non_person_bbox"])


    finally:
        return camera_info

def detect_fight(camera_info, detect_area, person_bbox_list, siglip_model, siglip_processor):
    try:
        if len(person_bbox_list):
            detect_id_list = person_bbox_list[:, 4]
            update_id_list = []

            bbox_ori, bbox_merged = merge_boxes(person_bbox_list, iou_threshold=0.01)

            for x1, y1, x2, y2, id_list, conf, label, _ in bbox_merged:
                if x1 < 0 : x1 = 0
                if y1 < 0 : y1 = 0
                bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

                detect_point =  get_bottom_point(bbox)

                if check_box_in_area(detect_point, detect_area):
                    people_img = camera_info["img"][int(y1) : int(y2), int(x1) : int(x2)]
                    pil_img = Image.fromarray(people_img.astype('uint8'), 'RGB')

                    texts = ["a photo of fighting people.",
                            "a photo of talking people on street",
                            "a photo of walking people on street", 
                            "a photo of standing people on street"]
                    
                    inputs = siglip_processor(text=texts, images=pil_img, padding="max_length", return_tensors="pt")

                    # with torch.no_grad():
                    #     outputs = siglip_model(**inputs.to("cuda"))
                    
                    #     logits_per_image = outputs.logits_per_image
                    #     probs = torch.sigmoid(logits_per_image) # these are the probabilities
                    with torch.no_grad():
                        with torch.autocast("cuda"):
                            outputs = siglip_model(**inputs.to("cuda"))
                        
                            logits_per_image = outputs.logits_per_image
                            probs = torch.sigmoid(logits_per_image) # these are the probabilities

                    if probs[0][0] > 0.3:
                        for id_ in id_list:
                            camera_info["person_info"].update_status(id_, detect_type = "fight", status = 2)
                            update_id_list.append(id_)

                else:
                    for id_ in id_list:
                        camera_info["person_info"].update_status(id_, detect_type = "fight", status = 0)

            for id_ in detect_id_list:
                if id_ not in update_id_list:
                    camera_info["person_info"].update_status(id_, detect_type = "fight", status = 0)

        for (x1, y1, x2, y2, id_, conf, cls, ind) in person_bbox_list: # 쓰러짐 알람 기록 알고리즘
            status = camera_info["person_info"].get_status(int(id_), detect_type = "fight")

            if status == 2 :
                if id_ not in camera_info["fight"].keys():
                    # camera_info["fight"][id_]  = [time.time(), -1, time.time()]
                    camera_info["fight"][id_]  = [time.time(), -1]

                else:
                    # camera_info["fight"][id_][2] = time.time()
                    if camera_info["fight"][id_][1] == -1 and time.time() - camera_info["fight"][id_][0] > 3 : # 검출 시간 기준 3초 이상 싸움이 지속될 경우 알림 발생
                        camera_info["fight"][id_][1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        camera_info["alarm"].append(["Fight", id_, camera_info["Fight"][id_][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        # print(bbox)
        # print(camera_info["person_bbox"])
        # print(camera_info["non_person_bbox"])


    finally:
        return camera_info


def detect_fire(camera_info, detect_area, bbox):
    try:
        detect_point =  get_center_point(bbox)
        fire_check_flag = 0

        if check_box_in_area(detect_point, detect_area):
            if len(camera_info["fire"]):
                for id, detect_info in camera_info["fire"].items():
                    iou = get_IOU(bbox, detect_info[3])

                    if iou > 0.5:
                        fire_check_flag = 1
                        detect_info[3] = bbox
                        detect_info[2] = time.time()

                        if detect_info[1] == -1 and time.time() - detect_info[0] > 5 and detect_info[4] > 30: # 최초 방화 검출 이후 10초 경과시 알람 발생
                            detect_info[1] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                            camera_info["alarm"].append(["Fire", id, detect_info[1]])

                        else:
                            detect_info[4] += 1
                
                if fire_check_flag == 0:
                    camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox, 0]

            else:
                camera_info["fire"][len(camera_info["fire"])] = [time.time(), -1, time.time(), bbox, 0]
                
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

    finally:
        return camera_info

def detect_action(camera_info, siglip_model, siglip_processor):
    person_bbox_list = camera_info["person_bbox"]
    non_person_bbox_list = camera_info["non_person_bbox"]

    for detect_info in camera_info["TF_ROI"]:
        detect_type = detect_info[0]
        detect_area = detect_info[1:]

        if detect_type == "Intrusion":
            camera_info = detect_intrusion(camera_info =  camera_info, 
                                            detect_area = detect_area,
                                            person_bbox_list = person_bbox_list,
                                            )
            
        elif detect_type == "Loitering" :
            camera_info = detect_loitering(camera_info =  camera_info, 
                                        detect_area = detect_area,
                                        person_bbox_list = person_bbox_list,
                                        )
            
        elif detect_type == "Falldown" :
            camera_info = detect_falldown(camera_info =  camera_info, 
                                            detect_area = detect_area,
                                            person_bbox_list = person_bbox_list,
                                            siglip_model = siglip_model,
                                            siglip_processor = siglip_processor,
                                            )

        
        elif detect_type == "Fight" :
            camera_info = detect_fight(camera_info =  camera_info, 
                                            detect_area = detect_area,
                                            person_bbox_list = person_bbox_list,
                                            siglip_model = siglip_model,
                                            siglip_processor = siglip_processor,
                                            )


    for (x1, y1, x2, y2, conf, cls) in non_person_bbox_list:
        #방화
        if x1 < 0 : x1 = 0
        if y1 < 0 : y1 = 0

        if cls == 1:
            bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int
            for detect_info in camera_info["TF_ROI"]:
                detect_type = detect_info[0]
                detect_area = detect_info[1:]

                if detect_type == "Fire" :
                    camera_info = detect_fire(camera_info =  camera_info, 
                                               detect_area = detect_area,
                                               bbox = bbox,
                                               )

    return camera_info

def ms_ai(camera_info_dict_ori, NVR_info, weight_name, video_save_flag):
    camera_info_dict = {}
    active_HAR = False
    start_time = time.time()

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    NVR_ID = NVR_info["ID"]
    NVR_PW = NVR_info["PW"]
    NVR_IP = NVR_info["IP"]

    video_save_buffer = {}

    HOST = "127.0.0.1"
    PORT = 65432

    ROI_color_dict = {"Loitering": [53, 225, 225], "Intrusion": [35, 28, 255], "Fire": [33, 145, 237],
                        "Fight": [255, 0, 127], "Falldown": [230, 255, 121]
                        }

    interval = 1.0 / 30

    for camera_name, camera_info in camera_info_dict_ori.items():
        num = camera_info["Num"]

        if len(camera_info["detect_info"]):        
            # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'
            pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'

            print(pipe)
            cap = Video_Buffer(pipe=pipe)
            # cap = cv2.VideoCapture(pipe, cv2.CAP_GSTREAMER)

            disconnect_cnt = 0
            no_connect_cnt = 0 
            time.sleep(1)

            while cap.frame_available() == False :
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {current_time} Try connect {pipe}")
                logger.info(f"Try connect {pipe}")
                time.sleep(1)
                disconnect_cnt += 1

                if no_connect_cnt > 2:
                    break

                if disconnect_cnt > 60 :
                    no_connect_cnt += 1
                    del cap
                    gc.collect()

                    cap = Video_Buffer(pipe=pipe)
                    time.sleep(5)

            logger.info(f"Connect {pipe}")

            tracker = boxmot.BotSort(reid_weights = Path(os.getcwd() + "/back/weight/ReID/osnet_x0_25_msmt17.pt"),
                                     device = device,
                                     half=True,
                                    per_class=False,
                                    track_high_thresh=0.4,       # 낮춘 값
                                    track_low_thresh=0.05,       # 낮춘 값
                                    new_track_thresh=0.5,        # 낮춘 값
                                    track_buffer=300,             # 늘린 값
                                    match_thresh=0.7,            # 낮춘 값
                                    proximity_thresh=0.4,        # 낮춘 값
                                    appearance_thresh=0.2,       # 낮춘 값
                                    cmc_method="ecc",
                                    frame_rate=30,
                                    fuse_first_associate=True,   # 변경된 값
                                    with_reid=True,)
            
            # tracker = boxmot.BYTETracker(track_thresh=camera_info["Conf"] / 100, 
            #                             match_thresh=0.8, 
            #                             track_buffer=150, 
            #                             frame_rate=30, 
            #                             per_class=False)   

            active_roi = get_active_info(camera_info["detect_info"], camera_info["detect_schedule"])

            TF_detect_info = TF_detect_area(active_roi, 
                                            img_size  = (cap._frame.shape[1], cap._frame.shape[0])
                                            # img_size  = (640, 480)
                                            )

            for roi_list in TF_detect_info:
                if roi_list[0] in ["Fight", "Falldown"] :
                    active_HAR = True

            # print(active_HAR)
            detect_cls_list = []

            if camera_info["Cls"][0]: detect_cls_list += [0]
            if camera_info["Cls"][1]: detect_cls_list += [1,2,3,4,5]
            if camera_info["Cls"][2]: detect_cls_list += [6]

            camera_info_dict[num] = {"cap" : cap,
                                    "name" : camera_name,
                                    "detect_cls" : detect_cls_list,
                                    "object_conf_score" : np.array(camera_info["Conf"]) / 100,
                                    "tracker" : tracker,
                                    "ROI_ori" : active_roi,                 #2 normalized(0 ~ 1) [detect class, [x1,y1], [xn,yn]]
                                    "TF_ROI" : TF_detect_info,              #3 [detect class, [x1,y1], [xn,yn]]
                                    "img" : np.zeros([480,640,3]),          #4 Img
                                    "person_bbox" : [],                     #5 Person bbox list
                                    "non_person_bbox" : [],                 #6 non person bbox list
                                    "alarm" : [],                           #7 Detect Alarm
                                    "loit" : {},                            #8 배회 검출정보 list 
                                    "intr" : {},                            #9 침입 검출정보 list
                                    "fall" : {},                            #10 쓰러짐 검출정보 list
                                    "fire" : {},                            #11 방화 검출정보 list
                                    "fight" : {},                           #12 싸움 검출정보 list
                                    "person_info" : Person_Info(camera_name = camera_name, nvr_ip=NVR_IP, PAR=camera_info["Cls"][3], host = HOST, port = PORT, ParTime = camera_info["ParTime"]),          #13 사람 정보
                                    }

            video_save_buffer[camera_name] = {"detect_info" : [],
                                            "img_ori_buffer" : []
                                                }       
    conf_score = 0.05

    model_name = f"ms-ai_{weight_name[2:]}-M"
    yolo_model_path_dict = {0 : str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}1.engine",
                            1 : str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}1.engine",
                            # 1 : f"/root/workspace/MS-AI_1000/v1.2.0-dev/back/weight/yolo/{weight_name}/{model_name}1.engine",

                            2 : str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}2.engine",
                            3 : str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}3.engine",
                            4 : str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}4.engine"}
    
    
    # yolo_model_path = yolo_model_path_dict[len(camera_info_dict)]  # load a pretrained model (recommended for training)
    yolo_model_path = str(os.getcwd()) + f"/back/weight/yolo/{weight_name}/{model_name}.pt"

    model = YOLO(yolo_model_path, task="detect")  # load a pretrained model (recommended for training)\

    if active_HAR:
        # from transformers import AutoProcessor, AutoModel
        # siglip_model = AutoModel.from_pretrained(str(os.getcwd()) + f"/back/weight/SigLip_512").cuda()
        # siglip_processor = AutoProcessor.from_pretrained(str(os.getcwd()) + f"/back/weight/SigLip_512")

        from transformers import SiglipProcessor, SiglipModel
        siglip_model = SiglipModel.from_pretrained(
                                            str(os.getcwd()) + f"/back/weight/SigLip_512",
                                            attn_implementation="flash_attention_2",
                                            torch_dtype=torch.float16,
                                            device_map="cuda",
                                        )
        siglip_processor = SiglipProcessor.from_pretrained(str(os.getcwd()) + f"/back/weight/SigLip_512")

    else:
        siglip_model = None
        siglip_processor = None

    while len(camera_info_dict):
        next_time = time.time()

        img_list = []
        camera_num_list = []
        t0 = time.time()

        for camera_num, camera_info in camera_info_dict.items():
            if cap.frame_available():
                # img = cv2.resize(camera_info["cap"].get_frame(),(640,480))
                img = camera_info["cap"].get_frame()

                img_list.append(img)
                camera_num_list.append(camera_num)
                camera_info_dict[camera_num]["img"] = img

            else:
                # pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{camera_num}'
                pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/video{num}'


                cap = Video_Buffer(pipe=pipe)
                time.sleep(0.5)
                if cap.frame_available():
                    camera_info_dict[camera_num]["cap"] = cap

                # img_list.append(np.zeros([480,640,3]))
                img_list.append(np.zeros([1080,1920,3]))


        if len(img_list):
            dets = model.predict(source=img_list, 
                                    imgsz = 640, 
                                    conf = conf_score, 
                                    classes = [0, 1, 2, 3, 4, 5, 6], 
                                    half = True, 
                                    verbose = False)
            t1 = time.time()
            bn_person_boxes, bn_non_person_boxes = remove_out_of_BBox(camera_info_dict = camera_info_dict, 
                                                                    bbox_bn= dets,
                                                                    camera_num_list = camera_num_list
                                                                    )
            for index, bbox in enumerate(bn_person_boxes):
                camera_info_dict[camera_num_list[index]]["person_bbox"] = camera_info_dict[camera_num_list[index]]["tracker"].update(bbox, img_list[index])
                camera_info_dict[camera_num_list[index]]["non_person_bbox"] = bn_non_person_boxes[index]

                # if active_HAR:
                try: 
                    # 사람의 bbox정보, 이동 경로, 검출 시간 갱신
                    camera_info_dict[camera_num_list[index]]["person_info"].update_id(img = img_list[index],track_info = camera_info_dict[camera_num_list[index]]["person_bbox"])
                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tb = traceback.format_exc()
                    print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
                    print(camera_info_dict[camera_num_list[index]]["person_bbox"])

            for camera_num, camera_info in camera_info_dict.items():
                #지능형 알고리즘 실행
                camera_info = detect_action(
                                            camera_info = camera_info,
                                            siglip_model = siglip_model,
                                            siglip_processor = siglip_processor,
                                            )
                # print(camera_name)
                # print(camera_info[7])

            t2 = time.time()

            
            # print(f"total : {1/(time.time() - t0)}")
            # print(f"t1 : {1/(t1 - t0)}")
            # print(f"t2 : {1/(t2 - t1)}")

            send_alarm_NVR(nvr_ip = NVR_IP,
                            nvr_id = NVR_ID, 
                            nvr_pw = NVR_PW, 
                            camera_info_dict = camera_info_dict,
                            ROI_color_dict = ROI_color_dict,
                            object_color_dict = COLOR)

            send_SERVER_ai_info(host = HOST,
                                port = PORT,
                                camera_info_dict = camera_info_dict,
                                video_save_buffer = video_save_buffer,
                                nvr_ip = NVR_IP,
                                video_save_flag = video_save_flag)
            
            camera_info_dict, start_time = camera_info_refresh(camera_info_dict, start_time)

            next_time += interval
            sleep_time = next_time - time.time()

            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                # 작업이 예상 시간보다 오래 걸린 경우
                next_time = time.time()



            # print(f"fps : {1/(time.time() - t0)}")
