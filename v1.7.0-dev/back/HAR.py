import time
import numpy as np
import cv2
import threading
import os 
from datetime import datetime
import requests
import traceback
import sys
import re
from logging_config import setup_logging
from back.utils import plot_one_box 
import asyncio
import concurrent.futures

# 로깅 설정
logger = setup_logging(logger_name="HAR_module", log_file="MS_AI_MAIN.log")

class Person_Info():
    def __init__(self, host, camera_name):
        self.info = dict()
        self.vlm_url = f"http://{host}:1206/vlm_QnA"
        self.save_path = os.path.join(os.getcwd(), "..", "backup", "VLM", "video")
        os.makedirs(self.save_path, exist_ok=True)
        self.camera_name = camera_name.replace(" ", "_")
        # VLM 요청 상태 추적을 위한 딕셔너리
        self.vlm_requests = {}  # {id_: {"status": "pending"/"completed", "result": None, "timestamp": time.time()}}

    def add_id(self, track_info, crop_img):
        x1, y1, x2, y2, id_, conf, label, _ = track_info
        id_ = int(id_)
        
        self.info[id_] = {"trejectory" : [[int((x2 + x1)/2), int(y2)]],
                         "status" : [0],
                         "bbox" : [[x1, y1, x2, y2]],
                         "last_time" : time.time(),
                         "falldown" : [],
                         "fight" : [],
                         "img_crop" : crop_img,
                        #  "img" : [],
                         "bbox_area" : [],
                         "request_time" : time.time()}

    # def update_id(self, img, track_info):
    def update_id(self, img, track_info):
        if len(track_info):
            for x1, y1, x2, y2, id_, conf, label, _ in track_info:
                id_ = int(id_)
                img_crop = adjust_coordinates_and_crop(img, x1, y1, x2, y2)
                
                if id_ in self.info.keys():
                    self.info[id_]["trejectory"].append([int((x2 + x1)/2), int(y2)]) 
                    # self.info[id_]["status"].append(status) 
                    self.info[id_]["last_time"] = time.time()
                    self.info[id_]["img_crop"] = img_crop 
                    # self.info[id_]["img"].append(img)
                    self.info[id_]["bbox_area"].append((x2 - x1) * (y2 - y1))
                    self.info[id_]["bbox"].append([int(x1), int(y1), int(x2), int(y2)])

                    if len(self.info[id_]["trejectory"]) > 60:
                        self.info[id_]["trejectory"].pop(0)
                else:
                    self.add_id([x1, y1, x2, y2, id_, conf, label, _], img_crop)

        self.refresh_info()

    def update_status(self, id_, detect_type, status):
        self.info[id_][detect_type].append(status) 

        if len(self.info[id_][detect_type]) > 11:
            self.info[id_][detect_type].pop(0)

    def get_status(self, id_, detect_type):
        if len(self.info[id_][detect_type]) > 3:
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
            del self.info[id_]
            # VLM 요청 상태도 함께 정리
            if id_ in self.vlm_requests:
                del self.vlm_requests[id_]

    def run_har_vlm(self, id_, detect_type):
        """비동기 VLM 요청을 시작하고 즉시 None 반환"""
        try:
            # 이미 진행 중인 요청이 있는지 확인
            if id_ in self.vlm_requests and self.vlm_requests[id_]["status"] == "pending":
                # logger.info(f"VLM 요청이 이미 진행 중입니다: camera={self.camera_name}, id={id_}")
                return None
            
            current_time = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
            video_save_path = os.path.join(self.save_path, f"{self.camera_name}_{int(id_)}_{current_time}.mp4")
            img_buffer = self.info[id_]["img_crop"]
            img_buffer = np.array(img_buffer)

            save_video(img_buffer, video_save_path)
            
            # VLM 요청 상태 등록
            self.vlm_requests[id_] = {
                "status": "pending",
                "result": None,
                "timestamp": time.time(),
                "video_path": video_save_path,
                "detect_type": detect_type
            }
            
            # 백그라운드에서 VLM 요청 실행
            thread = threading.Thread(
                target=self._send_har_vlm_async,
                args=(id_, video_save_path, detect_type)
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"VLM 요청 시작: camera={self.camera_name}, id={id_}, detect_type={detect_type}")
            return None  # 즉시 None 반환

        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            logger.error(f"사람 행동 VLM QnA API 호출 중 에러 발생 {current_time}: {e}\n{tb}")
            return None

    def _send_har_vlm_async(self, id_, video_path, detect_type):
        """백그라운드에서 실행되는 실제 VLM 요청 함수"""
        try:
            response = send_har_vlm(video_path, self.vlm_url, detect_type)
            
            # 결과 업데이트
            if id_ in self.vlm_requests:
                self.vlm_requests[id_]["status"] = "completed"
                self.vlm_requests[id_]["result"] = response
                self.vlm_requests[id_]["timestamp"] = time.time()
                
            logger.info(f"VLM 요청 완료: camera={self.camera_name}, id={id_}, result={response}")
            
        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            logger.error(f"비동기 VLM 요청 중 에러 발생 {current_time}: {e}\n{tb}")
            
            # 에러 상태로 업데이트
            if id_ in self.vlm_requests:
                self.vlm_requests[id_]["status"] = "error"
                self.vlm_requests[id_]["result"] = False
                self.vlm_requests[id_]["timestamp"] = time.time()

    def check_vlm_response(self, id_):
        """특정 ID의 VLM 응답 상태 확인"""
        if id_ not in self.vlm_requests:
            return None, "no_request"
        
        request_info = self.vlm_requests[id_]
        
        if request_info["status"] == "completed":
            result = request_info["result"]
            # 완료된 요청은 정리
            del self.vlm_requests[id_]
            return result, "completed"
        elif request_info["status"] == "error":
            result = request_info["result"]
            # 에러된 요청도 정리
            del self.vlm_requests[id_]
            return result, "error"
        elif request_info["status"] == "pending":
            # 60초 이상 대기 중인 요청은 타임아웃 처리
            if time.time() - request_info["timestamp"] > 300:
                logger.warning(f"VLM 요청 타임아웃: camera={self.camera_name}, id={id_}")
                del self.vlm_requests[id_]
                return False, "timeout"
            return None, "pending"
        
        return None, "unknown"

    def get_pending_vlm_requests(self):
        """대기 중인 VLM 요청 목록 반환"""
        pending_requests = {}
        for id_, request_info in self.vlm_requests.items():
            if request_info["status"] == "pending":
                pending_requests[id_] = request_info
        return pending_requests

