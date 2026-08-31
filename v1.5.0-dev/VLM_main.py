from fastapi import FastAPI, HTTPException
from io import BytesIO
from PIL import Image
import json
import os
from pathlib import Path   
import uvicorn

from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info

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

os.environ['CUDA_LAUNCH_BLOCKING'] = "1"  # 에러 발생 지점 정확히 추적
os.environ['TORCH_USE_CUDA_DSA'] = "1"     # device-side assertions 활성화

# 로깅 설정
logger = setup_logging(logger_name="VLM_server")

def check_gpu_memory():
    """GPU 메모리 상태 체크"""
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        gpu_allocated = torch.cuda.memory_allocated(0) / 1024**3
        gpu_cached = torch.cuda.memory_reserved(0) / 1024**3
        logger.info(f"GPU Total: {gpu_memory:.2f}GB, Allocated: {gpu_allocated:.2f}GB, Cached: {gpu_cached:.2f}GB")
        return gpu_memory, gpu_allocated, gpu_cached
    return 0, 0, 0

def cleanup_memory():
    """메모리 정리 함수"""
    try:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()
        logger.info("Memory cleanup completed")
    except Exception as e:
        logger.warning(f"Memory cleanup failed: {e}")

VLM_images_dir = os.path.join(os.getcwd(),"..", "backup", "VLM")
os.makedirs(VLM_images_dir, exist_ok=True)

logger.info("Starting model loading...")
check_gpu_memory()

model_path = os.getcwd() + "/back/weights/Qwen2.5-VL-3B-Instruct-AWQ"

try:
    # 메모리 효율적인 모델 로딩
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_path, 
        torch_dtype=torch.float16,  # bfloat16 대신 float16 사용
        device_map="auto",
        attn_implementation="flash_attention_2",
        low_cpu_mem_usage=True,     # CPU 메모리 사용량 최적화
        trust_remote_code=True      # 모델이 커스텀 코드를 사용하는 경우
    )
    
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    
    logger.info("Model loaded successfully")
    check_gpu_memory()
    
except Exception as e:
    logger.error(f"Model loading failed: {e}")
    raise

print("VLM model load")
app = FastAPI()

class MsgData(BaseModel):
    question : list
    video_path : str


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

@app.post("/vlm_QnA")
async def vlm_answer_img(data : MsgData):
    """LLM QnA API 함수 """
    global model, processor
    
    try:
        t0 = time.time()
        logger.info("Processing VLM request")
        check_gpu_memory()
        
        # 입력 데이터 검증
        validate_input_data(data)
        
        # print(data.question)

        # 텍스트 템플릿 적용
        text = processor.apply_chat_template(data.question, tokenize=False, add_generation_prompt=True)
        logger.info(f"Generated text template: {text[:100]}...")
        
        # 비전 정보 처리
        image_inputs, video_inputs, video_kwargs = process_vision_info(data.question, return_video_kwargs=True)
        logger.info(f"Vision inputs processed - Images: {len(image_inputs) if image_inputs else 0}, Videos: {len(video_inputs) if video_inputs else 0}")
        
        # 프로세서로 입력 준비
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
            **video_kwargs,
        )
        
        # GPU 메모리 체크 후 안전하게 GPU로 이동
        check_gpu_memory()
        
        # 입력을 단계별로 GPU로 이동
        try:
            if torch.cuda.is_available():
                # 각 텐서를 개별적으로 GPU로 이동
                gpu_inputs = {}
                for key, value in inputs.items():
                    if torch.is_tensor(value):
                        gpu_inputs[key] = value.to("cuda", non_blocking=True)
                    else:
                        gpu_inputs[key] = value
                inputs = gpu_inputs
                torch.cuda.synchronize()  # GPU 작업 동기화
                logger.info("Inputs moved to GPU successfully")
            else:
                logger.warning("CUDA not available, using CPU")
                
        except RuntimeError as cuda_error:
            logger.error(f"CUDA error when moving inputs to GPU: {cuda_error}")
            cleanup_memory()
            raise HTTPException(status_code=500, detail=f"GPU memory error: {str(cuda_error)}")

        check_gpu_memory()

        # 모델 추론
        logger.info("Starting model generation")
        with torch.no_grad():  # 그래디언트 계산 비활성화로 메모리 절약
            try:
                generated_ids = model.generate(
                    **inputs, 
                    max_new_tokens=512,  # 토큰 수 제한으로 메모리 사용량 조절
                    do_sample=False,     # 결정적 생성
                    pad_token_id=processor.tokenizer.eos_token_id
                )
            except RuntimeError as gen_error:
                logger.error(f"Generation error: {gen_error}")
                cleanup_memory()
                raise HTTPException(status_code=500, detail=f"Generation failed: {str(gen_error)}")

        # 생성된 토큰 처리
        generated_ids_trimmed = [
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs['input_ids'], generated_ids)
        ]
        
        response = processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )

        logger.info(f"Generation completed successfully : {time.time() - t0:.2f}s")

        remove_video_file(data.video_path)

        # 메모리 정리
        del generated_ids, generated_ids_trimmed, inputs, image_inputs, video_inputs, video_kwargs, text
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

def remove_video_file(video_path):
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            logger.info(f"비디오 파일 삭제 완료: {video_path}")
    except Exception as e:
        logger.warning(f"비디오 파일 삭제 실패: {video_path}, 에러: {e}")

def VLM_server():
    print("VLM SERVER START")
    logger.info("Starting VLM server on 127.0.0.1:1206")
    uvicorn.run(app, host="127.0.0.1", port=1206, log_level="warning")

if __name__ == "__main__" :
    try:
        VLM_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
    finally:
        cleanup_memory()
        os.system("chmod -R 777 ../backup")
