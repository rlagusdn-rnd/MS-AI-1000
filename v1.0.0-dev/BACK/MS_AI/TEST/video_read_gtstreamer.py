import cv2
import gi
import numpy as np

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

    def __init__(self, appsink_name = "camera1"):
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
        # self.video_source = 'rtspsrc location=rtsp://admin:admin13579@117.17.159.141/video1s2 latency=10'
        self.video_source = 'rtspsrc location=rtsp://admin:1234@117.17.159.143/video1 latency=10'

        # Cam -> CSI-2 -> H264 Raw (YUV 4-4-4 (12bits) I420)
        # self.video_codec = '! application/x-rtp, encoding-name=(string)H264, payload=96 ! rtph264depay ! h264parse ' # ! avdec_h264 ! queue '
        # self.video_codec = '! application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264 '
        self.video_codec = '! application/x-rtp, encoding-name=(string)H264, payload=96 ! rtph264depay ! h264parse '
        # self.video_codec = "! x264enc ! avdec_h264 ! videoconvert "
        # Python don't have nibble, convert YUV nibbles (4-4-4) to OpenCV standard BGR bytes (8-8-8)
        self.video_decode =  '! decodebin ! videoconvert ! video/x-raw,format=(string)BGR ! videoconvert'

        # Create a sink to get data
        self.video_sink_conf = f'! appsink name={appsink_name} emit-signals=true sync=false max-buffers=10 drop=true'
            # f'! appsink name={appsink_name} emit-signals=true sync=false '
        
        print(self.video_source)

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
        self._frame = cv2.resize(self._frame, (640,480))
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


if __name__ == '__main__':
    import time
    # Create the video object
    # Add port= if is necessary to use a different one
    video = Video_Buffer()
    time.sleep(1)

    while True:
        # Wait for the next frame

        if not video.frame_available():
            print("-------------------")
            print("No frame available")
            continue
        frame = video.get_frame()
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break