import numpy as np
from pathlib import Path
import sys

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # current directory
from ultralytics import YOLO

# 모델 로드
model_name = "ms-ai_v1.3_24-11-21-M1"
model = YOLO(f"./weight/yolo/2024-11-21/{model_name}.pt")
# model = YOLO("./weight/yolo/pt/ms-ai2401-finetune_M.pt")

# PyTorch to TensorRT
model.export(format='engine', device=0, half=True, batch = 1)

model_name = "ms-ai_v1.3_24-11-21-M2"
model = YOLO(f"./weight/yolo/2024-11-21/{model_name}.pt")

model.export(format='engine', device=0, half=True, batch = 2)

model_name = "ms-ai_v1.3_24-11-21-M3"
model = YOLO(f"./weight/yolo/2024-11-21/{model_name}.pt")
model.export(format='engine', device=0, half=True, batch = 3)


model_name = "ms-ai_v1.3_24-11-21-M4"
model = YOLO(f"./weight/yolo/2024-11-21/{model_name}.pt")
model.export(format='engine', device=0, half=True, batch = 4)

