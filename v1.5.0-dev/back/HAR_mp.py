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
from concurrent.futures import ThreadPoolExecutor

# 로깅 설정
logger = setup_logging()

class Person_Info():
    def __init__(self, host, camera_name):
        self.info = dict()
        self.vlm_url = f"http://{host}:1206/vlm_QnA"
        self.save_path = os.path.join(os.getcwd(), "..", "backup", "VLM", "video")
        os.makedirs(self.save_path, exist_ok=True)
        self.camera_name = camera_name.replace(" ", "_")
        # VLM 비동기 처리를 위한 스레드 풀
        self.vlm_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"VLM-{camera_name}")
        # VLM 결과를 저장할 딕셔너리 (id별로 결과 저장)
        self.vlm_results = {}
        # 멀티프로세스 환경에서 안전한 락 제거
        # 프로세스 간 동기화는 pipe를 통해 처리

    def add_id(self, track_info):
        x1, y1, x2, y2, id_, conf, label, _ = track_info
        id_ = int(id_)
        
        self.info[id_] = {"trejectory" : [[int((x2 + x1)/2), int(y2)]],
                         "status" : [0],
                         "bbox" : [[x1, y1, x2, y2]],
                         "last_time" : time.time(),
                         "falldown" : [],
                         "fight" : [],
                         "img_crop" : [],
                         "img" : [],
                         "bbox_area" : []}

    def update_id(self, img, track_info):
        if len(track_info):
            for x1, y1, x2, y2, id_, conf, label, _ in track_info:
                id_ = int(id_)
                if id_ in self.info.keys():
                    self.info[id_]["trejectory"].append([int((x2 + x1)/2), int(y2)]) 
                    self.info[id_]["last_time"] = time.time()

                    img_crop = adjust_coordinates_and_crop(img, x1, y1, x2, y2)

                    self.info[id_]["img_crop"].append(img_crop) 
                    self.info[id_]["img"].append(img)

                    self.info[id_]["bbox_area"].append((x2 - x1) * (y2 - y1))
                    self.info[id_]["bbox"].append([int(x1), int(y1), int(x2), int(y2)])

                    # 메모리 관리: 최대 60개 프레임만 유지
                    if len(self.info[id_]["trejectory"]) > 60:
                        self.info[id_]["trejectory"].pop(0)
                    
                    if len(self.info[id_]["img_crop"]) > 60:
                        self.info[id_]["img_crop"].pop(0)
                        
                    if len(self.info[id_]["img"]) > 60:
                        self.info[id_]["img"].pop(0)
                        
                    if len(self.info[id_]["bbox"]) > 60:
                        self.info[id_]["bbox"].pop(0)
                        
                    if len(self.info[id_]["bbox_area"]) > 60:
                        self.info[id_]["bbox_area"].pop(0)
                        
                else:
                    self.add_id([x1, y1, x2, y2, id_, conf, label, _])

        self.refresh_info()

    def update_status(self, id_, detect_type, status):
        if id_ in self.info:
            self.info[id_][detect_type].append(status) 

            if len(self.info[id_][detect_type]) > 11:
                self.info[id_][detect_type].pop(0)

    def get_status(self, id_, detect_type):
        if id_ not in self.info:
            return 0
            
        if len(self.info[id_][detect_type]) > 5:
            status_list, counts =  np.unique(np.array(self.info[id_][detect_type]), return_counts=True)
            status = status_list[np.argmax(counts)]
        else:
            status = 0

        return status

    def refresh_info(self):
        """오래된 ID 정보 정리"""
        delete_id = []
        current_time = time.time()
        
        for id_ in self.info.keys():
            if current_time - self.info[id_]["last_time"] > 60:
                delete_id.append(id_)

        for id_ in delete_id:
            try:
                del self.info[id_]
                # logger.debug(f"삭제된 ID: {id_} (카메라: {self.camera_name})")
            except KeyError:
                pass  # 이미 삭제된 경우

    def run_har_vlm(self, id_, detect_type):
        """id_에 있는 사람의 이미지 버퍼를 모두 영상으로 저장하고 해당 영상 경로와 질문을 vlm_url을 이용하여 답변 받기"""
        try:
            if id_ not in self.info or len(self.info[id_]["img_crop"]) < 5:
                logger.warning(f"ID {id_}에 대한 이미지 데이터가 부족합니다.")
                return False
                
            current_time = datetime.now().strftime("%y-%m-%d_%H-%M-%S")
            video_save_path = os.path.join(self.save_path, f"{self.camera_name}_{int(id_)}_{current_time}.mp4")
            img_buffer = self.info[id_]["img_crop"]
            img_buffer = np.array(img_buffer)

            if save_video(img_buffer, video_save_path):
                # 이전 VLM 결과가 있는지 확인
                if id_ in self.vlm_results:
                    result = self.vlm_results.pop(id_)
                    logger.info(f"기존 VLM 결과 사용: ID {id_}, 결과: {result}")
                    return result
                
                # 새로운 VLM 요청을 비동기로 처리
                future = self.vlm_executor.submit(send_har_vlm_async, video_save_path, self.vlm_url, detect_type, id_, self.vlm_results)
                logger.info(f"VLM 비동기 처리 시작: ID {id_}, 비디오: {video_save_path}")
                
                # 즉시 False를 반환하여 현재 알람은 발생시키지 않음
                # VLM 결과는 나중에 vlm_results에 저장됨
                return False
            else:
                logger.error(f"비디오 저장 실패: {video_save_path}")
                return False

        except Exception as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            tb = traceback.format_exc()
            logger.error(f"사람 행동 VLM QnA API 호출 중 에러 발생 {current_time}: {e}\n{tb}")
            return False

    def check_vlm_results(self):
        """VLM 결과를 확인하고 완료된 결과가 있으면 반환"""
        completed_results = []
        if self.vlm_results:
            # 완료된 결과들을 수집
            for id_, result in list(self.vlm_results.items()):
                if result is not None:  # 결과가 완료됨
                    completed_results.append((id_, result))
                    # 결과를 사용했으므로 제거하지는 않음 (run_har_vlm에서 제거)
        return completed_results

