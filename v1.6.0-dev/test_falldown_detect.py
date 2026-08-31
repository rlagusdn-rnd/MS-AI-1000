# """
# Falldown 검출 테스트 모듈
# - OpenCV VideoCapture로 영상 로드
# - YOLO로 사람 객체 검출
# - 검출된 사람 crop
# - SigLip으로 텍스트 유사도 비교
# - 유사도 결과 출력
# """

# import cv2
# cv2.namedWindow("frame", cv2.WINDOW_NORMAL)
# cv2.resizeWindow("frame", 1280, 720)
# import numpy as np
# import torch
# from PIL import Image
# from pathlib import Path
# import time
# import os
# import json
# from datetime import datetime
# from ultralytics import YOLO
# from transformers import SiglipProcessor, SiglipModel
# import boxmot

# def check_stop_person(bbox, trajectory):
#     """
#     사람이 멈춰있는지 확인
    
#     Args:
#         bbox: 현재 bbox [x1, y1, x2, y2]
#         trajectory: 이동 경로 리스트 [(x, y), (x, y), ...]
        
#     Returns:
#         bool: 멈춰있으면 True, 아니면 False
#     """
#     if len(trajectory) < 2:
#         return False
    
#     start_pts = trajectory[0]
#     end_pts = trajectory[-1]
    
#     distance_pts = np.array(end_pts) - np.array(start_pts)
    
#     # bbox 너비와 높이
#     w = bbox[2] - bbox[0]
#     h = bbox[3] - bbox[1]
    
#     # 시작점과 끝점의 거리가 bbox 크기의 1/3 이하면 멈춘 것으로 판단
#     if abs(distance_pts[0]) < w/3 and abs(distance_pts[1]) < h/3:
#         return True
#     else:
#         return False


# def get_center_point(bbox):
#     """bbox의 중심점 계산"""
#     x1, y1, x2, y2 = bbox
#     center_x = (x1 + x2) / 2
#     center_y = (y1 + y2) / 2
#     return (center_x, center_y)


# def adjust_coordinates_and_crop(im, x1, y1, x2, y2):
#     """
#     bbox를 정사각형으로 조정하고 최소 크기를 보장하여 crop
    
#     Args:
#         im: 원본 이미지
#         x1, y1, x2, y2: bbox 좌표
        
#     Returns:
#         crop_img: 조정된 crop 이미지 (최소 448x448)
#     """
#     # 이미지 크기 가져오기
#     h, w = im.shape[:2]
    
#     # 현재 bbox의 너비와 높이 계산
#     width = x2 - x1
#     height = y2 - y1
    
#     # 더 긴 쪽을 기준으로 정사각형 만들기
#     max_side = max(width, height)
#     center_x = (x1 + x2) / 2
#     center_y = (y1 + y2) / 2
    
#     # 최소 크기 448x448 보장
#     min_size = 448
#     if max_side < min_size:
#         max_side = min_size
    
#     # 정사각형 bbox 계산
#     half_side = max_side / 2
#     x1_new = center_x - half_side
#     y1_new = center_y - half_side
#     x2_new = center_x + half_side
#     y2_new = center_y + half_side
    
#     # 이미지 경계를 벗어나지 않도록 조정
#     x1_new = max(0, int(x1_new))
#     y1_new = max(0, int(y1_new))
#     x2_new = min(w, int(x2_new))
#     y2_new = min(h, int(y2_new))
    
#     # 이미지 크롭
#     crop_img = im[y1_new:y2_new, x1_new:x2_new]
    
#     # 최종 크기가 448x448보다 작은 경우 리사이즈
#     if crop_img.shape[0] < min_size or crop_img.shape[1] < min_size:
#         crop_img = cv2.resize(crop_img, (min_size, min_size))
    
#     return crop_img


# class FalldownDetectTester:
#     def __init__(self, video_path, yolo_model_path="yolo11n.pt", siglip_model_path="../weights/SigLip_512", save_path="./result"):
#         """
#         Args:
#             video_path: 테스트할 영상 파일 경로
#             yolo_model_path: YOLO 모델 경로
#             siglip_model_path: SigLip 모델 경로
#             save_path: 검출 결과 저장 경로
#         """
#         self.video_path = video_path
#         self.yolo_model_path = yolo_model_path
#         self.siglip_model_path = siglip_model_path
#         self.save_path = save_path
        
#         # 모델 초기화
#         self.yolo_model = None
#         self.siglip_model = None
#         self.siglip_processor = None
        
