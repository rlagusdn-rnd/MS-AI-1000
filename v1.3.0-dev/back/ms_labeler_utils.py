import os
from pathlib import Path
import cv2
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode
from tqdm import tqdm
import random
import shutil
import gc
import sys
import time

from transformers import (                         
                          AutoTokenizer, 
                          AutoModel, 
)

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

def convert_box(box:list) -> list:
    """Convert box from (class, x, y, w, h, score) to (x1, y1, x2, y2, score)."""
    cls, x, y, w, h, score = box
    return [cls, x, y, x + w, y + h, score]

def non_max_suppression(boxes, iou_threshold):
    if len(boxes) == 0:
        return []

    # Sort boxes by the yc (confidence score)
    boxes = sorted(boxes, key=lambda x: x[2], reverse=True)
    
    selected_boxes = []

    while boxes:
        current_box = boxes.pop(0)
        selected_boxes.append(current_box)
        boxes = [box for box in boxes if iou(current_box, box) < iou_threshold]

    return selected_boxes

def nms(boxes, iou_threshold=0.5):
    """Perform Non-Maximum Suppression (NMS) on the boxes."""
    # Convert all boxes to (x1, y1, x2, y2, score)
    boxes = [convert_box(box) for box in boxes]
    
    # Sort boxes by score in descending order
    boxes = sorted(boxes, key=lambda x: x[4], reverse=True)
    
    selected_boxes = []
    
    while boxes:
        # Select the box with the highest score
        current_box = boxes.pop(0)
        selected_boxes.append(current_box)
        
        boxes = [box for box in boxes if iou(current_box, box) < iou_threshold]
    
    return selected_boxes


def iou(box1, box2):
    """Calculate Intersection over Union (IoU) of two boxes."""
    x1, y1, x2, y2 = box1[1:5]
    xx1, yy1, xx2, yy2 = box2[1:5]
    
    inter_x1 = max(x1, xx1)
    inter_y1 = max(y1, yy1)
    inter_x2 = min(x2, xx2)
    inter_y2 = min(y2, yy2)
    
    inter_area = max(0, inter_x2 - inter_x1) * max(0, inter_y2 - inter_y1)
    box1_area = (x2 - x1) * (y2 - y1)
    box2_area = (xx2 - xx1) * (yy2 - yy1)
    
    return inter_area / float(box1_area + box2_area - inter_area)

def merge_boxes(box1, box2):
    """Merge two boxes by averaging their coordinates and taking the maximum score."""
    x1 = min(box1[1], box2[1])
    y1 = min(box1[2], box2[2])
    # x2 = max(box1[2], box2[2])
    # y2 = max(box1[3], box2[3])
    x2 = min(box1[3], box2[3])
    y2 = min(box1[4], box2[4])
    score = max(box1[5], box2[5])
    return [box1[0], x1, y1, x2, y2, score]

def nms_test(bbox_list_1, bbox_list_2, iou_threshold=0.8):
    merge_list = []
    unmerge_list = []

    # bbox_list_1 = [convert_box(box) for box in bbox_list_1]
    # bbox_list_2 = [convert_box(box) for box in bbox_list_2]

    # Create a copy to keep track of which boxes have been merged
    merged_1 = [False] * len(bbox_list_1)
    merged_2 = [False] * len(bbox_list_2)
    
    for i, box1 in enumerate(bbox_list_1):
        for j, box2 in enumerate(bbox_list_2):
            if iou(box1, box2) >= iou_threshold:
                merged_box = merge_boxes(box1, box2)
                merge_list.append(merged_box)
                merged_1[i] = True
                merged_2[j] = True
    
    for i, box in enumerate(bbox_list_1):
        if not merged_1[i]:
            unmerge_list.append(box)
    
    for j, box in enumerate(bbox_list_2):
        if not merged_2[j]:
            unmerge_list.append(box)
    
    return merge_list, unmerge_list


