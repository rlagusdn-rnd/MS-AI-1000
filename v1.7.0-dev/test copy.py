import base64
from io import BytesIO
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 1번 GPU만 노출

import cv2
# cv2.namedWindow("test", cv2.WINDOW_NORMAL)
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
import re
import shutil

from ultralytics import YOLO
from PIL import Image

MOONDREAM_MODEL_DATA_DIR = os.path.join(os.getcwd(),"../weights/moondream2")
os.environ["HF_MODULES_CACHE"] = MOONDREAM_MODEL_DATA_DIR
from transformers import AutoModelForCausalLM

from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

from qwen_vl_utils import process_vision_info

NAMES = {0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        4: "bus",
        5: "truck",
        6: "fire"}

coco_NAMES = {0: 0,
             1: 1,
             2: 2,
             3: 3,
             5: 4,
             7: 5}

# zeroshot_NAMES = {"a person" : 0,
#                  "a bicycle" : 1,
#                  "a car" : 2,
#                  "a motorcycle" : 3,
#                  "a bus" : 4,
#                  "a truck" : 5,
#                  "a fire" : 6}

zeroshot_NAMES = {"person" : 0,
                 "bicycle" : 1,
                 "car" : 2,
                 "motorcycle" : 3,
                 "bus" : 4,
                 "truck" : 5,
                 "fire" : 6}

