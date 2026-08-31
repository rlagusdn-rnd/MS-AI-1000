import sys
import cv2
import numpy as np
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import torch
import time
import random

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

kernel_erosion_1 = cv2.getStructuringElement(cv2.MORPH_RECT,(4,4))
kernel_erosion_2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,7))
# kernel_erosion_2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))

kernel_dilation_1 = cv2.getStructuringElement(cv2.MORPH_RECT,(1,1))
kernel_dilation_2 = cv2.getStructuringElement(cv2.MORPH_RECT,(20,20))

class Img_Buffer(object):
    def __init__(self):
        self.img = None
        self.frame_num = 0

    def set_input_data(self, data):
        self.frame_num = data[0]
        self.img = data[1]
    
    def get_img_data(self):
        return self.frame_num, self.img


class Person_Img_Buffer():
    def __init__(self, stack_size = 24):
        self.id_dict = {}
        self.stack_size = stack_size

    def gen_new_id(self, id, img_data):
        self.id_dict[id] = {"img_buffer" : [img_data],
                       "last_time" : time.time(),
                       "equal_id" : [],
                       "status" : None}

    def img_updata(self, id, img_data):
        self.id_dict[id]["img_buffer"].append(img_data)
        self.id_dict[id]["last_time"] = time.time()

        if len(self.id_dict[id]["img_buffer"]) > self.stack_size:
            self.id_dict[id]["img_buffer"].pop(0)

    def refresh_id_list(self):
        delete_list = []
        for id in self.id_dict.keys():
            if time.time() - self.id_dict[id]["last_time"] > 10:
                delete_list.append(id)

        for id in delete_list:
            del self.id_dict[id]


class Colors:
    # Ultralytics color palette https://ultralytics.com/
    def __init__(self):
        # hex = matplotlib.colors.TABLEAU_COLORS.values()
        hexs = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB',
                '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
        self.palette = [self.hex2rgb(f'#{c}') for c in hexs]
        self.n = len(self.palette)

    def __call__(self, i, bgr=False):
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):  # rgb order (PIL)
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))    

def video_capture(data_buffer, video_source):
    cap = cv2.VideoCapture(video_source)
    frame_num = 0

    total_frame = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frame / 2)

    while True:
        ret, rgb_ori = cap.read()
        rgb_ori = cv2.resize(rgb_ori, (1280, 720))
        if ret:
            frame_num += 1

            data_buffer.set_input_data([frame_num, rgb_ori])

            # 이미지에 글씨 추가
            # cv2.imshow("realtime_img", cv2.resize(rgb_ori, (0, 0), fx = 0.5, fy = 0.5))
            # key = cv2.waitKey(30)
            time.sleep(1/30)
            # if key == 27:
                # cap.release()
                # cv2.destroyAllWindows()

        else:
            print("End of video")
            cap.release()
            break

def get_extand_box(xyxy):
    x1 = xyxy[0]
    x2 = xyxy[2]
    y1 = xyxy[1]
    y2 = xyxy[3]

    width = x2 - x1
    height = y2 - y1

    if width > height:
        width *= 1.5
        height *= 3

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    elif width < height :
        width *= 3
        height *= 1.5

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    elif width == height :
        width *= 1.5
        height *= 1.5

        x1 -= width / 2 
        x2 += width / 2
        y1 -= height / 2
        y2 += height / 2

    if y1 < 0: y1 = 0
    if x1 < 0: x1 = 0

    return x1, x2, y1, y2

def resize_with_padding(image, target_height = 224, target_width = 224):
    height, width, _ = image.shape

    # Calculate the aspect ratio of the original image
    aspect_ratio = width / height

    # Calculate the target aspect ratio
    target_aspect_ratio = target_width / target_height

    # Calculate the new dimensions for resizing while maintaining the original aspect ratio
    if aspect_ratio > target_aspect_ratio:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    # Resize the image to the new dimensions
    resized_image = cv2.resize(image, (new_width, new_height))

    # Calculate the amount of padding required on each side
    pad_height = max(0, target_height - new_height)
    pad_width = max(0, target_width - new_width)

    # Calculate the top, bottom, left, and right padding sizes
    top_pad = pad_height // 2
    bottom_pad = pad_height - top_pad
    left_pad = pad_width // 2
    right_pad = pad_width - left_pad

    # Create a border around the image with zero padding
    padded_image = cv2.copyMakeBorder(
        resized_image, top_pad, bottom_pad, left_pad, right_pad, cv2.BORDER_CONSTANT, value=(0, 0, 0)
    )

    # Resize the padded image to the target size (224x224)
    resized_padded_image = cv2.resize(padded_image, (target_width, target_height))

    return resized_padded_image