def plot_one_box(x, img, color=None, label=None, line_thickness=3, fill_color = False):
    # Plots one bounding box on image img
    tl = line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1  # line/font thickness
    c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
    cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
    
    if fill_color:
        alpha = 0.3
        overlay = img.copy()
        cv2.rectangle(overlay, c1, c2, color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    if label:
        tf = max(tl - 1, 1)  # font thickness
        t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(img, label, (c1[0], c1[1] - 2), 0, tl / 3, [225, 255, 255], thickness=tf, lineType=cv2.LINE_AA)


def get_img_buffer(video_path:str) -> dict:
    cap = cv2.VideoCapture(video_path)
    frame_num = 0

    img_buffer = {}

    while True:
        ret, img = cap.read()
        
        if ret == False: break
        
        frame_num += 1

        # if frame_num % 10 == 0:
        if frame_num % 20 == 0:

            img_buffer[len(img_buffer)] = img

    return img_buffer

def save_final_dataset(event_name:str, img_buffer:dict, label_buffer:dict, data_save_dir:str) -> None:
    event_name = event_name[:-4]

    img_save_dir = os.path.join(data_save_dir, event_name, "images")
    label_save_dir = os.path.join(data_save_dir, event_name, "labels")

    if label_buffer:
        os.makedirs(img_save_dir, exist_ok=True)
        os.makedirs(label_save_dir, exist_ok=True)
    
        for i, img in img_buffer.items():
            if i % 3 == 0:
                label_txt = ""
                cv2.imwrite(f"{img_save_dir}/{event_name}_{str(0) * (4 - len(str(i)))}{i}.png", img)
    
                width, heigth = img.shape[1], img.shape[0]

                for cls, x1, y1, x2, y2, score in label_buffer[i]:
                    x1 = x1/width
                    x2 = x2/width
                    y1 = y1/heigth
                    y2 = y2/heigth
    
                    w = np.round(x2 - x1, 3)
                    h = np.round(y2 - y1, 3)
    
                    ncx = np.round(x1 + w / 2,3)
                    ncy = np.round(y1 + h / 2,3)
    
                    label_txt += f"{cls} {ncx} {ncy} {w} {h}\n"
                if label_txt:
                    label_name = f"{label_save_dir}/{event_name}_{str(0) * (4 - len(str(i)))}{i}.txt"
                    
                    with open(label_name, "w") as f:
                        f.write(label_txt)
            

def get_yolo_label(model, buffer:dict) -> dict:
    total_label = {}

    for frame_num, img in buffer.items():
        label = []
        # if frame_num % 3 == 0:
        if frame_num % 1.5 == 0:
            heigth, width = img.shape[0], img.shape[1]

            pred = model(img, 
                        imgsz = 640, 
                        conf = 0.22, 
                        iou = 0.5,
                        verbose=False
                        )

            boxes = pred[0].boxes.data.cpu().numpy().astype(float)

            del pred

            # for i in range(len(boxes)):
            for i, boxes in enumerate(boxes):
                if len(boxes) != 0:
                    x1, y1, x2, y2 = boxes[0:4].astype('int') # float64 to int
                    # conf = data[4]
                    cls = boxes[-1].astype('int')
                    # ind = tracks[i, 7].astype('int') # float64 to int

                    label.append([cls, x1, y1, x2, y2, boxes[4]])

        total_label[frame_num] = label

    return total_label

def make_square_bbox(bbox, img, extend_ratio = 1.5):
    label, x1, y1, x2, y2, conf = bbox
    img_height, img_width = img.shape[:2]

    # Calculate width, height, and maximum side length
    width = x2 - x1
    height = y2 - y1

    if (img_width < width * extend_ratio) or (img_height < height * extend_ratio):
        extend_ratio = 3

    max_side = max(width, height) * extend_ratio  # Increase by 1.3 times
    
    # Calculate the center of the bounding box
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # Calculate new coordinates
    new_x1 = center_x - max_side / 2
    new_y1 = center_y - max_side / 2
    new_x2 = center_x + max_side / 2
    new_y2 = center_y + max_side / 2
    
    # Ensure the new coordinates are within image boundaries
    new_x1 = max(new_x1, 0)
    new_y1 = max(new_y1, 0)
    new_x2 = min(new_x2, img_width)
    new_y2 = min(new_y2, img_height)
    
    return [new_x1, new_y1, new_x2, new_y2, conf, label]

def build_transform(input_size):
    IMAGENET_MEAN = (0.485, 0.456, 0.406)
    IMAGENET_STD = (0.229, 0.224, 0.225)

    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform


def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def dynamic_preprocess(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def check_LLM(model_path:str, img_buffer:dict, label:dict, verbose:bool = False) -> dict:

    llm_model = AutoModel.from_pretrained(model_path,
                                            torch_dtype=torch.bfloat16,
                                            low_cpu_mem_usage=True,
                                            trust_remote_code=True).eval().cuda()

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)


    transform = build_transform(input_size=448)

    generation_config_1 = dict(num_beams=1,
                            max_new_tokens=16,
                            do_sample=False,
                            )
    
    generation_config_2 = dict(num_beams=1,
                            max_new_tokens=1,
                            do_sample=False,
                            )
    for frame_num, img in img_buffer.items():
        bboxes = label[frame_num]
        new_label = []
        
        for cls, x1, y1, x2, y2, score in bboxes:
            res_2 = None
            extend_x1, extend_y1, extend_x2, extend_y2, score, cls = make_square_bbox([cls, x1, y1, x2, y2, score], img, extend_ratio=10)
            cropped_img_extend = img[int(extend_y1) : int(extend_y2), int(extend_x1) : int(extend_x2)]
            pil_img = Image.fromarray(cropped_img_extend).convert('RGB')
            images = dynamic_preprocess(pil_img, image_size=448, use_thumbnail=True, max_num=6)
            pixel_values_1 = [transform(image) for image in images]
            pixel_values_1 = torch.stack(pixel_values_1).to(torch.bfloat16).cuda()

            question = '<image>\nPlease describe the image in detail?'

            res, history = llm_model.chat(tokenizer, pixel_values_1, question, generation_config_1, history=None, return_history=True)

            del res, pixel_values_1

            new_x1, new_y1, new_x2, new_y2, score, cls = make_square_bbox([cls, x1, y1, x2, y2, score], img, extend_ratio = 1.2)
            cropped_img = img[int(new_y1) : int(new_y2), int(new_x1) : int(new_x2)]

            pil_img = Image.fromarray(cropped_img).convert('RGB')
            images = dynamic_preprocess(pil_img, image_size=448, use_thumbnail=True, max_num=6)
            pixel_values_2 = [transform(image) for image in images]
            pixel_values_2 = torch.stack(pixel_values_2).to(torch.bfloat16).cuda()

            question = "<image>\nDo you see person in this image?"

            res = llm_model.chat(tokenizer, pixel_values_2, question, generation_config_2, history=history, return_history=False).lower()


            if "yes" in res:
                new_label.append([cls, x1, y1, x2, y2, score])
                # print("ADD person bbox")


            if verbose:
                test_img = img.copy()
                # cv2.imshow(f"cropped_img_extend", cropped_img_extend)
                cv2.rectangle(test_img, (int(extend_x1), int(extend_y1)), (int(extend_x2), int(extend_y2)), (0,0,255), thickness=2, lineType=cv2.LINE_AA)
                cv2.rectangle(test_img, (int(new_x1), int(new_y1)), (int(new_x2), int(new_y2)), (255,0,0), thickness=2, lineType=cv2.LINE_AA)
                cv2.rectangle(test_img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), thickness=2, lineType=cv2.LINE_AA)
                
                cv2.imshow(f"example", test_img)

                print("-----------------------")
                print("question 2 : ",res)
                if res_2 is not None:
                    print("question 3 : ",res_2)

                cv2.waitKey(1)

                # cv2.destroyAllWindows()
            
            del pixel_values_2, history, images, cropped_img, cropped_img_extend

        label[frame_num] = new_label

    del llm_model, tokenizer
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.synchronize()

    return label

