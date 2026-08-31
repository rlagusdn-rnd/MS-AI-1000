import torch
import cv2
import numpy as np
import os
from pathlib import Path
import sys

from back.utils.util import Colors, Video_Buffer, remove_out_of_BBox, draw_detect_result, TF_detect_area, \
                            get_bottom_point, get_center_point, send_alarm_NVR, send_NVR_empty, \
                            camera_info_refresh, get_IOU, send_SERVER_camera_info, get_active_info

from ultralytics import YOLO
import boxmot
import time
from datetime import datetime, timezone, timedelta
import traceback
import gc

from back.lib.HAR.har_main import Har_System

KST = timezone(timedelta(hours=9))
HOST = "127.0.0.1"
PORT = 65432


def check_box_in_area(point_list, area_list):
    if len(area_list) == 0: return False

    if cv2.pointPolygonTest(np.array(area_list), (point_list[0], point_list[1]), False) == 1 :
        return True
    
    else : return False


#침입
def detect_intrusion(camera_info, detect_area, bbox, id):
    try:
        detect_point =  get_bottom_point(bbox)
        if check_box_in_area(detect_point, detect_area):
            if id not in camera_info["intr"]:
                camera_info["intr"][id] = [time.time(), -1, time.time()]

            else:
                camera_info["intr"][id][2] = time.time()
                if camera_info["intr"][id][1] == -1 and time.time() - camera_info["intr"][id][0] > 1 : # 검출 기준시간 1초
                    camera_info["intr"][id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    camera_info["alarm"].append(["Intrusion", id, camera_info["intr"][id][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

    finally:
        return camera_info
    
#배회
def detect_loitering(camera_info, detect_area, bbox, id):
    try:
        detect_point =  get_bottom_point(bbox)
        if check_box_in_area(detect_point, detect_area):
            if id not in camera_info["loit"].keys():
                camera_info["loit"][id] = [time.time(), -1, time.time()]

            else:
                camera_info["loit"][id][2] = time.time()
                if camera_info["loit"][id][1] == -1 and time.time() - camera_info["loit"][id][0] > 10 : # 검출 기준시간 10초
                    camera_info["loit"][id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    camera_info["alarm"].append(["Loitering", id, camera_info["loit"][id][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

    finally:
        return camera_info


def detect_falldown(camera_num, camera_info, detect_area, bbox, id, har_model):
    try:
        detect_point =  get_center_point(bbox)

        if check_box_in_area(detect_point, detect_area):
            person_img = camera_info["img"][int(bbox[1]):int(bbox[3]), int(bbox[0]):int(bbox[2])]
            har_model.update(id, camera_num, person_img)

            if len(har_model.id_dict[camera_num][id]["status"]) > 10:
                status_list, counts =  np.unique(np.array(har_model.id_dict[camera_num][id]["status"][-10:]), return_counts=True)

                status = status_list[np.argmax(counts)]

                if status == 1:
                    if id not in camera_info["fall"].keys():
                        camera_info["fall"][id]  = [time.time(), -1, time.time(), "har"]

                    else:
                        camera_info["fall"][id][2] = time.time()
                        if camera_info["fall"][id][1] == -1 and time.time() - camera_info["fall"][id][0] > 5 : # 검출 기준시간 10초
                            camera_info["fall"][id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            if (id not in camera_info["fall_clip"].keys()) or (id in camera_info["fall_clip"].keys() and camera_info["fall_clip"][id][1] == -1):
                                camera_info["alarm"].append(["Falldown", id, camera_info["fall"][id][1]])

            if len(har_model.id_dict[camera_num][id]["clip_falldown"]) > 10:
                status_list, counts =  np.unique(np.array(har_model.id_dict[camera_num][id]["clip_falldown"][-10:]), return_counts=True)

                status = status_list[np.argmax(counts)]

                if status == 1:
                    if id not in camera_info["fall_clip"].keys():
                        camera_info["fall_clip"][id]  = [time.time(), -1, time.time(), "clip"]

                    else:
                        camera_info["fall_clip"][id][2] = time.time()
                        if camera_info["fall_clip"][id][1] == -1 and time.time() - camera_info["fall_clip"][id][0] > 5 : # 검출 기준시간 10초
                            camera_info["fall_clip"][id][1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            if (id not in camera_info["fall"].keys()) or (id in camera_info["fall"].keys() and camera_info["fall"][id][1] == -1):
                                camera_info["alarm"].append(["Falldown", id, camera_info["fall_clip"][id][1]])

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        print(bbox)
        print(camera_info["person_bbox"])
        print(camera_info["non_person_bbox"])


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
                            detect_info[1] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
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

def detect_action(camera_num, camera_info, har_model):
    person_bbox_list = camera_info["person_bbox"]
    non_person_bbox_list = camera_info["non_person_bbox"]

    for (x1, y1, x2, y2, id, conf, cls, ind) in person_bbox_list:
        if x1 < 0 : x1 = 0
        if y1 < 0 : y1 = 0


        bbox = np.array([x1, y1, x2, y2],dtype="int") # float64 to int

        id = int(id)
        cls = int(cls)
        conf = float(conf)
        
        for detect_info in camera_info["TF_ROI"]:
            detect_type = detect_info[0]
            detect_area = detect_info[1:]

            if detect_type == "Intrusion":
                camera_info = detect_intrusion(camera_info =  camera_info, 
                                               detect_area = detect_area,
                                               bbox = bbox,
                                               id = id,
                                               )
            elif detect_type == "Loitering" :
                camera_info = detect_loitering(camera_info =  camera_info, 
                                               detect_area = detect_area,
                                               bbox = bbox,
                                               id = id,
                                               )
            elif detect_type == "Falldown" :
                camera_info = detect_falldown(camera_num = camera_num,
                                              camera_info =  camera_info, 
                                              detect_area = detect_area,
                                              bbox = bbox,
                                              id = id,
                                              har_model = har_model
                                               )
    for (x1, y1, x2, y2, conf, cls) in non_person_bbox_list:
        #방화
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

def ms_ai(camera_info_dict_ori, ROOT, NVR_info):
    colors = Colors()
    camera_info_dict = {}
    active_HAR = False

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    NVR_ID = NVR_info["ID"]
    NVR_PW = NVR_info["PW"]
    NVR_IP = NVR_info["IP"]

    # ROI_color_dict = {"Loitering": [0, 255, 255], "Intrusion": [255, 0, 255], "Fire": [97, 150, 242],
    #                 "Fight": [255, 0, 127], "Falldown": [102, 204, 0]
    #                 }
    
    ROI_color_dict = {"Loitering": [53, 225, 225], "Intrusion": [35, 28, 255], "Fire": [33, 145, 237],
                        "Fight": [255, 0, 127], "Falldown": [230, 255, 121]
                        }


    for camera_name, camera_info in camera_info_dict_ori.items():
        num = camera_info["Num"]
        # rtsp_url = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'
        # pipe = (f'rtspsrc location={rtsp_url} latency=0 protocols=0x00000004 ! '
        #         'rtph264depay ! h264parse ! '
        #         'avdec_h264 ! videoconvert ! appsink max-buffers=1 drop=true')

        if len(camera_info["detect_info"]):        
            # cap = cv2.VideoCapture(pipe, cv2.CAP_GSTREAMER)
            pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{num}'
            cap = Video_Buffer(pipe=pipe)

            time.sleep(1)

            # if cap.isOpened():
            while True:
                print(f"check connect {pipe}")
                if cap.frame_available():
                    break
            #  if cap.frame_available():
                #BBox 추적 알고리즘 모듈 생성
                # tracker = boxmot.BoTSORT(model_weights = Path(str(ROOT) + "/back/weight/ReID/osnet_x0_25_market.pt"),
                #                          device = device,
                #                          fp16 = False)
            
            tracker = boxmot.BYTETracker(track_thresh=camera_info["Conf"] / 100, 
                                        match_thresh=0.8, 
                                        track_buffer=150, 
                                        frame_rate=30, per_class=False)   

            active_roi = get_active_info(camera_info["detect_info"], camera_info["detect_schedule"])

            # normalize된 검출 영억을 이미지 크기에 맞게 재구성
            # TF_detect_info = TF_detect_area(camera_info["detect_info"], 
            #                                     img_size  = (cap.get(cv2.CAP_PROP_FRAME_WIDTH), 
            #                                                 cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

            TF_detect_info = TF_detect_area(active_roi, 
                                            img_size  = (cap._frame.shape[1], 
                                                        cap._frame.shape[0]))
            
            for roi_list in TF_detect_info:
                if "Falldown" in roi_list:
                    active_HAR = True
        
            camera_info_dict[num] = {"cap" : cap,
                                                "name" : camera_name,
                                            "person_conf_score" : camera_info["Conf"] / 100,
                                            "tracker" : tracker,
                                            "ROI_ori" : active_roi, #2 normalized [detect type , [ROI_n]]
                                            "TF_ROI" : TF_detect_info,              #3 [detect type , [ROI_n]]
                                            "img" : np.zeros([480,640,3]),            #4 Img
                                            "person_bbox" : [],                     #5 Person bbox list
                                            "non_person_bbox" : [],                 #6 non person bbox list
                                            "alarm" : [],                           #7 Detect Alarm
                                            "loit" : {},                            #8 배회 검출정보 list 
                                            "intr" : {},                            #9 침입 검출정보 list
                                            "fall" : {},                            #10 쓰러짐 검출정보 list
                                            "fall_clip" : {},                       #11 쓰러짐_clip 검출정보 list
                                            "fire" : {},                            #12 방화 검출정보 list
                                                }                     

    conf_score = 0.05
    fire_conf_score = 0.5

    model_name = "ms-ai2407-finetune_M"
    yolo_model_path_dict = {0 : str(ROOT) + f"/back/weight/yolo/engine/{model_name}1.engine",
                            1 : str(ROOT) + f"/back/weight/yolo/engine/{model_name}1.engine",
                            2 : str(ROOT) + f"/back/weight/yolo/engine/{model_name}2.engine",
                            3 : str(ROOT) + f"/back/weight/yolo/engine/{model_name}3.engine",
                            4 : str(ROOT) + f"/back/weight/yolo/engine/{model_name}4.engine"}
    
    yolo_model_path = yolo_model_path_dict[len(camera_info_dict)]  # load a pretrained model (recommended for training)
    model = YOLO(yolo_model_path, task="detect")  # load a pretrained model (recommended for training)\


    # print(TF_detect_info)
    if active_HAR:
        model_name = 'vit_b1_redu'
        weight_name = "2401.pt"

        model_weight_path = os.path.join(ROOT ,'back', 'lib', 'HAR','weights', "HAR", "224x224", model_name, weight_name)
        clip_path = os.path.join(ROOT ,'back', 'lib', 'HAR', 'weights', 'clip', "ViT-B-32.pt")
        model_yml_path = os.path.join(ROOT ,'back', 'lib', 'HAR','configs')

        har_model = Har_System(model_weight_path = model_weight_path, 
                            device = device, 
                            model_path = clip_path, 
                            feature_extract = 'clip', 
                            model_yml_path = model_yml_path, 
                            stack_size = 32)

    else:
        har_model = None

    while len(camera_info_dict):
        img_list = []
        camera_num_list = []

        t0 = time.time()

        for camera_num, camera_info in camera_info_dict.items():
            # success, img = camera_info["cap"].read()
            img = camera_info["cap"].get_frame()

            if cap.frame_available():
                img = cv2.resize(img,(640,480))
                img_list.append(img)
                camera_num_list.append(camera_num)
                camera_info_dict[camera_num]["img"] = img

            else:
                # rtsp_url = f'rtsp://{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{camera_num}'
                # pipe = (f'rtspsrc location={rtsp_url} latency=0 protocols=0x00000004 ! '
                #         'rtph264depay ! h264parse ! '
                #         'avdec_h264 ! videoconvert ! appsink max-buffers=1 drop=true')
                # cap = cv2.VideoCapture(pipe, cv2.CAP_GSTREAMER)
                pipe = f'{NVR_ID}:{NVR_PW}@{NVR_IP}/normal{camera_num}'

                cap = Video_Buffer(pipe=pipe)
                time.sleep(0.5)
                # if cap.isOpened():
                if cap.frame_available():
                    camera_info_dict[camera_num]["cap"] = cap

                img = np.zeros([480,640,3])
                img_list.append(img)

        t1_1 = time.time()

        if len(img_list):
            dets = model.predict(source=img_list, 
                                    imgsz = 640, 
                                    conf = conf_score, 
                                    classes = [0, 1], 
                                    half = True, 
                                    verbose = False)
            t1 = time.time()
            
            bn_person_boxes, bn_non_person_boxes = remove_out_of_BBox(camera_info_dict = camera_info_dict, 
                                                                    bbox_bn= dets,
                                                                    fire_conf_score = fire_conf_score,
                                                                    camera_num_list = camera_num_list
                                                                    )
                
            for index, bbox in enumerate(bn_person_boxes):
                camera_info_dict[camera_num_list[index]]["person_bbox"] = camera_info_dict[camera_num_list[index]]["tracker"].update(bbox, img_list[index])
                camera_info_dict[camera_num_list[index]]["non_person_bbox"] = bn_non_person_boxes[index]

            for camera_num, camera_info in camera_info_dict.items():
                #지능형 알고리즘 실행
                camera_info = detect_action(camera_num = camera_num, 
                                            camera_info = camera_info,
                                            har_model = har_model,
                                            )
                # print(camera_name)
                # print(camera_info[7])

            t2 = time.time()

            if har_model is not None :
                har_model.refresh_id_dict()

            if datetime.now(KST).strftime("%H:%M:%S")[3:] == "00:00": #매 시간 00분 00초에 메모리 관리를 위한 신경망 모델 갱신
                del model
                gc.collect()
                torch.cuda.empty_cache()

                model = YOLO(yolo_model_path, task = "detect")
                if active_HAR  :
                    del har_model

                    har_model = Har_System(model_weight_path = model_weight_path, 
                                        device = device, 
                                        model_path = clip_path, 
                                        feature_extract = 'clip', 
                                        model_yml_path = model_yml_path, 
                                        stack_size = 32)


                for camera_num, camera_info in camera_info_dict.items():
                    del camera_info["tracker"]
                    # tracker = boxmot.BoTSORT(model_weights = Path(str(ROOT) + "/back/weight/ReID/osnet_x0_25_market.pt"),
                    #                         device = device,
                    #                         fp16 = False)
                    tracker = boxmot.BYTETracker(track_thresh=camera_info["person_conf_score"], 
                                                match_thresh=0.8, 
                                                track_buffer=150, 
                                                frame_rate=30, per_class=False)        

                    camera_info["tracker"] = tracker
                
            # print(f"fps : {1/(time.time() - t0)}")
            # print(f"total : {time.time() - t0}")
            # print(f"t1 : {t1 - t0}")
            # print(f"t2 : {t2 - t1}")
            # print(f"t1_1 : {t1 - t1_1}")
            # print(f"t1_1_2 : {t1_1 - t0}")

            send_SERVER_camera_info(host = HOST,
                                    port = PORT,
                                    camera_info_dict = camera_info_dict,
                                    har_model = har_model,
                                    )

            send_alarm_NVR(nvr_ip = NVR_IP,
                        nvr_id = NVR_ID, 
                        nvr_pw = NVR_PW, 
                        camera_info_dict = camera_info_dict,
                        ROI_color_dict = ROI_color_dict)
            
            

            camera_info_dict = camera_info_refresh(camera_info_dict)

            # draw_detect_result(camera_info_dict = camera_info_dict, 
            #                 har_model = har_model,
            #                 colors = colors, 
            #                 names = dets[0].names, 
            #                 ROI_color_dict = ROI_color_dict,
            #                 )
            

            # for camera_name, camera_info in camera_info_dict.items():
            #     cv2.imshow(camera_name, camera_info["img"])


            # key = cv2.waitKey(1)

            # if key == 27:
            #     cv2.destroyAllWindows()
            #     send_NVR_empty(nvr_ip = NVR_IP, nvr_id = NVR_ID, nvr_pw = NVR_PW)

            #     del model
            #     del har_model

            #     for camera_num, camera_info in camera_info_dict.items():
            #         del camera_info["tracker"]

            #     del camera_info_dict

            #     gc.collect()
            #     torch.cuda.empty_cache()

            #     break
