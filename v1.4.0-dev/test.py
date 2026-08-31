# # from back.ms_labeler_main import train




# # train(NVR_IP = "117.17.159.143")

# from requests.auth import HTTPBasicAuth
# import requests


# nvr_ip = "192.168.0.249"
# nvr_id = "USER"
# nvr_pw = "Admin13579"

# auth = HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW
# camera_post = f'http://{nvr_ip}/api/cameras'
# # try:
# r = requests.get(camera_post,auth=auth, timeout= 3)
# # "<Response [200]>"
# print(str(r))
# print(str(r) == str("<Response [200]>"))


# import time

# # 테스트용 리스트 생성
# my_list = list(range(1000000))

# # enumerate() 사용
# start_time = time.time()
# for index, value in enumerate(my_list):
#     pass
# print(f"enumerate() duration: {time.time() - start_time} seconds")

# # range(len()) 사용
# start_time = time.time()
# for i in range(len(my_list)):
#     _ = my_list[i]
# print(f"range(len()) duration: {time.time() - start_time} seconds")

# import gi
# gi.require_version('Gst', '1.0')
# gi.require_version('GstRtspServer', '1.0')
# from gi.repository import Gst, GstRtspServer, GObject

# class RTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
#     def __init__(self, video_path):
#         super(RTSPMediaFactory, self).__init__()
#         self.video_path = video_path

#     def do_create_element(self, url):
#         # GStreamer pipeline to stream a video file
#         pipeline_str = f"filesrc location={self.video_path} ! decodebin ! videoconvert ! x264enc tune=zerolatency ! rtph264pay config-interval=1 name=pay0 pt=96"
#         return Gst.parse_launch(pipeline_str)


# class GstServer:
#     def __init__(self, video_path, ip):
#         GObject.threads_init()
#         Gst.init(None)

#         # RTSP 서버 초기화
#         self.server = GstRtspServer.RTSPServer()
#         self.server.set_service("65432")  # 포트 설정

#         # 비디오 파일을 소스로 하는 RTSP 서버 생성
#         self.factory = RTSPMediaFactory(video_path)
#         self.factory.set_shared(True)

#         mount_points = self.server.get_mount_points()
#         mount_points.add_factory("/video", self.factory)

#         # RTSP 서버 실행
#         self.server.attach(None)
#         print(f"RTSP server is running at rtsp://{ip}:65432/video")

#     def run(self):
#         loop = GObject.MainLoop()
#         try:
#             loop.run()
#         except KeyboardInterrupt:
#             print("Interrupted. Exiting.")


# if __name__ == "__main__":
#     # 스트리밍할 영상 경로와 IP 주소 입력
#     # video_path = "/path/to/your/video.mp4"

#     video_path = "/root/workspace/MS-AI_1000/v1.2.1-dev/../test.avi"
#     ip = "117.17.159.118"  # 예시로 로컬 IP 설정

#     # 서버 생성 및 실행
#     server = GstServer(video_path, ip)
#     server.run()


# from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
# from wsdiscovery import QName, Scope
# from onvif import ONVIFCamera
# import socket

# def discover_onvif_devices(timeout=15):
#     """
#     WS-Discovery를 사용하여 네트워크 상의 ONVIF 장치를 검색합니다.
    
#     :param timeout: 검색을 대기할 시간(초)
#     :return: 검색된 장치의 리스트
#     """
#     wsd = WSDiscovery()
#     wsd.start()
    
#     # ONVIF 장치의 서비스 타입 정의
#     onvif_service = QName('http://www.onvif.org/ver10/network/wsdl', 'NetworkVideoTransmitter')
    
#     print("장치를 검색 중입니다...")
#     # ONVIF 서비스 타입으로 장치 검색
#     services = wsd.searchServices(types=[onvif_service], timeout=timeout)
    
#     wsd.stop()
#     return services

# def extract_ip_from_address(address):
#     """
#     서비스 주소(URL)에서 IP 주소를 추출합니다.
    