def get_zero_shot_label(processor, model, device, buffer) -> dict:
    total_label = {}

    for frame_num, img in buffer.items():
        label_list = []

        # if frame_num % 3 == 0:
        if frame_num % 1.5 == 0:

            text = "person. car. dog. cat. tree."

            pil_img = Image.fromarray(img.astype('uint8'), 'RGB')

            inputs = processor(images=pil_img, 
                               text=text, 
                               return_tensors="pt").to(device)

            with torch.no_grad():
                outputs = model(**inputs)

                results = processor.post_process_grounded_object_detection(
                    outputs,
                    inputs.input_ids,
                    box_threshold=0.1,
                    text_threshold=0.60,
                    target_sizes=[pil_img.size[::-1]]
                )

                del inputs

            for i, boxes in enumerate(results[0]["boxes"].tolist()):
                if results[0]["labels"][i] == "person":
                    label_list.append([0] + boxes + [results[0]["scores"][i]])

            label_list = merge_overlapping_boxes(label_list, iou_threshold = 0.5)

        total_label[frame_num] = label_list

    return total_label

def get_bboxes_from_binary_img(mask):
    mask_uint8 = np.squeeze(mask).astype(np.uint8)  # 데이터 타입 변환
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boundingRect(contour) for contour in contours]

def save_temp_img(video_name, img_buffer, img_save_dir):
    if os.path.exists(img_save_dir):
        shutil.rmtree(img_save_dir)
    os.makedirs(img_save_dir, exist_ok=True)

    video_name = video_name[:-4]

    for frame_num, img in img_buffer.items():
        cv2.imwrite(f"{img_save_dir}/{frame_num}.jpg", img)

