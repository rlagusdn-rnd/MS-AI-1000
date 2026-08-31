import os
import cv2
import torch
from datetime import datetime, timedelta
import numpy as np
from tqdm import tqdm
import gc
import time
import requests
from requests.auth import HTTPBasicAuth
import shutil
import traceback
import sys

from back.ms_labeler_utils import (run_LLM,
                                   get_yolo_label, 
                                   get_zero_shot_label, 
                                   save_final_dataset, 
                                   get_img_buffer, 
                                   nms_test, 
                                   merge_overlapping_boxes, 
                                   train_model,
                                   convert_int8, 
                                   move_dataset_list, 
                                   remove_npy,
                                   create_dataset_list,
                                   SAM_label,
                                   remove_empty_folders,
)
MOONDREAM_MODEL_DATA_DIR = os.path.join(os.getcwd(),"..", "weights", "moondream2")
os.environ["HF_MODULES_CACHE"] = MOONDREAM_MODEL_DATA_DIR

from ultralytics import YOLO
from transformers import (AutoProcessor, 
                          AutoTokenizer, 
                          AutoModel, 
                          AutoModelForZeroShotObjectDetection, 
                          logging
)

from logging_config import setup_logging
from utils import load_crypography_json, save_crypography_json

logging.set_verbosity_error()
logging.disable_progress_bar()

# 로깅 설정
logger = setup_logging(logger_name="MS_LABELER", log_file="MS_LABELER.log")
TEST = False

VLM_URL = "http://127.0.0.1:1206"

from contextlib import redirect_stdout, redirect_stderr

def print_gpu_memory_usage():
    # 현재 사용 중인 GPU ID 확인
    gpu_id = torch.cuda.current_device()
    
    # 현재 GPU에서 사용 중인 메모리 (MB 단위)
    allocated_memory = torch.cuda.memory_allocated(gpu_id) / (1024 ** 2)
    
    # 캐시된 메모리 (MB 단위)
    cached_memory = torch.cuda.memory_reserved(gpu_id) / (1024 ** 2)
    
    print(f"GPU ID: {gpu_id}")
    print(f"Allocated Memory: {allocated_memory:.2f} MB")
    print(f"Cached Memory: {cached_memory:.2f} MB")

def get_labeling_video_num(camera_list_path):
    total_labeing_video_num = 0
    camera_name_list = os.listdir(camera_list_path)

    for camera_name in camera_name_list :
        if len(camera_name.split(".")) > 1: continue

        date_list_path = os.path.join(camera_list_path, camera_name)
        date_list = sorted(os.listdir(date_list_path))

        for date in date_list:
            if "videos_ori" in os.listdir(os.path.join(camera_list_path, camera_name, date)):
                video_list_path = os.path.join(camera_list_path, camera_name, date, "videos_ori")

                total_labeing_video_num += len(sorted(os.listdir(video_list_path)))

    return total_labeing_video_num

