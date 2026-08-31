import cv2
import numpy as np
from pathlib import Path
import sys

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # current directory
if str(ROOT / 'yolo_tracking') not in sys.path:
    sys.path.append(str(ROOT / 'yolo_tracking'))  
from ultralytics import YOLO

# 모델 로드
# model = YOLO("./ms_vision/weight/yolo/ms-ai2401-finetune.pt")
model = YOLO("./weight/yolo/pt/ms-ai2401-finetune_M.pt")

# PyTorch to TensorRT
model.export(format='engine', dynamic = True, device=0, half=True, batch = 5)
