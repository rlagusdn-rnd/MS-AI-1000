import sys
import os
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth
import subprocess

from multiprocessing import Process

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from contextlib import asynccontextmanager
import torch
from datetime import datetime

from back.ms_labeler_main import ms_labeler, train
from back.utils import send_NVR_empty
from back.ms_PAR_main import run_PAR

from fastapi import FastAPI, Response, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.requests import Request

import threading

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

from utils import (LoginData, 
                   CameraInfoData, 
                   Login_Chg_Data, 
                   MsgData,
                   Colors,
                   DictData,
                   VideoStreamTrack,
                   load_json,
                   save_json,
                   load_crypography_json,
                   save_crypography_json,
                   connect_camera_server,
                   check_alarm_video_history,
                   check_par_video_history,
                   get_init_camera_dict
                    )

import cv2
import numpy as np
import base64
import shutil
import json
import time

from turbojpeg import TurboJPEG
import asyncio

app = FastAPI()

current_video_stream = None
stream_lock = threading.Lock()

from typing import Dict

torch.multiprocessing.set_start_method('spawn', force=True)


cap = None

async def generate_frames():
    global cap
    jpeg = TurboJPEG()

    while True:
        if cap is not None and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("⚠️ 프레임을 읽을 수 없습니다. RTSP 연결을 확인하세요.")
                await asyncio.sleep(1)  # 1초 대기 후 재시도
                continue

            buffer = jpeg.encode(frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + buffer + b"\r\n"
            )
        else:
            print("⚠️ RTSP 스트림이 닫혀 있습니다. 다시 시도합니다.")
            await asyncio.sleep(1)  # 1초 대기 후 재시도

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.post("/set_rtsp")
async def set_rtsp(rtsp_url: str = Form(...)):
    global cap
    if cap is not None:
        cap.release()

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="RTSP 스트림을 열 수 없습니다. URL을 확인하세요.")

    return {"message": f"RTSP URL 설정 완료: {rtsp_url}"}



templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML 파일 제공
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 특정 이미지 직접 제공 예제 (필요한 경우)
@app.get("/images/{filename}")
async def get_image(filename: str):
    return FileResponse(f"GUI/images/{filename}")

# 특정 이미지 직접 제공 예제 (필요한 경우)
@app.get("/js/{filename}")
async def get_image(filename: str):
    return FileResponse(f"GUI/js/{filename}")

# 특정 이미지 직접 제공 예제 (필요한 경우)
@app.get("/font/{filename}")
async def get_image(filename: str):
    return FileResponse(f"GUI/font/{filename}")

# 특정 이미지 직접 제공 예제 (필요한 경우)
@app.get("/font/{filename}")
async def get_image(filename: str):
    return FileResponse(f"GUI/font/{filename}")

# 특정 이미지 직접 제공 예제 (필요한 경우)
@app.get("/{filename}")
async def get_image(filename: str):
    return FileResponse(f"GUI/{filename}")



if __name__ == "__main__" :
    import sys
    import os
    from pathlib import Path   

    try:
        import uvicorn

        uvicorn.run(app, host="0.0.0.0", port=65432)

    finally:
        os.system("chmod -R 777 ../backup")
        # vlm_process.terminate()
        # vlm_process.wait()

 