#     :param address: 서비스 주소 (예: 'http://192.168.1.100:8080/onvif/device_service')
#     :return: IP 주소 (예: '192.168.1.100')
#     """
#     try:
#         # URL에서 호스트 부분 추출
#         host = address.split('/')[2]
#         # 포트 번호 제거
#         ip = host.split(':')[0]
#         return ip
#     except IndexError:
#         return None

# def list_onvif_cameras():
#     """
#     네트워크 상의 ONVIF 호환 IP 카메라 목록을 가져옵니다.
    
#     :return: 카메라 정보 리스트
#     """
#     services = discover_onvif_devices()
#     cameras = []
    
#     for service in services:
#         x_addrs = service.getXAddrs()
#         types = service.getTypes()
#         scopes = service.getScopes()
#         for addr in x_addrs:
#             ip = extract_ip_from_address(addr)
#             if ip:
#                 # 카메라의 호스트 이름 또는 다른 정보 가져오기 (선택 사항)
#                 try:
#                     hostname = socket.gethostbyaddr(ip)[0]
#                 except socket.herror:
#                     hostname = "Unknown"
                
#                 cameras.append({
#                     'ip': ip,
#                     'hostname': hostname,
#                     'types': types,
#                     'scopes': scopes,
#                     'address': addr
#                 })
    
#     return cameras

# def get_camera_details(ip, port=80):
#     """
#     ONVIF 카메라의 세부 정보를 가져옵니다.
    
#     :param ip: 카메라의 IP 주소
#     :param port: ONVIF 서비스 포트 (기본값: 80)
#     :return: 카메라의 세부 정보
#     """
#     try:
#         # ONVIFCamera 객체 생성 (필요한 경우 사용자 이름과 비밀번호 입력)
#         # 만약 카메라가 인증을 필요로 하지 않는다면, 빈 문자열을 사용할 수 있습니다.
#         cam = ONVIFCamera(ip, port, 'username', 'password')  # 사용자 이름과 비밀번호를 실제 값으로 변경하세요.
        
#         # 서비스 객체 가져오기
#         media_service = cam.create_media_service()
        
#         # 프로파일 목록 가져오기
#         profiles = media_service.GetProfiles()
        
#         # 프로파일 이름과 스트림 URI 출력
#         for profile in profiles:
#             token = profile.token
#             stream_uri = media_service.GetStreamUri({'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}}, 'ProfileToken': token})
#             print(f"프로파일: {profile.Name}, RTSP URI: {stream_uri.Uri}")
        
#         return cam
#     except Exception as e:
#         print(f"카메라 {ip}에 연결할 수 없습니다: {e}")
#         return None

# if __name__ == "__main__":
#     cameras = list_onvif_cameras()
#     print(f"발견된 ONVIF 카메라 수: {len(cameras)}\n")
    
#     for idx, cam in enumerate(cameras, start=1):
#         print(f"카메라 {idx}:")
#         print(f"  IP 주소: {cam['ip']}")
#         print(f"  호스트 이름: {cam['hostname']}")
#         print(f"  서비스 유형: {cam['types']}")
#         print(f"  스코프: {cam['scopes']}")
#         print(f"  주소: {cam['address']}")
#         print()
    
#     # 선택적으로, 각 카메라의 세부 정보를 가져올 수 있습니다.
#     # 예를 들어, 첫 번째 카메라의 세부 정보를 가져오려면:
#     if cameras:
#         first_cam_ip = cameras[0]['ip']
#         print(f"첫 번째 카메라({first_cam_ip})의 세부 정보를 가져옵니다...")
#         get_camera_details(first_cam_ip)

# from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery

# # 실제 네트워크 상의 장치 검색
# wsd = WSDiscovery()
# wsd.start()
# services = wsd.searchServices()

# print("Discovered ONVIF Devices:")
# for service in services:
#     print(f"EPR: {service.getEPR()}")
#     print(f"XAddrs: {service.getXAddrs()}")
#     print(f"Scopes: {service.getScopes()}")
# wsd.stop()

