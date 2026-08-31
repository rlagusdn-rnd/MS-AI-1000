import os
import sys
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import cv2
import torch
import numpy as np
from logging_config import setup_logging
import traceback

# 로깅 설정
logger = setup_logging(logger_name="MS_TRASH_BACK_TRACKING", log_file="AI_SERVER.log")

def is_point_outside_bbox(point, bbox):
    """점이 bbox 밖에 있는지 확인하는 함수
    
    Args:
        point: (x, y) 좌표
        bbox: [x1, y1, x2, y2] 형태의 bbox
    
    Returns:
        bool: 점이 bbox 밖에 있으면 True, 안에 있으면 False
    """
    if point is None:
        return False
    
    x, y = point
    x1, y1, x2, y2 = bbox[0]
    
    return x < x1 or x > x2 or y < y1 or y > y2

def get_mask_center(mask_logits):
    """마스크의 중심점을 계산하는 함수
    
    Args:
        mask_logits: numpy array 형태의 마스크 (shape: (1, 1, H, W) or (1, H, W) or (H, W))
    
    Returns:
        (cx, cy): 마스크의 중심점 좌표, 마스크가 없으면 None
    """
    if isinstance(mask_logits, torch.Tensor):
        mask_logits = mask_logits.cpu().numpy()
    
    # 4D (1, 1, H, W) -> 2D (H, W)
    if mask_logits.ndim == 4:
        mask = mask_logits[0, 0]  # 배치와 객체 차원 제거
    # 3D (1, H, W) -> 2D (H, W)
    elif mask_logits.ndim == 3:
        mask = mask_logits[0]
    # 2D (H, W)
    elif mask_logits.ndim == 2:
        mask = mask_logits
    else:
        return None
    
    # 이진 마스크로 변환 (2D 유지)
    mask = (mask > 0.0).astype(np.uint8)
    
    # 마스크가 비어있으면 None 반환
    if np.sum(mask) == 0:
        return None
    
    # 마스크의 중심점 계산 (무게중심) - 반드시 2D 배열이어야 함
    moments = cv2.moments(mask)
    if moments["m00"] == 0:
        return None
    
    cx = int(moments["m10"] / moments["m00"])
    cy = int(moments["m01"] / moments["m00"])
    
    return (cx, cy)

def get_mask_bbox(mask_logits):
    """마스크에서 bounding box를 계산하는 함수
    
    Args:
        mask_logits: numpy array 형태의 마스크 (shape: (1, 1, H, W) or (1, H, W) or (H, W))
    
    Returns:
        (x1, y1, x2, y2): 마스크의 bbox 좌표, 마스크가 없으면 None
    """
    if isinstance(mask_logits, torch.Tensor):
        mask_logits = mask_logits.cpu().numpy()
    
    # 4D (1, 1, H, W) -> 2D (H, W)
    if mask_logits.ndim == 4:
        mask = mask_logits[0, 0]
    # 3D (1, H, W) -> 2D (H, W)
    elif mask_logits.ndim == 3:
        mask = mask_logits[0]
    # 2D (H, W)
    elif mask_logits.ndim == 2:
        mask = mask_logits
    else:
        return None
    
    # 이진 마스크로 변환
    mask = (mask > 0.0).astype(np.uint8)
    
    # 마스크가 비어있으면 None 반환
    if np.sum(mask) == 0:
        return None
    
    # 마스크의 외곽 좌표 찾기
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    
    if not np.any(rows) or not np.any(cols):
        return None
    
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    return (int(x1), int(y1), int(x2), int(y2))

def apply_mask_to_frame(frame, mask_logits, colors=None):
    """마스크를 프레임에 오버레이하는 함수"""
    if isinstance(mask_logits, torch.Tensor):
        mask_logits = mask_logits.cpu().numpy()
    
    # 2D 마스크인 경우 3D로 변환
    if mask_logits.ndim == 2:
        mask_logits = mask_logits[np.newaxis, :, :]
    
    if colors is None:
        colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (0, 255, 255)]
    
    mask_colored = np.zeros_like(frame, dtype=np.uint8)
    for class_idx in range(mask_logits.shape[0]):
        mask = (mask_logits[class_idx] > 0.0).astype(np.uint8) * 255
        for i in range(3):
            mask_colored[:, :, i] = np.clip(
                mask_colored[:, :, i] + (mask * (colors[class_idx][i] / 255)).astype(np.uint8),
                0, 255
            )
    return cv2.addWeighted(frame, 0.6, mask_colored, 0.4, 0)



