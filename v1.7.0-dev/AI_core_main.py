import shutil
import subprocess
from fastapi import FastAPI, HTTPException
from io import BytesIO
from PIL import Image
import json
import os
from pathlib import Path   
import uvicorn
import asyncio
from typing import List, Dict, Any

import requests
from requests.auth import HTTPBasicAuth

from transformers import AutoProcessor

from qwen_vl_utils import process_vision_info
# vLLM lazy import (메모리 초기화 지연)
LLM = None
SamplingParams = None

import torch
import base64
import numpy as np
import cv2
from pydantic import BaseModel
import gc
import psutil

from back.ms_labeler_utils import build_transform, dynamic_preprocess
from datetime import datetime
import traceback
from logging_config import setup_logging
from contextlib import redirect_stdout, redirect_stderr
import time

os.environ['VLLM_WORKER_MULTIPROC_METHOD'] = 'spawn'
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"  # 에러 발생 지점 정확히 추적
os.environ['TORCH_USE_CUDA_DSA'] = "1"     # device-side assertions 활성화
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'  # 메모리 단편화 방지

# 로깅 설정
logger = setup_logging(logger_name="AI_SERVER", log_file="AI_SERVER.log")

app = FastAPI()

class MsgData(BaseModel):
    question : list
    video_path : str
    data_type : str

class TrashDetectionData(BaseModel):
    camera_name: str
    detect_area: List[List[float]]
    current_img: str  # base64 encoded
    enroll_img: str   # base64 encoded
    enroll_time: float
    enroll_bbox: List[float]
    person_bbox_list: List[List[float]]
    non_person_bbox_list: List[List[float]]
    person_id: int
    fgmask: str  # base64 encoded
    fgmask_enroll: str  # base64 encoded

class TrashTrackingData(BaseModel):
    camera_name: str
    camera_num: int
    detect_time: str
    nvr_info: dict

class SiglipDetectionData(BaseModel):
    camera_name: str
    person_id: int
    image: str  # base64 encoded
    texts: List[str]
    detect_type: str  # "falldown" or "fight"



def check_gpu_memory():
    """GPU 메모리 상태 체크"""
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        gpu_allocated = torch.cuda.memory_allocated(0) / 1024**3
        gpu_cached = torch.cuda.memory_reserved(0) / 1024**3
        # logger.info(f"GPU Total: {gpu_memory:.2f}GB, Allocated: {gpu_allocated:.2f}GB, Cached: {gpu_cached:.2f}GB")
        return gpu_memory, gpu_allocated, gpu_cached
    return 0, 0, 0

def cleanup_memory():
    """메모리 정리 함수"""
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        # logger.info("Memory cleanup completed")
    except Exception as e:
        logger.warning(f"Memory cleanup failed: {e}")

VLM_images_dir = os.path.join(os.getcwd(),"..", "backup", "VLM")
os.makedirs(VLM_images_dir, exist_ok=True)

logger.info("Starting model loading...")
check_gpu_memory()

vlm_model = None
vlm_processor = None

def load_vlm_model():
    global vlm_model, vlm_processor
    # model_path = os.getcwd() + "/../weights/Qwen3-VL-4B-Instruct"
    # vlm_model = Qwen3VLForConditionalGeneration.from_pretrained(model_path, dtype=torch.bfloat16, attn_implementation="flash_attention_2", device_map="auto")
    # vlm_processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True, use_fast=True)

    try:
        from vllm import LLM

        # GPU VRAM 용량 확인 후 체크포인트 선택
        if torch.cuda.is_available():
            gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
            gpu_memory_gb = gpu_memory_bytes / (1024 ** 3)  # bytes to GB
            logger.info(f"GPU VRAM: {gpu_memory_gb:.2f} GB")
            
            if gpu_memory_gb <= 20:
                checkpoint_path = os.getcwd() + f"/../weights/Qwen3-VL-4B-Thinking-FP8"
                logger.info("Using Qwen3-VL-4B-Thinking-FP8 (VRAM <= 20GB)")
                gpu_memory_utilization = 0.8
            else:
                checkpoint_path = os.getcwd() + f"/../weights/Qwen3-VL-8B-Instruct-FP8"
                logger.info("Using Qwen3-VL-8B-Instruct-FP8 (VRAM > 20GB)")
                gpu_memory_utilization = 0.9

        
        # GPU 메모리 정리 후 로드
        cleanup_memory()
        
        gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
        logger.info(f"Loading VLM model with {gpu_count} GPU(s)")

        vlm_model = LLM(
            model=checkpoint_path,
            trust_remote_code=True,
            gpu_memory_utilization=gpu_memory_utilization,  # 90% -> 80%로 감소
            max_model_len=8192,  # 16384 -> 8192로 감소
            # max_model_len=2048,  # 16384 -> 8192로 감소
            enforce_eager=True,  # 메모리 효율성 향상
            tensor_parallel_size=gpu_count,
            seed=0
        )
        vlm_processor = AutoProcessor.from_pretrained(checkpoint_path)
        logger.info("VLM model loaded successfully")
    except Exception as e:
        logger.error(f"VLM model load failed: {e}")
        vlm_model = None
        vlm_processor = None
        raise