# def SAM_label(img_buffer, label, video_name):
#     from sam2.build_sam import build_sam2_video_predictor
#     from contextlib import redirect_stdout, redirect_stderr



#     with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
#         with open(os.devnull, 'w') as fnull:
#             with redirect_stdout(fnull), redirect_stderr(fnull):

#     # with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                
#                 temp_img_path = os.path.join(os.getcwd(), "..", "backup", "dataset", "temp", "images")
#                 save_temp_img(video_name, 
#                             img_buffer, 
#                             img_save_dir = temp_img_path)
            
#                 sam2_checkpoint = os.path.join(os.getcwd(),"back", "weight", "segment_anything_2", "sam2_hiera_large.pt")
#                 model_cfg = "./sam2_hiera_l.yaml"
#                 predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
#                 inference_state = predictor.init_state(video_path=temp_img_path, offload_video_to_cpu = True)
                
#                 label_dict = {}
#                 final_label = {}
                
#                 for frame_num, bbox_list in label.items():
#                     if bbox_list:
#                         for cls, x1, y1, x2, y2, score in bbox_list:
#                             t0 = time.time()
#                             predictor.reset_state(inference_state)

#                             ann_frame_idx = frame_num  # the frame index we interact with
#                             ann_obj_id = int(frame_num)  # give a unique id to each object we interact with (it can be any integers)

#                             points = np.array([[(x2 + x1)/2, (y2 + y1)/2]], dtype=np.float32)
#                             labels = np.array([1], np.int32)
#                             _, out_obj_ids, out_mask_logits = predictor.add_new_points(inference_state=inference_state,
#                                                                                         frame_idx=ann_frame_idx,
#                                                                                         obj_id=ann_obj_id,
#                                                                                         points=points,
#                                                                                         labels=labels,
#                                                                                         )
#                             # img_test = img_buffer[frame_num].copy()
#                             # cv2.circle(img_test, (int((x2 + x1)/2), int((y2 + y1)/2)), 5, (255, 0, 0), thickness= -1)
#                             # cv2.imshow('Point Example', img_test)
#                             # cv2.waitKey(0)
#                             # cv2.destroyAllWindows()

#                             video_segments = {} 
                    
#                             for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
#                                 video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.5).cpu().numpy()
#                                                                 for i, out_obj_id in enumerate(out_obj_ids)
#                                                                 }
                                
#                             for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, reverse=True):
#                                 video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.5).cpu().numpy()
#                                                                 for i, out_obj_id in enumerate(out_obj_ids)
#                                                                 }
                            
#                             for out_frame_idx in video_segments:
#                                 for out_obj_id, out_mask in video_segments[out_frame_idx].items():
#                                     bboxes = get_bboxes_from_binary_img(out_mask)

#                                     if out_frame_idx not in label_dict:
#                                         label_dict[out_frame_idx] = []

#                                     if len(bboxes) > 0:
#                                         for x, y, w, h in bboxes:
#                                             if w * h >= 100: # 너무 작은 bbox는 제거
#                                                 label_dict[out_frame_idx].append([0, x, y, x+w, y+h, 1])

#                             del _, out_obj_ids, out_mask_logits, video_segments

#                             # print(time.time() - t0)

#                 for frame_num, box_list in label_dict.items():
#                     final_label[frame_num] = merge_overlapping_boxes(box_list, iou_threshold = 0.3)

#                 try:
#                     os.remove(temp_img_path)
#                 except:
#                     pass

                
#                 del inference_state, predictor

