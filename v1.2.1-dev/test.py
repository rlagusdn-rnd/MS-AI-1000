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

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GObject

class RTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, video_path):
        super(RTSPMediaFactory, self).__init__()
        self.video_path = video_path

    def do_create_element(self, url):
        # GStreamer pipeline to stream a video file
        pipeline_str = f"filesrc location={self.video_path} ! decodebin ! videoconvert ! x264enc tune=zerolatency ! rtph264pay config-interval=1 name=pay0 pt=96"
        return Gst.parse_launch(pipeline_str)


class GstServer:
    def __init__(self, video_path, ip):
        GObject.threads_init()
        Gst.init(None)

        # RTSP 서버 초기화
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service("65432")  # 포트 설정

        # 비디오 파일을 소스로 하는 RTSP 서버 생성
        self.factory = RTSPMediaFactory(video_path)
        self.factory.set_shared(True)

        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/video", self.factory)

        # RTSP 서버 실행
        self.server.attach(None)
        print(f"RTSP server is running at rtsp://{ip}:65432/video")

    def run(self):
        loop = GObject.MainLoop()
        try:
            loop.run()
        except KeyboardInterrupt:
            print("Interrupted. Exiting.")


if __name__ == "__main__":
    # 스트리밍할 영상 경로와 IP 주소 입력
    # video_path = "/path/to/your/video.mp4"

    video_path = "/root/workspace/MS-AI_1000/v1.2.1-dev/../test.avi"
    ip = "117.17.159.118"  # 예시로 로컬 IP 설정

    # 서버 생성 및 실행
    server = GstServer(video_path, ip)
    server.run()