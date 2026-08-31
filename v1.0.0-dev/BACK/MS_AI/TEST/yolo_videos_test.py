import cv2
import numpy as np
from pathlib import Path
import sys

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # current directory

sys.path.append(str(FILE.parents[1]))  
sys.path.append(str(FILE.parents[1] / 'yolo_tracking'))  

from yolo_tracking.ultralytics import YOLO
from yolo_tracking import boxmot


import time
import datetime
import random

import os
import torch


def plot_one_box(x, img, color=None, label=None, line_thickness=3):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    color = color or [random.randint(0, 255) for _ in range(3)]
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)



def save_image_text(img, save_path, img_name,frame_num, text): # 시험 모듈 (지연이랑, 박스 카운트)
    img_path = save_path + img_name.format(frame_num)

# device = "cuda:0" if torch.cuda.is_available() else "cpu"
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# model = YOLO('./weight/yolo/ms-ai-L-2403_60.pt')  # load a pretrained model (recommended for training)\
model = YOLO('./weight/yolo/ms_ai2403_2_L.engine')# load a pretrained model (recommended for training)\
# model = YOLO('./weight/yolo/drcl_best.pt')  # load a pretrained model (recommended for training)\
# model = YOLO('./weight/yolo/last.engine')# load a pretrained model (recommended for training)\


# model_test = YOLO('./weight/yolo/ms-ai-L-2403_60.pt')  # load a pretrained model (recommended for training)\

# tracker = boxmot.BYTETracker(track_thresh=0.05, 
#                              match_thresh=0.8, 
#                              track_buffer=30, 
#                              frame_rate=30)

tracker = boxmot.BoTSORT(model_weights = Path("./weight/ReID/osnet_x0_25_market.pt"),
                         device = device,
                         fp16 = True
                         )



source = "../../../videos/fire_10.mp4"
# source = "./TEST/test.mp4"

vid = cv2.VideoCapture(source)

conf_score = 0.05
total_frame = vid.get(cv2.CAP_PROP_FRAME_COUNT)
vid.set(cv2.CAP_PROP_POS_FRAMES, total_frame / 2)

color = (0, 0, 255)  # BGR
thickness = 2
fontscale = 1
frame_num = 0
save_txt = ""

output_file = 'output.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
# 비디오 프레임의 너비와 높이 가져오기
frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 비디오 작성자 객체 생성 및 출력 파일 설정
out = cv2.VideoWriter(output_file, fourcc, 30.0, (frame_width, frame_height))
File_Path = Path(__file__).resolve()

while True:
    t0 = time.time()

    frame_num += 1
    ret, im = vid.read()
    
    # if video_streamer.frame_available():
    #     im = video_streamer.get_frame()
    # else:
    #     im = np.zeros((720, 1280, 3), np.uint8)
    #     print(f"video is empty")
    
    # dets = model.predict(source=im, imgsz = 1280, conf = 0.30, iou = 0.5, classes = [0, 1, 2, 3, 4, 7], half = True, verbose=False)
    dets = model.predict(source=im, imgsz = 1280, conf = conf_score, iou = 0.5, classes = [0, 1], half = True, verbose=False)
    boxes = dets[0].boxes.data.cpu().numpy().astype(float)

    # tracks = tracker.update(boxes, im)

    # model_test.update()

    # dets = model.track(source=im, imgsz = 1280, conf = conf_score, iou = 0.5, classes = [0, 1], half = True, verbose=False, persist=True, \
                            # tracker= os.path.join(str(File_Path.parents[1]), 'yolo_tracking', 'ultralytics', 'cfg', 'trackers', 'botsort.yaml'))
                            # tracker= os.path.join(str(File_Path.parents[1]), 'yolo_tracking', 'ultralytics', 'cfg', 'trackers', 'bytetrack.yaml'))
                       
    # # print bboxes with their associated id, cls and conf

    result_img = dets[0].plot()
    # print(tracks)


    # cv2.imshow("frame", cv2.resize(result_img, (0, 0), fx = 0.5, fy = 0.5))
    cv2.imshow("frame", result_img)

    # out.write(result_img)

    # if len(boxes):
    #     now = datetime.datetime.fromtimestamp(time.time()/1000.0)
    #     for i in range(len(boxes)):
    #         save_txt += f"{frame_num}, person, {np.round(boxes[i][-2],2)}, {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
    #     cv2.imwrite(f"./images/{frame_num}.jpg", result_img)
        
    #     print(save_txt)

    print(f"FPS: {1/(time.time() - t0)}")

    # break on pressing q
    if cv2.waitKey(1) & 0xFF == 27:
        break

# with open(f"./images/{frame_num}.txt", "w") as f:
#     f.write(save_txt)

cv2.destroyAllWindows()
vid.release()
out.release()