def process_backtracking_trash(camera_name, camera_num, detect_time, nvr_info):
    """쓰레기 역추적 API 엔드포인트
        camera_name: 카메라 이름
        camera_num: 카메라 번호
        detect_time: 검출 시간 예: 2025-10-30T10-36
        nvr_info: NVR 정보 (nvr_ip, nvr_id, nvr_pw)
    """
    try:
        t0 = time.time()
        trash_info_path = os.path.join(os.getcwd(), "..", "backup", "trash_data", "info")
        # 예: 함박관_정문2_2025-10-30T10-36.json
        trash_info_file = os.path.join(trash_info_path, f"{camera_name}_{detect_time}.json")
        logger.info(f"쓰레기 정보 파일 경로: {trash_info_file}")
        
        if not os.path.exists(trash_info_file):
            logger.error(f"쓰레기 정보 파일이 존재하지 않음: {trash_info_file}")
            return {"status": False, "error": f"쓰레기 정보 파일을 찾을 수 없음: {trash_info_file}"}

        with open(trash_info_file, "r") as f:
            trash_info = json.load(f)
            trash_bbox_norm = trash_info["trash_object_bbox"]  # [0.27, 0.733, 0.3, 0.80] (정규화된 좌표)
            detect_time = trash_info["detect_time"]  # 2025-10-30T09:54:34
            enroll_time = trash_info["enroll_time"]  # 2025-10-30T09:54:17
            logger.info(f"쓰레기 정보 파일 로드 완료: {trash_info}")

        # NVR에서 영상 다운로드
        video_file = "back_tracking_video_ori.mp4"
        url = f"http://{nvr_info['nvr_ip']}/download/video{camera_num}.mp4?start={enroll_time}&end={detect_time}&index=1"
        resp = requests.get(url, auth=HTTPBasicAuth(nvr_info['nvr_id'], nvr_info['nvr_pw']), stream=True, timeout=30)
        resp.raise_for_status()

        with open(video_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 비디오 읽기 및 버퍼링
        logger.info("쓰레기 역추적 비디오 프레임 로드 중...")
        cap = cv2.VideoCapture(video_file)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        video_buffer = []
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 모든 프레임 저장 (또는 샘플링: frame_num % 2 == 0)
            video_buffer.append(frame)
            frame_num += 1

        cap.release()
        logger.info(f"쓰레기 역추적 비디오 프레임 로드 완료 - 프레임 수: {len(video_buffer)}")


        # 출력 비디오 설정
        # output_video = f"./{camera_name}_backtracking.mp4"
        # out = cv2.VideoWriter(output_video, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

        # video_file 삭제
        try:
            if os.path.exists(video_file):
                os.remove(video_file)
                logger.info(f"원본 다운로드 파일 삭제됨: {video_file}")
        except Exception as e:
            logger.warning(f"원본 비디오 삭제 실패: {video_file} ({e})")

        # 정규화된 bbox를 실제 픽셀 좌표로 변환
        x1_norm, y1_norm, x2_norm, y2_norm = trash_bbox_norm
        trash_bbox = np.array([[int(x1_norm * width), int(y1_norm * height), int(x2_norm * width), int(y2_norm * height)]], dtype=np.float32)
        
        # SAM 모델로 역추적
        sam_checkpoint = str(os.getcwd()) + "/../weights/segment_anything_2/sam2.1_hiera_base_plus.pt"
        model_cfg = "configs/sam2.1/sam2.1_hiera_b+.yaml"

        device = torch.device("cuda")

        sys.path.insert(0, str(os.getcwd()) + "/../")
        from sam2.build_sam import build_sam2_camera_predictor
        predictor = build_sam2_camera_predictor(model_cfg, sam_checkpoint, device=device)

        # 객체의 bbox 위치 추적
        outside_detected = False

        dt = datetime.strptime(detect_time, "%Y-%m-%dT%H:%M:%S")
        detect_time_formatted = dt.strftime("%Y-%m-%dT%H-%M-%S")
        outside_image_path = f"../backup/trash_data/images/{camera_name}_{detect_time_formatted}"
        os.makedirs(outside_image_path, exist_ok=True)

        first_frame = True
        x1, y1, x2, y2 = trash_bbox[0].astype(int)

        for idx, frame in enumerate(reversed(video_buffer)):
            with torch.autocast(device_type=device.type, dtype=torch.bfloat16 if device.type == 'cuda' else torch.float32):
                if first_frame:
                    # 첫 프레임 로드 (마지막 프레임)
                    predictor.load_first_frame(frame)
                    
                    # 쓰레기 객체 프롬프트 추가
                    _, out_obj_ids, out_mask_logits = predictor.add_new_prompt(
                        frame_idx=0,
                        obj_id=1,
                        bbox=trash_bbox
                    )
                    first_frame = False
                    first_frame_img = cv2.rectangle(frame.copy(), (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(first_frame_img, "Trash Object", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                else:
                    # 이전 프레임 추적
                    _, out_mask_logits = predictor.track(frame)
        
            mask_logits = out_mask_logits.cpu().numpy()
            # frame_with_mask = apply_mask_to_frame(frame, mask_logits)
            mask_center = get_mask_center(mask_logits)
            
            # bbox 밖으로 벗어나는지 체크
            if not outside_detected and mask_center is not None:
                if is_point_outside_bbox(mask_center, trash_bbox):
                    outside_detected = True
                    
                    # 마스크 bbox 계산
                    mask_bbox = get_mask_bbox(mask_logits)
                    
                    # 저장용 이미지 복사
                    save_frame = frame.copy()
                    
                    # 마스크 bbox 그리기 (파란색)
                    if mask_bbox is not None:
                        mx1, my1, mx2, my2 = mask_bbox
                        cv2.rectangle(save_frame, (mx1, my1), (mx2, my2), (0, 255, 0), 2)
                        cv2.putText(save_frame, "Trash Object", (mx1, my1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    
                    # 움직이는 순간 이미지 클립하고 저장
                    cv2.imwrite(os.path.join(outside_image_path, "0.jpg"), save_frame)
                    cv2.imwrite(os.path.join(outside_image_path, "1.jpg"), first_frame_img)
                    
                    logger.info(f"마스크 중심점이 bbox 밖으로 벗어남 감지! - 프레임: {len(video_buffer) - idx - 1}, 중심점: {mask_center}, 초기 bbox: [{x1}, {y1}, {x2}, {y2}], 이미지 저장: {outside_image_path}")
                    
                    break
            # 비디오에 쓰기
            # out.write(frame_with_mask)

        # out.release()
        elapsed_time = time.time() - t0
        logger.info(f"쓰레기 역추적 완료 - 카메라: {camera_name}, 카메라 번호: {camera_num}, 검출 시간: {detect_time}, 소요시간: {elapsed_time:.2f}s")
        

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"쓰레기 역추적 에러 발생 at {current_time}: {e}\n{tb}")