def clip_coords(boxes, shape):
    # Clip bounding xyxy bounding boxes to image shape (height, width)
    boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, shape[1])  # x1, x2
    boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, shape[0])  # y1, y2

def iou(box_0, box_1):
    b0x_0, b0y_0, b0x_1 ,b0y_1 = box_0
    b1x_0, b1y_0, b1x_1 ,b1y_1 = box_1

    min_x = np.argmin([b0x_0,b1x_0])
    min_y = np.argmin([b0y_0,b1y_0])

    if min_x == 0 and min_y == 0:
        if ((b0x_0 <= b1x_0 <= b0x_1) or (b0x_0 <= b1x_1 <= b0x_1)) and ((b0y_0 <= b1y_0 <= b0y_1) or (b0y_0 <= b1y_1 <= b0y_1)):
            return True
    if min_x == 0 and min_y == 1:
        if ((b0x_0 <= b1x_0 <= b0x_1) or (b0x_0 <= b1x_1 <= b0x_1)) and ((b1y_0 <= b0y_0 <= b1y_1) or (b1y_0 <= b0y_1 <= b1y_1)):
            return True
    if min_x == 1 and min_y == 0:
        if ((b1x_0 <= b0x_0 <= b1x_1) or (b1x_0 <= b0x_1 <= b1x_1)) and ((b0y_0 <= b1y_0 <= b0y_1) or (b0y_0 <= b1y_1 <= b0y_1)):
            return True
    if min_x == 1 and min_y == 1:
        if ((b1x_0 <= b0x_0 <= b1x_1) or (b1x_0 <= b0x_1 <= b1x_1) ) and ((b1y_0 <= b0y_0 <= b1y_1) or (b1y_0 <= b0y_1 <= b1y_1) ):
            return True

    return False

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


def get_detection_point(bboxes):
    detection_center_point = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]

    detection_point_top = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.1)]
    detection_point_bottom = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.5), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.95)]
    detection_point_left = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.1), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]
    detection_point_right = [int(bboxes[0] + (bboxes[2] - bboxes[0]) * 0.9), int(bboxes[1] + (bboxes[3] - bboxes[1]) * 0.5)]

    return [detection_point_top, detection_point_bottom, detection_point_left, detection_point_right]


def object_detection(img, img_ori, device, model, augment, names, colors, conf_thres, iou_thres, classes_list = None, draw_box = False): # YOLO
    pass

def tracking_process(tracker, im, boxes, person_img_buffer, resize_transforms, names, colors, draw_box = False):
    tracks = tracker.update(boxes, im) # --> (x, y, x, y, id, conf, cls, ind)
    if tracks.shape[0] != 0:
        for i in range(len(tracks)):
            xyxy = tracks[i, 0:4].astype('int') # float64 to int
            id = tracks[i, 4].astype('int') # float64 to int
            conf = tracks[i, 5]
            cls = tracks[i, 6].astype('int') # float64 to int
            # ind = tracks[i, 7].astype('int') # float64 to int
            color_cls = cls
            
            if id in person_img_buffer.id_dict.keys():
                    status = person_img_buffer.id_dict[id]["status"]
                    if status == "fall down":
                        color_cls = 10
                    elif status == "fight":
                        color_cls = 30
            else:
                status = None
                
            label = None if False else f"{id} {names[cls]} {conf:.2f} {status}"

            try:
                if cls == 0:
                    crop_img = im[int(xyxy[1]):int(xyxy[3]), int(xyxy[0]):int(xyxy[2])]
                    if crop_img.shape[0] > 0 and crop_img.shape[1] > 0:
                        img_resize = resize_with_padding(crop_img, resize_transforms)

                        if id not in person_img_buffer.id_dict.keys():
                            person_img_buffer.gen_new_id(id, img_resize)
                        else :
                            person_img_buffer.img_updata(id, img_resize)

            except Exception as e:
                print(e)
                continue

            if draw_box:
                plot_one_box(xyxy, im, label=label, color=colors(int(color_cls)), line_thickness=2) # 박스 그리기
    return im