#         # falldown 검출용 텍스트
#         # self.texts = [
#         #     "a photo of person collapsed on floor",
#         #     "a photo of person fallen down on floor",
#         #     "a photo of person walked on floor", 
#         #     "a photo of standing person on floor", 
#         #     "a photo of sitting person on floor",
#         #     "a person collapsed on their hands and knees",
#         #     "a person on all fours after a fall",
#         #     "a person crouching on the floor after falling"

#         # ]

#         self.texts = [
#             "a photo of person collapsed on floor",
#             "a person collapsed on their hands and knees",
#             "a person crouching on the floor after falling",

#             "a photo of walking person on floor", 
#             "a photo of standing person on floor", 
#             "a photo of sitting person on floor",
#         ]
        
#         # falldown 검출 기록 저장
#         self.falldown_detections = []
        
#         # 각 track ID별 trajectory 저장 (이동 경로 추적)
#         self.person_trajectories = {}
        
#         # 각 track ID별 falldown 카운트 저장
#         self.falldown_counts = {}
        
#         # 이미 알림을 보낸 track ID 저장
#         self.falldown_alerted = set()
        
#         self._load_models()
    
#     def _load_models(self):
#         """YOLO와 SigLip 모델 로드"""
#         print("=" * 80)
#         print("모델 로딩 시작...")
#         print("=" * 80)
        
#         # YOLO 모델 로드
#         print(f"\n[1/2] YOLO 모델 로딩: {self.yolo_model_path}")
#         self.yolo_model = YOLO(self.yolo_model_path)
#         print("✓ YOLO 모델 로딩 완료")
        
#         # SigLip 모델 로드
#         print(f"\n[2/2] SigLip 모델 로딩: {self.siglip_model_path}")
#         siglip_path = str(os.getcwd()) + "/" + self.siglip_model_path

#         from transformers import BitsAndBytesConfig
        
#         quantization_config = BitsAndBytesConfig(load_in_4bit=True)

#         self.siglip_model = SiglipModel.from_pretrained(
#             siglip_path,
#             # attn_implementation="flash_attention_2",
#             # torch_dtype=torch.float16,
#             quantization_config=quantization_config,
#             device_map="auto",
#             attn_implementation="sdpa"
#         )
#         self.siglip_processor = SiglipProcessor.from_pretrained(siglip_path)
#         print("✓ SigLip 모델 로딩 완료")

#         self.tracker = boxmot.BotSort(reid_weights = Path(os.getcwd() + "/../weights/ReID/osnet_ain_x1_0_msmt17.pt"),
#                                      device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu"),
#                                      half=True,
#                                     per_class=False,
#                                     track_high_thresh=0.4,       # 낮춘 값
#                                     track_low_thresh=0.05,       # 낮춘 값
#                                     new_track_thresh=0.5,        # 낮춘 값
#                                     track_buffer=300,             # 늘린 값
#                                     match_thresh=0.7,            # 낮춘 값
#                                     proximity_thresh=0.4,        # 낮춘 값
#                                     appearance_thresh=0.2,       # 낮춘 값
#                                     cmc_method="ecc",
#                                     frame_rate=30,
#                                     fuse_first_associate=True,   # 변경된 값
#                                     with_reid=True,)

#         print("\n" + "=" * 80)
#         print("모든 모델 로딩 완료!")
#         print("=" * 80 + "\n")
    
#     def detect_siglip_similarity(self, person_img):
#         """
#         SigLip을 사용하여 이미지와 텍스트 유사도 계산
        
#         Args:
#             person_img: 사람 crop 이미지 (numpy array, BGR)
            
#         Returns:
#             probs_list: 각 텍스트에 대한 유사도 확률 리스트
#         """
#         # OpenCV BGR을 PIL RGB로 변환
#         img_rgb = cv2.cvtColor(person_img, cv2.COLOR_BGR2RGB)
#         pil_img = Image.fromarray(img_rgb.astype('uint8'), 'RGB')
        
#         # SigLip 처리
#         inputs = self.siglip_processor(
#             text=self.texts, 
#             images=pil_img, 
#             padding="max_length",
#             max_length=64,
#             return_tensors="pt"
#         )
#         inputs = inputs.to(self.siglip_model.device)

#         outputs = self.siglip_model(**inputs)
#         logits_per_image = outputs.logits_per_image
#         probs = torch.sigmoid(logits_per_image)

#         # 결과를 리스트로 변환
#         probs_list = probs[0].cpu().tolist()
        
