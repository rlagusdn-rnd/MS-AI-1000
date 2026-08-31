import os
import cv2
import torch
from datetime import datetime
import numpy as np
from tqdm import tqdm
import gc
import time
import requests
import shutil
import traceback
import sys

from back.ms_labeler_utils import (run_LLM,
                                   get_yolo_label, 
                                   get_zero_shot_label, 
                                   save_final_dataset, 
                                   plot_one_box,
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

from ultralytics import YOLO
from transformers import (AutoProcessor, 
                          AutoModelForCausalLM, 
                          AutoTokenizer, 
                          AutoModel, 
                          AutoModelForZeroShotObjectDetection, 
                          logging
)

logging.set_verbosity_error()
logging.disable_progress_bar()

TEST = False
VLM_URL = "http://127.0.0.1:1206/vlm_QnA"
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



def ms_labeler(camera_list_path:str, weight_name:str, zero_shot_flag):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", weight_name)
    # zero_shot_flag = zero_shot_flag

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "default.pt"

    last_yolo_weight_path = os.path.join(yolo_weight_path, yolo_weight_path, model_name)

    NVR_ID = camera_list_path.split("/")[-1]
    
    camera_name_list = os.listdir(camera_list_path)
    total_labeing_video_num = get_labeling_video_num(camera_list_path)
    complete_video_cnt = 0
    labeling_time_list = []

    print("-------------MS-Labeler 시작-------------")
    print(f"zero shot mode : {zero_shot_flag}")
    print(f"labeling weight name : {model_name}")
    print(f"labeling video num : {total_labeing_video_num}")

    time.sleep(6)

    for camera_name in camera_name_list :
        if len(camera_name.split(".")) > 1:
            continue
        date_list_path = os.path.join(camera_list_path, camera_name)
        date_list = sorted(os.listdir(date_list_path))

        for date in date_list:
            pre_video_name = None

            if "videos_ori" in os.listdir(os.path.join(camera_list_path, camera_name, date)):
                video_list_path = os.path.join(camera_list_path, camera_name, date)
                video_name_list = sorted(os.listdir(video_list_path))

                with torch.no_grad():
                    # for video_name in tqdm(video_name_list, desc=f"Processing Videos for {camera_name} in {date}"):
                    for video_name in video_name_list:
                        try:
                            if pre_video_name is None: pre_video_name = video_name
                            else:
                                if abs((datetime.strptime(video_name[:8], "%H.%M.%S") - datetime.strptime(pre_video_name[:8], "%H.%M.%S")).total_seconds()) < 600: 
                                    os.remove(os.path.join(video_list_path, video_name))
                                    total_labeing_video_num += 1
                                    continue

                            t0 = time.time()
                            try: print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Auto labeling processing {camera_name} {date} {video_name} [{complete_video_cnt}/{total_labeing_video_num}] {np.mean(labeling_time_list)}")
                            except: print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Auto labeling processing {camera_name} {date} {video_name} [{complete_video_cnt}/{total_labeing_video_num}] 00:00")
                            pre_video_name = video_name
                        
                            data_save_dir = os.path.join(os.getcwd(), ".." ,"backup", "dataset", NVR_ID, camera_name, date)
                            img_buffer = get_img_buffer(video_path = os.path.join(video_list_path, video_name))

                            yolo_model = YOLO(last_yolo_weight_path)  # load a pretrained model (recommended for training)\
                            yolo_label_data = get_yolo_label(model = yolo_model, buffer = img_buffer)
                            del yolo_model

                            if zero_shot_flag:
                                processor = AutoProcessor.from_pretrained(os.path.join(os.getcwd(), "..", "weights", "grounding-dino-base"))
                                zero_shot_ob_model = AutoModelForZeroShotObjectDetection.from_pretrained(os.path.join(os.getcwd(),"..", "weights", "grounding-dino-base")).to(device)
                                zeroshot_label_data = get_zero_shot_label(model = zero_shot_ob_model, buffer = img_buffer, processor = processor, device = device)

                                del zero_shot_ob_model
                                
                                # zeroshot_label_data = {}
                                for frame_num in yolo_label_data.keys():
                                    zeroshot_label_data[frame_num] = []
                            
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
                            
                            if zero_shot_flag:
                                LLM_bbox = run_LLM(img_buffer = img_buffer, label = llm_input_bboxes, VLM_server_url = VLM_URL)
                            else: LLM_bbox = llm_input_bboxes

                            bboxes_list = {}

                            for frame_num in img_buffer.keys():
                                bboxes_list[frame_num] = merge_overlapping_boxes(non_llm_input_bboxes[frame_num] + LLM_bbox[frame_num], 
                                                                                iou_threshold = 0.33)

                            sam_label = SAM_label(img_buffer = img_buffer,
                                                label = bboxes_list,
                                                video_name = video_name)


                            save_final_dataset(event_name = video_name,
                                            img_buffer = img_buffer, 
                                            label_buffer = sam_label,
                                            data_save_dir = data_save_dir, 
                                            )
                            
                            os.remove(os.path.join(video_list_path, video_name))

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

                        except Exception as e:
                                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                tb = traceback.format_exc()
                                print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
                                os.remove(os.path.join(video_list_path, video_name))

    cv2.destroyAllWindows()
    os.system("chmod 777 -R ./")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : END SEFL-Labeling")

    HOST = "127.0.0.1"
    PORT = 65432

    url = f"http://{HOST}:{PORT}/end_ms_labeler"
    response = requests.put(url, json={"msg" : "ms_labeling"})

def train(NVR_IP:str, weight_name:str):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : Start Training")

    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", weight_name)

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "default.pt"

    train_data_path = os.path.join(os.getcwd(), "..", "backup", "dataset")
    create_dataset_list(train_data_path, NVR_IP)

    yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo")

    train_model(yolo_weight_path = os.path.join(yolo_weight_path, weight_name, model_name))
    with open(os.devnull, 'w') as fnull:
        with redirect_stdout(fnull), redirect_stderr(fnull):
            # torch.cuda.reset_max_memory_allocated()
            # torch.cuda.reset_max_memory_cached()
            torch.cuda.empty_cache()
            gc.collect()

    weight_path_list = convert_int8(train_data_path)

    date = datetime.now().strftime("%Y-%m-%d")  # 예: 2024-07-25

    new_weight_path = os.path.join(os.getcwd(), "..", "weight", "yolo", date)
    os.makedirs(new_weight_path, exist_ok=True)

    for weight_path in weight_path_list:
        cmd = f"mv {weight_path} {new_weight_path}/"
        os.system(cmd)

    move_dataset_list(train_data_path, NVR_IP)
    remove_npy()

    try:
        remove_empty_folders(os.path.join(train_data_path, NVR_IP))
        shutil.rmtree(os.path.join(os.getcwd(), "train"))

    except:
        pass
    
    os.system("chmod 777 -R ./")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : END Training")

    HOST = "127.0.0.1"
    PORT = 65432

    url = f"http://{HOST}:{PORT}/end_ms_labeler"
    response = requests.put(url, json={"msg" : "ms_train"})