def adjust_coordinates_and_crop(im, x1, y1, x2, y2):
    """좌표 조정 및 이미지 크롭 함수 - 멀티프로세스 환경에서 안전하도록 개선"""
    try:
        # 이미지 크기 가져오기
        h, w = im.shape[:2]
        
        # 입력 좌표 유효성 검사
        x1, y1, x2, y2 = max(0, int(x1)), max(0, int(y1)), min(w, int(x2)), min(h, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            # 유효하지 않은 bbox인 경우 기본 크기 반환
            return np.zeros((448, 448, 3), dtype=np.uint8)
        
        # 현재 bbox의 너비와 높이 계산
        width = x2 - x1
        height = y2 - y1
        
        # 더 긴 쪽을 기준으로 정사각형 만들기
        max_side = max(width, height)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # 최소 크기 448x448 보장
        min_size = 448
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
        
        # 크롭된 이미지가 비어있지 않은지 확인
        if crop_img.size == 0:
            return np.zeros((min_size, min_size, 3), dtype=np.uint8)
        
        # 최종 크기가 448x448보다 작은 경우 리사이즈
        if crop_img.shape[0] < min_size or crop_img.shape[1] < min_size:
            crop_img = cv2.resize(crop_img, (min_size, min_size))
        
        return crop_img
        
    except Exception as e:
        logger.error(f"이미지 크롭 중 에러 발생: {e}")
        return np.zeros((448, 448, 3), dtype=np.uint8)

def send_har_vlm_async(video_path, vlm_url, detect_type, person_id, vlm_results_dict):
    """비동기로 VLM API를 호출하는 함수"""
    try:
        result = send_har_vlm(video_path, vlm_url, detect_type)
        # 결과를 딕셔너리에 저장
        vlm_results_dict[person_id] = result
        logger.info(f"VLM 비동기 처리 완료: ID {person_id}, 결과: {result}")
        return result
    except Exception as e:
        logger.error(f"VLM 비동기 처리 중 에러: ID {person_id}, 에러: {e}")
        vlm_results_dict[person_id] = False
        return False

def send_har_vlm(video_path, vlm_url, detect_type):
    """VLM API을 이용한 사람 행동 검출 - 타임아웃 설정 추가"""
    try:
        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            logger.error(f"유효하지 않은 비디오 파일: {video_path}")
            return False
            
        messages = [{
                        "role": "user",
                        "content": [
                            {
                                "type": "video",
                                "video": video_path,
                                "max_pixels": 448 * 448,
                                "fps": 2,
                            },
                            {"type": "text", "text": "Please watch the video and write a report explaining the video according to the form that follows.\n"+
                                                    "1. **Full video description**: [Video description]\n"+
                                                    "2. **Explanation of behavior towards people**: [Movement towards people]\n"+
                                                    "3. **External description of a person**: [External description of a person]\n"+
                                                    "4. **Situation Summary**: [Situation Summary]\n"+
                                                    f"5. **Final Answer**: [Is a {detect_type} detected based on video analysis? If yes, yes; if no, no]\n\n"
                                                }
                        ],
                    }]

        # 타임아웃 설정으로 무한 대기 방지 (60초 타임아웃)
        response = requests.post(vlm_url, json={"question": messages}, timeout=120)

        logger.info(f"send har vlm : {video_path}")

        if response.status_code == 200:
                response_json = response.json()
                logger.info(f"VLM API 응답 원본: {response_json}")
                
                # VLM 응답 파싱
                parsed_response = parse_vlm_response(response_json["answer"])
                logger.info(f"VLM 파싱 결과: {parsed_response}")
                
                # 비디오 파일 삭제
                try:
                    os.remove(video_path)
                    logger.info(f"비디오 파일 삭제 완료: {video_path}")
                except Exception as e:
                    logger.warning(f"비디오 파일 삭제 실패: {video_path}, 에러: {e}")
                    
                # 파싱된 결과에서 detection_result 확인
                if 'detection_result' in parsed_response:
                    detection_result = parsed_response['detection_result']
                    logger.info(f"최종 검출 결과: {detection_result}")
                    return detection_result
                elif 'error' in parsed_response:
                    logger.error(f"VLM 응답 파싱 실패: {parsed_response['error']}")
                    # 파싱이 실패한 경우 원본에서 직접 체크
                    if isinstance(response_json["answer"], list) and len(response_json["answer"]) > 0:
                        answer_text = str(response_json["answer"][0]).lower()
                    else:
                        answer_text = str(response_json["answer"]).lower()
                    
                    result = "yes" in answer_text
                    logger.info(f"파싱 실패로 인한 대체 검출 결과: {result}")
                    return result
                else:
                    logger.error(f"VLM 응답에서 detection_result를 찾을 수 없음: {parsed_response}")
                    return False
                    
        else:
            logger.error(f"VLM API 요청 실패. 상태 코드: {response.status_code}")
            # 비디오 파일 삭제 (실패한 경우에도)
            try:
                os.remove(video_path)
            except:
                pass
            return False

    except requests.exceptions.Timeout:
        logger.error(f"VLM API 요청 타임아웃 (60초): {video_path}")
        # 타임아웃 시에도 비디오 파일 삭제
        try:
            os.remove(video_path)
        except:
            pass
        return False
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"사람 행동 VLM QnA API 호출 중 에러 발생 {current_time}: {e}\n{tb}")
        # 에러 시에도 비디오 파일 삭제
        try:
            os.remove(video_path)
        except:
            pass
        return False

