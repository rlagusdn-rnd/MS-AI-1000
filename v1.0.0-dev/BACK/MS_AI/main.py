import sys
import os
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # yolov5 strongsort root directory
WEIGHTS = ROOT / 'weights'

# if str(ROOT / 'yolo_tracking') not in sys.path:
sys.path.append(str(ROOT))  
sys.path.append(str(ROOT / 'lib'))  

# if str(ROOT / 'ms_vision') not in sys.path:
#     sys.path.append(str(ROOT / 'ms_vision'))  

from datetime import datetime, timezone, timedelta

import torch

import time
import numpy as np
import cv2
import gc

from lib.ultralytics import YOLO
from lib import boxmot

from utils.detect_utils import Img_Buffer, Colors, remove_out_of_BBox
from utils.ai_utils import Har_System, get_camera_info, get_grid_frame,\
                                    draw_detect_area_multi_camera, reset_camera_info_detect_list, detect_action_yolo
from nvr_utils import send_NVR, send_NVR_empty, restart_NVR_camera
from utils.util import Video_Buffer

from models.action_classcifition_model import Img_Feature_Extraction_Clip, Action_Classification_Model_Vit_b1

from loguru import logger as LOGGER


def ai_main(msg_buffer, gruop_id, camera_info_dict_ori, nvr_info, grid_size, video_save_path, img_save_path, is_admin):
        home_path = str(Path.home())

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # device = "cuda:0" if torch.cuda.is_available() else "cpu"
        conf_score = 0.01
        person_conf_score=0.33,
        fire_conf_score=0.05

        cls_names = { 0 : "person", 1 : "fire"}
        File_Path = Path(__file__).resolve()

        # yolo_model_path = str(File_Path.parents[0]) + '/weight/yolo/ms-ai2401.engine'  # load a pretrained model (recommended for training)
        yolo_model_path = str(File_Path.parents[0]) + '/weight/yolo/engine/ms-ai2401-finetune.engine'  # load a pretrained model (recommended for training)
        # yolo_model_path = str(File_Path.parents[0]) + '/weight/yolo/ms-ai2401-finetune.pt'  # load a pretrained model (recommended for training)
        # yolo_model_path = str(File_Path.parents[0]) + '/weight/yolo/engine/ms_ai2403_2_L.engine'  # load a pretrained model (recommended for training)
        # yolo_model_path = str(File_Path.parents[0]) + '/weight/yolo/last.pt'  # load a pretrained model (recommended for training)
        
        
        model = YOLO(yolo_model_path)  # load a pretrained model (recommended for training)\
        
        # model.to(device)
        
        # tracker = boxmot.BYTETracker(track_thresh=0.05, 
        #                             match_thresh=0.8, 
        #                             track_buffer=30, 
        #                             frame_rate=30)
        
        print(Path(str(File_Path.parents[0]) + "/weight/ReID/osnet_x0_25_market.pt"))

        tracker = boxmot.BoTSORT(model_weights = Path(str(File_Path.parents[0]) + "/weight/ReID/osnet_x0_25_market.pt"),
                         device = device,
                         fp16 = False
                         )
        
        print(yolo_model_path)
        print(model.names)

        print("AI 모델 생성 완료")

        # 동영상 저장을 위한 코덱 설정
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        if grid_size == 2:
            output_shape = (1280, 960)
        elif grid_size == 4:
            output_shape = (2560, 1920)
        else:
            output_shape = (640, 480)

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        camera_info_dict = {}

        height, width = 480, 640
        # height, width = 1080, 1920

        camera_num = 0

        nvr_id, nvr_password, nvr_ip  = nvr_info


        enevt_svg, event_post = "http://" + nvr_ip + "/api/events/svg", "http://" + nvr_ip + "/api/events"

        # 카메라 정보
        for key, value in camera_info_dict_ori.items():
            camera_info_dict[key] = get_camera_info(value, 
                                                    height, 
                                                    width, 
                                                    grid_size, 
                                                    camera_num)
            camera_num += 1

        video_buffer_list = []
        # Group 단위 Video pipeline 생성
        for key, value in camera_info_dict.items():
            print(value['ip'], value['appsink_name'])
            video_buffer_list.append([key, Video_Buffer(value['ip'], value['appsink_name'])])

        msg_buffer.set_check_connect_flag(True)

        # send_NVR_ROI(camera_info_dict, nvr_id, nvr_password, enevt_svg)

        record_once_flag = True
        har_model_gen_flag = False
        colors = Colors()
        stop_person_id_dict = {}

        for camera_id in camera_info_dict.keys():
            for cls in camera_info_dict[camera_id]["detect_id_dict"].keys():
                if har_model_gen_flag == False and (cls == "Falldown" or cls == "Fight"):
                    model_name = 'vit_b1_redu'
                    weight_name = "2401.pt"

                    Action_Classification_weight_path = os.path.join(str(File_Path.parents[0]) ,'weight', "HAR", "224x224", model_name, weight_name)
                    model_yml_path = os.path.join(str(File_Path.parents[0]) ,'configs')
                    clip_path = os.path.join(str(File_Path.parents[0]), 'weight', 'clip', "ViT-B-32.pt")

                    model_info = torch.load(Action_Classification_weight_path)

                    har_model = Action_Classification_Model_Vit_b1()
                    har_model.load_state_dict(model_info["model_state_dict"])
                    har_model.to(device).eval()

                    # har_system = Har_System(har_model = har_model, device = device, feature_type = "clip", model_yml_path = model_yml_path, stack_size=32)
                    har_system = Har_System(har_model = har_model, device = device, model_path = clip_path, feature_type = "clip", model_yml_path = model_yml_path, stack_size=32)

                    har_model_gen_flag = True

        if har_model_gen_flag == False:
            har_system = None

        KST = timezone(timedelta(hours=9))
        # AI 모델 실행
        with torch.no_grad():
            while True:
                t0 = time.time()
                frame_list = []

                for i in range(grid_size * grid_size):
                    try:
                        if video_buffer_list[i][1].frame_available():
                            frame_list.append(video_buffer_list[i][1].get_frame())
                        else:
                            frame_list.append(np.zeros((height, width, 3), np.uint8))
                            # print(f"frame_list {i} is empty")

                    except Exception as e :
                        frame_list.append(np.zeros((height, width, 3), np.uint8))
                        # print(f"frame_list {i} is empty")
                        # print(e)
                t0 = time.time()
                im0 = get_grid_frame(frame_list, grid_size)
                t1 = time.time()

                # print(im0.shape)

                dets = model.predict(source=im0, 
                                    imgsz = 1280, 
                                    conf = conf_score, 
                                    classes = [0, 1], 
                                    half = True, 
                                    verbose = False
                                    )
                
                # boxes = dets[0].boxes.data.cpu().numpy().astype(float)


                # dets = model.track(source=im0, imgsz = 1280, conf = conf_score, iou = 0.5, classes = [0, 1], half = False, verbose=False, persist=True, \
                        # tracker= os.path.join(str(File_Path.parents[0]), 'yolo_tracking', 'ultralytics', 'cfg', 'trackers', 'botsort.yaml'))
                t2 = time.time()
                # print(dets[0].boxes.data)
                person_boxes, non_person_boxes = remove_out_of_BBox(camera_info_dict = camera_info_dict, 
                                                                    bbox = dets[0].boxes.data.cpu().numpy().astype(float),
                                                                    person_conf_score = person_conf_score,
                                                                    fire_conf_score = fire_conf_score
                                                                    )
                
                
                person_tracks = tracker.update(person_boxes, im0)
                
                camera_info_dict, stop_person_id_dict = detect_action_yolo(camera_info_dict   = camera_info_dict, 
                                                                            tracking_outputs    = person_tracks,
                                                                            non_person_boxes =  non_person_boxes,
                                                                            video_buffer_list   = video_buffer_list,
                                                                            img                 = im0,  
                                                                            har_system          = har_system,
                                                                            img_size            = (width, height),
                                                                            grid_size           = grid_size, 
                                                                            stop_person_id_dict = stop_person_id_dict,
                                                                            debug               = False,
                                                                            )
                
                    
                t4 = time.time()


                img_output = draw_detect_area_multi_camera(camera_info_dict = camera_info_dict, 
                                                        im0 = im0, 
                                                        track_boxes = person_tracks, 
                                                        non_person_boxes = non_person_boxes,
                                                        colors = colors, 
                                                        har_system = har_system,
                                                        har_model_gen_flag = har_model_gen_flag, 
                                                        draw_box = True,
                                                        names = cls_names
                                                        )

                # msg_buffer.push_camera_data(camera_info_dict)
                send_NVR(camera_info_dict, nvr_id, nvr_password, enevt_svg, event_post, email=False)

                # print("-----------------------------------")
                # for key, value in camera_info_dict.items():
                #     print(key)
                #     print(value)

                camera_info_dict = reset_camera_info_detect_list(camera_info_dict)

                output = cv2.resize(img_output, output_shape)

                # cv2.imshow(f'AI_analyze_{gruop_id}', cv2.resize(img_track, (0, 0), fx = 0.5, fy = 0.5))
                # cv2.imshow(f'Group_{gruop_id}', cv2.resize(output, (0, 0), fx = 0.5, fy = 0.5))

                if is_admin :
                    cv2.imshow(f'AI_analyze_{gruop_id}', output)

                # cv2.imshow(f'test', dets[0].plot())

                # print(f"FPS: {1/(time.time() - t0)}")
                # print("Grid : ", int((t1 - t0) * 1000))
                # print("Yolo : ", int((t2 - t1) * 1000))
                # print("Track : ", int((t3 - t2) * 1000))
                # print("Action : ", int((t4 - t3) * 1000))

                if msg_buffer.get_snapshot_flag():
                    cv2.imwrite(f'{img_save_path}/group_{gruop_id}_{current_datetime}.jpg', output)
                    msg_buffer.set_snapshot_flag(False)

                if msg_buffer.get_record_flag():
                    if record_once_flag:
                        out = cv2.VideoWriter(f'{video_save_path}/group_{gruop_id}_{current_datetime}.avi', fourcc, 30.0, output_shape)
                        record_once_flag = False

                    out.write(output)

                key = cv2.waitKey(1)


                if har_model_gen_flag == True:
                    har_system.reset_id()

                if datetime.now(KST).strftime("%H:%M:%S")[3:] == "00:00": #매 시간 00분 00초에 NVR과 연결된 카메라 재시작
                    # print("restart NVR")
                    # restart_NVR_camera(camera_info_dict, nvr_ip, nvr_id, nvr_password)

                    del model
                    gc.collect()
                    torch.cuda.empty_cache()
                    stop_person_id_dict = {}
                    model = YOLO(yolo_model_path)  # load a pretrained model (recommended for training)\
                    # tracker = boxmot.BYTETracker(track_thresh=0.05, 
                    #          match_thresh=0.8, 
                    #          track_buffer=30, 
                    #          frame_rate=30)

                    tracker = boxmot.BoTSORT(model_weights = Path(str(File_Path.parents[0]) + "/weight/ReID/osnet_x0_25_market.pt"),
                         device = device,
                         fp16 = False
                         )

                if key == 27 or msg_buffer.get_close():
                    send_NVR_empty(camera_info_dict, nvr_id, nvr_password, enevt_svg)
                    cv2.destroyAllWindows()
                    # Group 단위 Video pipeline 종료
                    for video_buffer in video_buffer_list:
                        video_buffer[1].stop()
                        
                    # 신경망 모델 삭제
                    del model
                    del stop_person_id_dict
                    break