def adjust_coordinates_and_crop(im, x1, y1, x2, y2):
    # 이미지 크기 가져오기
    h, w = im.shape[:2]
    
    # 현재 bbox의 너비와 높이 계산
    width = x2 - x1
    height = y2 - y1
    
    # 더 긴 쪽을 기준으로 정사각형 만들기
    max_side = max(width, height)
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    
    # 최소 크기 448x448 보장
    min_size = 224
    if max_side < min_size:
        max_side = min_size
    
    # 정사각형 bbox 계산
    half_side = max_side / 2
    x1_new = center_x - half_side
    y1_new = center_y - half_side
    x2_new = center_x + half_side
    y2_new = center_y + half_side
    
    # 이미지 경계를 벗어나지 않도록 조정
    x1_new = max(0, int(x1_new))
    y1_new = max(0, int(y1_new))
    x2_new = min(w, int(x2_new))
    y2_new = min(h, int(y2_new))
    
    # 이미지 크롭
    crop_img = im[y1_new:y2_new, x1_new:x2_new]
    
    # 최종 크기가 448x448보다 작은 경우 리사이즈
    if crop_img.shape[0] < min_size or crop_img.shape[1] < min_size:
        crop_img = cv2.resize(crop_img, (min_size, min_size))
    
    return crop_img

