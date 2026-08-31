import time
import datetime

ip = "192.168.0.2"
port = 8554
url = 'rtsp://' + ip + ':' + str(port) +'/'

# url = 'rtsp://admin:admin13579@117.17.159.196:554/stream2 ! rtph264depay ! h264parse ! omxh264dec ! appsink max-buffers=1 drop=true'
# url = 'rtsp://admin:Admin13579@117.17.159.221:554/video1'
# url = 'rtsp://admin:admin13579@117.17.159.141:554/video1'
# url = 'rtsp://admin:1234@117.17.159.143:554/'


# url = 'rtsp://117.17.159.143/video1'

url = 'rtsp://admin:1234@117.17.159.143/video1?profile=high'

# instance = vlc.Instance("--no-ts-trust-pcr", "--ts-seek-percent", "--no-video")
# instance = vlc.Instance()


# # Create a media player with the default instance
# player = instance.media_list_player_new()

# # Load the media file
# media = instance.media_list_new([url])
# player.set_media_list(media)

# player.play()
# # while player.get_state() != vlc.State.Ended:
# while True:
#     #print(player.get_media_player().get_media().get_meta(0))
#     #print(str(datetime.timedelta(seconds=player.get_media_player().get_time() / 1000, microseconds=0)).split(".")[0])
#     time.sleep(1)


import cv2
import numpy as np
cap = cv2.VideoCapture(url)


while True:
    success, im = cap.read()

    if success:
        cv2.imshow("img",im)
        key = cv2.waitKey(1)

        if key == 27 :
            break


cv2.destroyAllWindows()
cap.release()