#         # 메모리 정리
#         del img_rgb, pil_img, inputs, outputs, logits_per_image, probs
#         torch.cuda.empty_cache()
        
#         return probs_list
    
#     def _print_and_save_falldown_results(self):
#         """falldown 검출 결과 출력 및 파일 저장"""
#         print("\n" + "=" * 80)
#         print("🚨 FALLDOWN 검출 결과")
#         print("=" * 80)
        
#         if len(self.falldown_detections) == 0:
#             print("✅ falldown이 검출되지 않았습니다.")
#             print("=" * 80 + "\n")
#             return
        
#         print(f"총 {len(self.falldown_detections)}건의 falldown이 검출되었습니다.\n")
        
#         # 검출 결과 상세 출력
#         for i, detection in enumerate(self.falldown_detections, 1):
#             print(f"[{i}] 프레임 {detection['frame_number']} ({detection['time_sec']:.2f}초)")
#             print(f"    - 영상: {detection['video_name']}")
#             print(f"    - Track ID: {detection['track_id']}")
#             print(f"    - Trajectory 길이: {detection['trajectory_length']}개")
#             print(f"    - Falldown 카운트: {detection['falldown_count']}회")
#             print(f"    - Falldown 확률: {detection['falldown_prob']*100:.2f}%")
#             print(f"    - 판정 근거: {detection['detection_reason']}")
#             print()
        
#         # JSON 파일로 저장
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         video_name_no_ext = os.path.splitext(os.path.basename(self.video_path))[0]
#         output_filename = f"{self.save_path}/falldown_detection_{video_name_no_ext}_{timestamp}.json"
        
#         try:
#             with open(output_filename, 'w', encoding='utf-8') as f:
#                 json.dump({
#                     "video_path": self.video_path,
#                     "video_name": os.path.basename(self.video_path),
#                     "total_detections": len(self.falldown_detections),
#                     "timestamp": timestamp,
#                 }, f, indent=2, ensure_ascii=False)
            
#             print(f"💾 검출 결과가 파일로 저장되었습니다: {output_filename}")
#         except Exception as e:
#             print(f"⚠ 파일 저장 실패: {e}")
        
#         print("=" * 80 + "\n")
    
#     def run_test(self, skip_frames=30, max_frames=None, conf_threshold=0.33):
#         """
#         영상에서 falldown 검출 테스트 실행
        
#         Args:
#             skip_frames: 프레임 스킵 간격 (성능 향상용)
#             max_frames: 처리할 최대 프레임 수 (None이면 전체)
#             conf_threshold: YOLO 검출 신뢰도 임계값
#         """
#         # 테스트 시작 전 초기화
#         self.falldown_detections = []
#         self.person_trajectories = {}
#         self.falldown_counts = {}
#         self.falldown_alerted = set()
#         self.tracker.reset()
        
#         print("=" * 80)
#         print("Falldown 검출 테스트 시작")
#         print("=" * 80)
#         print(f"영상 경로: {self.video_path}")
#         print(f"프레임 스킵: {skip_frames}")
#         print(f"YOLO 신뢰도 임계값: {conf_threshold}")
#         print("=" * 80 + "\n")
        
#         # 영상 캡처 객체 생성
#         cap = cv2.VideoCapture(self.video_path)
        
#         if not cap.isOpened():
#             raise ValueError(f"영상을 열 수 없습니다: {self.video_path}")
        
#         # 영상 정보
#         fps = cap.get(cv2.CAP_PROP_FPS)
#         total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
#         width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
#         print(f"영상 정보:")
#         print(f"  - 해상도: {width}x{height}")
#         print(f"  - FPS: {fps:.2f}")
#         print(f"  - 전체 프레임 수: {total_frames}")
#         print(f"  - 영상 길이: {total_frames/fps:.2f}초\n")
        
#         frame_count = 0
#         processed_count = 0
#         person_detection_count = 0
        
#         stop_flag = False
#         try:
#             while True:
#                 ret, frame = cap.read()
                
#                 if not ret or stop_flag:
#                     break

#                 frame = cv2.resize(frame, (1280, 720))
                
#                 # cv2.imshow("frame", frame)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     break

#                 # 최대 프레임 수 체크
#                 if max_frames and processed_count >= max_frames:
#                     print(f"\n최대 프레임 수({max_frames}) 도달. 테스트 종료.")
#                     break
                
#                 processed_count += 1
#                 current_time = frame_count / fps
                