#VLM API을 이용한 사람 행동 검출
def send_har_vlm(video_path, vlm_url, detect_type):
    try:
        messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "video",
                                "video": video_path,
                                "max_pixels": 448 * 448,
                                "fps": 1,
                            },
                            # {"type": "text", "text": "Please watch the video and write a report explaining the video according to the form that follows.\n"+
                            #                         "1. **Full video description**: [Video description]\n"+
                            #                         "2. **Explanation of behavior towards people**: [Movement towards people]\n"+
                            #                         "3. **External description of a person**: [External description of a person]\n"+
                            #                         "4. **Situation Summary**: [Situation Summary]\n"+
                            #                         f"5. **Final Answer**: [Is a {detect_type} detected based on video analysis? If yes, yes; if no, no]\n\n"
                            #                     }
                            {"type": "text", "text": "Please watch the video and write a report explaining the video according to the form that follows.\n"+
                                                    "1. **Full video description**: [Video description]\n"+
                                                    "2. **Explanation of behavior towards people**: [Movement towards people]\n"+
                                                    f"3. **Final Answer**: [Is a {detect_type} detected based on video analysis? If yes, yes; if no, no]\n\n"
                                                }
                        ],
                    }]

        response = requests.post(vlm_url, json={"question": messages, "video_path": video_path, "data_type": "video"}) 
        logger.info(f"send har vlm : {video_path}")

        if response.status_code == 200:
                response = response.json()
                # logger.info(f"VLM API 응답 원본: {response}")
                
                # VLM 응답 파싱
                parsed_response = parse_vlm_response(response["answer"])
                # logger.info(f"VLM 파싱 결과: {parsed_response}")
                
                
                    
                # 파싱된 결과에서 detection_result 확인
                if 'detection_result' in parsed_response:
                    detection_result = parsed_response['detection_result']
                    logger.info(f"최종 검출 결과: {detection_result}")
                    return detection_result
                elif 'error' in parsed_response:
                    logger.error(f"VLM 응답 파싱 실패: {parsed_response['error']}")
                    # 파싱이 실패한 경우 원본에서 직접 체크
                    if isinstance(response["answer"], list) and len(response["answer"]) > 0:
                        answer_text = str(response["answer"][0]).lower()
                    else:
                        answer_text = str(response["answer"]).lower()
                    
                    result = "yes" in answer_text
                    logger.info(f"파싱 실패로 인한 대체 검출 결과: {result}")
                    return result
                else:
                    logger.error(f"VLM 응답에서 detection_result를 찾을 수 없음: {parsed_response}")
                    logger.error(f"VLM 응답: {response}")
                    return False
                    
        else:
            logger.error(f"VLM API 요청 실패: status_code={response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"VLM API 요청 타임아웃: {video_path}")
        return False
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"사람 행동 VLM QnA API 호출 중 에러 발생 {current_time}: {e}\n{tb}")
        return False

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
        current_time = datetime.now().strftime("%Y-%m-%d%H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"이미지 저장 중 에러 발생 {current_time}: {e}\n{tb}")


def save_video(img_buffer, output_file_path):
    try:
        if len(img_buffer) == 0:
            logger.warning(f"빈 이미지 버퍼로 인해 비디오 저장 실패: {output_file_path}")
            return False
            
        # 디렉토리 생성 확인
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        height, width, _ = img_buffer[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30  # 초당 프레임 수 (FPS)

        video_writer = cv2.VideoWriter(output_file_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            logger.error(f"VideoWriter 초기화 실패: {output_file_path}")
            return False
            
        for i, img in enumerate(img_buffer):
            video_writer.write(img)

        video_writer.release()
        
        # 파일이 실제로 생성되었는지 확인
        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 0:
            logger.info(f"비디오 저장 성공: {output_file_path} (크기: {os.path.getsize(output_file_path)} bytes)")
            return True
        else:
            logger.error(f"비디오 파일 생성 실패: {output_file_path}")
            return False

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"영상 저장 중 에러 발생 {current_time}: {e}\n{tb}")
        return False

def parse_vlm_response(response_text):
    """
    VLM 응답을 번호별로 파싱하여 딕셔너리로 반환하는 함수
    
    Args:
        response_text (str or list): VLM에서 받은 응답 텍스트 또는 리스트
        
    Returns:
        dict: 각 섹션별로 파싱된 결과
        
    Example:
        response = "1. **Full video description**: A man is sitting..."
        result = parse_vlm_response(response)
        print(result['full_video_description'])
    """
    try:
        # 입력이 리스트인 경우 첫 번째 요소를 사용하거나 조인
        if isinstance(response_text, list):
            if len(response_text) == 0:
                return {'error': 'Empty response list', 'raw_response': response_text}
            elif len(response_text) == 1:
                response_text = response_text[0]
            else:
                # 여러 요소가 있는 경우 조인
                response_text = '\n'.join(response_text)
                
        # 입력이 문자열이 아닌 경우 문자열로 변환
        if not isinstance(response_text, str):
            response_text = str(response_text)
            
        # 정규표현식 패턴: 숫자. **제목**: 내용
        pattern = r'(\d+)\.\s*\*\*([^*]+)\*\*:\s*([^0-9]*?)(?=\d+\.\s*\*\*|\Z)'
        
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        parsed_result = {}
        
        for match in matches:
            section_number = int(match[0])
            section_title = match[1].strip()
            section_content = match[2].strip()
            
            # 제목을 소문자로 변환하고 공백을 언더스코어로 변경
            key = section_title.lower().replace(' ', '_').replace('-', '_')
            
            parsed_result[key] = {
                'number': section_number,
                'title': section_title,
                'content': section_content
            }
            
            # 편의를 위해 직접 접근 가능한 키도 추가
            parsed_result[f'section_{section_number}'] = section_content
            
        # Final Answer에서 yes/no 추출
        if 'final_answer' in parsed_result:
            final_answer = parsed_result['final_answer']['content'].lower()
            parsed_result['detection_result'] = 'yes' in final_answer
            
        return parsed_result
        
    except Exception as e:
        logger.error(f"VLM 응답 파싱 중 에러 발생: {e}")
        return {'error': str(e), 'raw_response': response_text}

def parse_vlm_response_simple(response_text):
    """
    VLM 응답을 간단하게 번호별로 리스트로 반환하는 함수
    
    Args:
        response_text (str): VLM에서 받은 응답 텍스트
        
    Returns:
        list: 각 섹션의 내용을 순서대로 담은 리스트
    """
    try:
        # 정규표현식 패턴: 숫자. **제목**: 내용
        pattern = r'\d+\.\s*\*\*[^*]+\*\*:\s*([^0-9]*?)(?=\d+\.\s*\*\*|\Z)'
        
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        # 각 섹션 내용의 앞뒤 공백 제거
        sections = [match.strip() for match in matches]
        
        return sections
        
    except Exception as e:
        logger.error(f"VLM 응답 간단 파싱 중 에러 발생: {e}")
        return [response_text]
        