def save_video(img_buffer, output_file_path):
    """비디오 저장 함수 - 멀티프로세스 환경에서 안전하도록 개선"""
    video_writer = None
    try:
        if len(img_buffer) == 0:
            logger.warning(f"빈 이미지 버퍼로 인해 비디오 저장 실패: {output_file_path}")
            return False
            
        # 디렉토리 생성 확인
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        # 첫 번째 유효한 이미지 찾기
        valid_img = None
        for img in img_buffer:
            if img is not None and img.size > 0:
                valid_img = img
                break
                
        if valid_img is None:
            logger.warning(f"유효한 이미지가 없어 비디오 저장 실패: {output_file_path}")
            return False
            
        height, width, _ = valid_img.shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30  # 초당 프레임 수 (FPS)

        video_writer = cv2.VideoWriter(output_file_path, fourcc, fps, (width, height))
        
        if not video_writer.isOpened():
            logger.error(f"VideoWriter 초기화 실패: {output_file_path}")
            return False
            
        frame_count = 0
        for img in img_buffer:
            if img is not None and img.size > 0:
                # 이미지 크기가 다른 경우 리사이즈
                if img.shape[:2] != (height, width):
                    img = cv2.resize(img, (width, height))
                video_writer.write(img)
                frame_count += 1

        video_writer.release()
        video_writer = None
        
        # 파일이 실제로 생성되었고 최소 프레임 수를 만족하는지 확인
        if os.path.exists(output_file_path) and os.path.getsize(output_file_path) > 1000 and frame_count >= 5:
            logger.info(f"비디오 저장 성공: {output_file_path}")
            return True
        else:
            logger.error(f"비디오 파일 생성 실패 또는 크기 부족: {output_file_path}")
            # 실패한 파일 삭제
            try:
                if os.path.exists(output_file_path):
                    os.remove(output_file_path)
            except:
                pass
            return False

    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"영상 저장 중 에러 발생 {current_time}: {e}\n{tb}")
        return False
    finally:
        # video_writer가 열려있다면 확실히 닫기
        if video_writer is not None:
            try:
                video_writer.release()
            except:
                pass