def person_action_classification(person_img_buffer, img_extraction_model, cls_model, device):
    for id in person_img_buffer.id_dict.keys():
        if len(person_img_buffer.id_dict[id]["img_buffer"]) == 24:
            img_list = person_img_buffer.id_dict[id]["img_buffer"]
            rgb_stack_input = torch.cat(img_list, dim = 1).to(device).unsqueeze(0)

            with torch.no_grad():
                img_feature = img_extraction_model(rgb_stack_input)
                pred = cls_model(img_feature)
                status = np.argmax(pred.cpu())

                if status == 0:
                    person_img_buffer.id_dict[id]["status"] = "normal"
                
                elif status == 1:
                    person_img_buffer.id_dict[id]["status"] = "fall down"
                
                elif status == 2:
                    person_img_buffer.id_dict[id]["status"] = "fight"


    torch.cuda.synchronize()
    
def remove_out_of_BBox(camera_info_dict, bbox, person_conf_score = 0.33, fire_conf_score = 0.05):
    new_person_bbox = []
    new_non_person_bbox = []

    for i in range(len(bbox)) : 
        if len(bbox[i]) != 6:
            continue

        x1, y1, x2, y2 = bbox[i][0], bbox[i][1], bbox[i][2], bbox[i][3]
        conf = bbox[i][4]
        cls = bbox[i][5]

        add_bbox_flag = False

        x1 = int(x1)
        x2 = int(x2)
        y1 = int(y1)
        y2 = int(y2)

        for camera_id, camera_info in camera_info_dict.items():
            if add_bbox_flag : break
            for detect_type, roi_list in camera_info["detect_area"].items():
                if add_bbox_flag : break
                for roi in roi_list:
                    if cv2.pointPolygonTest(roi, (int((x1 + x2)/2) , int((y1 + y2)/2)), False) == 1 :

                        if cls == 0 and conf > person_conf_score:
                            new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        elif cls == 1 and conf > fire_conf_score:
                            new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        add_bbox_flag = True
                        break

                    elif cv2.pointPolygonTest(roi, (x1, y1), False) == 1 :
                        if cls == 0 and conf > person_conf_score:
                            new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        elif cls == 1 and conf > fire_conf_score:
                            new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        add_bbox_flag = True
                        break

                    elif cv2.pointPolygonTest(roi, (x2, y1), False) == 1 :
                        if cls == 0 and conf > person_conf_score:
                            new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        elif cls == 1 and conf > fire_conf_score:
                            new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        add_bbox_flag = True
                        break

                    elif cv2.pointPolygonTest(roi, (x1, y2), False) == 1 :
                        if cls == 0 and conf > person_conf_score:
                            new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        elif cls == 1 and conf > fire_conf_score:
                            new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        add_bbox_flag = True
                        break

                    elif cv2.pointPolygonTest(roi, (x2, y2), False) == 1 :
                        if cls == 0 and conf > person_conf_score:
                            new_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        elif cls == 1 and conf > fire_conf_score:
                            new_non_person_bbox.append([x1, y1, x2, y2, conf, cls])
                        add_bbox_flag = True
                        break

    if len(new_person_bbox) == 0 and len(new_non_person_bbox) == 0:
        return torch.tensor([[],[],[],[],[],[]]).view([0,6]).numpy(), torch.tensor([[],[],[],[],[],[]]).view([0,6]).numpy()

    elif len(new_person_bbox) == 0 and len(new_non_person_bbox):
        return torch.tensor([[],[],[],[],[],[]]).view([0,6]).numpy(), np.array(new_non_person_bbox)

    elif len(new_person_bbox) and len(new_non_person_bbox) == 0:
        return np.array(new_person_bbox), torch.tensor([[],[],[],[],[],[]]).view([0,6]).numpy()
    
    return np.array(new_person_bbox), np.array(new_non_person_bbox)