def ms_labeler(nvr_info_dict:dict, weight_name:str, zero_shot_flag):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", weight_name)

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "default.pt"

    last_yolo_weight_path = os.path.join(yolo_weight_path, yolo_weight_path, model_name)
    ALARM_TYPE_DIC = {2 : "침입", 1 : "배회", 6 : "쓰러짐", 4 : "방화", 7 : "싸움", 5 : "무단투기"}
    


    # camera_num_to_camera_name = {}

    # for nvr_ip, camrea_info_dict in ai_server_camera_info.items():
    #     for camera_name, camera_info in camrea_info_dict.items():
    #         camera_num_to_camera_name[camera_info["camera_id"]] = camera_name
    label_init_flag = True
    while label_init_flag:
        AI_info = load_crypography_json(os.path.join(os.getcwd(), "cache", "AI_info.json"))
        # login_info = load_crypography_json(os.path.join(os.getcwd(), "cache", "login_info.json"))
        ai_server_camera_info = load_crypography_json(os.path.join(os.getcwd(), "cache", "camera_info.json"))
        
        if AI_info["LABELER"]["last_labeling_time"] == "":
            video_time_start = (datetime.now() - timedelta(weeks=2)).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            video_time_start = AI_info["LABELER"]["last_labeling_time"]

        labelint_video_list = []
        # camera_id_input = ""

        for nvr_ip, camrea_info_dict in ai_server_camera_info.items():
            camera_num_to_camera_name = {}
            for camera_name, camera_info in camrea_info_dict.items():
                # camera_id_input += f"{int(camera_info['camera_id'])-1},"
                camera_id_input = f"{int(camera_info['camera_id'])-1}"
                camera_num_to_camera_name[int(camera_info['camera_id'])-1] = camera_name

                auth = HTTPBasicAuth(nvr_info_dict[nvr_ip]["id"], nvr_info_dict[nvr_ip]["pw"]) # NVR에 대한 ID / PW

                event_info_post = f'http://{nvr_ip}/api/events?types=70&since={video_time_start}&devices={camera_id_input}&sort=1&limit=1000'

                r = requests.get(event_info_post, auth=auth, timeout= 1)
                event_info_ori = r.json()
                for event in event_info_ori["events"]:
                    if "micro_ai" in event.keys():
                        labelint_video_list.append({"camera_name": camera_num_to_camera_name[event["devices"][0]], 
                                                    "video_time": event["timestamp"],
                                                    "detect_type": ALARM_TYPE_DIC[event["micro_ai"]["type"]],
                                                    "camera_num" : event["devices"][0],
                                                    "nvr_ip" : nvr_ip,
                                                    "nvr_id" : nvr_info_dict[nvr_ip]["id"],
                                                    "nvr_pw" : nvr_info_dict[nvr_ip]["pw"]
                                                    })

        # labelint_video_list.sort(key=lambda x: x["video_time"], reverse=True)
        labelint_video_list.sort(key=lambda x: x["video_time"], reverse=False)


        total_labeing_video_num = len(labelint_video_list)
        complete_video_cnt = 0
        labeling_time_list = []

        logger.info("-------------MS-Labeler 시작-------------")
        logger.info(f"zero shot mode : {True if zero_shot_flag else False}")
        logger.info(f"labeling weight name : {model_name}")
        logger.info(f"labeling video num : {total_labeing_video_num}")

        for video_info in labelint_video_list :
            try:
                #NVR에서 영상 다운로드
                # video_info에서 정보 추출
                camera_name = video_info["camera_name"]
                camera_num = video_info["camera_num"]
                video_timestamp = video_info["video_time"]

                # timestamp를 datetime으로 변환
                video_dt = datetime.fromtimestamp(video_timestamp)
                date = video_dt.strftime("%Y-%m-%d")  # 예: 2024-10-23
                video_time = video_dt.strftime("%Y-%m-%dT%H:%M:%S") # 예: 2024-10-23T13:32:54

                # AI_info["LABELER"]["last_labeling_time"]와 video_time을 비교하여 차이가 1분 이상 나지 않으면 continue
                if AI_info["LABELER"]["last_labeling_time"] != "":
                    last_labeling_datetime = datetime.strptime(AI_info["LABELER"]["last_labeling_time"], "%Y-%m-%dT%H:%M:%S")
                    # video_time은 문자열 (예: "2024-10-23T13:32:54"), datetime으로 변환
                    current_video_datetime = datetime.strptime(video_time, "%Y-%m-%dT%H:%M:%S")
                    time_diff_seconds = abs((current_video_datetime - last_labeling_datetime).total_seconds())
                    if time_diff_seconds < 60:  # 1분(60초) 미만이면 continue
                        continue

                # 영상 범위 설정 (10초) : 시작은 -5초, 끝은 +5초
                time_start_dt = video_dt - timedelta(seconds=5)
                time_end_dt = video_dt + timedelta(seconds=5)
                start_time = time_start_dt.strftime("%Y-%m-%dT%H:%M:%S")
                end_time = time_end_dt.strftime("%Y-%m-%dT%H:%M:%S")

                OUTPUT_FILENAME = f"tmp_label_video.mp4"

                nvr_ip = video_info["nvr_ip"]
                nvr_username = video_info["nvr_id"]
                nvr_password = video_info["nvr_pw"]

                # index=1(일반 MP4) 파라미터 사용
                url = f"http://{nvr_ip}/download/video{camera_num+1}.mp4?start={start_time}&end={end_time}&index=1"
                logger.info(f"Request video download: {url}")

                try:
                    resp = requests.get(url, auth=HTTPBasicAuth(nvr_username, nvr_password), stream=True, timeout=10)
                    resp.raise_for_status()
                    with open(OUTPUT_FILENAME, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    logger.info(f"Video downloaded: {OUTPUT_FILENAME}")
                except requests.exceptions.HTTPError as err:
                    AI_info["LABELER"]["last_labeling_time"] = video_time
                    save_crypography_json(
                        info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
                        info = AI_info
                    )
                    continue
                except requests.exceptions.ConnectionError as err:
                    logger.info(f"Connection error: {err}")
                    AI_info["LABELER"]["last_labeling_time"] = video_time
                    save_crypography_json(
                        info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
                        info = AI_info
                    )

                    continue
                except requests.exceptions.Timeout as err:
                    logger.info(f"Timeout error: {err}")
                    AI_info["LABELER"]["last_labeling_time"] = video_time
                    save_crypography_json(
                        info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
                        info = AI_info
                    )

                    continue
                except requests.exceptions.RequestException as err:
                    logger.info(f"Unknown error: {err}")
                    AI_info["LABELER"]["last_labeling_time"] = video_time
                    save_crypography_json(
                        info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
                        info = AI_info
                    )

                    continue

                with torch.no_grad():
                    t0 = time.time()
                    try: logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Auto labeling processing {camera_name} {date} {video_time} [{complete_video_cnt}/{total_labeing_video_num}] {np.mean(labeling_time_list)}")
                    except: logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Auto labeling processing {camera_name} {date} {video_time} [{complete_video_cnt}/{total_labeing_video_num}] 00:00")

                    save_date = date if isinstance(date, str) else date.strftime("%y.%m.%d") #25.01.01

                    event_name = f"{video_time.split('T')[1].replace(':','.')}_{video_info['detect_type']}" #12.15.23_배회

                    data_save_dir = os.path.join(os.getcwd(), ".." ,"backup", "dataset", "auto_labeled_data", nvr_ip, camera_name, save_date)
                    img_buffer = get_img_buffer(video_path = OUTPUT_FILENAME)

                    yolo_model = YOLO(last_yolo_weight_path)  # load a pretrained model (recommended for training)\
                    yolo_label_data = get_yolo_label(model = yolo_model, buffer = img_buffer)
                    del yolo_model

                    if zero_shot_flag:
                        MOONDREAM_MODEL_DATA_DIR = os.path.join(os.getcwd(),"..", "weights", "moondream2")
                        logger.info(f"Zero-shot labeling start")
                        zeroshot_label_data = get_zero_shot_label(buffer=img_buffer, 
                                                                model_path=MOONDREAM_MODEL_DATA_DIR)
                    else:
                        zeroshot_label_data = {}
                        for frame_num in yolo_label_data.keys():
                            zeroshot_label_data[frame_num] = []
                    
                    with open(os.devnull, 'w') as fnull:
                        with redirect_stdout(fnull), redirect_stderr(fnull):
                            # torch.cuda.reset_max_memory_allocated()
                            # torch.cuda.reset_max_memory_cached()
                            torch.cuda.empty_cache()
                            gc.collect()

                    non_llm_input_bboxes = {}
                    llm_input_bboxes = {}

                    for frame_num in yolo_label_data.keys():
                        non_llm_input_bboxes[frame_num], llm_input_bboxes[frame_num] = nms_test(yolo_label_data[frame_num], 
                                                                                                zeroshot_label_data[frame_num], 
                                                                                                iou_threshold=0.75)
                    
                    LLM_bbox = run_LLM(img_buffer = img_buffer, label = llm_input_bboxes, VLM_server_url = VLM_URL)

                    bboxes_list = {}

                    for frame_num in img_buffer.keys():
                        bboxes_list[frame_num] = merge_overlapping_boxes(non_llm_input_bboxes[frame_num] + LLM_bbox[frame_num], 
                                                                        iou_threshold = 0.33)

                    sam_label = SAM_label(img_buffer = img_buffer,
                                        label = bboxes_list,
                                        )

                    # 각 프레임별로 bbox가 다른 bbox에 완전히 포함되어 있다면(그리고 라벨이 같다면) 제거
                    for frame_num in list(sam_label.keys()):
                        bboxes = sam_label[frame_num]
                        filtered_bboxes = []
                        for i, boxA in enumerate(bboxes):
                            classA = boxA[0]
                            x1A, y1A, x2A, y2A = boxA[1], boxA[2], boxA[3], boxA[4]
                            is_contained = False
                            for j, boxB in enumerate(bboxes):
                                if i == j:
                                    continue
                                classB = boxB[0]
                                # 같은 라벨(class)인지 먼저 확인
                                if classA != classB:
                                    continue
                                x1B, y1B, x2B, y2B = boxB[1], boxB[2], boxB[3], boxB[4]
                                # boxA가 boxB에 완전히 포함되어 있는지 확인
                                if x1A >= x1B and y1A >= y1B and x2A <= x2B and y2A <= y2B:
                                    is_contained = True
                                    break
                            if not is_contained:
                                # INSERT_YOUR_CODE
                                width = x2A - x1A
                                height = y2A - y1A
                                area = width * height
                                if area <= 700:
                                    continue
                                filtered_bboxes.append(boxA)
                        sam_label[frame_num] = filtered_bboxes

                    save_final_dataset(event_name = event_name,
                                    img_buffer = img_buffer, 
                                    label_buffer = sam_label,
                                    data_save_dir = data_save_dir, 
                                    )
                    
                    del img_buffer, sam_label, bboxes_list, non_llm_input_bboxes, llm_input_bboxes

                    with open(os.devnull, 'w') as fnull:
                        with redirect_stdout(fnull), redirect_stderr(fnull):
                            # torch.cuda.reset_max_memory_allocated()
                            # torch.cuda.reset_max_memory_cached()
                            torch.cuda.empty_cache()
                            gc.collect()

                    # print_gpu_memory_usage()
                    complete_video_cnt += 1
                    labeling_time_list.append(time.time()-t0)

                    AI_info["LABELER"]["last_labeling_time"] = video_time
                    save_crypography_json(
                        info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
                        info = AI_info
                    )

                    label_init_flag = False

            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                tb = traceback.format_exc()
                logger.error(f"Error occurred at {current_time}: {e}\n{tb}")

    # cv2.destroyAllWindows()
    os.system("chmod 777 -R ./")
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : END SEFL-Labeling")

    response = requests.post(VLM_URL + "/unload-vlm-model",
                            json={"question" : [],
                            "data_type" : "",
                            "video_path" : ""})
    if response.status_code != 200:
        logger.error(f"Failed to finish auto labeling: {response.status_code}")
        logger.error(f"Response: {response.text}")
        return

    print(video_time)

    try:
        AI_info["LABELER"]["last_labeling_time"] = video_time
        save_crypography_json(
            info_filename_save_path = os.path.join(os.getcwd(), "cache", "AI_info.json"), 
            info = AI_info
        )
    except:
        pass

    HOST = "127.0.0.1"
    PORT = 65432

    url = f"http://{HOST}:{PORT}/stop-self-labeling-training"
    response = requests.put(url, json={"msg" : "ms_labeling"})

def train(weight_name:str):
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Start Training")

    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", weight_name)

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "yolo11s.pt"

    train_data_path = os.path.join(os.getcwd(), "..", "backup", "dataset")
    create_dataset_list(train_data_path)

    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo")
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : base model {model_name} Training")

    train_model(yolo_weight_path = os.path.join(yolo_weight_path, weight_name, model_name))
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            # torch.cuda.reset_max_memory_allocated()
            # torch.cuda.reset_max_memory_cached()
            torch.cuda.empty_cache()
            gc.collect()

    weight_path_list = convert_int8(train_data_path)

    date = datetime.now().strftime("%Y-%m-%d")  # 예: 2024-07-25

    new_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", date)
    os.makedirs(new_weight_path, exist_ok=True)

    for weight_path in weight_path_list:
        cmd = f"mv {weight_path} {new_weight_path}/"
        os.system(cmd)

    move_dataset_list(train_data_path)
    remove_npy()

    try:
        remove_empty_folders(os.path.join(train_data_path, "auto_labeled_data"))
        shutil.rmtree(os.path.join(os.getcwd(), "train"))

    except:
        pass
    
    os.system("chmod 777 -R ./")
    logger.info(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : END Training")

    HOST = "127.0.0.1"
    PORT = 65432

    url = f"http://{HOST}:{PORT}/stop-self-labeling-training"
    response = requests.put(url, json={"msg" : "ms_train"})