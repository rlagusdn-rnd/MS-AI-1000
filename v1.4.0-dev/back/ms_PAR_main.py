import os
import cv2
import base64
import requests
from datetime import datetime
import traceback
import sys
import json
import numpy as np
from logging_config import setup_logging
# 로깅 설정
logger = setup_logging()

VLM_URL = "http://127.0.0.1:1206/vlm_qna_par"
SERVER_URL = "http://127.0.0.1:65432/end_par"

color_map = {
    "Black" : 0,
    "White" : 1,
    "Blue" : 2,
    "Brown" : 3,
    "Green" : 4,
    "Grey" : 5,
    "Orange" : 6,
    "Pink" : 7,
    "Red" : 8,
    "Yellow" : 9,
}

color_map_num = {
    0 : "Black" ,
    1 : "White" ,
    2 : "Blue" ,
    3 : "Brown" ,
    4 : "Green" ,
    5 : "Grey" ,
    6 : "Orange",
    7 : "Pink" ,
    8 : "Red" ,
    9 : "Yellow"
}

def run_PAR(par_data_path, save_path):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : start PAR")
    os.makedirs(save_path, exist_ok=True)

    camera_list = os.listdir(par_data_path)
    
    for camera_name in camera_list:
        date_list = os.listdir(os.path.join(par_data_path, camera_name))

        for date in date_list:
            time_list = os.listdir(os.path.join(par_data_path, camera_name, date))
            os.makedirs(os.path.join(save_path, camera_name, date), exist_ok=True)

            for time_name in time_list:
                attribute_dict = {
                    "hat" : [0, 0],
                    "top" : [0, 0],
                    "top_color" : [0,0,0,0,0,0,0,0,0,0],
                    "bot" : [0, 0],
                    "bot_color" : [0,0,0,0,0,0,0,0,0,0],

                }
                img_list = os.listdir(os.path.join(par_data_path, camera_name, date, time_name))
                print(os.path.join(par_data_path, camera_name, date, time_name))
                logger.info(f"par 진행 중 {os.path.join(par_data_path, camera_name, date, time_name)}")
                try:
                    for img_name in img_list:
                        if img_name.split(".")[-1] == "json" or img_name.split(".")[-1] == "mp4" : continue
                        question = []

                        img = cv2.imread(os.path.join(par_data_path, camera_name, date, time_name, img_name))
                        cropped_img_extend = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        _, img_encoded = cv2.imencode('.png', cropped_img_extend)
                        img_bytes = img_encoded.tobytes()  # NumPy 배열을 bytes로 변환
                        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                        text = "<image>\n" + "Tell me the person's wearing a hat or cap in the following format:\n" \
                                + "{type: 'hat', answer : 'yes or no or unknown'}"
                        question.append(text)
                        
                        text = "<image>\n" + "Tell me the person's upper clothing type and color in the following format:\n" \
                        + "{type: 'type_of_clothing', 1st_color: 'Frist color_of_clothing', 2nd_color: 'Second color_of_clothing'}\n"\
                        + "The clothing types are: 'Short Sleeve', 'Long Sleeve'.\n"\
                        + "The clothing colors are: 'Black', 'White', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Red', 'Yellow'."

                        question.append(text) 

                        text = "<image>\n" + "Tell me the person's bottom clothing type and color in the following format:\n" \
                        + "{type: 'type_of_clothing', 1st_color: 'Frist color_of_clothing', 2nd_color: 'Second color_of_clothing'}\n"\
                        + "The clothing types are: 'Jeans', 'Shorts pants', 'Short Skirt', 'Trousers, 'Suits''.\n"\
                        + "The clothing colors are: 'Black', 'White', 'Blue', 'Brown', 'Green', 'Grey', 'Orange', 'Pink', 'Red', 'Yellow'."
                        question.append(text)

                        response = requests.post(VLM_URL,
                                                json={"image" : [img_base64],
                                                    "question" : question})
                        
                        if response.status_code == 200:
                            response = response.json()
                            answer_list = response["answer"]
                            print(answer_list)
                            answer_list = convert_answer(answer_list)
                            # print("--------------")
                            # print(len(answer_list), answer_list)

                            for i, answer in enumerate(answer_list):
                                if i == 0:
                                    try:
                                        if answer["answer"] == "yes" or answer["answer"] == "unknown":
                                            attribute_dict["hat"][0] += 1
                                        
                                        else:
                                            attribute_dict["hat"][1] += 1

                                    except:
                                        pass

                                if i == 1:
                                    try:
                                        if answer["type"] == "long":
                                            attribute_dict["top"][0] += 1
                                        else:
                                            attribute_dict["top"][1] += 1

                                        if answer["1st_color"] in color_map.keys():
                                            attribute_dict["top_color"][color_map[answer["1st_color"]]] += 1
                                        if answer["2nd_color"] in color_map.keys():
                                            attribute_dict["top_color"][color_map[answer["2nd_color"]]] += 1
                                    except:
                                        pass

                                if i == 2:
                                    try:
                                        if answer["type"] == "long":
                                            attribute_dict["bot"][0] += 1
                                        else:
                                            attribute_dict["bot"][1] += 1
                                        if answer["1st_color"] in color_map.keys():
                                            attribute_dict["bot_color"][color_map[answer["1st_color"]]] += 1
                                        if answer["2nd_color"] in color_map.keys():
                                            attribute_dict["bot_color"][color_map[answer["2nd_color"]]] += 1
                                    except:
                                        pass

                    save_attribue(attribute_dict, save_path=os.path.join(par_data_path, camera_name, date, time_name, "label.json"))


                    cmd = f'mv "{os.path.join(par_data_path, camera_name, date, time_name)}" "{os.path.join(save_path, camera_name, date)}"'
                    os.system(cmd)


                except Exception as e:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    tb = traceback.format_exc()
                    print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)

                    logger.error(f"{e}\n{tb} {sys.stderr}")

                    # os.makedirs(os.path.join(save_path, "no" , camera_name, date), exist_ok=True)
                    
                    # cmd = f'mv "{os.path.join(par_data_path, camera_name, date, time_name)}" "{os.path.join(save_path, "no" , camera_name, date)}"'
                    # os.system(cmd)

                # response = requests.put(SERVER_URL, json={"msg" : ""})

    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : END PAR")
    
    response = requests.put(SERVER_URL, json={"msg" : ""})

