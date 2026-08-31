import os
import cv2
import torch
from datetime import datetime
import numpy as np
from tqdm import tqdm
import gc
import time

from back.ms_labeler_utils import (check_LLM, 
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
                                   SAM_label
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

def ms_labeler(camera_list_path, weight_name):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    yolo_weight_path = os.path.join(os.getcwd(), "back", "weight", "yolo", weight_name)

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "default.pt"

    last_yolo_weight_path = os.path.join(yolo_weight_path, yolo_weight_path, model_name)

    NVR_ID = camera_list_path.split("/")[-1]
    
    camera_name_list = os.listdir(camera_list_path)

    print("MS-Labeler 시작")
    print(camera_name_list)

    for camera_name in camera_name_list :
        if len(camera_name.split(".")) > 1:
            continue
        date_list_path = os.path.join(camera_list_path, camera_name)
        date_list = sorted(os.listdir(date_list_path))

        for date in date_list:
            pre_video_name = None

            if "videos_ori" in os.listdir(os.path.join(camera_list_path, camera_name, date)):
                video_list_path = os.path.join(camera_list_path, camera_name, date, "videos_ori")

                video_name_list = sorted(os.listdir(video_list_path))

                with torch.no_grad():
                    for video_name in tqdm(video_name_list, desc=f"Processing Videos for {camera_name} in {date}"):
                        print(f"processing {video_name}")
                        if pre_video_name is None: pre_video_name = video_name

                        else:
                            if abs((datetime.strptime(video_name[:8], "%H.%M.%S") - datetime.strptime(pre_video_name[:8], "%H.%M.%S")).total_seconds()) < 5: 
                                # print(f"{abs((t1 - t2).total_seconds())}초 차이 {t1} {t2}")
                                os.remove(os.path.join(video_list_path, video_name))
                                continue
                                
                        # print("111111111111111111111111111")
                        # print_gpu_memory_usage()
                        pre_video_name = video_name

                        yolo_model = YOLO(last_yolo_weight_path)  # load a pretrained model (recommended for training)\

                        processor = AutoProcessor.from_pretrained(os.path.join(os.getcwd(), "back", "weight", "grounding-dino-base"))
                        zero_shot_ob_model = AutoModelForZeroShotObjectDetection.from_pretrained(os.path.join(os.getcwd(),"back", "weight", "grounding-dino-base")).to(device)
                    
                        data_save_dir = os.path.join(os.getcwd(), "backup", "dataset", NVR_ID, camera_name, date)

                        img_buffer = get_img_buffer(video_path = os.path.join(video_list_path, video_name))

                        yolo_label_data = get_yolo_label(model = yolo_model, buffer = img_buffer)
                        zeroshot_label_data = get_zero_shot_label(model = zero_shot_ob_model, buffer = img_buffer, processor = processor, device = device)

                        del yolo_model, zero_shot_ob_model

                        torch.cuda.reset_max_memory_allocated()
                        torch.cuda.reset_max_memory_cached()
                        torch.cuda.empty_cache()
                        gc.collect()

                        # print("222222222222222222222222222")
                        # print_gpu_memory_usage()

                        non_llm_input_bboxes = {}
                        llm_input_bboxes = {}

                        for frame_num, label in yolo_label_data.items():
                            non_llm_input_bboxes[frame_num], llm_input_bboxes[frame_num] = nms_test(yolo_label_data[frame_num], 
                                                                                                    zeroshot_label_data[frame_num], 
                                                                                                    iou_threshold=0.75)
                            
                        LLM_bbox = check_LLM(model_path = os.getcwd() + "/back/weight/InternVL2-4B", 
                                            img_buffer = img_buffer,
                                            label = llm_input_bboxes,
                                            verbose = TEST
                                            )
                        
                        # print("3333333333333333333333333333333")
                        # print_gpu_memory_usage()

                        bboxes_list = {}

                        for frame_num, img in img_buffer.items():
                            bboxes_list[frame_num] = merge_overlapping_boxes(non_llm_input_bboxes[frame_num] + LLM_bbox[frame_num], 
                                                                             iou_threshold = 0.5)

                        sam_label = SAM_label(img_buffer = img_buffer,
                                            label = bboxes_list,
                                            video_name = video_name)


                        # sam_label = bboxes_list
                        
                        # print("444444444444444444444444444444444")
                        # print_gpu_memory_usage()

                        save_final_dataset(event_name = video_name,
                                           img_buffer = img_buffer, 
                                           label_buffer = sam_label,
                                           data_save_dir = data_save_dir, 
                                           )
                        
                        os.remove(os.path.join(video_list_path, video_name))

                        del img_buffer, sam_label, bboxes_list, non_llm_input_bboxes, llm_input_bboxes

                        torch.cuda.reset_max_memory_allocated()
                        torch.cuda.reset_max_memory_cached()
                        torch.cuda.empty_cache()
                        gc.collect()

                        # print("55555555555555555555555555555555555")
                        # print_gpu_memory_usage()


    cv2.destroyAllWindows()
    os.system("chmod 777 -R ./")
    print("END SEFL-Labeling")

def train(NVR_IP, weight_name):
    print("Start Training")

    yolo_weight_path = os.path.join(os.getcwd(), "back", "weight", "yolo", weight_name)

    if weight_name != "default":
        model_name = f"ms-ai_{weight_name[2:]}-M.pt"
    else:
        model_name = "default.pt"

    train_data_path = os.path.join(os.getcwd(), "backup", "dataset")
    create_dataset_list(train_data_path, NVR_IP)

    yolo_weight_path = os.path.join(os.getcwd(), "back", "weight", "yolo")

    train_model(yolo_weight_path = os.path.join(yolo_weight_path, weight_name, model_name))

    weight_path_list = convert_int8(train_data_path)

    date = datetime.now().strftime("%Y-%m-%d")  # 예: 2024-07-25

    new_weight_path = os.path.join(os.getcwd(), "back", "weight", "yolo", date)
    os.makedirs(new_weight_path, exist_ok=True)

    for weight_path in weight_path_list:
        cmd = f"mv {weight_path} {new_weight_path}/"
        os.system(cmd)

    move_dataset_list(train_data_path, NVR_IP)
    remove_npy()
    
    os.system("chmod 777 -R ./")
    print("END Training")
