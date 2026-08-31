from fastapi import FastAPI, HTTPException
from io import BytesIO
from PIL import Image
import json
import os
from pathlib import Path   
import uvicorn

from transformers import (                         
                          AutoTokenizer, 
                          AutoModel, 
)

import torch
import base64
import numpy as np
import cv2
from pydantic import BaseModel


from back.ms_labeler_utils import build_transform, dynamic_preprocess

from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

# model_path = os.getcwd() + "/back/weight/InternVL2-8B-MPO"
# llm_model = AutoModel.from_pretrained(model_path,
#                                         torch_dtype=torch.bfloat16,
#                                         load_in_4bit=True,
#                                         low_cpu_mem_usage=True,
#                                         use_flash_attn=True,
#                                         trust_remote_code=True).eval()

model_path = os.getcwd() + "/back/weight/InternVL2_5-4B-MPO"
model = AutoModel.from_pretrained(
                                model_path,
                                torch_dtype=torch.bfloat16,
                                load_in_8bit=True,
                                low_cpu_mem_usage=True,
                                use_flash_attn=True,
                                trust_remote_code=True).eval()

tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True, use_fast=False)
transform = build_transform(input_size=448)
generation_config = dict(max_new_tokens=128, do_sample=False)

print("VLM model load")
app = FastAPI()

class MsgData(BaseModel):
    image: list
    question : list

@app.post("/vlm_qna_label")
# async def vlm_answer_img(task : str, image: list, question : str):
async def vlm_answer_img(data : MsgData):
    global llm_model, tokenizer, generation_config, transform
    try:
        img_data = np.frombuffer(base64.b64decode(data.image[0]), np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        pil_img = Image.fromarray(img)


        images = dynamic_preprocess(pil_img, image_size=448, use_thumbnail=True, max_num=6)
        pixel_values = [transform(image) for image in images]
        pixel_values = torch.stack(pixel_values).to(torch.bfloat16).cuda()

        answer = llm_model.chat(tokenizer, pixel_values, data.question[0], generation_config)

        return {"answer": answer, "status": True}


    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/vlm_qna_par")
# async def vlm_answer_img(task : str, image: list, question : str):
async def vlm_answer_img(data : MsgData):
    global llm_model, tokenizer, generation_config, transform
    try:
        img_data = np.frombuffer(base64.b64decode(data.image[0]), np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        pil_img = Image.fromarray(img)


        images = dynamic_preprocess(pil_img, image_size=448, use_thumbnail=True, max_num=6)
        pixel_values = [transform(image) for image in images]
        pixel_values = torch.stack(pixel_values).to(torch.bfloat16).cuda()

        answer = []

        for question in data.question:
            answer.append(llm_model.chat(tokenizer, pixel_values, question, generation_config))

        return {"answer": answer, "status": True}


    except Exception as e:
        print(e)
        

        raise HTTPException(status_code=500, detail=str(e))

def VLM_server():
    print("VLM SERVER START")
    uvicorn.run(app, host="127.0.0.1", port=1206, log_level="warning")\
    # uvicorn.run(app, host="127.0.0.1", port=1206)

if __name__ == "__main__" :
    try:
        VLM_server()
        # uvicorn.run(app, host="127.0.0.1", port=1206, log_level="warning")
    finally:
        os.system("chmod -R 777 ../backup")