#                 # print(f"\n{'='*80}")
#                 # print(f"[프레임 {frame_count}/{total_frames}] 시간: {current_time:.2f}초")
#                 # print(f"{'='*80}")
                
#                 # YOLO로 사람 검출 (class 0 = person)
#                 t0 = time.time()
#                 results = self.yolo_model(frame, classes=[0], imgsz=1280, half=True, conf=0.33, verbose=False)
                
#                 # Tracker 업데이트
#                 if len(results) > 0 and len(results[0].boxes) > 0:
#                     dets = results[0].boxes.data.cpu().numpy()
#                     tracks = self.tracker.update(dets, frame)
#                 else:
#                     tracks = np.empty((0, 8))
                
#                 yolo_time = time.time() - t0
#                 plot_img = frame.copy()
                
#                 # 검출 결과 처리
#                 if len(tracks) > 0:
#                     for idx, track in enumerate(tracks):
#                         # bbox 좌표 추출
#                         (x1, y1, x2, y2, id_, conf, cls, ind) = track

#                         plot_img = cv2.rectangle(plot_img, (int(x1), int(y1)), (int(x2), int(y2)), (0,255,0), 2)
#                         plot_img = cv2.putText(plot_img, f"{id_}", (int(x1), int(y1)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)


#                         # bbox와 track ID
#                         x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                         track_id = int(id_)
#                         bbox = [x1, y1, x2, y2]
                        
#                         # trajectory 업데이트 (중심점 기록)
#                         center_point = get_center_point(bbox)
#                         if track_id not in self.person_trajectories:
#                             self.person_trajectories[track_id] = []
#                             self.falldown_counts[track_id] = 0
#                         self.person_trajectories[track_id].append(center_point)
                        
#                         # trajectory 길이 제한 (최대 100개 포인트만 유지)
#                         if len(self.person_trajectories[track_id]) > 35:
#                             self.person_trajectories[track_id].pop(0)
                        
#                         # falldown 검출 조건: trajectory가 30개 이상이고 사람이 멈춰있을 때만 검출
#                         trajectory = self.person_trajectories[track_id]
#                         if len(trajectory) <= 30:
#                             # trajectory가 충분하지 않으면 카운트 초기화
#                             self.falldown_counts[track_id] = 0
#                             continue
                        
#                         if not check_stop_person(bbox, trajectory):
#                             # 멈춰있지 않으면 카운트 초기화
#                             self.falldown_counts[track_id] = 0
#                             continue
                        
#                         # 사람 이미지 crop (정사각형, 최소 448x448)
#                         person_img = adjust_coordinates_and_crop(frame, x1, y1, x2, y2)

#                         # cv2.imshow("person_img", person_img)
                        
#                         # 유효성 검사
#                         if person_img is None or person_img.size == 0:
#                             continue
                        
#                         # SigLip 유사도 계산
#                         t1 = time.time()
#                         probs = self.detect_siglip_similarity(person_img)
#                         siglip_time = time.time() - t1
#                         print(siglip_time)
                        
#                         print(f"\n    📊 텍스트 유사도 결과:")
#                         for i, (text, prob) in enumerate(zip(self.texts, probs)):
#                             # falldown이면 강조 표시
#                             marker = "🔴" if i == 0 else "  "
#                             prob_percent = prob * 100
#                             bar_length = int(prob_percent / 2)  # 50칸 막대그래프
#                             bar = "█" * bar_length + "░" * (50 - bar_length)
#                             print(f"    {marker} [{bar}] {prob_percent:6.2f}% - {text}")
                        
#                         # falldown 판정 로직 (ms_ai_main.py와 동일)
#                         is_falldown_frame = False
#                         falldown_reason = ""
                        
#                         if len(probs) >= 4:
#                             # 조건 1: probs[0] > 0.50 이고 나머지 모든 확률이 0.3 미만
#                             if probs[0] > 0.80 and (probs[1] + probs[2]) > 0.15 and all(p < 0.2 for p in probs[3:6]):
#                                 is_falldown_frame = True
#                                 falldown_reason = "조건1: falldown 확률 > 50% & 나머지 < 30%"

#                             elif probs[0] > 0.70 and probs[1] + probs[2] > 0.15 and all(p < 0.1 for p in probs[3:6]):
#                                 is_falldown_frame = True
#                                 falldown_reason = "조건1: falldown 확률 > 50% & 나머지 < 30%"
                            
