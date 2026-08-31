import sys
import os
from pathlib import Path

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0] # yolov5 strongsort root directory

sys.path.append(str(ROOT/ 'MS_AI' / 'lib'))  

sys.path.append(str(ROOT / 'MS_AI'))  

import base64
import os
import random
import numpy as np
import cv2
import json
from datetime import datetime
import socket
import threading, time

import backend_utils
from backend_utils import aes_cipher, make_group_dict, get_roi, check_time
from MS_AI.nvr_utils import get_search_data_NVR, check_NVR_camera_info_init, refresh_NVR_camera_info
from MS_AI.utils.util import AI_Msg_Buffer
from MS_AI.main import ai_main

from multiprocessing import Process
from multiprocessing.managers import BaseManager

import requests
import torch

torch.multiprocessing.set_start_method('spawn', force=True)

class Backend():
    def __init__(self):
        super(Backend, self).__init__()
        try:
            self.ciper = aes_cipher()
            self.socket_setting = ("127.0.0.1", 18393, '!@')
            self.info_filename_save = os.path.dirname(os.path.realpath(__file__))+ '/user.json'

            if 'user.json'  in os.listdir(os.path.dirname(os.path.realpath(__file__))):
                self.info_filename = os.path.dirname(os.path.realpath(__file__))+ '/user.json'
            else:
                self.info_filename = os.path.dirname(os.path.realpath(__file__))+ '/user_init.json'

            self.info = self.load_info()
            self.save_info()
            self.info_filename = os.path.dirname(os.path.realpath(__file__))+ '/user.json'
            self.info_backup_filename = os.path.dirname(os.path.realpath(__file__))+ '/user_backup.json'

            # LOGIN 이전
            self.info["userid"] = ""

            self.camera_info_dict = {} # {camera_id:camera_buffer_class}
            self.camera_group_info_dict = {} # {group_id:camera_id}

            # 프론트엔드와의 통신을 위한 쓰레드
            self.socket_worker = SocketServer(self)
            self.socket_worker.daemon = True
            self.socket_worker.start()

            self.date_format = "%Y-%m-%d %H:%M:%S"
            self.record_flag = {}

            self.nvr_info = [self.info["info"]["server"]["userid"], self.info["info"]["server"]["password"], self.info["info"]["server"]["ip"] + ":" + str(self.info["info"]["server"]["port"])]

        except Exception as ex:
            backend_utils.error(ex)
            print("프로그램이 오류로 종료됩니다. 관리자에게 문의하시기 바랍니다.")
            exit()

    def treat_cmd(self, input_json):
        # json = {cmd:cmd, data:data}
        result = {"cmd": "", "data": {}, "error": "", "action": ""}
        self.save_info_backup()
        # print(input_json)
        try:
            cmd = input_json["cmd"]
            # default echo action
            result["cmd"] = input_json["cmd"]
            result["data"] = input_json["data"]
            #self.save_info()

            print(cmd)

            #region == LOGIN ==
            if cmd=="login":
                self.trun_off_ai()
                print(input_json)
                userid = input_json["data"]["userid"].strip()
                password = input_json["data"]["password"].strip()
                if userid=="admin":
                    #admin password 가 없을때는 admin이 암호
                    if self.info["info"]["admin"]["password"]=="":
                        self.info["info"]["admin"]["password"] = self.ciper.enc("admin")
                    if password == self.ciper.dec(self.info["info"]["admin"]["password"]):
                        self.info["is_admin"] = 1
                        self.info["userid"]=userid
                        self.save_info()
                    else :
                        result["error"] = "비밀번호가 다릅니다."
                else:
                    if userid == self.info["info"]["setting"]["userid"]:
                        #password가 없을 때는 그냥 통과
                        if self.info["info"]["setting"]["password"]=="" or password == self.ciper.dec(self.info["info"]["setting"]["password"]):
                            self.info["is_admin"] = 0
                            self.info["userid"] = userid
                            self.save_info()
                        else:
                            result["error"] = "비밀번호가 다릅니다."
                    else:
                        result["error"] = "사용자 아이디가 다릅니다."

            # endregion

            elif cmd == 'mg-init':
                #카메라 정보 새로 확인
                if self.info["info"]["server"]["userid"] != "":
                    self.info = check_NVR_camera_info_init(self.info)
                for camera in self.info["info"]["cameras"]:
                    # self.get_fake_camera_image(camera)
                    self.connect_camera(camera, self.info["info"]["groups"])
                    self.get_camera_image(camera)
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                info = backend_utils.clone(self.info)
                # 프론트에서 보여질 비밀번호 숨김
                info["info"]["setting"]["password"] = ""
                info["info"]["admin"]["password"] = ""

                result["data"] = info

                self.save_info()

            # region == camera ==
            elif cmd == 'mg-camera-add':
                self.info["info"]["cameras"].append(input_json["data"]["camera"])
                camera = self.info["info"]["cameras"][len(self.info["info"]["cameras"])-1]
                # self.get_fake_camera_image(camera)
                self.connect_camera(camera, self.info["info"]["groups"])
                self.get_camera_image(camera)
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                result["data"] = camera
                self.save_info()
            elif cmd == 'mg-camera-update':
                self.info["info"]["cameras"][input_json["data"]["no"]] = input_json["data"]["camera"]
                camera = self.info["info"]["cameras"][input_json["data"]["no"]]
                # self.get_fake_camera_image(camera)
                self.camera_edit(input_json["data"]["no"], camera)
                self.get_camera_image(camera)
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                result["data"] = camera
                self.save_info()
            elif cmd == 'mg-camera-remove':
                no = int(self.info["info"]["cameras"][int(input_json["data"]["no"])]["property"]["no"].replace("Camera", ""))
                self.disconnect_camera(no)
                self.info["info"]["cameras"].pop(input_json["data"]["no"])
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()
            elif cmd == 'mg-camera-undo':
                self.info["info"]["cameras"][input_json["data"]["no"]] = input_json["data"]["camera"]
                camera = self.info["info"]["cameras"][input_json["data"]["no"]]
                # self.get_fake_camera_image(camera)
                self.get_camera_image(camera)
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                result["data"] = camera
                self.save_info()
            # 카메라 정보 새로 확인
            elif cmd == 'mg-camera-refresh':
                self.info = refresh_NVR_camera_info(self.info)
                for camera in self.info["info"]["cameras"]:
                    # self.get_fake_camera_image(camera)
                    self.get_camera_image(camera)
                    self.connect_camera(camera, self.info["info"]["groups"])
                result["data"] = self.info["info"]["cameras"]
                self.save_info()
            # endregion

            # region == group ==
            elif cmd == 'mg-group-add':
                # print("*" * 10)
                # print("group add")
                # print("*" * 10)

                self.info["info"]["groups"].append(input_json["data"]["group"])
                for item in input_json["data"]["camera_groups"]:
                    self.info["info"]["cameras"][item["no"]]["group_no"] = item["group_no"]
                    no = item["no"]

                    if item["group_no"] == -1:
                        self.camera_info_dict[no]['group_name'] = -1
                    else:
                        self.camera_info_dict[no]['group_name'] =  self.info["info"]["groups"][item["group_no"]]["name"]
                
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()
            elif cmd == 'mg-group-update':
                # print("*" * 10)
                # print("group update")
                # print("*" * 10)
                # print(input_json["data"])

                self.info["info"]["groups"][input_json["data"]["no"]] = input_json["data"]["group"]
                for item in input_json["data"]["camera_groups"]:
                    self.info["info"]["cameras"][item["no"]]["group_no"] = item["group_no"]
                    no = item["no"]

                    if item["group_no"] == -1:
                        self.camera_info_dict[no]['group_name'] = -1
                    else:
                        self.camera_info_dict[no]['group_name'] =  self.info["info"]["groups"][item["group_no"]]["name"]

                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()
            elif cmd == 'mg-group-remove':
                # print("*" * 10)
                # print("group remove")
                # print("*" * 10)
                group = self.info["info"]["groups"][int(input_json["data"]["no"])]
                group_name = self.info["info"]["groups"][int(input_json["data"]["no"])]["name"]
                del self.camera_group_info_dict[group_name]
                self.info["info"]["groups"].pop(int(input_json["data"]["no"]))

                # print(input_json["data"])

                for item in input_json["data"]["camera_groups"]:
                    self.info["info"]["cameras"][item["no"]]["group_no"] = item["group_no"]
                    no = item["no"]
                    self.camera_info_dict[no]['group_name'] = -1

                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()
            elif cmd == 'mg-group-event-update':
                self.info["info"]["cameras"][int(input_json["data"]["no"])] = input_json["data"]["camera"]
                no = int(input_json["data"]["no"])
                self.camera_info_dict[no]['ROI'] = get_roi(input_json["data"]["camera"]['roi'])
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])
                self.save_info()
            elif cmd == 'mg-group-time-update':
                self.info["info"]["groups"][int(input_json["data"]["no"])] = input_json["data"]["group"]
                self.save_info()
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])
            elif cmd == 'mg-group-analysis':
                group = self.info["info"]["groups"][int(input_json["data"]["no"])]
                group_name = group["name"]
                group["is_processing"] = 0 if group["is_processing"]==1 else 1
                self.camera_group_info_dict[group_name]["AI_processing"] = group["is_processing"]
                self.save_info()
            elif cmd == 'mg-group-change-grid':
                # print("*" * 10)
                # print("group change grid")
                # print("*" * 10)

                try:
                    self.info["info"]["groups"][int(input_json["data"]["no"])]["grid"] = input_json["data"]["grid"]
                    group_name = self.info["info"]["groups"][int(input_json["data"]["no"])]["name"]

                    self.camera_group_info_dict[group_name]["grid_size"] = input_json["data"]["grid"]

                except:
                    pass
                # print("------------------------")
                # print(self.camera_group_info_dict)
                # print("------------------------")
                # print(self.info["info"]["groups"])
                # print("------------------------")
                # print(self.camera_info_dict)
                # self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()

            elif cmd == 'mg-group-record':
                group = self.info["info"]["groups"][int(input_json["data"]["no"])]
                group["is_recording"] = 0 if group["is_recording"] == 1 else 1
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])

                self.save_info()
            elif cmd == 'mg-group-snapshot':
                group = self.info["info"]["groups"][int(input_json["data"]["no"])]
                group_name = group["name"]
                self.camera_group_info_dict[group_name]["snap_shot"] = 1

            # endregion

            # region == user password ==
            elif cmd == 'mg-password-admin':
                password = input_json["data"].strip()
                self.info["info"]["admin"]["password"] = self.ciper.enc(password)
                self.save_info()
            elif cmd == 'mg-password-user':
                password = input_json["data"].strip()
                self.info["info"]["setting"]["password"] = self.ciper.enc(password)
                self.save_info()
                pass
            # endregion

            # region == setting ==
            elif cmd == 'mg-setting-search':
                param = input_json["data"]
                """
                    start:f.sdate.value +' '+f.stime.value,
                    end:f.edate.value +' '+f.etime.value,
                    event_kind:f.event_kind.value,
                    target:f.target.value,
                    order:f.order.value,
                    page:page, 현재 페이지 최소 1
                    num_list:ut.num_list 페이지당 아이템 수
                """
                log_data = get_search_data_NVR(self.nvr_info[0], self.nvr_info[1], self.nvr_info[2], param['start'], param['end'], param['event_kind'], param['target'], param['order'])
                
                result["data"] = {"total":len(log_data), "rows":[]}
                no = param["num_list"] * (param["page"]-1) + 1

                for i in range(param["num_list"]):
                    if no <=len(log_data) :
                        row = {"no":no,"event":log_data[no-1][2], "camera":f"카메라 {log_data[no-1][1]}", "target":log_data[no-1][3], "datetime": log_data[no-1][0]}
                        result["data"]["rows"].append(row)
                        no += 1

            elif cmd == 'mg-setting-export': #TODO EXPORT 데이터는 검색과 동일
                print('TODO mg-setting-export')
                pass
            elif cmd == 'mg-setting-remove': #TODO FILE REMOVE 데이터는 검색과 동일
                print('TODO mg-setting-remove')
                pass
            elif cmd == 'mg-setting-reconnect':
                self.info["info"]["setting"]["reconnect"] = input_json["data"]
                self.save_info()
            elif cmd == 'mg-setting-folder':
                self.info["info"]["setting"]["folder"] = input_json["data"]

                for i in self.camera_group_info_dict.keys():
                    self.camera_group_info_dict[i]["video_save_path"] = self.info["info"]["setting"]["folder"]["record"]
                    self.camera_group_info_dict[i]["img_save_path"] = self.info["info"]["setting"]["folder"]["snapshot"]

                self.save_info()
            elif cmd == 'mg-setting-privacy':
                self.info["info"]["setting"]["userid"] = input_json["data"]["userid"]
                self.info["info"]["setting"]["password"] = self.ciper.enc(input_json["data"]["password"])
                self.save_info()

            elif cmd == 'mg-setting-resource': #TODO CPU/RAM/GPU
                pass
            # endregion

            # region == admin ==
            elif cmd == 'mg-admin-update':
                self.info["info"]["admin"] = input_json["data"]
                self.save_info()
            # endregion

            # region == server ==
            elif cmd == 'mg-server-update':
                # user.json 초기화
                self.info_filename = os.path.dirname(os.path.realpath(__file__))+ '/user_init.json'
                self.info = self.load_info()
                self.info["info"]["server"] = input_json["data"]

                self.nvr_info = [self.info["info"]["server"]["userid"], self.info["info"]["server"]["password"], self.info["info"]["server"]["ip"] + ":" + str(self.info["info"]["server"]["port"])]
                self.save_info()
                self.info = check_NVR_camera_info_init(self.info)
                for camera in self.info["info"]["cameras"]:
                    # self.get_fake_camera_image(camera)
                    self.connect_camera(camera, self.info["info"]["groups"])
                    self.get_camera_image(camera)
                self.camera_group_info_dict = make_group_dict(self.camera_info_dict, self.info["info"]["groups"], self.info["info"]["setting"]["folder"])
                self.save_info()

                # camera 정보 새로고침
                self.info = refresh_NVR_camera_info(self.info)
                for camera in self.info["info"]["cameras"]:
                    # self.get_fake_camera_image(camera)
                    self.get_camera_image(camera)
                    self.connect_camera(camera, self.info["info"]["groups"])
                result["data"] = self.info["info"]["cameras"]
                self.save_info()
            # endregion

        except Exception as ex:
            backend_utils.error(ex)
            result["error"] = str(ex)
            # restore info data from backup
            self.info = self.load_info_backup()
        finally:
            return result

    def get_fake_camera_image(self, camera):
        try:
            no = int(camera["property"]["no"].replace("Camera", ""))
            if no==9:
                camera["is_connected"]=0
                camera["image"]["src"]=""
                camera["image"]["w"]=0
                camera["image"]["h"]=0
                camera["image"]["fps"]=0
                camera["image"]["datatime"]=""
            else:
                noise = random.randint(0,50) + (no % 10 * 6)
                scolor = [100, 100, 100]
                scolor[no % 3] += noise
                img_array = self.fake_draw_gradient_image(camera["property"]["no"], scolor)
                ret, imgencode = cv2.imencode('.jpg', img_array)
                camera["is_connected"] = 1
                camera["image"]["src"] = 'data:image/jpg;base64,' + str(base64.b64encode(imgencode))[2:].replace("'", "")
                camera["image"]["w"] = 640
                camera["image"]["h"] = 480
                camera["image"]["fps"] = 1
                camera["image"]["datatime"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except Exception as ex:
            backend_utils.error(ex)
        finally:
            return camera

    def get_camera_image(self, camera):
        try:
            try:
                NVR_IP = self.info["info"]["server"]["ip"]
                NVR_ID = self.info["info"]["server"]["userid"]
                NVR_ps = self.info["info"]["server"]["password"]
                no = int(camera["property"]["no"].replace("Camera", ""))
                
                response = requests.get(f"http://{NVR_ID}:{NVR_ps}@{NVR_IP}/live/video{no}.jpg?profile=normal")
                # ret, imgencode = cv2.imencode('.jpg', response)
                imgencode = response.content
                camera["is_connected"] = 1
                camera["image"]["src"] = 'data:image/jpg;base64,' + str(base64.b64encode(imgencode))[2:].replace("'", "")
                camera["image"]["w"] = 640
                camera["image"]["h"] = 480
                camera["image"]["fps"] = 30
                camera["image"]["datatime"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            except:
                no = int(camera["property"]["no"].replace("Camera", ""))
                # print(f"camera {no} is not connected")
                noise = random.randint(0,50) + (no % 10 * 6)
                scolor = [100, 100, 100]
                scolor[no % 3] += noise
                img_array = self.fake_draw_gradient_image(camera["property"]["no"], scolor)
                ret, imgencode = cv2.imencode('.jpg', img_array)
                camera["is_connected"] = 1
                camera["image"]["src"] = 'data:image/jpg;base64,' + str(base64.b64encode(imgencode))[2:].replace("'", "")
                camera["image"]["w"] = 640
                camera["image"]["h"] = 480
                camera["image"]["fps"] = 1
                camera["image"]["datatime"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        except Exception as ex:
            backend_utils.error(ex)
        finally:
            return camera

    def connect_camera(self, camera_info, group_info):
        try:
            NVR_IP = self.info["info"]["server"]["ip"]
            NVR_ID = self.info["info"]["server"]["userid"]
            NVR_ps = self.info["info"]["server"]["password"]

            no = int(camera_info["property"]["no"].replace("Camera", "")) - 1
            # no = int(camera_info["property"]["no"].replace("Camera", ""))

            ip_address = camera_info["property"]["ip"]
            user_id = camera_info["property"]["userid"]
            password = camera_info["property"]["password"]
            stream = camera_info["property"]["stream_no"].lower().replace(" ", "")
            port = camera_info["property"]["port"]
            group_no = int(camera_info["group_no"])
            if group_no == -1:
                group_name = -1
            else:
                group_name = group_info[int(camera_info["group_no"])]['name']

            # video_source = f"rtsp://{user_id}:{password}@{ip_address}:{port}/{stream}"
            nvr_source = f"rtsp://{NVR_ID}:{NVR_ps}@{NVR_IP}/video{no+1}"
            video_source = f"rtsp://{user_id}:{password}@{ip_address}:{port}/{stream}"


            appsink_name = str("appsink{}".format(no))

            # 카메라 info 생성 및 카메라 pipe 생성
            # self.camera_info_dict[no] = {"VideoBuffer" : ms.Video_Buffer(video_source, appsink_name),
            #                              "video_source" : [video_source, appsink_name],
            #                              "Group" : int(camera["group_no"]),
            #                              "ROI" : ms.get_roi(camera["roi"])}

            self.camera_info_dict[no] = {"video_source" : [video_source, appsink_name],
                                         "nvr_source" : [nvr_source, appsink_name],
                                         "group_name" : group_name,
                                         "ROI" : get_roi(camera_info["roi"])}


            # cap_main = cv2.VideoCapture(video_source)            
            # self.camera_info_dict[no] = {"VideoBuffer" : cap_main,
            #                             "video_source" : [video_source, appsink_name],
            #                             "Group" : int(camera["group_no"]),
            #                             "DetectType": ms.kor_uni_decoder(camera["event_kind"]),
            #                             "ROI" : ms.roi_to_numpy(camera["roi"])}
                    
        except Exception as ex:
            backend_utils.error(ex)
        finally:
            return camera_info
        
    def disconnect_camera(self, camera_id):
        # print(self.camera_info_dict)
        # self.camera_info_dict[camera_id]["VideoBuffer"].stop()
        del self.camera_info_dict[camera_id]

    def camera_edit(self, befor_camera_index, camera):
        befor_camera_num = list(self.camera_info_dict.keys())[int(befor_camera_index)]
        # self.camera_info_dict[befor_camera_num]["VideoBuffer"].stop()
        # del self.camera_info_dict[befor_camera_num]
        self.connect_camera(camera, self.info["info"]["groups"])

    def fake_draw_gradient_image(self, text, scolor):
        rectangle_position = ((0,0), (640,640))
        rotate = 1
        frame = np.full(shape=(640, 640, 3), fill_value=255, dtype=np.uint8)
        (xMin, yMin), (xMax, yMax) = rectangle_position
        color = np.array(scolor, np.uint8)[np.newaxis, :]
        mask1 = np.rot90(np.repeat(np.tile(np.linspace(1, 0, (rectangle_position[1][1] - rectangle_position[0][1])),
                                           ((rectangle_position[1][0] - rectangle_position[0][0]), 1))[:, :,
                                   np.newaxis], 3, axis=2), rotate)
        frame[yMin:yMax, xMin:xMax, :] = mask1 * frame[yMin:yMax, xMin:xMax, :] + (1 - mask1) * color
        frame = frame[:480, :, :]
        cv2.putText(frame, text, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return frame

    def load_info(self):
        try:
            with open(self.info_filename, "r", encoding="UTF-8") as f:
                return json.load(f)
        except Exception as ex:
            backend_utils.error(ex)
            return {}

    def save_info(self):
        try:
            with open(self.info_filename_save, "w", encoding="UTF-8") as f:
                f.write(json.dumps(self.info, indent=4))
        except Exception as ex:
            backend_utils.error(ex)

    def load_info_backup(self):
        try:
            with open(self.info_backup_filename, "r", encoding="UTF-8") as f:
                return json.load(f)
        except Exception as ex:
            backend_utils.error(ex)
            return {}

    def save_info_backup(self):
        try:
            with open(self.info_backup_filename, "w", encoding="UTF-8") as f:
                f.write(json.dumps(self.info, indent=4))
        except Exception as ex:
            backend_utils.error(ex)
    def templet(self):
        try:
            pass
        except Exception as ex:
            backend_utils.error(ex)

    def trun_off_ai(self):
        # print(self.info["info"]["groups"])
        for i in range(len(self.info["info"]["groups"])):
            group = self.info["info"]["groups"][i]
            group["is_processing"] = 0 
            self.info["info"]["groups"][i]["is_processing"] = 0
        self.save_info()

"""
프론트엔드와 소켓 통신을 위한 쓰레드
"""
# BACKEND SOCKET SERVER
class SocketServer(threading.Thread):
    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.server = None
        self.is_cancel = False

    def run(self):
        HOST, PORT, DELIMITER = self.parent.socket_setting
        BUFFER = 2048
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 주소 재사용 활성화
            self.server.bind((HOST, PORT))
            print("Start server")
            self.server.listen(1)
            while not self.is_cancel :
                try:
                    conn, addr = self.server.accept()
                    # print('connection from ', addr)
                    buffer = b''
                    result_json = {"cmd": "", "data": {}, "error": "", "action": ""}
                    while True:
                        buffer += conn.recv(BUFFER)
                        # print('received ', len(buffer))
                        received_str = buffer.decode('utf-8')
                        if received_str.find(DELIMITER)>-1:
                            received_str = received_str[:received_str.find(DELIMITER)]
                            input_json = json.loads(received_str)
                            result_json = self.parent.treat_cmd(input_json)
                            break
                except Exception as ex:
                    result_json["error"] = str(ex)
                    backend_utils.error(ex)
                    raise Exception('THREAD RESTART 1')
                finally:
                    conn.send((json.dumps(result_json) + DELIMITER).encode('utf-8'))
                    # print('connection ended ', addr)
        except Exception as ex:
            backend_utils.error(ex)
            self.run()
            #self.is_stop = True


if __name__ == '__main__':
    be = Backend()
    
    AI_Procss = {}
    try:
        BaseManager.register('AI_msg_buffer', AI_Msg_Buffer)
        manager = BaseManager()
        manager.start()
    except Exception as ex:
        backend_utils.error(ex)

    AI_msg_pipe_dict = {}
    while True:
        time.sleep(0.03)

        # print("------------------------")
        # print(be.camera_group_info_dict)
        # print("------------------------")
        # print(be.info["info"]["groups"])
        # print("------------------------")
        # print(be.camera_info_dict)

        for gruop_name, group_info in be.camera_group_info_dict.items():
            if gruop_name == -1:
                continue
            camera_info_dict = {}
            video_buffer_list = []
            is_admin = True if be.info["is_admin"] == 1 else False
            # print("gruop_id",gruop_id)
            # print(group_info["process_time"])
            # print(ms.check_time(group_info["process_time"]))

            #ai 분석 활성화
            if group_info["AI_processing"] == 1 and (gruop_name not in AI_Procss) and check_time(group_info["process_time"]):
                for camera_id in group_info["ID_list"]:
                    camera_info_dict[camera_id] = be.camera_info_dict[camera_id]

                AI_msg_pipe_dict[gruop_name] = manager.AI_msg_buffer()

                AI_Procss[gruop_name] = Process(target=ai_main, args=[AI_msg_pipe_dict[gruop_name], \
                                                                gruop_name, \
                                                                camera_info_dict, \
                                                                be.nvr_info, \
                                                                group_info["grid_size"], \
                                                                group_info['video_save_path'],\
                                                                group_info['img_save_path'],
                                                                is_admin])
                AI_Procss[gruop_name].start()
                print("AI process start")
                process_start_time = time.time()

                # while True:
                #     if AI_msg_pipe_dict[gruop_name].get_check_connect_flag() == True:
                #         break

                #     if time.time() - process_start_time > 10:
                #         print("reconnect AI process")
                #         AI_Procss[gruop_name].terminate()
                #         del AI_Procss[gruop_name]
                #         del AI_msg_pipe_dict[gruop_name]

                #         time.sleep(0.5)
                #         AI_msg_pipe_dict[gruop_name] = manager.AI_msg_buffer()
                #         AI_Procss[gruop_name] = Process(target=ai_main, args=[AI_msg_pipe_dict[gruop_name], \
                #                                                         gruop_name, \
                #                                                         camera_info_dict, \
                #                                                         be.nvr_info, \
                #                                                         group_info["grid_size"], \
                #                                                         group_info['video_save_path'],\
                #                                                         group_info['img_save_path']])
                #         AI_Procss[gruop_name].start()
                #         process_start_time = time.time()

            #ai 분석 비활성화
            if (gruop_name in AI_Procss) and (group_info["AI_processing"] == 0 or check_time(group_info["process_time"]) == False) :
                AI_msg_pipe_dict[gruop_name].stop()
                time.sleep(0.5)
                group_info["AI_processing"] = 0
                AI_Procss[gruop_name].terminate()
                del AI_Procss[gruop_name]
                del AI_msg_pipe_dict[gruop_name]
                print("AI process terminate")

            #ai 녹화 활성화
            if group_info["record"] == 1 and (gruop_name in AI_Procss) and AI_msg_pipe_dict[gruop_name].get_record_flag() == False :
                # print(group_info['video_save_path'])
                os.makedirs(group_info['video_save_path'], exist_ok= True)
                AI_msg_pipe_dict[gruop_name].set_record_flag(True)

            #ai 녹화 비활성화
            if group_info["record"] == 0 and (gruop_name in AI_Procss) and AI_msg_pipe_dict[gruop_name].get_record_flag() == True :
                os.makedirs(group_info['video_save_path'], exist_ok= True)

                AI_msg_pipe_dict[gruop_name].set_record_flag(False)

            #스냅샷 활성화
            if group_info["snap_shot"] == 1 and (gruop_name in AI_Procss) :
                # print(group_info['img_save_path'])
                os.makedirs(group_info['img_save_path'], exist_ok= True)

                AI_msg_pipe_dict[gruop_name].set_snapshot_flag(True)
                group_info["snap_shot"] = 0

            # AI 분석 결과 NVR로 전송
            # if (gruop_name in AI_Procss) and len(AI_msg_pipe_dict[gruop_name].get_data()) > 0:
            #     camera_info_dict = AI_msg_pipe_dict[gruop_name].get_data()
            #     # print("receive data : ",AI_msg_pipe_dict[gruop_id].get_data())

            #     # try:
            #     send_NVR(camera_info_dict, 
            #             be.nvr_info[0], 
            #             be.nvr_info[1], 
            #             "http://" + be.nvr_info[2] + "/api/events/svg", 
            #             "http://" + be.nvr_info[2] + "/api/events",
            #             email=False)
                # except:
                    # print("NVR send error")

