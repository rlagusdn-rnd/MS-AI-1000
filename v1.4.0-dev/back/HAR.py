import time
import numpy as np
import cv2
import threading
import os 
from datetime import datetime
import requests
import traceback
import sys
from logging_config import setup_logging
from back.utils import plot_one_box 

# 로깅 설정
logger = setup_logging()

class Person_Info():
    def __init__(self, camera_name, nvr_ip, PAR, host, port, ParTime):
        self.info = dict()
        current_hour = int(datetime.now().hour)  # 시간만 추출

        if PAR and check_time_range(current_hour, ParTime):
            self.run_par = True
        else:
            self.run_par = False

        self.url = f"http://{host}:{port}/start_par"
        if self.run_par:
            self.save_path = os.path.join(os.getcwd(), "..", "backup", "PAR", nvr_ip, camera_name)
            os.makedirs(self.save_path, exist_ok=True)

    def add_id(self, track_info):
        x1, y1, x2, y2, id_, conf, label, _ = track_info
        id_ = int(id_)
        
        self.info[id_] = {"trejectory" : [[int((x2 + x1)/2), int(y2)]],
                         "status" : [0],
                         "bbox" : [[x1, y1, x2, y2]],
                        #  "stop" : False,
                         "last_time" : time.time(),
                         "falldown" : [],
                         "fight" : [],
                         "img_crop" : [],
                         "img" : [],
                         "bbox_area" : []}

    def update_id(self, img, track_info):
        if len(track_info):
            for x1, y1, x2, y2, id_, conf, label, _ in track_info:
                id_ = int(id_)
                if id_ in self.info.keys():
                    self.info[id_]["trejectory"].append([int((x2 + x1)/2), int(y2)]) 
                    # self.info[id_]["status"].append(status) 
                    self.info[id_]["last_time"] = time.time()
                    if self.run_par :
                        self.info[id_]["img_crop"].append(img[int(y1 - 10) : int(y2 + 10), int(x1 - 10) : int(x2 + 10)]) 
                        self.info[id_]["img"].append(img) 
                        self.info[id_]["bbox_area"].append((x2 - x1) * (y2 - y1))
                        self.info[id_]["bbox"].append([int(x1), int(y1), int(x2), int(y2)])



                    if len(self.info[id_]["trejectory"]) > 60:
                        self.info[id_]["trejectory"].pop(0)

                else:
                    self.add_id([x1, y1, x2, y2, id_, conf, label, _])


        self.refresh_info()

    def update_status(self, id_, detect_type, status):
        self.info[id_][detect_type].append(status) 

        if len(self.info[id_][detect_type]) > 11:
            self.info[id_][detect_type].pop(0)

    def get_status(self, id_, detect_type):
        if len(self.info[id_][detect_type]) > 5:
        #     status_list, counts =  np.unique(np.array(self.info[id_][-5:]), return_counts=True)
        #     status = status_list[np.argmax(counts)]
        
        # else:
            status_list, counts =  np.unique(np.array(self.info[id_][detect_type]), return_counts=True)
            status = status_list[np.argmax(counts)]

        else:
            status = 0

        return status

    def refresh_info(self):
        delete_id = []
        for id_ in self.info.keys():
            if time.time() - self.info[id_]["last_time"] > 60:
                delete_id.append(id_)

        for id_ in delete_id:
            if len(self.info[id_]["img_crop"]) > 5:
                current_time = datetime.now().strftime("%y-%m-%d %H:%M:%S")
                img_save_path = os.path.join(self.save_path, current_time.split(" ")[0], current_time.split(" ")[1])

                thread = threading.Thread(target=save_image, args=(self.info[id_]["img_crop"].copy(),img_save_path, self.url))
                thread.start()
                thread_video = threading.Thread(target=save_video, args=(self.info[id_]["img"].copy(),img_save_path, self.info[id_]["bbox"], np.argmax(np.array(self.info[id_]["bbox_area"]))))
                thread_video.start()

            del self.info[id_]

# 이미지 저장 함수
def save_image(image_data, path, url):
    try:
        os.makedirs(path, exist_ok=True)
        pass_flag = False
        save_num = len(image_data) // 5
        for i, img in enumerate(image_data):
            img_name = f"{i}.png"
            if img is not None and (pass_flag or (i % save_num) == 0) :
                if img.shape[0] * img.shape[1] < 1500:
                    pass_flag = True
                    continue
                cv2.imwrite(path + "/" + img_name, img)  # 이미지 저장

                # print(f"Image saved to {path}")
                pass_flag = False

        response = requests.put(url, json={"msg" : ""})
        logger.info(f"save img : {path}")
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)


def save_video(img_buffer, save_path, bbox_list, max_area_index):
    try:
        if len(img_buffer):
            os.makedirs(save_path, exist_ok=True)

            height, width, _ = img_buffer[0].shape

            output_file = os.path.join(save_path, "output_video.mp4")

            # fourcc = cv2.VideoWriter_fourcc(*'H264')  # H.264 코덱
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')

            fps = 30  # 초당 프레임 수 (FPS)
            # VideoWriter 객체 생성
            video_writer = cv2.VideoWriter(output_file, fourcc, fps, (width, height))

            for i, img in enumerate(img_buffer):
                img = plot_one_box(bbox_list[i], img.copy(), bbox = True, color=(0,150,95), line_thickness=2) # 박스 그리기
                video_writer.write(img)

            logger.info(f"save Video : {save_path}")

            video_writer.release()

            cv2.imwrite(save_path + "/" + "show_img.png", img_buffer[max_area_index])  # 이미지 저장


    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
        
def check_time_range(current_hour, run_time):
    start, end = run_time
    # 시간 범위가 자정을 기준으로 넘어가는 경우
    if int(start) > int(end):
        return current_hour >= int(start) or current_hour < int(end)
    # 일반적인 경우
    return int(start) <= current_hour < int(end)