# from onvif import ONVIFCamera

# # 카메라 IP 및 포트 수동 설정
# ip = "117.17.159.205"  # 카메라의 IP 주소
# port = 80           # ONVIF 서비스 포트 (일반적으로 80)
# username = "admin"  # ONVIF 사용자 이름
# password = "admin13579"  # ONVIF 비밀번호

# try:
#     camera = ONVIFCamera(ip, port, username, password)
#     print(f"Connected to ONVIF camera at {ip}:{port}")
# except Exception as e:
#     print(f"Failed to connect to ONVIF camera: {e}")

# import socket
# import struct
# import uuid

# def discover_onvif_devices(timeout=2):
#     # WS-Discovery 멀티캐스트 주소와 포트
#     multicast_address = "239.255.255.250"
#     multicast_port = 3702

#     # WS-Discovery 요청 메시지
#     message_id = uuid.uuid4()  # 고유 메시지 ID 생성
#     soap_message = f"""<?xml version="1.0" encoding="UTF-8"?>
#     <Envelope xmlns="http://www.w3.org/2003/05/soap-envelope" xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" xmlns:dn="http://www.onvif.org/ver10/device/wsdl">
#         <Header>
#             <wsa:MessageID>urn:uuid:{message_id}</wsa:MessageID>
#             <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
#             <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
#         </Header>
#         <Body>
#             <Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">
#                 <Types>dn:Device</Types>
#             </Probe>
#         </Body>
#     </Envelope>"""

#     # UDP 소켓 생성 (멀티캐스트용)
#     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
#     sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)  # 멀티캐스트 TTL 설정
#     sock.settimeout(timeout)  # 타임아웃 설정

#     # 멀티캐스트 요청 전송
#     print("Sending WS-Discovery probe...")
#     sock.sendto(soap_message.encode(), (multicast_address, multicast_port))

#     # 응답 수신
#     print("Waiting for responses...")
#     devices = []
#     try:
#         while True:
#             data, addr = sock.recvfrom(4096)  # 응답 수신
#             devices.append((data.decode(), addr))
#     except socket.timeout:
#         pass

#     # 결과 출력
#     print(f"Discovered {len(devices)} ONVIF devices:\n")
#     for response, addr in devices:
#         print(f"Device at {addr[0]}:{addr[1]}:\n{response}\n")

#     sock.close()
#     return devices


# if __name__ == "__main__":
#     discover_onvif_devices()



# import asyncio
# import cv2
# import numpy as np
# import logging
# from fastapi import FastAPI, WebSocket
# from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
# from aiortc.contrib.media import MediaBlackhole, MediaRecorder
# from starlette.responses import HTMLResponse
# from av import VideoFrame

# # 로그 설정
# logging.basicConfig(level=logging.INFO)

# app = FastAPI()
# pcs = set()  # WebRTC PeerConnection 저장소

# # RTSP 스트림 URL (사용자 환경에 맞게 변경)
# RTSP_URL = "rtsp://USER:Admin13579@192.168.0.249/video1"

# class RTSPVideoStreamTrack(VideoStreamTrack):
#     def __init__(self):
#         super().__init__()
#         self.cap = cv2.VideoCapture(RTSP_URL)
    
#     async def recv(self):
#         loop = asyncio.get_event_loop()
#         return await loop.run_in_executor(None, self._read_frame)

#     def _read_frame(self):
#         ret, frame = self.cap.read()

#         print(ret)
#         print(ret)


#         if not ret:
#             # return None
#             pass

#         # OpenCV에서 읽은 frame을 AIORTC VideoFrame으로 변환
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
#         video_frame.pts = None
#         video_frame.time_base = None
#         return video_frame

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     pc = RTCPeerConnection()
#     pcs.add(pc)

#     @pc.on("iceconnectionstatechange")
#     async def on_ice_connection_state_change():
#         if pc.iceConnectionState == "failed":
#             await pc.close()
#             pcs.discard(pc)