#                             elif probs[0] > 0.50 and (probs[1] + probs[2]) > 0.15 and all(p < 0.05 for p in probs[3:6]):
#                                 is_falldown_frame = True
#                                 falldown_reason = "조건1: falldown 확률 > 50% & 나머지 < 30%"

#                             # 조건 2: argmax가 0이고 나머지 모든 확률이 0.01 미만
#                             # elif probs[0] > 0.30 and (probs[1] + probs[2]) > 0.3 and all(p < 0.01 for p in probs[3:6]):
#                             #     is_falldown_frame = True
#                             #     falldown_reason = "조건2: falldown이 최대값 & 나머지 < 1%"

#                             # 조건 2: argmax가 0이고 나머지 모든 확률이 0.01 미만
#                             elif probs[0] > 0.2 and (probs[1] + probs[2]) > 0.15 and all(p < 0.01 for p in probs[3:6]):
#                                 is_falldown_frame = True
#                                 falldown_reason = "조건2: falldown이 최대값 & 나머지 < 1%"
                        

#                         # falldown 카운트 업데이트
#                         if is_falldown_frame:
#                             self.falldown_counts[track_id] += 1

#                         print(f"    - Falldown 카운트: {self.falldown_counts[track_id]}")
#                         # 10번 이상 누적되면 실제 falldown으로 판정
#                         if self.falldown_counts[track_id] >= 5 and track_id not in self.falldown_alerted:
#                             # falldown 검출 기록 저장
#                             detection_info = {
#                                 "video_path": self.video_path,
#                                 "video_name": os.path.basename(self.video_path),
#                                 "frame_number": frame_count,
#                                 "time_sec": current_time,
#                                 "track_id": track_id,
#                                 "trajectory_length": len(trajectory),
#                                 "falldown_count": self.falldown_counts[track_id],
#                                 "falldown_prob": probs[0],
#                                 "all_probs": {
#                                     "falldown": probs[0],
#                                     "walking": probs[1],
#                                     # "riding": probs[2],
#                                     "standing": probs[2],
#                                     "sitting": probs[3]
#                                 },
#                                 "detection_reason": falldown_reason
#                             }
#                             self.falldown_detections.append(detection_info)
#                             self.falldown_alerted.add(track_id)
                            
#                             print(f"\n    🚨 FALLDOWN 감지! (Track ID: {track_id}, 카운트: {self.falldown_counts[track_id]}, 유사도: {probs[0]*100:.2f}%)")
#                             print(f"    📋 판정 근거: {falldown_reason}")
#                             cv2.imwrite(f"{self.save_path}/falldown_detection_{os.path.basename(self.video_path)}_{frame_count}_ID{track_id}.jpg", plot_img)
#                             # stop_flag = True
#                         else:
#                             # print(f"\n    ✅ 정상 상태 (falldown 아님)")
#                             pass
                    
#                 cv2.imshow("frame", plot_img)

#             cap.release()
            
#             print("\n" + "=" * 80)
#             print("테스트 완료 요약")
#             print("=" * 80)
#             print(f"총 프레임 수: {frame_count}")
#             print(f"처리된 프레임 수: {processed_count}")
#             print(f"총 검출된 사람 수: {person_detection_count}")
#             if processed_count > 0:
#                 print(f"평균 검출 수: {person_detection_count/processed_count:.2f}명/프레임")
#             print("=" * 80 + "\n")
            
#             # falldown 검출 결과 출력 및 저장
#             if len(self.falldown_detections) > 0:
#                 # self._print_and_save_falldown_results()
#                 pass
#             else:
#                 # 검출되지 않은 경우: 결과 JSON에 영상 이름 남기기
#                 # INSERT_YOUR_CODE
#                 # 검출되지 않은 영상 이름을 no_detect_list.txt에 누적 기록
#                 try:
#                     no_detect_file = f"{self.save_path}/no_detect_list.txt"
#                     with open(no_detect_file, "a", encoding="utf-8") as f:
#                         video_name = os.path.basename(self.video_path)
#                         f.write(video_name + "\n")