#                 # torch.cuda.reset_max_memory_allocated()
#                 # torch.cuda.reset_max_memory_cached()
#                 torch.cuda.empty_cache()

#                 gc.collect()

#     return final_label

def SAM_label(img_buffer, label, video_name):
    from sam2.build_sam import build_sam2_video_predictor
    from contextlib import redirect_stdout, redirect_stderr

    with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
        with open(os.devnull, 'w') as fnull:
            with redirect_stdout(fnull), redirect_stderr(fnull):

    # with torch.autocast(device_type='cuda', dtype=torch.bfloat16):
                
                temp_img_path = os.path.join(os.getcwd(), "..", "backup", "dataset", "temp", "images")
                save_temp_img(video_name, 
                            img_buffer, 
                            img_save_dir = temp_img_path)
            
                sam2_checkpoint = os.path.join(os.getcwd(),"back", "weight", "segment_anything_2", "sam2_hiera_large.pt")
                model_cfg = "./sam2_hiera_l.yaml"
                predictor = build_sam2_video_predictor(model_cfg, sam2_checkpoint)
                inference_state = predictor.init_state(video_path=temp_img_path, offload_video_to_cpu = True)
                
                label_dict = {}
                final_label = {}
                
                for frame_num, bbox_list in label.items():
                    predictor.reset_state(inference_state)

                    if bbox_list:
                        for i , (cls, x1, y1, x2, y2, score) in enumerate(bbox_list):
                            t0 = time.time()

                            ann_frame_idx = frame_num  # the frame index we interact with
                            ann_obj_id = int(i)  # give a unique id to each object we interact with (it can be any integers)

                            box = np.array([int(x1), int(y1), int(x2), int(y2)])
                            _, out_obj_ids, out_mask_logits = predictor.add_new_points_or_box(inference_state=inference_state,
                                                                                    frame_idx=ann_frame_idx,
                                                                                    obj_id=ann_obj_id,
                                                                                    box=box,
                                                                                )

                        video_segments = {} 
                
                        for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state):
                            video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.5).cpu().numpy()
                                                            for i, out_obj_id in enumerate(out_obj_ids)
                                                            }
                            
                        for out_frame_idx, out_obj_ids, out_mask_logits in predictor.propagate_in_video(inference_state, reverse=True):
                            video_segments[out_frame_idx] = {out_obj_id: (out_mask_logits[i] > 0.5).cpu().numpy()
                                                            for i, out_obj_id in enumerate(out_obj_ids)
                                                            }
                        
                        for out_frame_idx in video_segments:
                            for out_obj_id, out_mask in video_segments[out_frame_idx].items():
                                bboxes = get_bboxes_from_binary_img(out_mask)

                                if out_frame_idx not in label_dict:
                                    label_dict[out_frame_idx] = []

                                if len(bboxes) > 0:
                                    for x, y, w, h in bboxes:
                                        if w * h >= 100: # 너무 작은 bbox는 제거
                                            label_dict[out_frame_idx].append([0, x, y, x+w, y+h, 1])

                        del _, out_obj_ids, out_mask_logits, video_segments

                            # print(time.time() - t0)

                for frame_num, box_list in label_dict.items():
                    final_label[frame_num] = merge_overlapping_boxes(box_list, iou_threshold = 0.33)

                try:
                    os.remove(temp_img_path)
                except:
                    pass

                
                del inference_state, predictor

                # torch.cuda.reset_max_memory_allocated()
                # torch.cuda.reset_max_memory_cached()
                torch.cuda.empty_cache()

                gc.collect()

    return final_label

def train_model(yolo_weight_path:str) -> None:
    from ultralytics import YOLO
    from pathlib import Path
    from datetime import datetime
    import yaml

    data = {
            'path': f'{os.getcwd()}/../backup/dataset',
            'train': ['train.txt'],  # train images (relative to 'path')
            'val': ['val.txt'],  # val images (relative to 'path')
            'test': [],  # test images (optional)
            'names': {
                    0: 'person',
                    1: 'fire'
                    }
        }

    # YAML 파일 생성
    with open(f'{os.getcwd()}/back/cfg/main.yaml', 'w') as file:
        yaml.dump(data, file, default_flow_style=False)

    #train data move to main dataset

    # current_time = datetime.now().strftime("%Y%m%d")

    model = YOLO(yolo_weight_path)
    results = model.train(data=f'{os.getcwd()}/back/cfg/main.yaml',
                          project = "./train",
                          name = f"last",
                            exist_ok = True,
                            epochs = 5,
                            imgsz = 640,
                            batch = 32 ,
                            device = '0',
                            save_period = -1,
                            freeze = 10,
                            plots = False,
                            workers = 2,
                            cache = "disk"
                            # cache = False
                            )     

    del model