#     video_track = RTSPVideoStreamTrack()
#     pc.addTrack(video_track)

#     data = await websocket.receive_json()
#     offer = RTCSessionDescription(sdp=data["sdp"], type=data["type"])
#     await pc.setRemoteDescription(offer)
#     answer = await pc.createAnswer()
#     await pc.setLocalDescription(answer)

#     await websocket.send_json({
#         "sdp": pc.localDescription.sdp,
#         "type": pc.localDescription.type
#     })

# @app.get("/")
# async def index():
#     html_content = open("test.html", "r").read()
#     return HTMLResponse(content=html_content, status_code=200)

# main.py
# from fastapi import FastAPI, Request, Form
# from fastapi.responses import HTMLResponse, StreamingResponse
# from fastapi.staticfiles import StaticFiles
# from fastapi.templating import Jinja2Templates
# import cv2
# import asyncio
# from turbojpeg import TurboJPEG

# app = FastAPI()
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# # RTSP URL 저장을 위한 전역 변수
# current_rtsp_url = None
# cap = None

# jpeg = TurboJPEG()


# async def generate_frames():
#     global cap
#     while True:
#         if cap is not None and cap.isOpened():
#             ret, frame = cap.read()
#             if not ret:
#                 break
#             # _, buffer = cv2.imencode('.jpg', frame)

#             # yield (b'--frame\r\n'
#                 #    b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
#             buffer = jpeg.encode(frame)	
#             yield (
#                 b"--frame\r\n"
#                 b"Content-Type: image/jpeg\r\n\r\n" + buffer + b"\r\n"
#             )

#         await asyncio.sleep(0.01)  # 30ms 대기 (약 30 FPS)

# @app.get("/", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("test.html", {"request": request})

# @app.post("/set_rtsp")
# async def set_rtsp(rtsp_url: str = Form(...)):
#     global current_rtsp_url, cap
#     current_rtsp_url = rtsp_url
#     if cap is not None:
#         cap.release()
#     cap = cv2.VideoCapture(current_rtsp_url)
#     return {"message": "RTSP URL 설정 완료"}

# @app.get("/video_feed")
# async def video_feed():
#     return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

# if __name__ == "__main__" :
#     import uvicorn

#     uvicorn.run(app, host="0.0.0.0", port=65432)


import torch
import numpy as np
from ultralytics import YOLO
import cv2
import time
# cv2.namedWindow("test")

# model = YOLO("./back/weight/yolo/2024-12-31/ms-ai_24-12-31-M.pt")  # load a pretrained model (recommended for training)\
model = YOLO("yolo11l")  # load a pretrained model (recommended for training)\

print("Trying to connect to RTSP...")
url = "rtsp://admin:admin@117.16.130.67:554/stream1"
cap = cv2.VideoCapture(url)

url = "rtsp://admin:admin@117.16.130.68:554/stream1"
cap_2 = cv2.VideoCapture(url)
if not cap.isOpened():
    print("Failed to open video stream")
    exit()

print("RTSP stream opened")

avg_list = []

while True:
    success, frame = cap.read()
    success, frame2 = cap_2.read()

    # if not success:
        # break

    t0 = time.time()

    dets = model.predict(source=[frame], 
                                    imgsz = 640, 
                                    conf = 0.33, 
                                    # classes = [0, 1, 2, 3, 4, 5, 6], 
                                    half = True, 
                                    verbose = False)
                                    
    # dets = model.track(source=[frame], 
    #                                 imgsz = 640, 
    #                                 conf = 0.33, 
    #                                 # classes = [0, 1, 2, 3, 4, 5, 6], 
    #                                 half = True, 
    #                                 verbose = False,
    #                                 persist=True,
    #                                 tracker="botsort.yaml")
                                    
    

    torch.cuda.synchronize()
    avg_list.append(time.time() - t0)
    print(time.time() - t0)

    print(np.mean(np.array(avg_list)))

    cv2.imshow("test", dets[0].plot())

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# import torch
# import numpy as np
# import cv2
# import time
# import supervision as sv
# from rfdetr import RFDETRBase
# from rfdetr.util.coco_classes import COCO_CLASSES

