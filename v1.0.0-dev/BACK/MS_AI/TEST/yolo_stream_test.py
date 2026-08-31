import cv2
import numpy as np
from pathlib import Path
import sys

FILE = Path(__file__).resolve()
sys.path.append(str(FILE.parents[0]))  # add ROOT to PATH
sys.path.append(str(FILE.parents[1]))  # add ROOT to PATH
sys.path.append(str(FILE.parents[1]) + "/yolo_tracking")  # add ROOT to PATH


from yolo_tracking.ultralytics import YOLO
from yolo_tracking import boxmot

import torch
import time
import datetime

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class Video_Buffer():
    """BlueRov video capture class constructor
    Attributes:
        port (int): Video UDP port
        video_codec (string): Source h264 parser
        video_decode (string): Transform YUV (12bits) to BGR (24bits)
        video_pipe (object): GStreamer top-level pipeline
        video_sink (object): Gstreamer sink element
        video_sink_conf (string): Sink configuration
        video_source (string): Udp source ip and port
    """

    def __init__(self, ip, appsink_name):
        """Summary
        Args:
            port (int, optional): UDP port
        """

        """
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 latency=100 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 ! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264 ! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert ! appsink emit-signals=true sync=false max-buffers=3 drop=true
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 ! decodebin ! queue ! autovideosink sync=false recover-policy=keyframe
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 ! rtph264depay ! h264parse ! decodebin ! autovideosink
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 latency=10 ! queue ! rtpjitterbuffer latency=10 ! rtph264depay ! avdec_h264 ! autovideosink sync=false
        rtspsrc location=rtsp://admin:admin13579@117.17.159.197:554/stream2 latency=10 ! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264 ! decodebin ! videoconvert ! video/x-raw ! videoconvert ! appsink emit-signals=true sync=false max-buffers=2 drop=true"""


        Gst.init(None)

        self._frame = None
        # [Software component diagram](https://www.ardusub.com/software/components.html)
        self.video_source = 'rtspsrc location={} latency=10'.format(ip)
        # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        # self.video_codec = '! application/x-rtp, encoding-name=(string)H264, payload=96 ! rtph264depay ! h264parse ' # ! avdec_h264 ! queue '
        # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264 '
        self.video_codec = '! rtph264depay ! h264parse ! avdec_h264 ! queue'
        # self.video_codec = "! x264enc ! avdec_h264 ! videoconvert "
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode = '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR'
        # Create a sink to get data
        self.video_sink_conf = f'! appsink name={appsink_name} emit-signals=true sync=false max-buffers=10 drop=true'
            # f'! appsink name={appsink_name} emit-signals=true sync=false '

        self.video_pipe = None
        self.video_sink = None
        self.appsink_name = appsink_name

        self.run()

    def start_gst(self, config=None):
        """ Start gstreamer pipeline and sink
        Pipeline description list e.g:
            [
                'videotestsrc ! decodebin', \
                '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                '! appsink'
            ]
        Args:
            config (list, optional): Gstreamer pileline description list
        """

        if not config:
            config = \
                [
                    'videotestsrc ! decodebin',
                    '! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert',
                    '! appsink'
                ]

        command = ' '.join(config)
        self.video_pipe = Gst.parse_launch(command)
        self.video_pipe.set_state(Gst.State.PLAYING)
        self.video_sink = self.video_pipe.get_by_name(self.appsink_name)

    @staticmethod
    def gst_to_opencv(sample):
        """Transform byte array into np array
        Args:
            sample (TYPE): Description
        Returns:
            TYPE: Description
        """
        buf = sample.get_buffer()
        caps = sample.get_caps()
        array = np.ndarray(
            (
                caps.get_structure(0).get_value('height'),
                caps.get_structure(0).get_value('width'),
                3
            ),
            buffer=buf.extract_dup(0, buf.get_size()), dtype=np.uint8)
        return array

    def get_frame(self):
        """ Get Frame
        Returns:
            iterable: bool and image frame, cap.read() output
        """
        return self._frame

    def frame_available(self):
        """Check if frame is available
        Returns:
            bool: true if frame is available
        """
        return type(self._frame) != type(None)

    def run(self):
        try:
            """ Get frame to update _frame
            """

            self.start_gst(
                [
                    self.video_source,
                    self.video_codec,
                    self.video_decode,
                    self.video_sink_conf
                ])

            self.video_sink.connect('new-sample', self.callback)

            bus = self.video_pipe.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.on_message)
        except Exception as e :
            print(e)
            pass

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR or t == Gst.MessageType.EOS:
            self.video_pipe.set_state(Gst.State.NULL)
            self.run()

    def callback(self, sink):
        sample = sink.emit('pull-sample')
        new_frame = self.gst_to_opencv(sample)
        self._frame = new_frame

        return Gst.FlowReturn.OK
    
    def stop(self):
        """Stop the pipeline"""
        self.video_pipe.set_state(Gst.State.NULL)