def create_dataset_list(dataset_path):
    # train_txt = "train.txt"
    # val_txt = "val.txt"
    train_txt = ""
    val_txt = ""

    folder_list = os.listdir(dataset_path)

    for folder_name in folder_list:
        if folder_name not in ["train.txt", "val.txt"]:
            train_img_path = os.path.join(dataset_path, folder_name, "train", "images")
            val_img_path = os.path.join(dataset_path, folder_name, "val", "images")

            train_img_list = os.listdir(train_img_path)

            try:
                val_img_list = os.listdir(val_img_path)
            except:
                val_img_list = []

            if train_img_list:
                train_img_list = sorted(train_img_list)
                for img_name in train_img_list:
                    save_path = os.path.join("./", folder_name, "train", "images")
                    img_path = os.path.join(save_path, img_name)
                    train_txt += f"{img_path}\n"

            if val_img_list:
                val_img_list = sorted(val_img_list)
                for img_name in val_img_list:
                    save_path = os.path.join("./", folder_name, "val", "images")
                    img_path = os.path.join(save_path, img_name)
                    val_txt += f"{img_path}\n"

    if len(train_txt) > 0:
        with open("./dataset/train.txt", "w") as f:
            f.write(train_txt)

    if len(val_txt) > 0:
        with open("./dataset/val.txt", "w") as f:
            f.write(val_txt)
    

def iou_2(box1, box2):
    x1_min, y1_min, x1_max, y1_max = box1[1:5]
    x2_min, y2_min, x2_max, y2_max = box2[1:5]

    inter_x_min = max(x1_min, x2_min)
    inter_x_max = min(x1_max, x2_max)
    inter_y_min = max(y1_min, y2_min)
    inter_y_max = min(y1_max, y2_max)

    if inter_x_min < inter_x_max and inter_y_min < inter_y_max:
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area
    else:
        return 0.0

def merge_boxes_2(box1, box2):
    # x1, y1, w1, h1 = box1[1:5]
    # x2, y2, w2, h2 = box2[1:5]
    x1_min, y1_min, x1_max, y1_max = box1[1:5]
    x2_min, y2_min, x2_max, y2_max = box2[1:5]

    # x1_min, y1_min, x1_max, y1_max = x1, y1, x1 + w1, y1 + h1
    # x2_min, y2_min, x2_max, y2_max = x2, y2, x2 + w2, y2 + h2

    new_x_min = min(x1_min, x2_min)
    new_y_min = min(y1_min, y2_min)
    new_x_max = max(x1_max, x2_max)
    new_y_max = max(y1_max, y2_max)
    new_conf = max(box1[5], box2[5])

    return [box1[0], new_x_min, new_y_min, new_x_max, new_y_max, new_conf]
    # return [box1[0], new_x_min, new_y_min, new_x_max - new_x_min, new_y_max - new_y_min, new_conf]

def merge_boxes_avg(box1, box2):
    # x1, y1, w1, h1 = box1[1:5]
    # x2, y2, w2, h2 = box2[1:5]
    x1_min, y1_min, x1_max, y1_max = box1[1:5]
    x2_min, y2_min, x2_max, y2_max = box2[1:5]

    # x1_min, y1_min, x1_max, y1_max = x1, y1, x1 + w1, y1 + h1
    # x2_min, y2_min, x2_max, y2_max = x2, y2, x2 + w2, y2 + h2

    new_x_min = np.mean([x1_min, x2_min])
    new_y_min = np.mean([y1_min, y2_min])
    new_x_max = np.mean([x1_max, x2_max])
    new_y_max = np.mean([y1_max, y2_max])
    new_conf = np.mean([box1[5], box2[5]])

    return [box1[0], new_x_min, new_y_min, new_x_max, new_y_max, new_conf]