# model = RFDETRBase()

# print("Trying to connect to RTSP...")
# url = "rtsp://admin:admin@117.16.130.67:554/stream1"

# cap = cv2.VideoCapture(url)
# if not cap.isOpened():
#     print("Failed to open video stream")
#     exit()

# print("RTSP stream opened")

# avg_list = []

# while True:
#     success, frame = cap.read()
#     # if not success:
#         # break

#     t0 = time.time()

#     detections = model.predict(frame[:, :, ::-1].copy(), threshold=0.33)


#     torch.cuda.synchronize()
#     avg_list.append(time.time() - t0)

#     print(np.mean(np.array(avg_list)))
#     labels = [
#         f"{COCO_CLASSES[class_id]} {confidence:.2f}"
#         for class_id, confidence
#         in zip(detections.class_id, detections.confidence)
#     ]

#     annotated_frame = frame.copy()
#     annotated_frame = sv.BoxAnnotator().annotate(annotated_frame, detections)
#     annotated_frame = sv.LabelAnnotator().annotate(annotated_frame, detections, labels)

#     cv2.imshow("test", annotated_frame)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()



# import torch
# import numpy as np
# from ultralytics import YOLO
# import cv2
# import time
# import supervision as sv
# from rfdetr import RFDETRBase
# from rfdetr.util.coco_classes import COCO_CLASSES

# # cv2.namedWindow("test")

# # model = YOLO("./back/weight/yolo/2024-12-31/ms-ai_24-12-31-M.pt", task="detect")  # load a pretrained model (recommended for training)\
# yolo_model = YOLO("yolo11m", task="detect")  # load a pretrained model (recommended for training)\
# detr_model = RFDETRBase(resolution=560)


# print("Trying to connect to RTSP...")
# # url = "rtsp://admin:admin@202.30.100.15:554/stream1"
# url = "rtsp://admin:admin@117.16.130.67:554/stream1"


# cap = cv2.VideoCapture(url)
# if not cap.isOpened():
#     print("Failed to open video stream")
#     exit()

# print("RTSP stream opened")

# fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 코덱 설정 (예: XVID, MJPG, H264 등)
# output_file = "output_video.avi"  # 저장할 비디오 파일 이름

# fps = 30.0  # 초당 프레임 수 (FPS)
# frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # 비디오의 너비
# frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # 비디오의 높이

# # VideoWriter 객체 생성 (파일 이름, 코덱, FPS, 해상도)
# out = cv2.VideoWriter(output_file, fourcc, fps, (1280*2, 720))

# avg_list = []

# while True:
#     success, frame = cap.read()
#     frame = cv2.resize(frame, (1280, 720))
#     # if not success:
#         # break

#     t0 = time.time()

#     dets = yolo_model.predict(source=[frame], 
#                                     imgsz = 640, 
#                                     conf = 0.5, 
#                                     # classes = [0, 1, 2, 3, 4, 5, 6], 
#                                     half = False, 
#                                     verbose = False)

    
#     detections = detr_model.predict(frame[:, :, ::-1].copy(), threshold=0.5)

#     torch.cuda.synchronize()
#     avg_list.append(time.time() - t0)

#     # print(np.mean(np.array(avg_list)))

#     labels = [
#         f"{COCO_CLASSES[class_id]} {confidence:.2f}"
#         for class_id, confidence
#         in zip(detections.class_id, detections.confidence)
#     ]

#     annotated_frame = frame.copy()
#     # annotated_frame = dets[0].plot()
#     annotated_frame = sv.BoxAnnotator().annotate(annotated_frame, detections)
#     annotated_frame = sv.LabelAnnotator().annotate(annotated_frame, detections, labels)

#     test = cv2.hconcat([dets[0].plot(), annotated_frame])

#     cv2.imshow("test", test)
#     out.write(test)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# out.release()
# cv2.destroyAllWindows()