def save_image_text(img, save_path, img_name,frame_num, text): # 시험 모듈 (지연이랑, 박스 카운트)
    img_path = save_path + img_name.format(frame_num)

device = "cuda:0" if torch.cuda.is_available() else "cpu"

# model = YOLO('../weight/yolo/yolov8m_1280_90_3070.engine')  # load a pretrained model (recommended for training)\
model = YOLO('./weight/yolo/ms-ai-L-2403_60.pt')  # load a pretrained model (recommended for training)\
model.to(device)
tracker = boxmot.BoTSORT(model_weights = Path("./weight/ReID/osnet_x0_25_market.pt"),
                         device = model.device,
                         fp16 = True
                         )

# source = "./videos/falldown_2.mp4"
source = "rtsp://admin:1234@117.17.159.2/video16" #2
# source = "rtsp://admin:admin13579@117.17.159.146:554/stream2" #1
# source = "rtsp://admin:admin13579@117.17.159.149:554/stream2"  #3
# source = "rtsp://admin:admin13579@117.17.159.221:554/video1"



video_streamer = Video_Buffer(source, "appsink_name_1")

# vid = cv2.VideoCapture(source)

# total_frame = vid.get(cv2.CAP_PROP_FRAME_COUNT)
# vid.set(cv2.CAP_PROP_POS_FRAMES, total_frame / 2)

color = (0, 0, 255)  # BGR
thickness = 2
fontscale = 1
frame_num = 0
conf_score = 0.01
save_txt = ""

while True:
    t0 = time.time()

    frame_num += 1
    # ret, im = vid.read()
    
    if video_streamer.frame_available():
        im = video_streamer.get_frame()
    else:
        im = np.zeros((720, 1280, 3), np.uint8)
        print(f"video is empty")
    
    # dets = model.predict(source=im, imgsz = 1280, conf = 0.20, iou = 0.5, classes = [0], half = True, verbose=False)
    # dets = model.predict(source=im, imgsz = 1280, conf = 0.01, iou = 0.5, half = False, verbose=False)
    # results = model.track(source=im, imgsz = 1280, conf = 0.01, iou = 0.5, half = False, verbose=False, persist=True, \
    #                       tracker='./yolo_tracking/ultralytics/cfg/trackers/bytetrack.yaml')

    dets = model.predict(source=im, imgsz = 1280, conf = conf_score, iou = 0.5, classes = [0, 1], half = True, verbose=False)
    boxes = dets[0].boxes.data.cpu().numpy().astype(float)

    tracks = tracker.update(boxes, im)    

    result_img = dets[0].plot()
    print(tracks)

    # boxes = dets[0].boxes.data.cpu().numpy().astype(float)
    # tracks = tracker.update(boxes, im) # --> (x, y, x, y, id, conf, cls, ind)
    # if tracks.shape[0] != 0:
    #     xyxys = tracks[:, 0:4].astype('int') # float64 to int
    #     ids = tracks[:, 4].astype('int') # float64 to int
    #     confs = tracks[:, 5]
    #     clss = tracks[:, 6].astype('int') # float64 to int
    #     inds = tracks[:, 7].astype('int') # float64 to int

    # # print bboxes with their associated id, cls and conf
    #     for xyxy, id, conf, cls in zip(xyxys, ids, confs, clss):
    #         im = cv2.rectangle(
    #             im,
    #             (xyxy[0], xyxy[1]),
    #             (xyxy[2], xyxy[3]),
    #             color,
    #             thickness
    #         )
    #         cv2.putText(
    #             im,
    #             f'id: {id}, conf: {np.round(conf,2)}, c: {dets[0].names[cls]}',
    #             (xyxy[0], xyxy[1]-10),
    #             cv2.FONT_HERSHEY_SIMPLEX,
    #             fontscale,
    #             color,
    #             thickness
    #         )

    cv2.imshow("frame", cv2.resize(result_img, (0, 0), fx = 0.5, fy = 0.5))
    # cv2.imshow("frame", result_img)

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

with open(f"./images/{frame_num}.txt", "w") as f:
    f.write(save_txt)
# video_streamer.stop()
cv2.destroyAllWindows()