def merge_overlapping_boxes(boxes:dict, iou_threshold:float) -> list:
    if len(boxes) == 0:
        return []

    merged_boxes = []
    while boxes:
        box = boxes.pop(0)
        to_merge = [box]
        for other_box in boxes[:]:
            if iou_2(box, other_box) >= iou_threshold:
                to_merge.append(other_box)
                boxes.remove(other_box)

        # Merge all to_merge boxes
        while len(to_merge) > 1:
            box1 = to_merge.pop(0)
            box2 = to_merge.pop(0)
            merged_box = merge_boxes_avg(box1, box2)
            to_merge.append(merged_box)

        merged_boxes.append(to_merge[0])

    return merged_boxes



def create_dataset_list(dataset_path:str, NVR_IP:str) -> None:
    train_txt = ""
    val_txt = ""

    folder_list = os.listdir(dataset_path)

    for folder_name in folder_list:
        if folder_name not in ["train.txt", "val.txt", "temp"]:
            if folder_name == NVR_IP:
                camera_name_path = os.path.join(dataset_path, folder_name)
                camera_name_list = os.listdir(camera_name_path)

                for camera_name in camera_name_list:
                    date_path = os.path.join(camera_name_path, camera_name)
                    date_list = sorted(os.listdir(date_path))

                    for date in date_list:
                        event_path = os.path.join(date_path, date)
                        event_list = sorted(os.listdir(event_path))

                        for event in event_list:
                            train_img_path = os.path.join(event_path, event, "images")
                            train_img_list = os.listdir(train_img_path)

                            if train_img_list:
                                train_img_list = sorted(train_img_list)
                                for img_name in train_img_list:
                                    save_path = os.path.join("./", folder_name, camera_name, date, event, "images", img_name)
                                    train_txt += f"{save_path}\n"

            elif folder_name == "before":
                date_path = os.path.join(dataset_path, folder_name)
                date_list = sorted(os.listdir(date_path))
                
                for date in date_list:
                    train_img_path = os.path.join(date_path, date, "images")
                    train_img_list = os.listdir(train_img_path)

                    half_length = len(train_img_list) // 2
                    selected_train_img = random.sample(train_img_list, half_length)

                    if selected_train_img:
                        selected_train_img = sorted(selected_train_img)
                        for img_name in selected_train_img:
                            save_path = os.path.join("./", date_path, date, "images", img_name)
                            train_txt += f"{save_path}\n"

            else:
                train_img_path = os.path.join(dataset_path, folder_name, "train", "images")
                val_img_path = os.path.join(dataset_path, folder_name, "val", "images")

                train_img_list = os.listdir(train_img_path)

                half_length = len(train_img_list) // 2
                selected_train_img = random.sample(train_img_list, half_length)

                try:
                    val_img_list = os.listdir(val_img_path)
                except:
                    val_img_list = []

                if selected_train_img:
                    selected_train_img = sorted(selected_train_img)
                    for img_name in selected_train_img:
                        save_path = os.path.join("./", folder_name, "train", "images", img_name)
                        train_txt += f"{save_path}\n"

                if val_img_list:
                    val_img_list = sorted(val_img_list)
                    for img_name in val_img_list:
                        save_path = os.path.join("./", folder_name, "val", "images", img_name)
                        val_txt += f"{save_path}\n"

    if len(train_txt) > 0:
        with open("../backup/dataset/train.txt", "w") as f:
            f.write(train_txt)

    if len(val_txt) > 0:
        with open("../backup/dataset/val.txt", "w") as f:
            f.write(val_txt)