def unload_vlm_model():
    global vlm_model, vlm_processor

    del vlm_model, vlm_processor

    vlm_model = None
    vlm_processor = None

    # 1. nvidia-smi로 VLLM::EngineCore 프로세스 PID 찾아서 강제 종료
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader'],
            capture_output=True, text=True
        )
        logger.info(f"nvidia-smi output: {result.stdout.strip()}")
        for line in result.stdout.strip().split('\n'):
            if 'VLLM::EngineCore' in line or 'vllm' in line.lower():
                # 형식: "2902711, VLLM::EngineCore" 또는 "2902711, /path/to/vllm"
                parts = line.split(',')
                if len(parts) >= 1:
                    pid_str = parts[0].strip()
                    if pid_str.isdigit():
                        pid = int(pid_str)
                        logger.info(f"Found VLLM::EngineCore process with PID: {pid}, killing...")
                        os.system(f'kill -9 {pid}')
                        logger.info(f"VLLM::EngineCore process (PID: {pid}) killed successfully")
    except Exception as e:
        logger.warning(f"Failed to kill VLLM::EngineCore process: {e}")

    # 2. 파이썬 가비지 컬렉션으로 남은 객체 정리
    gc.collect()
    
    # 3. CUDA 캐시 비우기 (실제 VRAM 반환)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect() # 멀티 프로세스 공유 메모리 정리

    logger.info("VLM model unloaded and VRAM cleared completely")

def prepare_inputs_for_vllm(messages, processor):
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    # qwen_vl_utils 0.0.14+ reqired
    image_inputs, video_inputs, video_kwargs = process_vision_info(
        messages,
        image_patch_size=processor.image_processor.patch_size,
        return_video_kwargs=True,
        return_video_metadata=True
    )
    mm_data = {}
    if image_inputs is not None:
        mm_data['image'] = image_inputs
    if video_inputs is not None:
        mm_data['video'] = video_inputs

    return {
        'prompt': text,
        'multi_modal_data': mm_data,
        'mm_processor_kwargs': video_kwargs
    }

def load_sam_model():
    # SAM2 모델 로드
    logger.info("Starting SAM2 model loading...")
    sam_model = None
    try:
        import sys
        sys.path.insert(0, str(os.getcwd()) + "/../")
        from sam2.build_sam import build_sam2
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

        sam_checkpoint = str(os.getcwd()) + "/../weights/segment_anything_2/sam2.1_hiera_base_plus.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_b+.yaml"

        sam2 = build_sam2(model_cfg, sam_checkpoint, device='cuda', apply_postprocessing=False)

        sam_model = SAM2AutomaticMaskGenerator(
            model=sam2,
            points_per_side=16,
            points_per_batch=64,
            pred_iou_thresh=0.3,
            stability_score_thresh=0.88,
            stability_score_offset=0.7,
            crop_n_layers=1,
            box_nms_thresh=0.7,
            crop_n_points_downscale_factor=2,
            min_mask_region_area=25.0,
        )
        logger.info("SAM2 모델 로드 완료")
    except Exception as e:
        logger.error(f"SAM2 모델 로드 실패: {e}")
        sam_model = None

def validate_input_data(data: MsgData):
    """입력 데이터 검증"""
    if not data.question:
        raise ValueError("Question list is empty")
    
    # 각 메시지 검증
    for msg in data.question:
        if not isinstance(msg, dict):
            raise ValueError("Each question item must be a dictionary")
        if 'role' not in msg or 'content' not in msg:
            raise ValueError("Each message must have 'role' and 'content' fields")
    
    return True

def remove_video_file(video_path):
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"비디오 파일 삭제 완료: {video_path}")
    except Exception as e:
        logger.warning(f"비디오 파일 삭제 실패: {video_path}, 에러: {e}")

def move_video_file(video_path, move_path, response):
    try:
        move_path = os.path.join(move_path, os.path.basename(video_path).split(".")[0])
        os.makedirs(move_path, exist_ok=True)
        if os.path.exists(video_path):
            shutil.move(video_path, move_path)
            with open(os.path.join(move_path, "response.txt"), "w") as f:
                f.write(response[0])
            logger.info(f"비디오 파일 이동 완료: {video_path}")
    except Exception as e:
        logger.warning(f"비디오 파일 이동 실패: {video_path}, 에러: {e}")