#                     print(f"💾 미검출 영상 이름이 '{no_detect_file}'에 누적 저장되었습니다: {video_name}")
#                 except Exception as e:
#                     print(f"⚠ 미검출 목록 파일 저장 실패: {e}")
#                 # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#                 # video_name_no_ext = os.path.splitext(os.path.basename(self.video_path))[0]
#                 # output_filename = f"falldown_detection_{video_name_no_ext}_{timestamp}_none.json"
#                 # try:
#                 #     with open(output_filename, 'w', encoding='utf-8') as f:
#                 #         json.dump({
#                 #             "video_path": self.video_path,
#                 #             "video_name": os.path.basename(self.video_path),
#                 #             "total_detections": 0,
#                 #             "timestamp": timestamp,
#                 #             "note": "No falldown detected"
#                 #         }, f, indent=2, ensure_ascii=False)
#                 #     print(f"💾 (미검출) 결과가 파일로 저장되었습니다: {output_filename}")
#                 # except Exception as e:
#                 #     print(f"⚠ 미검출 결과 파일 저장 실패: {e}")
#                 pass
                
#         except KeyboardInterrupt:
#             print("\n\n⚠ 사용자에 의해 테스트 중단됨")
        

            


# def main():
#     """메인 함수"""
#     os.makedirs("./result", exist_ok=True)
#     os.makedirs("./result_no", exist_ok=True)

#     total_video_num = 0
#     YOLO_MODEL_PATH = "../weights/yolo/2024-12-31/ms-ai_24-12-31-M.pt"
#     SIGLIP_MODEL_PATH = "../weights/SigLip_512"
    

#     # video_folder = os.path.join("/root/DB_1/falldown_test/Training/videos/Y")
#     # save_path = "./result"

#     video_folder = os.path.join("/root/DB_1/falldown_test/Training/videos/N")
#     save_path = "./result_no"

#     video_list = os.listdir(video_folder)
    
#     for video_cls_folder_name in video_list:
#         # if video_cls_folder_name in ["FY", "SY","BY"] :
#         if True:
#             VIDEO_PATH = os.path.join(video_folder, video_cls_folder_name)
#             video_list = os.listdir(VIDEO_PATH)
#             for video_name in video_list:
#                 if video_name.split("_")[-1] in ["C1", "C2", "C3", "C4"]:
#                     total_video_num += 1
#                     VIDEO_NAME_PATH = os.path.join(VIDEO_PATH, video_name)
#                     video_path = os.path.join(VIDEO_NAME_PATH, f"{video_name}.mp4")
#                     tester = FalldownDetectTester(
#                         video_path=video_path,
#                         yolo_model_path=YOLO_MODEL_PATH,
#                         siglip_model_path=SIGLIP_MODEL_PATH,
#                         save_path=save_path
#                     )
#                     tester.run_test(skip_frames=30, max_frames=None, conf_threshold=0.5)

#     print(f"총 영상 수: {total_video_num}")

# def main_single_video():
#     """메인 함수"""
#     YOLO_MODEL_PATH = "../weights/yolo/2024-12-31/ms-ai_24-12-31-M.pt"
#     SIGLIP_MODEL_PATH = "../weights/SigLip_512"

#     # video_name = "02129_H_A_N_C2"
#     # video_path = os.path.join(f"/root/DB_1/falldown_test/Validation/videos/N/FY/{video_name}/{video_name}.mp4")

#     video_name = "00241_H_D_FY_C4"
#     video_path = os.path.join(f"/root/DB_1/falldown_test/Validation/videos/Y/FY/{video_name}/{video_name}.mp4")



#     tester = FalldownDetectTester(
#         video_path=video_path,
#         yolo_model_path=YOLO_MODEL_PATH,
#         siglip_model_path=SIGLIP_MODEL_PATH
#     )
#     tester.run_test(skip_frames=30, max_frames=None, conf_threshold=0.5)


# if __name__ == "__main__":
#     main()
#     # main_single_video()

import torch
import requests
from PIL import Image
from transformers import AutoProcessor, AutoModel, BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(load_in_4bit=True)
model = AutoModel.from_pretrained("google/siglip2-large-patch16-512", quantization_config=bnb_config, device_map="auto", attn_implementation="sdpa")
processor = AutoProcessor.from_pretrained("google/siglip2-large-patch16-512", quantization_config=bnb_config)

url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
image = Image.open(requests.get(url, stream=True).raw)
candidate_labels = ["a Pallas cat", "a lion", "a Siberian tiger"]

# follows the pipeline prompt template to get same results
texts = [f'This is a photo of {label}.' for label in candidate_labels]
# IMPORTANT: we pass `padding=max_length` and `max_length=64` since the model was trained with this
inputs = processor(text=texts, images=image, padding="max_length", max_length=64, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model(**inputs)

logits_per_image = outputs.logits_per_image
probs = torch.sigmoid(logits_per_image)
print(f"{probs[0][0]:.1%} that image 0 is '{candidate_labels[0]}'")