def convert_int8(dataset_path:str) -> list:
    from ultralytics import YOLO
    from datetime import datetime

    date = datetime.now().strftime("%Y-%m-%d")  # 예: 2024-07-25

    weight_path = os.path.join(os.getcwd(), "train", "last", "weights")
    weight_list = os.listdir(weight_path)

    val_txt = ""
    val_img_path = os.path.join(dataset_path, "coco", "val", "images")

    val_img_list = os.listdir(val_img_path)

    selected_val_img = random.sample(val_img_list, 500)

    if selected_val_img:
        selected_val_img = sorted(selected_val_img)
        for img_name in selected_val_img:
            save_path = os.path.join("./", "coco", "val", "images", img_name)
            val_txt += f"{save_path}\n"

    if len(val_txt) > 0:
        with open("../backup/dataset/val.txt", "w") as f:
            f.write(val_txt)

    cfg_path = os.path.join(os.getcwd(), "back", "cfg", "main.yaml")

    model_name_list = []

    if "last.pt" in weight_list:
        for i in range(1,5):
            model_name = f"ms-ai_{date[2:]}-M{i}"

            cmd = f"cp {weight_path}/last.pt {weight_path}/{model_name}.pt"
            os.system(cmd)

            model_path = os.path.join(os.getcwd(), "train", "last", "weights", f"{model_name}.pt")

            model = YOLO(model_path)
            # model = YOLO("./weight/yolo/pt/ms-ai2401-finetune_M.pt")

            # PyTorch to TensorRT
            # model.export(format='engine', device=0, half=True, batch = 1)
            model.export(format='engine', device=0, int8 = True, batch = i, data = cfg_path)
            # model.export(format='engine', device=0, int8 = True, batch = i)


            cmd = f"rm -rf {weight_path}/{model_name}.cache"
            os.system(cmd)
            cmd = f"rm -rf {weight_path}/{model_name}.onnx"
            os.system(cmd)
            cmd = f"rm -rf {weight_path}/{model_name}.pt"
            os.system(cmd)

            model_name_list.append(os.path.join(os.getcwd(), "train", "last", "weights", f"{model_name}.engine"))

    model_name = f"ms-ai_{date[2:]}-M"
    cmd = f"cp {weight_path}/last.pt {weight_path}/{model_name}.pt"
    os.system(cmd)

    cmd = f"rm -rf {weight_path}/last.pt"
    os.system(cmd)

    model_name_list.append(os.path.join(os.getcwd(), "train", "last", "weights", f"{model_name}.pt"))

    os.system("chmod 777 -R ./")

    return model_name_list

def move_dataset_list(dataset_path:str, NVR_IP:str) -> None:
    camera_name_path = os.path.join(dataset_path, NVR_IP)
    camera_name_list = os.listdir(camera_name_path)

    for camera_name in camera_name_list:  
        date_path = os.path.join(camera_name_path, camera_name)
        date_list = sorted(os.listdir(date_path))

        for date in date_list:
            img_data_path = os.path.join(dataset_path, "before", date, "images")
            labels_data_path = os.path.join(dataset_path, "before", date, "labels")

            os.makedirs(img_data_path, exist_ok=True)
            os.makedirs(labels_data_path, exist_ok=True)

            event_path = os.path.join(date_path, date)
            event_list = sorted(os.listdir(event_path))

            for event in event_list:
                train_img_path = os.path.join(event_path, event, "images")
                train_img_list = os.listdir(train_img_path)

                if train_img_list:
                    train_img_list = sorted(train_img_list)
                    for img_name in train_img_list:
                        if img_name.split(".")[-1] == "png":
                            img_path = os.path.join(dataset_path, NVR_IP, camera_name, date, event, "images", img_name)
                        # cmd = f"mv {img_path} {img_data_path}/"
                        # os.system(cmd)

                            try:
                                shutil.move(img_path, img_data_path)
                                
                                label_path = os.path.join(dataset_path, NVR_IP, camera_name, date, event, "labels", img_name[:-4]+".txt")
                                # cmd = f"mv {label_path} {labels_data_path}/"
                                # os.system(cmd)
                                shutil.move(label_path, labels_data_path)

                            except :
                                pass
    
    cmd = f"rm -rf {os.path.join(dataset_path, NVR_IP)}"
    os.system(cmd)
    

def remove_npy() -> None:
    import glob
    npy_files = glob.glob(os.path.join(os.getcwd(), "..", "backup", "dataset", '**', '*.npy'), recursive=True)
    cache_files = glob.glob(os.path.join(os.getcwd(), "..", "backup", "dataset", '**', '*.cache'), recursive=True)

    for file_path in npy_files:
        try:
            os.remove(file_path)
            # print(f"파일 '{file_path}'이(가) 삭제되었습니다.")
        except Exception as e:
            print(f"파일 '{file_path}'을(를) 삭제하는 중 오류가 발생했습니다: {e}")

    for file_path in cache_files:
        try:
            os.remove(file_path)
            # print(f"파일 '{file_path}'이(가) 삭제되었습니다.")
        except Exception as e:
            print(f"파일 '{file_path}'을(를) 삭제하는 중 오류가 발생했습니다: {e}")