def save_attribue(attribute_dict, save_path):
    data = {"Hat" : None,
            "Top" : None,
            "Bot" : None,
            "TopColor" : [],
            "BotColor" : [],
            }

    if attribute_dict["hat"][0] == attribute_dict["hat"][1]: data["Hat"] = -1
    else: data["Hat"] = int(np.argmax(attribute_dict["hat"]))

    if attribute_dict["top"][0] == attribute_dict["top"][1]: data["Top"] = -1
    else: data["Top"] = int(np.argmax(attribute_dict["top"]))

    if attribute_dict["bot"][0] == attribute_dict["bot"][1]: data["Bot"] = -1
    else: data["Bot"] = int(np.argmax(attribute_dict["bot"]))

    for i in range(2):
        data["TopColor"].append(int(np.argmax(attribute_dict["top_color"])))
        attribute_dict["top_color"][np.argmax(attribute_dict["top_color"])] = 0

        data["BotColor"].append(int(np.argmax(attribute_dict["bot_color"])))
        attribute_dict["bot_color"][np.argmax(attribute_dict["bot_color"])] = 0

    with open(save_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

        
def convert_answer(data_list):
    result_list = []
    for data in data_list:
        data = data.strip("{}").strip()
        
        # 콜론을 기준으로 키-값 쌍 분리
        items = [item.strip() for item in data.split(",")]
        
        # 딕셔너리 생성
        result = {}
        for item in items:
            try:
                key, value = item.split(":", 1)
                value = value.replace(" ", "").strip() 
                value = value.strip().strip("'")
                if value == "Shortspants" or value == "ShortSleeve" or value == "ShortSkirt":
                    value = "short"

                elif value == "LongSleeve" or value == "Jeans" or value == "Trousers" or value == "Suits":
                    value = "long"

                result[key.strip()] = value

            except Exception as e:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                tb = traceback.format_exc()
                print(f"Error occurred at {current_time}: {e}\n{tb}", file=sys.stderr)
                print(item)

        if "2nd_color" not in result.keys():
            result["2nd_color"] = None

        result_list.append(result)

    return result_list