# ==================== 쓰레기 검출 관련 헬퍼 함수 ====================
def visualize_sam_and_intersection(frame, masks, binary_diff, offset=(0, 0)):
    """SAM 마스크와 변화 감지 영역의 교집합을 시각화하는 함수"""
    try:
        if len(masks) == 0:
            return None, None
        
        oy, ox = offset
        h, w = frame.shape[:2]
        
        # SAM 시각화
        sam_visualization = frame.copy()
        intersection_color = np.zeros_like(frame)
        
        # 각 마스크를 다른 색상으로 표시
        for i, ann in enumerate(masks):
            sam_mask = ann['segmentation']
            color = np.random.randint(0, 255, size=3, dtype=np.uint8)
            
            # SAM 마스크를 원본 프레임 크기로 확장
            full_sam_mask = np.zeros((h, w), dtype=np.uint8)
            mask_h, mask_w = sam_mask.shape
            full_sam_mask[oy:oy+mask_h, ox:ox+mask_w] = (sam_mask * 255).astype(np.uint8)
            
            # SAM 마스크 시각화 (블렌딩)
            mask_bool = full_sam_mask > 0
            for c in range(3):
                sam_visualization[mask_bool, c] = (
                    sam_visualization[mask_bool, c] * 0.5 + color[c] * 0.5
                ).astype(np.uint8)
            
            # 변화 감지 영역과 교집합 계산
            intersection = cv2.bitwise_and(binary_diff, full_sam_mask)
            intersection_bool = intersection > 0
            intersection_color[intersection_bool] = color
        
        return sam_visualization, intersection_color
    
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"SAM 시각화 에러 발생 : {current_time}: {e}\n{tb}")
        return None, None