def calculate_iou(box1, box2):
    """
    두 박스 간의 IOU를 계산합니다.
    box1, box2: [x1, y1, x2, y2] 형태
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # 교집합 영역 계산
    x1_inter = max(x1_1, x1_2)
    y1_inter = max(y1_1, y1_2)
    x2_inter = min(x2_1, x2_2)
    y2_inter = min(y2_1, y2_2)
    
    if x2_inter <= x1_inter or y2_inter <= y1_inter:
        return 0.0
    
    intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    
    # 합집합 영역 계산
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0

def apply_nms(boxes, iou_threshold=0.5):
    """
    NMS를 적용하여 중복 박스를 제거합니다.
    boxes: [[cls, x1, y1, x2, y2, score], ...] 형태의 리스트
    """
    if len(boxes) == 0:
        return []
    
    # 클래스별로 그룹화
    class_groups = {}
    for box in boxes:
        cls = box[0]
        if cls not in class_groups:
            class_groups[cls] = []
        class_groups[cls].append(box)
    
    result_boxes = []
    
    # 각 클래스별로 NMS 적용
    for cls, cls_boxes in class_groups.items():
        if len(cls_boxes) == 0:
            continue
        
        # 점수 기준으로 정렬 (높은 점수부터)
        cls_boxes = sorted(cls_boxes, key=lambda x: x[5], reverse=True)
        
        while len(cls_boxes) > 0:
            # 가장 높은 점수의 박스 선택
            best_box = cls_boxes.pop(0)
            result_boxes.append(best_box)
            
            # 나머지 박스들과 IOU 비교
            remaining_boxes = []
            for box in cls_boxes:
                iou = calculate_iou(best_box[1:5], box[1:5])
                if iou < iou_threshold:
                    remaining_boxes.append(box)
            
            cls_boxes = remaining_boxes
    
    return result_boxes

def merge_label_data(yolo_label_data, zeroshot_label_data, iou_threshold=0.5):
    """
    YOLO와 Zero-shot 라벨 데이터를 통합합니다.
    
    Args:
        yolo_label_data: YOLO 라벨 데이터 {frame_num: [[cls, x1, y1, x2, y2, score], ...]}
        zeroshot_label_data: Zero-shot 라벨 데이터 {frame_num: [[cls, x1, y1, x2, y2, score], ...]}
        iou_threshold: NMS에서 사용할 IOU 임계값
    
    Returns:
        merged_label_data: 통합된 라벨 데이터 {frame_num: [[cls, x1, y1, x2, y2, score], ...]}
    """
    merged_label_data = {}
    
    # 모든 프레임에 대해 처리
    all_frames = set(yolo_label_data.keys()) | set(zeroshot_label_data.keys())
    
    for frame_num in all_frames:
        # 두 라벨 데이터에서 해당 프레임의 박스들을 가져옴
        yolo_boxes = yolo_label_data.get(frame_num, [])
        zeroshot_boxes = zeroshot_label_data.get(frame_num, [])
        
        # 모든 박스를 하나의 리스트로 합침
        all_boxes = yolo_boxes + zeroshot_boxes
        
        # NMS 적용하여 중복 박스 제거
        merged_boxes = apply_nms(all_boxes, iou_threshold)
        
        merged_label_data[frame_num] = merged_boxes
    
    return merged_label_data

def split_video_to_image(video_path, train_data_video_name):
    """
    비디오를 로드하고 초당 2장씩 이미지를 추출하여 10초마다 다른 폴더에 저장하는 함수
    
    Args:
        video_path (str): 비디오 파일 경로
        train_data_video_name (str): 비디오 파일 이름
    """
    cap = cv2.VideoCapture(video_path)
    
    # 비디오 속성 가져오기
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # 초당 n장 추출을 위한 프레임 간격 계산
    frame_interval = fps // 1  # 1초당 n장

    # 10초마다 폴더 변경을 위한 계산
    frames_per_10_seconds = fps * 10  # 10초당 프레임 수
    
    # 기본 이미지 저장 경로
    base_save_dir = os.path.join(train_data_path, "tmp_images", train_data_video_name)
    os.makedirs(base_save_dir, exist_ok=True)
    
    frame_count = 0
    saved_count = 0
    current_folder_index = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            if frame_count % frame_interval != 0:
                shutil.rmtree(os.path.join(base_save_dir, f"segment_{current_folder_index:03d}"))
            break
            
        # frame_interval 마다 이미지 저장
        if frame_count % frame_interval == 0:
            # 10초마다 폴더 변경
            current_folder_index = frame_count // frames_per_10_seconds
            
            # 현재 10초 구간에 해당하는 폴더 생성
            current_save_dir = os.path.join(base_save_dir, f"segment_{current_folder_index:03d}")
            os.makedirs(current_save_dir, exist_ok=True)
            
            # img_name = f"{train_data_video_name[:-4]}_{saved_count:04d}.jpg"
            img_name = f"{saved_count:02d}.jpg"
            cv2.imwrite(os.path.join(current_save_dir, img_name), cv2.resize(frame, (1280, 720)))
            saved_count += 1
            
        frame_count += 1
        
    cap.release()

def get_img_buffer(video_path:str) -> list:
    img_buffer = []

    for img_name in sorted(os.listdir(video_path)):
        img_path = os.path.join(video_path, img_name)
        img = cv2.imread(img_path)

        img_buffer.append(img)

    return img_buffer

def get_yolo_label(model_path:str,buffer:list, init_model = False) -> dict:
    model = YOLO(model_path)

    yolo_label_data = {}
    
    # 배치 크기 설정
    batch_size = 8
    
    # 프레임 번호와 이미지를 분리
    frame_nums = list(range(len(buffer)))
    images = buffer
    
    # 배치 단위로 처리
    for i in range(0, len(images), batch_size):
        batch_frames = frame_nums[i:i+batch_size]
        batch_images = images[i:i+batch_size]
        
        # 배치로 예측 수행
        if init_model:
            results = model.predict(batch_images, classes = [0, 1, 2, 3, 5, 7], imgsz=640, conf=0.33, iou=0.5, verbose=False)

            # 각 결과 처리
            for j, result in enumerate(results):
                frame_num = batch_frames[j]
                boxes = result.boxes.data.cpu().numpy().astype(float)
                
                frame_labels = []
                for box in boxes:
                    if len(box) != 0:
                        x1, y1, x2, y2 = box[0:4].astype('int')  # float64 to int
                        cls = box[-1].astype('int')
                        if cls in coco_NAMES.keys():
                            cls = coco_NAMES[cls]

                        if cls == 0 and box[4] < 0.56: #사람에 대한 검출 정확도 향상
                            continue

                        frame_labels.append([cls, x1, y1, x2, y2, box[4]])
                
                yolo_label_data[frame_num] = frame_labels
        else:
            results = model.predict(batch_images, imgsz=640, conf=0.33, iou=0.5, verbose=False)
            # results = model.predict(batch_images, classes = [0, 2, 4, 5], imgsz=640, conf=0.33, iou=0.5, verbose=False)

            for j, result in enumerate(results):
                frame_num = batch_frames[j]
                boxes = result.boxes.data.cpu().numpy().astype(float)
                
                frame_labels = []
                for box in boxes:
                    if len(box) != 0:
                        x1, y1, x2, y2 = box[0:4].astype('int')  # float64 to int
                        cls = box[-1].astype('int')
                        if cls == 0 and box[4] < 0.56: #사람에 대한 검출 정확도 향상
                            continue
                        frame_labels.append([cls, x1, y1, x2, y2, box[4]])

                yolo_label_data[frame_num] = frame_labels

    return yolo_label_data

# def get_zero_shot_label(buffer:list, device):
#     model_path = os.getcwd() + "/../weights/grounding-dino-base"
#     model = AutoModelForZeroShotObjectDetection.from_pretrained(model_path).to(device)
#     processor = AutoProcessor.from_pretrained(model_path)

#     zeroshot_label_data = {}

#     for frame_num in range(len(buffer)):
#         zeroshot_label_data[frame_num] = []

#     text_labels = [["a person", "a bicycle", "a car", "a motorcycle", "a bus", "a truck", "a fire"]]

#     for frame_num, img in enumerate(buffer):
#         pli_img = Image.fromarray(img.astype('uint8'), 'RGB')
#         inputs = processor(images=pli_img, text=text_labels, return_tensors="pt").to(device)

#         with torch.no_grad():
#             outputs = model(**inputs)

#         results = processor.post_process_grounded_object_detection(
#             outputs,
#             inputs.input_ids,
#             box_threshold=0.4,
#             text_threshold=0.3,
#             target_sizes=[pli_img.size[::-1]]
#         )

#         for i, boxes in enumerate(results[0]["boxes"].tolist()):
#             if results[0]["labels"][i] in zeroshot_NAMES.keys() :
#                 # zeroshot_NAMES에서 클래스 ID를 가져와서 NAMES에 매핑
#                 class_id = zeroshot_NAMES[results[0]["labels"][i]]
#                 zeroshot_label_data[frame_num].append([class_id] + boxes + [results[0]["scores"][i]])

#     return zeroshot_label_data


def get_zero_shot_label(buffer:list, device):
    

    model = AutoModelForCausalLM.from_pretrained(
        pretrained_model_name_or_path=MOONDREAM_MODEL_DATA_DIR,
        cache_dir=MOONDREAM_MODEL_DATA_DIR,
        trust_remote_code=True,
        local_files_only=True,
        device_map={"": "cuda"}  
    )

    zeroshot_label_data = {}

    for frame_num in range(len(buffer)):
        zeroshot_label_data[frame_num] = []

    # text_labels = ["person", "bicycle", "car", "motorcycle", "bus", "truck", "fire"]
    text_labels = ["person", "car", "bus", "truck"]

    for frame_num, img in enumerate(buffer):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
        pli_img = Image.fromarray(img_rgb.astype('uint8'), 'RGB')

        for text_label in text_labels:
            with torch.no_grad():
                output_text = model.detect(image=pli_img, object=text_label)

            for bbox_list in output_text["objects"]:
                x_min, y_min, x_max, y_max = bbox_list["x_min"] * img.shape[1], bbox_list["y_min"] * img.shape[0], bbox_list["x_max"] * img.shape[1], bbox_list["y_max"] * img.shape[0]
                class_id = zeroshot_NAMES[text_label]
                zeroshot_label_data[frame_num].append([class_id, x_min, y_min, x_max, y_max, 0.33])

    del model
    torch.cuda.empty_cache()
    gc.collect()

    return zeroshot_label_data

def make_square_bbox(bbox, img, extend_ratio = 1.5):
    label, x1, y1, x2, y2, conf = bbox
    img_height, img_width = img.shape[:2]

    # Calculate width, height, and maximum side length
    width = x2 - x1
    height = y2 - y1

    max_side = max(width, height) * extend_ratio  # Increase by 1.3 times
    
    # Calculate the center of the bounding box
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Calculate new coordinates
    new_x1 = center_x - max_side / 2
    new_y1 = center_y - max_side / 2
    new_x2 = center_x + max_side / 2
    new_y2 = center_y + max_side / 2
    
    # Ensure the new coordinates are within image boundaries
    new_x1 = max(new_x1, 0)
    new_y1 = max(new_y1, 0)
    new_x2 = min(new_x2, img_width)
    new_y2 = min(new_y2, img_height)
    
    return [new_x1, new_y1, new_x2, new_y2, conf, label]

def parse_assistant_response(response_text):
    """
    LLM 응답에서 assistant 부분만 파싱하는 함수
    
    Args:
        response_text (str): LLM의 전체 응답 텍스트
        
    Returns:
        str: assistant의 답변 부분만 추출된 문자열
    """
    if not response_text:
        return ""
    
    # 리스트인 경우 첫 번째 요소 사용
    if isinstance(response_text, list):
        response_text = response_text[0]
    
    # 방법 1: 이중 중괄호 형식 {{answer: yes/no}} 파싱
    double_brace_pattern = r'\{\{answer:\s*(yes|no)\}\}'
    double_brace_match = re.search(double_brace_pattern, response_text, re.IGNORECASE)
    if double_brace_match:
        result = double_brace_match.group(1).lower()
        return result
    
    # 방법 2: JSON 형식에서 target_detected 파싱
    json_pattern = r'"target_detected":\s*"(yes|no)"'
    json_match = re.search(json_pattern, response_text, re.IGNORECASE)
    if json_match:
        result = json_match.group(1).lower()
        return result
    
    # 방법 3: {answer: 'yes'/'no'} 형식 파싱 (기존)
    answer_pattern = r'\{answer:\s*[\'"](yes|no)[\'"]\}'
    answer_match = re.search(answer_pattern, response_text, re.IGNORECASE)
    if answer_match:
        result = answer_match.group(1).lower()
        return result
    
    # 방법 4: assistant 다음의 첫 번째 단어 추출 (기존 로직)
    if "assistant" in response_text.lower():
        # 마지막 assistant의 위치를 찾음
        assistant_index = response_text.lower().rfind("assistant")
        if assistant_index != -1:
            # assistant 다음의 텍스트 추출
            after_assistant = response_text[assistant_index + len("assistant"):]
            
            # 공백과 개행 제거 후 첫 번째 단어만 추출
            words = after_assistant.strip().split()
            
            if words:
                result = words[0].strip('.,!?').lower()  # 문장부호 제거하고 소문자로 변환
                # yes/no만 허용
                if result in ['yes', 'no']:
                    return result
                # 감탄사나 특수문자로 된 긍정적 응답 처리
                elif result in ['!!!!', '!!!', '!!', '!', 'y', 'ye', 'yep', 'yeah', 'ok', 'okay', 'sure', 'correct', 'right', 'true']:
                    return 'yes'
    
    # 방법 5: 정규표현식으로 마지막 assistant 다음의 첫 번째 단어 추출
    assistant_pattern = r'.*assistant\s*([A-Za-z!]+)'
    assistant_match = re.search(assistant_pattern, response_text, re.IGNORECASE | re.DOTALL)
    
    if assistant_match:
        result = assistant_match.group(1).strip().lower()
        # yes/no만 허용
        if result in ['yes', 'no']:
            return result
        # 감탄사나 특수문자로 된 긍정적 응답 처리
        elif result in ['!!!!', '!!!', '!!', '!', 'y', 'ye', 'yep', 'yeah', 'ok', 'okay', 'sure', 'correct', 'right', 'true']:
            return 'yes'
    
    # 방법 6: 줄 단위로 분할하여 마지막 assistant가 포함된 줄에서 첫 번째 단어 추출
    lines = response_text.strip().split('\n')
    for i in range(len(lines)-1, -1, -1):  # 뒤에서부터 검색
        line = lines[i]
        if 'assistant' in line.lower():
            # assistant 제거 후 첫 번째 단어 추출
            clean_line = line.replace('assistant', '').strip()
            words = clean_line.split()
            if words:
                result = words[0].strip('.,!?').lower()
                # yes/no만 허용
                if result in ['yes', 'no']:
                    return result
                # 감탄사나 특수문자로 된 긍정적 응답 처리
                elif result in ['!!!!', '!!!', '!!', '!', 'y', 'ye', 'yep', 'yeah', 'ok', 'okay', 'sure', 'correct', 'right', 'true']:
                    return 'yes'
    
    # 방법 7: 문자열 분할 후 마지막 부분에서 첫 번째 단어 추출
    parts = response_text.split("assistant")
    if len(parts) > 1:
        words = parts[-1].strip().split()
        if words:
            result = words[0].strip('.,!?').lower()
            # yes/no만 허용
            if result in ['yes', 'no']:
                return result
            # 감탄사나 특수문자로 된 긍정적 응답 처리
            elif result in ['!!!!', '!!!', '!!', '!', 'y', 'ye', 'yep', 'yeah', 'ok', 'okay', 'sure', 'correct', 'right', 'true']:
                return 'yes'
    
    # 아무것도 찾지 못한 경우 빈 문자열 반환
    return ""

def run_LLM(img_buffer : dict, label : dict):
    # model_path = os.getcwd() + "/../weights/Qwen2.5-VL-3B-Instruct-AWQ"
    # model_path = os.getcwd() + "/../weights/Qwen2.5-VL-7B-Instruct-AWQ"
    # model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    #     model_path,
    #     torch_dtype=torch.bfloat16,
    #     attn_implementation="flash_attention_2",
    #     device_map={"": "cuda:0"},
    # )

    model_path = os.getcwd() + "/../weights/Qwen3-VL-4B-Instruct"
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        model_path,
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="auto",
    )

    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True, use_fast=True)

    # model.generation_config.temperature=None
    # model.generation_config.top_p=None
    # model.generation_config.top_k=None

    for frame_num, img in enumerate(img_buffer):
        bboxes = label[frame_num]
        new_label = []

        for cls, x1, y1, x2, y2, score in bboxes:
            extend_x1, extend_y1, extend_x2, extend_y2, score, cls = make_square_bbox([cls, x1, y1, x2, y2, score], img, extend_ratio=5)
            cropped_img_extend = img[int(extend_y1) : int(extend_y2), int(extend_x1) : int(extend_x2)]

            if (cropped_img_extend.shape[0] > img.shape[0]/3) or cropped_img_extend.shape[1] > img.shape[1]/3:
                extend_x1, extend_y1, extend_x2, extend_y2, score, cls = make_square_bbox([cls, x1, y1, x2, y2, score], img, extend_ratio=3)
                cropped_img_extend = img[int(extend_y1) : int(extend_y2), int(extend_x1) : int(extend_x2)]

                if (cropped_img_extend.shape[0] > img.shape[0]/3) or cropped_img_extend.shape[1] > img.shape[1]/3:
                    extend_x1, extend_y1, extend_x2, extend_y2, score, cls = make_square_bbox([cls, x1, y1, x2, y2, score], img, extend_ratio=1.5)
                    cropped_img_extend = img[int(extend_y1) : int(extend_y2), int(extend_x1) : int(extend_x2)]

            cropped_img_extend = cv2.cvtColor(cropped_img_extend, cv2.COLOR_BGR2RGB) 
            pil_img = Image.fromarray(cropped_img_extend.astype('uint8'), 'RGB')
            ## Base64 encoded image
            img_buffer = BytesIO()
            pil_img.save(img_buffer, format='JPEG')
            pil_img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

            try:
                if int(cls) in [1, 3]:
                    messages = [{"role": "user", 
                            "content": [{"type": "image", 
                                "image": f"data:image;base64,{pil_img_base64}"}, 
                                {"type": "text", 
                                # "text": "You determine " + f"{NAMES[1]}" +  " or " + f"{NAMES[3]}" + " in this image. " + "Answer in the following format:\n" + "{{anwser: 'yes or no', reason: 'reason for your answer'}}"}]}]
                                # "text": "You determine " + "Two-Wheeled Vehicles" + " in this image. " + "Answer in the following format:\n" + "{{anwser: 'yes or no', reason: 'reason for your answer'}}"}]}]
                                "text": "You determine " + "Two-Wheeled Vehicles" + " in this image. " + "Answer in the following format:\n" + "{{anwser: 'yes or no'}}"}]}]

                else:
                    messages = [{"role": "user", 
                            "content": [{"type": "image", 
                                "image": f"data:image;base64,{pil_img_base64}"}, 
                                {"type": "text", 
                                "text": "You determine " + f"{NAMES[cls]}" + " in this image. " + "Answer in the following format:\n" + "{{anwser: 'yes or no'}}"}]}]

            except Exception as e:
                    print(e)
                    print(cls, x1, y1, x2, y2, score)


            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            image_inputs, video_inputs, video_kwargs = process_vision_info(messages, return_video_kwargs=True)

            inputs = processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
                **video_kwargs,
            )

            gpu_inputs = {}
            for key, value in inputs.items():
                if torch.is_tensor(value):
                    gpu_inputs[key] = value.to("cuda", non_blocking=True)
                else:
                    gpu_inputs[key] = value
            inputs = gpu_inputs
            torch.cuda.synchronize()  # GPU 작업 동기화


            generated_ids = model.generate(
                    **inputs, 
                    max_new_tokens=1024,  # 토큰 수 제한으로 메모리 사용량 조절
                    do_sample=False,     # 결정적 생성
                    pad_token_id=processor.tokenizer.eos_token_id
                )

            response = processor.batch_decode(
                generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )
            torch.cuda.synchronize()
            # assistant 부분만 파싱
            assistant_answer = parse_assistant_response(response)

            print(f"Parsed assistant answer: {NAMES[cls]}, {assistant_answer}")

            if "yes" in assistant_answer.lower():
                new_label.append([cls, x1, y1, x2, y2, score])

            else:
                print(response)
                # file_name = f"./images/{NAMES[cls]}_{assistant_answer}_{time.time()}.jpg"
                # cv2.imwrite(file_name,cv2.cvtColor(cropped_img_extend, cv2.COLOR_RGB2BGR))

            # file_name = f"./images/{NAMES[cls]}_{assistant_answer}_{time.time()}.jpg"
            # cv2.imwrite(file_name,cv2.cvtColor(cropped_img_extend, cv2.COLOR_RGB2BGR))


        label[frame_num] = new_label

    try:    
        del model, processor, generated_ids, inputs, image_inputs, video_inputs, video_kwargs, text

    except Exception as e:
        print(e)
        
    torch.cuda.empty_cache()
    gc.collect()

    return label

def mask_to_bbox(mask):
    """
    세그멘테이션 마스크에서 bbox를 추출하는 함수
    
    Args:
        mask (numpy.ndarray): 이진 마스크 (True/False 또는 0/1)
        
    Returns:
        list: [x, y, w, h] 형태의 bbox 리스트
    """
    mask_uint8 = np.squeeze(mask).astype(np.uint8)  # 데이터 타입 변환
    # cv2.imshow("test",mask_uint8*255)
    # cv2.waitKey(0)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    return [cv2.boundingRect(contour) for contour in contours]


def nms(boxes, iou_threshold=0.5):
    """
    NMS를 적용하여 중복 박스를 제거하는 함수
    
    Args:
        boxes (list): [[cls, x1, y1, x2, y2, score], ...] 형태의 박스 리스트
        iou_threshold (float): IOU 임계값
        
    Returns:
        list: NMS 적용 후 남은 박스 리스트
    """
    if len(boxes) == 0:
        return []
    
    # 클래스별로 그룹화
    class_groups = {}
    for box in boxes:
        cls = box[0]
        if cls not in class_groups:
            class_groups[cls] = []
        class_groups[cls].append(box)
    
    result_boxes = []
    
    # 각 클래스별로 NMS 적용
    for cls, cls_boxes in class_groups.items():
        if len(cls_boxes) == 0:
            continue
        
        # 점수 기준으로 정렬 (높은 점수부터)
        cls_boxes = sorted(cls_boxes, key=lambda x: x[5], reverse=True)
        
        if len(cls_boxes) > 1:
            while len(cls_boxes) > 0:
                # 가장 높은 점수의 박스 선택
                best_box = cls_boxes.pop(0)
                result_boxes.append(best_box)
                
                # 나머지 박스들과 IOU 비교
                remaining_boxes = []
                for box in cls_boxes:
                    iou = calculate_iou(best_box[1:5], box[1:5])
                    # best_box와 box가 완전히 동일한 경우 box는 제거 (즉, remaining_boxes에 추가하지 않음)
                    if best_box[1:5] == box[1:5]:
                        continue

                    if iou < iou_threshold:
                        remaining_boxes.append(box)
                
                cls_boxes = remaining_boxes

        elif len(cls_boxes) == 1:
            result_boxes.append(cls_boxes[0])

    return result_boxes
def run_sam(img_buffer : list, label : dict, img_path : str):
    # 레이블이 비어있는지 확인
    if not label or all(len(boxes) == 0 for boxes in label.values()):
        print("No labels to process with SAM")
        return label

    from sam2.build_sam import build_sam2_video_predictor
    model_cfg = "configs/sam2.1/sam2.1_hiera_b+.yaml"

    sam2_checkpoint = os.path.join(os.getcwd(),"..", "weights", "segment_anything_2", "sam2.1_hiera_base_plus.pt")

    predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
    inference_state = predictor.init_state(video_path=img_path, 
                                            offload_video_to_cpu = True,
                                            offload_state_to_cpu = True)

    obj_id_dict ={} #id별 클래스 기록 용도
    label_dict = {} #sam2 추적 결과 저장
    final_label = {} #최종 라벨 저장
    
    for frame_num, bbox_list in label.items():
        predictor.reset_state(inference_state)

        try:
            if bbox_list:
                for i , (cls, x1, y1, x2, y2, score) in enumerate(bbox_list):
                    find_equal_box = False
                    if len(label_dict)>0 and frame_num in label_dict.keys():
                        for box_list_2 in label_dict[frame_num]:
                            if cls == box_list_2[0] and calculate_iou(box_list_2[1:5], [x1, y1, x2, y2]) > 0.75:
                                find_equal_box = True
                                break

                    if find_equal_box: #만약 이전에 동일한 박스가 있으면 해당 박스는 SAM 추적 박스에서 억제
                        continue

                    t0 = time.time()
                    ann_frame_idx = frame_num  # the frame index we interact with
                    ann_obj_id = int(i)  # give a unique id to each object we interact with (it can be any integers)
                    obj_id_dict[ann_obj_id] = [cls, score]

                    box = np.array([int(x1), int(y1), int(x2), int(y2)])
                    _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(inference_state=inference_state,
                                                                                        frame_idx=ann_frame_idx,
                                                                                        obj_id=ann_obj_id,
                                                                                        box=box,
                                                                                    )
                video_segments = {}
                #정방향 
                for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
                    video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.).cpu().numpy()
                                                            for i, out_obj_id in enumerate(out_obj_ids)
                                                            }
                #역방향 
                for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, reverse=True):
                    video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.).cpu().numpy()
                                                    for i, out_obj_id in enumerate(out_obj_ids)
                                                    }

                for out_frame_idx in video_segments:
                    for out_obj_id, out_mask in video_segments[out_frame_idx].items():
                        bboxes = mask_to_bbox(out_mask)

                        if len(bboxes) > 0:
                            for box in bboxes:
                                x, y, w, h = box
                                if w * h >= 250: # 너무 작은 bbox는 제거
                                    min_x = min(box[0] for box in bboxes)
                                    min_y = min(box[1] for box in bboxes)
                                    max_x = max(box[0] + box[2] for box in bboxes)  # x + width
                                    max_y = max(box[1] + box[3] for box in bboxes)  # y + height

                                    bboxes = [[min_x, min_y, max_x - min_x, max_y - min_y]]

                        if out_frame_idx not in label_dict:
                            label_dict[out_frame_idx] = []
                        
                        if len(bboxes) > 0:
                            for x, y, w, h in bboxes:
                                if w * h >= 250: # 너무 작은 bbox는 제거
                                    label_dict[out_frame_idx].append([obj_id_dict[out_obj_id][0], x, y, x+w, y+h, obj_id_dict[out_obj_id][1]])
        except Exception as e:
            print(e)
            # label_dict[frame_num] = bbox_list
            pass

    for frame_num, box_list in label_dict.items():
        if len(box_list) > 0:
            final_label[frame_num] = nms(box_list, iou_threshold=0.3)
        else:
            final_label[frame_num] = label[frame_num]

    return final_label

def save_final_dataset(save_video_name : str, save_dir : str, tmp_img_path : str, img_buffer : list, label_buffer : dict):
    img_file_name = os.listdir(os.path.join(tmp_img_path))
    img_file_name = [int(file_name.split(".")[0]) for file_name in img_file_name]
    img_file_name.sort()

    os.makedirs(os.path.join(save_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(save_dir, "labels"), exist_ok=True)

    for i, img in enumerate(img_buffer):
        if i % 3 != 0:
            continue
        cv2.imwrite(os.path.join(save_dir, "images", f"{save_video_name}_{img_file_name[i]}.jpg"), img)

        if label_buffer:
            label_txt = ""
            width, heigth = img.shape[1], img.shape[0]
            for cls, x1, y1, x2, y2, score in label_buffer[i]:
                x1 = x1/width
                x2 = x2/width
                y1 = y1/heigth
                y2 = y2/heigth

                w = np.round(x2 - x1, 3)
                h = np.round(y2 - y1, 3)

                ncx = np.round(x1 + w / 2,3)
                ncy = np.round(y1 + h / 2,3)

                label_txt += f"{cls} {ncx} {ncy} {w} {h}\n"
            if label_txt:
                label_name = f"{save_dir}/labels/{save_video_name}_{img_file_name[i]}.txt"
                
                with open(label_name, "w") as f:
                    f.write(label_txt)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
weight_name = "ms-ai_24-12-31-M.pt"
# weight_name = "yolov8m.pt"
# weight_name = "yolov8m_standard.pt"


yolo_weight_path = os.path.join(os.getcwd(), "..", "weights", "yolo", weight_name)

# train_data_path = os.path.join(os.getcwd(), "dataset", "drop_trash", "train")
train_data_path = os.path.join("/root", "DB_1", "falldown_test", "train")

train_data_video_path = os.path.join(train_data_path, "videos")
train_data_video_name_list = os.listdir(train_data_video_path)
train_data_video_name = train_data_video_name_list[0]

for train_data_video_name in tqdm(train_data_video_name_list, desc=f"Processing videos {train_data_video_name}"):

    #비디오 10초씩 나누고 이미지화
    video_path = os.path.join(train_data_video_path, train_data_video_name)
    split_video_to_image(video_path, train_data_video_name[:-4])

    for segment_img_name in os.listdir(os.path.join(train_data_path, "tmp_images", train_data_video_name[:-4])):
        segment_img_path = os.path.join(train_data_path, "tmp_images", train_data_video_name[:-4], segment_img_name)

        img_buffer = get_img_buffer(video_path = segment_img_path)

        yolo_label_data = get_yolo_label(yolo_weight_path, buffer = img_buffer, init_model = False)

        zeroshot_label_data = get_zero_shot_label(buffer = img_buffer, device = device)
        # YOLO와 Zero-shot 라벨 데이터 통합
        merged_label_data = merge_label_data(yolo_label_data, zeroshot_label_data, iou_threshold=0.5)
        
        LLM_label_data = run_LLM(img_buffer = img_buffer, label = merged_label_data)
        sam_label = run_sam(img_buffer = img_buffer, label = LLM_label_data, img_path = segment_img_path)

        save_final_dataset(save_video_name=train_data_video_name[:-4],
                           save_dir = os.path.join(train_data_path),
                           tmp_img_path = segment_img_path,
                           img_buffer = img_buffer, 
                           label_buffer = sam_label,
                            )


    shutil.rmtree(os.path.join(train_data_path, "tmp_images", train_data_video_name[:-4]))
    # 비디오 파일을 원본 폴더로 이동
    os.makedirs(os.path.join(train_data_path, "videos_ori"), exist_ok=True)
    print(video_path, os.path.join(train_data_path, "videos_ori", train_data_video_name))
    shutil.move(video_path, os.path.join(train_data_path, "videos_ori", train_data_video_name))

        # 박스 plot하는 함수
        # for frame_num, boxes in sam_label.items():
        #     img = img_buffer[frame_num].copy()
        #     for box in boxes:
        #         cls, x1, y1, x2, y2, score = box
        #         cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
        #         cv2.putText(img, f"{cls}:{score:.2f}", (int(x1), int(y1)-10), 
        #                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
            
        #     save_dir = os.path.join(os.getcwd(), "test", train_data_video_name[:-4], segment_video_name)
        #     os.makedirs(save_dir, exist_ok=True)
        #     cv2.imwrite(os.path.join(save_dir, f"{frame_num}_after.jpg"), img)

        # for frame_num, boxes in merged_label_data.items():
        #     img = img_buffer[frame_num].copy()
        #     for box in boxes:
        #         cls, x1, y1, x2, y2, score = box
        #         cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
        #         cv2.putText(img, f"{cls}:{score:.2f}", (int(x1), int(y1)-10), 
        #                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
            
        #     save_dir = os.path.join(os.getcwd(), "test", train_data_video_name[:-4], segment_video_name)
        #     os.makedirs(save_dir, exist_ok=True)
        #     cv2.imwrite(os.path.join(save_dir, f"{frame_num}_before.jpg"), img)