def parse_vlm_response(response_text):
    """
    VLM 응답을 번호별로 파싱하여 딕셔너리로 반환하는 함수 - 개선된 버전
    
    Args:
        response_text (str or list): VLM에서 받은 응답 텍스트 또는 리스트
        
    Returns:
        dict: 각 섹션별로 파싱된 결과
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
                response_text = '\n'.join(str(item) for item in response_text)
                
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
            
        # Final Answer에서 yes/no 추출 - 더 강건한 파싱
        if 'final_answer' in parsed_result:
            final_answer = parsed_result['final_answer']['content'].lower()
            # yes가 포함되어 있고 no가 없거나, yes가 no보다 먼저 나오는 경우
            yes_pos = final_answer.find('yes')
            no_pos = final_answer.find('no')
            
            if yes_pos != -1 and (no_pos == -1 or yes_pos < no_pos):
                parsed_result['detection_result'] = True
            else:
                parsed_result['detection_result'] = False
        else:
            # Final Answer 섹션이 없는 경우 전체 텍스트에서 검색
            response_lower = response_text.lower()
            yes_pos = response_lower.find('yes')
            no_pos = response_lower.find('no')
            
            if yes_pos != -1 and (no_pos == -1 or yes_pos < no_pos):
                parsed_result['detection_result'] = True
            else:
                parsed_result['detection_result'] = False
            
        return parsed_result
        
    except Exception as e:
        logger.error(f"VLM 응답 파싱 중 에러 발생: {e}")
        return {'error': str(e), 'raw_response': response_text, 'detection_result': False}

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

# 이미지 저장 함수 (기존 코드에서 사용되지 않지만 호환성을 위해 유지)
def save_image(image_data, path, url):
    """이미지 저장 함수 - 멀티프로세스 환경에서는 사용하지 않음"""
    try:
        os.makedirs(path, exist_ok=True)
        pass_flag = False
        save_num = max(1, len(image_data) // 5)
        
        for i, img in enumerate(image_data):
            img_name = f"{i}.png"
            if img is not None and (pass_flag or (i % save_num) == 0):
                if img.shape[0] * img.shape[1] < 1500:
                    pass_flag = True
                    continue
                cv2.imwrite(os.path.join(path, img_name), img)
                pass_flag = False

        response = requests.put(url, json={"msg": ""}, timeout=10)
        logger.info(f"save img : {path}")
    except Exception as e:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        logger.error(f"이미지 저장 중 에러 발생 {current_time}: {e}\n{tb}")
        