def _create_trash_detection_visualization(enroll_img, current_img, binary_diff, 
                                         sam_visualization, person_bbox_list, 
                                         non_person_bbox_list, enroll_bbox, enroll_time,
                                         fgmask=None, fgmask_enroll=None):
    """쓰레기 검출 과정을 시각화하는 8개 이미지 그리드를 생성"""
    try:
        if sam_visualization is None:
            return None, 0, 0, 0, 0
        
        # 1. 등록 이미지
        img1 = enroll_img.copy()
        
        # 2. 현재 프레임
        img2 = current_img.copy()
        
        # 3. binary_diff 시각화 전 (객체/그림자 제거 전)
        if time.time() - enroll_time > 60:
            current_frame_gaussian = cv2.GaussianBlur(current_img, (5, 5), 0)
            trash_check_gaussian = cv2.GaussianBlur(enroll_img, (5, 5), 0)
        else:
            current_frame_gaussian = current_img
            trash_check_gaussian = enroll_img
        
        frame_diff_raw = cv2.absdiff(trash_check_gaussian, current_frame_gaussian)
        diff_gray_raw = cv2.cvtColor(frame_diff_raw, cv2.COLOR_BGR2GRAY)
        _, binary_diff_raw = cv2.threshold(diff_gray_raw, 50, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        binary_diff_raw = cv2.morphologyEx(binary_diff_raw, cv2.MORPH_CLOSE, kernel)
        binary_diff_raw = cv2.morphologyEx(binary_diff_raw, cv2.MORPH_OPEN, kernel)
        img3 = cv2.cvtColor(binary_diff_raw, cv2.COLOR_GRAY2BGR)
        
        # 4. 객체/그림자 마스크 시각화
        person_mask = _create_exclude_mask(current_img.shape, person_bbox_list, enroll_bbox, binary_diff_raw)
        non_person_mask = _create_exclude_mask(current_img.shape, non_person_bbox_list, enroll_bbox, binary_diff_raw)
        combined_mask = cv2.bitwise_or(person_mask, non_person_mask)
        img4 = cv2.cvtColor(combined_mask, cv2.COLOR_GRAY2BGR)
        
        # 5. binary_diff 시각화 후 (객체/그림자 제거 후)
        img5 = cv2.cvtColor(binary_diff, cv2.COLOR_GRAY2BGR) if len(binary_diff.shape) == 2 else binary_diff
        
        # 6. SAM 시각화
        img6 = sam_visualization
        
        # 7. FGMask (현재 프레임)
        if fgmask is not None:
            # grayscale로 변환 (BGR인 경우)
            if len(fgmask.shape) == 3:
                fgmask_gray = cv2.cvtColor(fgmask, cv2.COLOR_BGR2GRAY)
            else:
                fgmask_gray = fgmask
            img7 = cv2.cvtColor(fgmask_gray, cv2.COLOR_GRAY2BGR)
        else:
            img7 = np.zeros_like(img1)
            cv2.putText(img7, "No FGMask", (10, img7.shape[0]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        
        # 8. FGMask Enroll (등록 프레임)
        if fgmask_enroll is not None:
            # grayscale로 변환 (BGR인 경우)
            if len(fgmask_enroll.shape) == 3:
                fgmask_enroll_gray = cv2.cvtColor(fgmask_enroll, cv2.COLOR_BGR2GRAY)
            else:
                fgmask_enroll_gray = fgmask_enroll
            img8 = cv2.cvtColor(fgmask_enroll_gray, cv2.COLOR_GRAY2BGR)
        else:
            img8 = np.zeros_like(img1)
            cv2.putText(img8, "No FGMask Enroll", (10, img8.shape[0]//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
        
        # 크기 통일
        h_viz, w_viz = img1.shape[:2]
        img2 = cv2.resize(img2, (w_viz, h_viz))
        img3 = cv2.resize(img3, (w_viz, h_viz))
        img4 = cv2.resize(img4, (w_viz, h_viz))
        img5 = cv2.resize(img5, (w_viz, h_viz))
        img6 = cv2.resize(img6, (w_viz, h_viz))
        img7 = cv2.resize(img7, (w_viz, h_viz))
        img8 = cv2.resize(img8, (w_viz, h_viz))
        
        # 텍스트 추가
        cv2.putText(img1, "1. Enroll Image", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img2, "2. Current Frame", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img3, "3. Diff (Before Mask)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img4, "4. Exclude Mask (w/ Shadow)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img5, "5. Diff (After Mask)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img6, "6. SAM Visualization", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img7, "7. FGMask (Current)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img8, "8. FGMask (Enroll)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 2x4 그리드로 배치
        row1 = cv2.hconcat([img1, img2, img3, img4])
        row2 = cv2.hconcat([img5, img6, img7, img8])
        concat_before_resize = cv2.vconcat([row1, row2])
        
        # 원본 concat 크기 저장
        concat_h, concat_w = concat_before_resize.shape[:2]
        
        # 최종 크기로 리사이즈
        concat = cv2.resize(concat_before_resize, (1920, 1080))
        
        return concat, h_viz, w_viz, concat_h, concat_w
    
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"시각화 생성 에러 발생 : {current_time}: {e}\n{tb}")
        return None, 0, 0, 0, 0

def _draw_trash_bbox_on_visualization(concat, trash_bbox, current_img_shape, 
                                     h_viz, w_viz, concat_h, concat_w):
    """검출된 쓰레기 bbox를 시각화 이미지에 그리기"""
    try:
        if concat is None or h_viz <= 0 or w_viz <= 0:
            return
        
        trash_x1, trash_y1, trash_x2, trash_y2 = trash_bbox
        
        # 원본 프레임에서 리사이즈된 이미지로 좌표 변환
        frame_h, frame_w = current_img_shape[:2]
        scale_x = w_viz / frame_w
        scale_y = h_viz / frame_h
        
        # bbox를 리사이즈된 이미지 좌표로 변환
        bbox_x1_resized = int(trash_x1 * scale_x)
        bbox_y1_resized = int(trash_y1 * scale_y)
        bbox_x2_resized = int(trash_x2 * scale_x)
        bbox_y2_resized = int(trash_y2 * scale_y)
        
        # concat 이미지에서 두 번째 이미지의 시작 위치 (img2는 첫 번째 행의 두 번째)
        img2_offset_x = w_viz  # img1의 너비만큼 오른쪽
        img2_offset_y = 0  # 첫 번째 행
        
        # concat 전 좌표에 offset 추가
        concat_x1 = bbox_x1_resized + img2_offset_x
        concat_y1 = bbox_y1_resized + img2_offset_y
        concat_x2 = bbox_x2_resized + img2_offset_x
        concat_y2 = bbox_y2_resized + img2_offset_y
        
        # concat을 (1920, 1080)으로 리사이즈했으므로 최종 스케일 적용
        final_scale_x = 1920 / concat_w
        final_scale_y = 1080 / concat_h
        
        final_x1 = int(concat_x1 * final_scale_x)
        final_y1 = int(concat_y1 * final_scale_y)
        final_x2 = int(concat_x2 * final_scale_x)
        final_y2 = int(concat_y2 * final_scale_y)
        
        # bbox 그리기 (빨간색)
        cv2.rectangle(concat, (final_x1, final_y1), (final_x2, final_y2), (0, 0, 255), 3)
        cv2.putText(concat, "TRASH DETECTED", (final_x1, final_y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        logger.info(f"쓰레기 bbox 시각화 - 원본: ({trash_x1},{trash_y1},{trash_x2},{trash_y2}) -> "
                   f"concat: ({final_x1},{final_y1},{final_x2},{final_y2})")
        
    except Exception as e:
        logger.error(f"bbox 시각화 에러: {e}")

def _save_visualization_image(concat, camera_name, person_id, trash_objects):
    """시각화 이미지를 파일로 저장"""
    try:
        if concat is None:
            return
        
        debug_dir = os.path.join(os.getcwd(), "..", "backup", "trash_detection_debug")
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{f'[TRASH] {trash_objects[0]["overlap_ratio1"]} {trash_objects[0]["overlap_ratio2"]}' if len(trash_objects) else '[NO_TRASH]'}_{camera_name}_P{person_id}_{timestamp}.jpg"
        filepath = os.path.join(debug_dir, filename)
        cv2.imwrite(filepath, concat)
        # logger.info(f"쓰레기 검출 시각화 이미지 저장: {filepath}")
        
    except Exception as e:
        logger.error(f"시각화 이미지 저장 실패: {e}")

def _create_exclude_mask(frame_shape, people_bbox, init_bbox, binary_diff):
    """객체들의 bbox와 연결된 모든 영역(그림자 포함)을 기반으로 마스크 생성"""
    height, width = frame_shape[:2]
    person_mask = np.zeros((height, width), dtype=np.uint8)

    # 모든 bbox 수집
    all_bboxes = []
    if init_bbox and len(init_bbox) == 4:
        all_bboxes.append(init_bbox)
    all_bboxes.extend([bbox[:4] for bbox in people_bbox])
    
    # binary_diff에서 연결된 컴포넌트 찾기
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_diff, connectivity=8)
    
    # 각 bbox에 대해 처리
    for bbox in all_bboxes:
        x1, y1, x2, y2 = bbox
        x1_expanded = max(0, int(x1) - 20)
        y1_expanded = max(0, int(y1) - 20)
        x2_expanded = min(width, int(x2) + 20)
        y2_expanded = min(height, int(y2) + 20)
        
        # bbox 영역 기본 마스킹
        cv2.rectangle(person_mask, (x1_expanded, y1_expanded), (x2_expanded, y2_expanded), 255, -1)
        
        # bbox 영역 내에서 활성화된 픽셀과 연결된 모든 컴포넌트 찾기
        bbox_region = labels[y1_expanded:y2_expanded, x1_expanded:x2_expanded]
        unique_labels = np.unique(bbox_region)
        
        # bbox와 연결된 컴포넌트들을 마스크에 추가 (그림자 포함)
        for label in unique_labels:
            if label == 0:  # 배경 제외
                continue
            # 해당 컴포넌트 전체를 마스크에 추가
            person_mask[labels == label] = 255
    
    return person_mask

def _detect_changes_excluding_people(current_frame, people_bbox, non_people_bbox, enroll_time, enroll_img, enroll_bbox, fgmask=None, fgmask_enroll=None):
    """사람 영역을 제외한 변화 감지 수행"""
    # 이미지의 등록 시간과 현재 시간을 비교 후 오래된 경우 노이즈 제거를 위해 가우시안 필터 적용 
    if time.time() - enroll_time > 60:
        current_frame_gaussian = cv2.GaussianBlur(current_frame, (5, 5), 0)
        trash_check_gaussian = cv2.GaussianBlur(enroll_img, (5, 5), 0)
    else:
        current_frame_gaussian = current_frame
        trash_check_gaussian = enroll_img

    # 차이 계산 (절대값 차이)
    frame_diff = cv2.absdiff(trash_check_gaussian, current_frame_gaussian)
    
    # 그레이스케일로 변환
    diff_gray = cv2.cvtColor(frame_diff, cv2.COLOR_BGR2GRAY)

    # 임계값 적용 (작은 변화는 무시)
    _, binary_diff = cv2.threshold(diff_gray, 50, 255, cv2.THRESH_BINARY)

    # 모폴로지 연산으로 노이즈 제거
    kernel = np.ones((5, 5), np.uint8)
    binary_diff = cv2.morphologyEx(binary_diff, cv2.MORPH_CLOSE, kernel)
    binary_diff = cv2.morphologyEx(binary_diff, cv2.MORPH_OPEN, kernel)

    # 객체 영역 마스크 생성 (그림자 포함)
    person_mask = _create_exclude_mask(current_frame.shape, people_bbox, enroll_bbox, binary_diff)
    non_person_mask = _create_exclude_mask(current_frame.shape, non_people_bbox, enroll_bbox, binary_diff)

    # 객체 및 그림자 영역을 차이 이미지에서 제외
    binary_diff[person_mask > 0] = 0
    binary_diff[non_person_mask > 0] = 0
    
    # fgmask 영역도 제외 (fgmask가 제공된 경우)
    if fgmask is not None:
        # fgmask를 grayscale로 변환 (BGR인 경우)
        if len(fgmask.shape) == 3:
            fgmask_gray = cv2.cvtColor(fgmask, cv2.COLOR_BGR2GRAY)
        else:
            fgmask_gray = fgmask.copy()
        fgmask_gray[fgmask_gray > 0] = 255
        
        # fgmask 영역을 binary_diff에서 제거
        binary_diff[fgmask_gray > 0] = 0

    if fgmask_enroll is not None:
        # fgmask_enroll를 grayscale로 변환 (BGR인 경우)
        if len(fgmask_enroll.shape) == 3:
            fgmask_enroll_gray = cv2.cvtColor(fgmask_enroll, cv2.COLOR_BGR2GRAY)
        else:
            fgmask_enroll_gray = fgmask_enroll.copy()

        # fgmask_enroll 영역을 binary_diff에서 제거
        fgmask_enroll_gray[fgmask_enroll_gray > 0] = 255
        
        binary_diff[fgmask_enroll_gray > 0] = 0
        
    return binary_diff

def _detect_trash_objects(sam_masks, change_mask, roi_polygon, offset=(0, 0), threshold_ratio=0.7):
    """SAM 마스크와 변화 감지 영역을 비교하여 쓰레기 객체를 감지하는 함수"""
    trash_objects = []
    
    if len(sam_masks) == 0 or np.sum(change_mask) == 0:
        return False, []

    oy, ox = offset

    # 변화 영역에서 연결된 구성 요소들을 찾기
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(change_mask, connectivity=8)

    # 배경 (label 0)을 제외한 실제 객체들만 처리
    for label in range(1, num_labels):
        component_mask = (labels == label).astype(np.uint8) * 255
        
        # 각 구성 요소의 bounding box 정보
        x1, y1, w, h, area = stats[label]
        component_bbox = [x1, y1, x1 + w, y1 + h]
        
        # 구성 요소와 ROI 폴리곤 내부 겹침 확인
        center_x = (x1 + x1 + w) / 2
        center_y = (y1 + y1 + h) / 2
        
        # 폴리곤 내부에 중심점이 있는지 확인
        if cv2.pointPolygonTest(roi_polygon, (center_x, center_y), False) < 0:
            continue  # ROI 외부 객체는 무시

        for i, ann in enumerate(sam_masks):
            sam_mask = ann['segmentation']
            sam_mask_uint8 = (sam_mask * 255).astype(np.uint8)
            
            sam_x1, sam_y1, sam_w, sam_h = ann['bbox']
            
            # SAM 마스크를 원본 프레임 크기로 확장 (offset 적용)
            full_sam_mask = np.zeros_like(change_mask, dtype=np.uint8)
            mask_h, mask_w = sam_mask.shape
            full_sam_mask[oy:oy+mask_h, ox:ox+mask_w] = sam_mask_uint8
            
            # 현재 구성 요소와 SAM 마스크의 교집합 계산
            intersection = cv2.bitwise_and(component_mask, full_sam_mask)
            intersection_pixels = np.sum(intersection > 0)
            
            # 구성 요소 픽셀 수와 SAM 마스크 픽셀 수
            component_pixels = np.sum(component_mask > 0)
            sam_pixels = np.sum(full_sam_mask > 0)
            
            # 겹침 비율 계산
            overlap_ratio1 = intersection_pixels / component_pixels if component_pixels > 0 else 0
            overlap_ratio2 = intersection_pixels / sam_pixels if sam_pixels > 0 else 0
            
            # 쓰레기 객체 판단 조건
            is_trash = (overlap_ratio1 + overlap_ratio2) > threshold_ratio * 2
            
            if is_trash:
                trash_objects.append({
                    'mask_idx': i,
                    'component_label': label,
                    'intersection_pixels': intersection_pixels,
                    'overlap_ratio1': overlap_ratio1,
                    'overlap_ratio2': overlap_ratio2,
                    'component_bbox': component_bbox,
                    'sam_bbox': [sam_x1 + ox, sam_y1 + oy, sam_x1 + sam_w + ox, sam_y1 + sam_h + oy]
                })
                
    return len(trash_objects) > 0, trash_objects


@app.post("/unload-vlm-model")
async def unload_vlm_model_endpoint(data : MsgData):
    """자가학습 종료 API 함수 """
    global vlm_model, vlm_processor
    unload_vlm_model()
    return {"status": True}

@app.post("/vlm-QnA")
async def vlm_answer_img(data : MsgData):
    """LLM QnA API 함수 """
    global vlm_model, vlm_processor

    if vlm_model is None or vlm_processor is None:
        try:
            load_vlm_model()
        except Exception as e:
            logger.error(f"Model loading failed in endpoint: {e}")
            return {"answer": [], "status": False, "error": f"Model loading failed: {str(e)}"}
    
    if vlm_model is None or vlm_processor is None:
        return {"answer": [], "status": False, "error": "VLM model not available"}

    try:
        t0 = time.time()
        from vllm import SamplingParams

        sampling_params = SamplingParams(
            temperature=0,
            max_tokens=1024,
            top_k=-1,
            stop_token_ids=[],
        )
        inputs = [prepare_inputs_for_vllm(message, vlm_processor) for message in [data.question]]

        outputs = vlm_model.generate(inputs, sampling_params)
        response = outputs[0].outputs[0].text

        # logger.info("Processing VLM request")
        # check_gpu_memory()
        
        # # 입력 데이터 검증
        # validate_input_data(data)
        
        # # 텍스트 템플릿 적용
        # text = vlm_processor.apply_chat_template(
        #         data.question,
        #         tokenize=False,
        #         add_generation_prompt=True
        #     )
        # # logger.info(f"Generated text template: {text[:100]}...")
        
        # # 비전 정보 처리
        # images, videos, video_kwargs = process_vision_info(data.question, image_patch_size=16, return_video_kwargs=True, return_video_metadata=True)

        # if videos is not None:
        #     videos, video_metadatas = zip(*videos)
        #     videos, video_metadatas = list(videos), list(video_metadatas)
        # else:
        #     video_metadatas = None

        # # logger.info(f"Vision inputs processed - Images: {len(image_inputs) if image_inputs else 0}, Videos: {len(video_inputs) if video_inputs else 0}")
        
        # # 프로세서로 입력 준비
        # inputs = vlm_processor(text=text, images=images, videos=videos, video_metadata=video_metadatas, return_tensors="pt", do_resize=False, **video_kwargs)
        # inputs = inputs.to(vlm_model.device)
        
        # # GPU 메모리 체크 후 안전하게 GPU로 이동
        # check_gpu_memory()
        
        # # 입력을 단계별로 GPU로 이동
        # try:
        #     if torch.cuda.is_available():
        #         # 각 텐서를 개별적으로 GPU로 이동
        #         gpu_inputs = {}
        #         for key, value in inputs.items():
        #             if torch.is_tensor(value):
        #                 gpu_inputs[key] = value.to("cuda", non_blocking=True)
        #             else:
        #                 gpu_inputs[key] = value
        #         inputs = gpu_inputs
        #         torch.cuda.synchronize()  # GPU 작업 동기화
        #         # logger.info("Inputs moved to GPU successfully")
        #     else:
        #         logger.warning("CUDA not available, using CPU")
                
        # except RuntimeError as cuda_error:
        #     logger.error(f"CUDA error when moving inputs to GPU: {cuda_error}")
        #     cleanup_memory()
        #     raise HTTPException(status_code=500, detail=f"GPU memory error: {str(cuda_error)}")

        # check_gpu_memory()

        # # 모델 추론
        # logger.info("Starting model generation")
        # with torch.no_grad():  # 그래디언트 계산 비활성화로 메모리 절약
        #     try:
        #         generated_ids = vlm_model.generate(
        #             **inputs, 
        #             # max_new_tokens=512,  # 토큰 수 제한으로 메모리 사용량 조절
        #             max_new_tokens=512,  # 토큰 수 제한으로 메모리 사용량 조절
        #             do_sample=False,     # 결정적 생성
        #             pad_token_id=vlm_processor.tokenizer.eos_token_id
        #         )
        #     except RuntimeError as gen_error:
        #         logger.error(f"Generation error: {gen_error}")
        #         cleanup_memory()
        #         raise HTTPException(status_code=500, detail=f"Generation failed: {str(gen_error)}")

        # # 생성된 토큰 처리
        # generated_ids_trimmed = [
        #     out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs['input_ids'], generated_ids)
        # ]
        
        # response = vlm_processor.batch_decode(
        #     generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        # )

        logger.info(f"Generation completed successfully : {time.time() - t0:.2f}s")

        if data.data_type == "video":
            # remove_video_file(data.video_path)
            move_video_file(data.video_path, os.path.join(os.getcwd(), "..", "backup", "VLM", "done"), response)


        # 메모리 정리
        # del generated_ids, generated_ids_trimmed, inputs, video_kwargs, text, video_metadatas, images, videos
        del inputs, outputs
        cleanup_memory()
        
        return {"answer": response, "status": True}

    except ValueError as ve:
        logger.error(f"Input validation error: {ve}")
        remove_video_file(data.video_path)

        return {"answer": [], "status": False, "error": str(ve)}
        
    except HTTPException:
        raise  # HTTPException은 그대로 전파
        
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"Unexpected error occurred at {current_time}: {e}\n{tb}")
        remove_video_file(data.video_path)
        
        # 메모리 정리
        cleanup_memory()
        
        return {"answer": [], "status": False, "error": f"Internal server error: {str(e)}"}

@app.post("/detect_trash")
async def detect_trash_endpoint(data: TrashDetectionData):
    """쓰레기 검출 API 엔드포인트"""
    global sam_model
    
    try:
        t0 = time.time()
        logger.info(f"쓰레기 검출 요청 - 카메라: {data.camera_name}, Person ID: {data.person_id}")
        
        if sam_model is None:
            logger.error("SAM 모델이 로드되지 않음")
            return {"status": False, "alarms": [], "error": "SAM model not loaded"}
        
        # Base64 이미지 디코드
        current_img_bytes = base64.b64decode(data.current_img)
        current_img_array = np.frombuffer(current_img_bytes, dtype=np.uint8)
        current_img = cv2.imdecode(current_img_array, cv2.IMREAD_COLOR)
        
        enroll_img_bytes = base64.b64decode(data.enroll_img)
        enroll_img_array = np.frombuffer(enroll_img_bytes, dtype=np.uint8)
        enroll_img = cv2.imdecode(enroll_img_array, cv2.IMREAD_COLOR)
        
        fgmask_bytes = base64.b64decode(data.fgmask)
        fgmask_array = np.frombuffer(fgmask_bytes, dtype=np.uint8)
        fgmask = cv2.imdecode(fgmask_array, cv2.IMREAD_COLOR)

        fgmask_enroll_bytes = base64.b64decode(data.fgmask_enroll)
        fgmask_enroll_array = np.frombuffer(fgmask_enroll_bytes, dtype=np.uint8)
        fgmask_enroll = cv2.imdecode(fgmask_enroll_array, cv2.IMREAD_COLOR)
        
        # ROI polygon 변환
        roi_polygon = np.array(data.detect_area, dtype=np.int32)
        
        # 변화 감지
        binary_diff = _detect_changes_excluding_people(
            current_frame=current_img,
            people_bbox=data.person_bbox_list,
            non_people_bbox=data.non_person_bbox_list,
            enroll_time=data.enroll_time,
            enroll_img=enroll_img,
            enroll_bbox=data.enroll_bbox,
            fgmask=fgmask,
            fgmask_enroll=fgmask_enroll
        )
        
        # ROI 영역 crop
        if len(data.detect_area) >= 4:
            x, y, w, h = cv2.boundingRect(roi_polygon)
            
            # 프레임 경계 체크
            x = max(0, x)
            y = max(0, y)
            w = min(w, current_img.shape[1] - x)
            h = min(h, current_img.shape[0] - y)
            
            # ROI crop
            roi_crop = current_img[y:y+h, x:x+w].copy()
            
            # SAM2 마스크 생성
            # logger.info(f"SAM2 마스크 생성 시작 - ROI 크기: ({w}, {h})")
            masks = sam_model.generate(roi_crop)
            # logger.info(f"SAM2 마스크 생성 완료 - 마스크 수: {len(masks)}")
            
            # SAM 시각화 생성 (디버그용)
            sam_visualization, intersection_color = visualize_sam_and_intersection(
                frame=current_img.copy(),
                masks=masks,
                binary_diff=binary_diff,
                offset=(y, x)
            )
            
            # 쓰레기 객체 감지
            is_trash, trash_objects = _detect_trash_objects(
                sam_masks=masks,
                change_mask=binary_diff,
                roi_polygon=roi_polygon,
                offset=(y, x),
                threshold_ratio=0.8
            )
            
            # 8개 이미지 그리드 생성 (디버그용 시각화)
            concat, h_viz, w_viz, concat_h, concat_w = _create_trash_detection_visualization(
                enroll_img=enroll_img,
                current_img=current_img,
                binary_diff=binary_diff,
                sam_visualization=sam_visualization,
                person_bbox_list=data.person_bbox_list,
                non_person_bbox_list=data.non_person_bbox_list,
                enroll_bbox=data.enroll_bbox,
                enroll_time=data.enroll_time,
                fgmask=fgmask,
                fgmask_enroll=fgmask_enroll
            )
            
            alarms = []
            if is_trash:
                logger.info(f"쓰레기 검출 성공 - 카메라: {data.camera_name}, Person ID: {data.person_id},  객체 수: {len(trash_objects)}")
                for obj in trash_objects:
                    sam_bbox = obj.get('sam_bbox')
                    component_bbox = obj.get('component_bbox')
                    
                    if sam_bbox and component_bbox:
                        # 두 bbox의 교집합 계산
                        trash_x1 = max(sam_bbox[0], component_bbox[0])
                        trash_y1 = max(sam_bbox[1], component_bbox[1])
                        trash_x2 = min(sam_bbox[2], component_bbox[2])
                        trash_y2 = min(sam_bbox[3], component_bbox[3])
                        
                        if trash_x1 >= trash_x2 or trash_y1 >= trash_y2:
                            trash_x1, trash_y1, trash_x2, trash_y2 = sam_bbox
                    elif sam_bbox:
                        trash_x1, trash_y1, trash_x2, trash_y2 = sam_bbox
                    elif component_bbox:
                        trash_x1, trash_y1, trash_x2, trash_y2 = component_bbox
                    else:
                        continue
                    
                    # 시각화 이미지에 bbox 그리기
                    _draw_trash_bbox_on_visualization(
                        concat=concat,
                        trash_bbox=[trash_x1, trash_y1, trash_x2, trash_y2],
                        current_img_shape=current_img.shape,
                        h_viz=h_viz,
                        w_viz=w_viz,
                        concat_h=concat_h,
                        concat_w=concat_w
                    )
                    
                    detect_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    enroll_time = datetime.fromtimestamp(data.enroll_time).strftime("%Y-%m-%dT%H:%M:%S")
                    # bbox를 current_img 크기에 맞게 정규화 (0~1)
                    h, w = current_img.shape[:2]
                    trash_bbox = [
                        round(float(trash_x1) / w, 3),
                        round(float(trash_y1) / h, 3),
                        round(float(trash_x2) / w, 3),
                        round(float(trash_y2) / h, 3),
                    ]
                    alarms.append(["Trash", trash_bbox, detect_time, enroll_time])
                    # logger.info(f"쓰레기 알림 생성 - bbox={trash_bbox}")
            
            # 시각화 이미지 저장
            _save_visualization_image(concat, data.camera_name, data.person_id, trash_objects)
            
            elapsed_time = time.time() - t0
            logger.info(f"쓰레기 검출 완료 - 카메라: {data.camera_name}, Person ID: {data.person_id} 소요시간: {elapsed_time:.2f}s")
            
            # 메모리 정리
            del current_img, enroll_img, binary_diff, masks
            cleanup_memory()
            
            return {
                "status": True,
                "alarms": alarms,
                "camera_name": data.camera_name,
                "person_id": data.person_id
            }
        else:
            logger.warning("ROI 영역이 유효하지 않음")
            return {"status": False, "alarms": [], "error": "Invalid ROI"}
            
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰레기 검출 에러 발생 at {current_time}: {e}\n{tb}")
        cleanup_memory()
        return {"status": False, "alarms": [], "error": f"Internal server error: {str(e)}"}


def AI_core_server():
    print("VLM SERVER START")
    logger.info("Starting AI core server on 127.0.0.1:1206")
    uvicorn.run(app, host="0.0.0.0", port=1206, log_level="warning")

if __name__ == "__main__" :
    try:
        AI_core_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
    finally:
        cleanup_memory()
        os.system("chmod -R 777 ../backup")