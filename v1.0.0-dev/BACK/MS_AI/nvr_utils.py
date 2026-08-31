
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import numpy as np
import json
import xml.etree.ElementTree as ET
import datetime
import time

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

def send_email_alarm(alarm, camera_num):
    gmail_sender = 'diddytpq5@gmail.com'
    gmail_passwd = 'zqpx escp ebme yjyf'
    TO = 'ysyang@microsystems.co.kr'

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(gmail_sender, gmail_passwd)

    msg = MIMEMultipart()
    msg['From'] = gmail_sender
    msg['To'] = TO
    msg['Subject'] = Header(f'{camera_num + 1} 번 카메라 알람', 'utf-8').encode()

    body = MIMEText(f"{camera_num + 1} 번 카메라 {alarm[3]} {alarm[0]} 상황 감지", 'plain', 'utf-8')
    msg.attach(body)

    try:
        server.sendmail(gmail_sender, [TO], msg.as_string())
        print('email sent')
    except Exception as e:
        print('error sending mail:', e)

    server.quit()

def get_nvr_address(file_dir):
    tree = ET.parse(file_dir)
    root = tree.getroot()

    NVR_root = root.find("NVR")
    nvr_ID = NVR_root.find("ID").text
    nvr_password = NVR_root.find("password").text
    nvr_event_address = NVR_root.find("enevt_svg").text
    nvr_event_post_address = NVR_root.find("event_post").text

    return nvr_ID, nvr_password, nvr_event_address, nvr_event_post_address


# def resize_xy_pos(x, y, original_resolution=(1920,1080)):
#     if x <= (original_resolution[0]/2):
#         x_pos = x * 3
    
#     else:
#         x_pos = (x - original_resolution[0]/2) * 3

#     if y <= original_resolution[1]/2:
#         y_pos = y * 2.25
    
#     else:
#         y_pos = (y - original_resolution[1]/2) * 2.25

#     return int(x_pos), int(y_pos)

def resize_xy_pos(x, y, original_resolution=(640,480), target_resolution=(1920,1080)):
    x_ratio = target_resolution[0] / original_resolution[0]
    y_ratio = target_resolution[1] / original_resolution[1]

    if x > (original_resolution[0]):
        x -= original_resolution[0]

    if y > (original_resolution[1]):
        y -= original_resolution[1]

    converted_x = x * x_ratio
    converted_y = y * y_ratio

    return int(converted_x), int(converted_y)

def get_bbox_origin_pos(bboxes, original_resolution=(641,481), target_resolution = (1920,1080)):

    new_bboxes = []

    if len(bboxes):
        for cls, bbox in bboxes:

            x_ratio = target_resolution[0] / original_resolution[0]
            y_ratio = target_resolution[1] / original_resolution[1]

            bbox[0] = bbox[0] % original_resolution[0] * x_ratio
            bbox[1] = bbox[1] % original_resolution[1] * y_ratio
            bbox[2] = bbox[2] % original_resolution[0] * x_ratio
            bbox[3] = bbox[3] % original_resolution[1] * y_ratio

            bbox[2] = bbox[2] - bbox[0]
            bbox[3] = bbox[3] - bbox[1]

            bbox = bbox.astype(int)

            new_bboxes.append([cls, bbox])
    else:
        return []

    return new_bboxes

def get_svg_DA(msg, DA_list, color) -> str:

    msg += """<polygon style="fill-opacity:0;
            stroke:rgb{};
            stroke-opacity:0.8;
            stroke-width:5.0"
            points=" """.format(color)
    
    if len(DA_list):
        for x, y in (DA_list):
            x_pos, y_pos = resize_xy_pos(x, y)
            msg += "{},{} ".format(int(x_pos),int(y_pos))

    msg += ''' " /> \n'''

    return msg

def get_svg_DA_pc(msg, DA_A_list, DA_B_list, color_A, color_B) -> str:

    msg += """<polygon style="fill-opacity:0;
    stroke:rgb{};
    stroke-opacity:0.8;
    stroke-width:5.0"
    points=" """.format(color_A)
    if len(DA_A_list):
        for x, y in (DA_A_list):
            x_pos, y_pos = resize_xy_pos(x, y)
            msg += "{},{} ".format(int(x_pos),int(y_pos))

    msg += ''' " /> \n'''
    msg += """<polygon style="fill-opacity:0;
    stroke:rgb{};
    stroke-opacity:0.8;
    stroke-width:5.0"
    points=" """.format(color_B)

    if len(DA_B_list):
        for x, y in (DA_B_list):
            x_pos, y_pos = resize_xy_pos(x, y)
            msg += "{},{} ".format(int(x_pos),int(y_pos))

    msg += ''' " /> \n'''

    return msg

def get_svg_bbox(msg, bbox_list) -> str:

    for cls, bbox in bbox_list:

        x1, y1, w, h = bbox

        if cls == 1 :
            color = "#8d0000"
        
        else :
            color = "#0702a6"


        msg += '''<rect style="fill:{};
                        fill-opacity:0.1;
                        stroke:{};
                        stroke-opacity: 0.8;
                        stroke-width:5.0;" \n'''.format(color, color)
        msg += '''  x="{}" y="{}" width="{}" height="{}" /> \n'''.format(x1,y1,w,h)

    return msg

def get_svg_alarm(camera_ip, alarm_type, direction = False):
    if direction:
        if direction == "enter" : direction = 1
        else : direction = 2
        
        msg = {
                "type": 70,
                "source_address": camera_ip ,
                "micro_ai": {
                    "type": alarm_type,
                    "object" : 1,
                    "direction" : direction
                }
            }
    
    else: 
        msg = {
            "type": 70,
            "source_address": camera_ip ,
            "micro_ai": {
                "type": alarm_type,
                "object" : 1
            }
        }
    
    json_data = json.dumps(msg)
    return json_data

def send_NVR(camera_info_list, nvr_id, nvr_password, enevt_svg, event_post, email = False):
    auth=HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
    # enevt_svg='http://117.17.159.143:80/api/events/svg' # 이벤트 주소
    # event_post='http://117.17.159.143:80/api/events' # 이벤트 주소
    # enevt_svg='http://192.168.1.50:80/api/events/svg' # 이벤트 주소
    # event_post='http://192.168.1.50:80/api/events' # 이벤트 주소
    
    color_Loit = (255, 255, 0)
    color_Intr = (255, 0, 255)
    color_pc_A = (255, 0, 0)
    color_pc_B = (0, 0, 255)
    color_Fire = (242, 150, 97)
    color_que = (0, 255, 255)
    color_Fight = (127, 0, 255)
    color_Falldown = (0, 204, 102)

    # camera_1_bbox, camera_2_bbox, camera_3_bbox, camera_4_bbox = get_bbox_origin_pos(bbox_list)
    # camera_bbox_info = [camera_1_bbox, camera_2_bbox, camera_3_bbox, camera_4_bbox]

    # bbox_info_dict = {}

    # for i, key in enumerate(camera_info_list.keys()):
    #     bbox_info_dict[key] = camera_bbox_info[i]
        

    # for i in range(len(camera_info_list)):
    for i in camera_info_list.keys():
        bbox_info = get_bbox_origin_pos(camera_info_list[i]["bbox_list"])

        ip_before = camera_info_list[i]["ip_source"][camera_info_list[i]["ip_source"].find("@")+1:]
        camera_ip = ip_before[:ip_before.find(":")]
        # camera_ip = ip_before[:ip_before.find("/")]

        # svg_data = '''<svg id="posco-ai" source-address="{}" viewBox="0 0 1920 1080"> \n'''.format(camera_ip)
        svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> \n'''.format(i)
        
        for detect_class, area  in camera_info_list[i]["detect_area"].items():
            if detect_class == "Loitering":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Loit)
            elif detect_class == "Intrusion":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Intr)
            elif detect_class == "Fire":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Fire)
            elif detect_class == "Fight":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Fight)
            elif detect_class == "Falldown":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Falldown)
            elif detect_class == "Entering":
                svg_data = get_svg_DA_pc(svg_data, area[0], area[1], color_pc_A, color_pc_B)

            svg_data = get_svg_bbox(svg_data, bbox_info)
            r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

            headers = {
                "Content-Type": "application/json",
            }
            # print("-----NVR -----")
            # print(camera_info_list)
            if len(camera_info_list[i]["alarm_list"]):
                # print(camera_info_list[i]["alarm_list"])
                for j in range(len(camera_info_list[i]["alarm_list"])):
                    if camera_info_list[i]["alarm_list"][j][0] == "loitering":
                        alarm_type = 1
                        # alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type)
                        # r = requests.post(event_post,auth=auth, data=alarm_msg)
                        data = {"type": 70, "source_address": camera_ip, "micro_ai": {"type": alarm_type, "object": 1}}

                        r = requests.put(event_post, headers=headers, json=data, auth=auth)


                    elif camera_info_list[i]["alarm_list"][j][0] == "intrusion":
                        alarm_type = 2
                        # alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type)
                        data = {"type": 70, "source_address": camera_ip, "micro_ai": {"type": alarm_type, "object": 1}}

                        r = requests.put(event_post, headers=headers, json=data, auth=auth)
                        # print(camera_info_list[i]["alarm_list"])
                        # print(j)
                        # print(f"{camera_ip} send alarm intrusion")

                    elif camera_info_list[i]["alarm_list"][j][0] in ["enter", "exit"]:
                        alarm_type = 3
                        direction = camera_info_list[i]["alarm_list"][j][0]
                        alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type, direction = direction)
                        r = requests.post(event_post,auth=auth, data=alarm_msg)
                        # r = requests.put(event_post, headers=headers, json=alarm_msg, auth=auth)

                        # print(f"send {alarm_type}")

                    elif camera_info_list[i]["alarm_list"][j][0] == "fire":
                        alarm_type = 4
                        alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type)
                        # r = requests.post(event_post,auth=auth, data=alarm_msg)
                        data = {"type": 70, "source_address": camera_ip, "micro_ai": {"type": alarm_type, "object": 1}}


                        r = requests.put(event_post, headers=headers, json=data, auth=auth)

                        # print(f"{camera_ip} send alarm fire")

                    elif camera_info_list[i]["alarm_list"][j][0] == "falldown":
                        alarm_type = 6
                        alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type)

                        data = {"type": 70, "source_address": camera_ip, "micro_ai": {"type": alarm_type, "object": 1}}

                        r = requests.put(event_post, headers=headers, json=data, auth=auth)

                        # print(f"{camera_ip} send alarm falldown")
                        
                    elif camera_info_list[i]["alarm_list"][j][0] == "fight":
                        alarm_type = 7
                        # alarm_msg = get_svg_alarm(camera_ip, alarm_type = alarm_type)
                        # r = requests.post(event_post,auth=auth, data=alarm_msg)
                        data = {"type": 70, "source_address": camera_ip, "micro_ai": {"type": alarm_type, "object": 1}}

                        r = requests.put(event_post, headers=headers, json=data, auth=auth)

                    if email == True:
                        send_email_alarm(camera_info_list[i]["alarm_list"][j], camera_num = i)


        # if camera_info_list[i]["detect_type"] == "Loitering":
        #     svg_data = get_svg_DA(svg_data, camera_info_list[i]["detect_area"], color_Loit)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        #     if len(camera_info_list[i]["alarm_list"]):
        #         for j in range(len(camera_info_list[i]["alarm_list"])):
        #             alarm_msg = get_svg_alarm(camera_ip, alarm_type = 1)
        #             r = requests.post(event_post,auth=auth, data=alarm_msg)

        # if camera_info_list[i]["detect_type"] == "Intrusion":
        #     svg_data = get_svg_DA(svg_data, camera_info_list[i]["detect_area"], color_Intr)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        #     if len(camera_info_list[i]["alarm_list"]):
        #         for j in range(len(camera_info_list[i]["alarm_list"])):
        #             alarm_msg = get_svg_alarm(camera_ip, alarm_type = 2)
        #             r = requests.post(event_post,auth=auth, data=alarm_msg)

        # if camera_info_list[i]["detect_type"] == "Queueing":
        #     svg_data = get_svg_DA(svg_data, camera_info_list[i]["DA"], color_que)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))
            # if len(camera_info_list[i]["alarm_list"]):
            #     for j in range(len(camera_info_list[i]["alarm_list"])):
            #     alarm_msg = get_svg_alarm(camera_ip, alarm_type = 3)
            #     r=requests.post(event_post,auth=auth, data=alarm_msg)


        # if camera_info_list[i]["detect_type"] == "Entering":
        #     svg_data = get_svg_DA_pc(svg_data, camera_info_list[i]["detect_area_A"], camera_info_list[i]["detect_area_B"], color_pc_A, color_pc_B)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))
            
        #     if len(camera_info_list[i]["alarm_list"]):
        #         for j in range(len(camera_info_list[i]["alarm_list"])):
        #             direction = camera_info_list[i]["alarm_list"][j][0]
        #             alarm_msg = get_svg_alarm(camera_ip, alarm_type = 3, direction = direction)
        #             r = requests.post(event_post,auth=auth, data=alarm_msg)
            

def send_NVR_ROI(camera_info_list, nvr_id, nvr_password, enevt_svg):
    auth=HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
    # enevt_svg='http://117.17.159.143:80/api/events/svg' # 이벤트 주소
    # event_post='http://117.17.159.143:80/api/events' # 이벤트 주소
    # enevt_svg='http://192.168.1.50:80/api/events/svg' # 이벤트 주소
    # event_post='http://192.168.1.50:80/api/events' # 이벤트 주소
    
    color_Loit = (255, 255, 0)
    color_Intr = (255, 0, 255)
    color_pc_A = (255, 0, 0)
    color_pc_B = (0, 0, 255)
    color_que = (0, 255, 255)

    for i in camera_info_list.keys():
        bbox_info = get_bbox_origin_pos(camera_info_list[i]["bbox_list"])

        ip_before = camera_info_list[i]["ip_source"][camera_info_list[i]["iip_sourcep"].find("@")+1:]
        camera_ip = ip_before[:ip_before.find(":")]
        # camera_ip = ip_before[:ip_before.find("/")]

        svg_data = '''<svg id="posco-ai" source-address="{}" viewBox="0 0 1920 1080"> \n'''.format(camera_ip)

        for detect_class, area  in camera_info_list[i]["detect_area"].items():
            if detect_class == "Loitering":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Loit)
            elif detect_class == "Intrusion":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, area[j], color_Intr)
            # elif detect_class == "Queue":
            #     svg_data = get_svg_DA(svg_data, area, color_que)
            elif detect_class == "Entering":
                svg_data = get_svg_DA_pc(svg_data, area[0], area[1], color_pc_A, color_pc_B)

            r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

def send_NVR_empty(camera_info_list, nvr_id, nvr_password, enevt_svg):
    auth=HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
    # enevt_svg='http://117.17.159.143:80/api/events/svg' # 이벤트 주소
    # event_post='http://117.17.159.143:80/api/events' # 이벤트 주소
    # enevt_svg='http://192.168.1.50:80/api/events/svg' # 이벤트 주소
    # event_post='http://192.168.1.50:80/api/events' # 이벤트 주소
    
    color_Loit = (255, 255, 0)
    color_Intr = (255, 0, 255)
    color_pc_A = (255, 0, 0)
    color_pc_B = (0, 0, 255)
    color_que = (0, 255, 255)

    for i in camera_info_list.keys():
        bbox_info = []

        ip_before = camera_info_list[i]["ip_source"][camera_info_list[i]["ip_source"].find("@")+1:]
        camera_ip = ip_before[:ip_before.find(":")]
        # camera_ip = ip_before[:ip_before.find("/")]


        svg_data = '''<svg id="posco-ai" source-address="{}" viewBox="0 0 1920 1080"> \n'''.format(camera_ip)

        for detect_class, area  in camera_info_list[i]["detect_area"].items():
            if detect_class == "Loitering":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, [], color_Loit)
            elif detect_class == "Intrusion":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, [], color_Intr)
            elif detect_class == "Fire":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, [], color_Intr)
            elif detect_class == "Fight":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, [], color_Intr)
            elif detect_class == "Falldown":
                for j in range(len(area)):
                    svg_data = get_svg_DA(svg_data, [], color_Intr)
            elif detect_class == "Entering":
                svg_data = get_svg_DA_pc(svg_data, [], [], color_pc_A, color_pc_B)

            r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        # if camera_info_list[i]["detect_type"] == "Loitering":
        #     svg_data = get_svg_DA(svg_data, [], color_Loit)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        # if camera_info_list[i]["detect_type"] == "Intrusion":
        #     svg_data = get_svg_DA(svg_data, [], color_Intr)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        # if camera_info_list[i]["detect_type"] == "Queueing":
        #     svg_data = get_svg_DA(svg_data, [], color_que)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))

        # if camera_info_list[i]["detect_type"] == "Entering":
        #     svg_data = get_svg_DA_pc(svg_data, [], [], color_pc_A, color_pc_B)
        #     svg_data = get_svg_bbox(svg_data, bbox_info)
        #     r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))
            
def get_search_data_NVR(nvr_id, nvr_password, nvr_ip, start, end, event_kind, target, order):
    if order == -1:
        order = 0
    auth = HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
    event_post = f'http://{nvr_ip}/api/events' # event_post='http://117.17.159.143:80/api/events' # 이벤트 주소

    start = start.replace(" ", ":")
    end = end.replace(" ", ":")
    request_data = event_post + f"?types=70&since={start}&until={end}&limit=1000&sort={order}"
    r = requests.get(request_data,auth=auth)

    log_data = r.json()

    log_list = []  #[[시간, 카메라id, 이벤트종류, 검출 객체],[...]]

    for event_dict in log_data["events"]:

        detect_time = datetime.datetime.fromtimestamp(event_dict["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')

        # {'total': 0, 'offset': 0, 'limit': 10, 
        #  'events': [{'type': 70, 'timestamp': 1688809339, 'rowid': 14081, 'devices': [3], 'micro_ai': {'type': 3, 'object': 1, 'direction': 2}}, 
        #             {'type': 70, 'timestamp': 1688809339, 'rowid': 14080, 'devices': [3], 'micro_ai': {'type': 3, 'object': 1, 'direction': 2}}, 
        #             {'type': 70, 'timestamp': 1688808906, 'rowid': 14079, 'devices': [3], 'micro_ai': {'type': 2, 'object': 1, 'direction': 0}}, 

        
        if event_dict["micro_ai"]["type"] == 1:
            detect_class = "배회"
        elif event_dict["micro_ai"]["type"] == 2:
            detect_class = "침입"
        elif event_dict["micro_ai"]["type"] == 3:
            detect_class = "출입확인"
        elif event_dict["micro_ai"]["type"] == 4:
            detect_class = "방화"
        elif event_dict["micro_ai"]["type"] == 5:
            detect_class = "투기"
        elif event_dict["micro_ai"]["type"] == 6:
            detect_class = "쓰러짐"
        elif event_dict["micro_ai"]["type"] == 7:
            detect_class = "싸움"
        else : detect_class = "none"

        if event_dict["micro_ai"]["object"] == 1:
            object_class = "사람"

        if event_kind == detect_class:
            log_list.append([detect_time, event_dict["devices"][0], detect_class, object_class])

    return log_list

def check_NVR_camera_info_init(data):
    if len(data["info"]["cameras"]) == 0:
        nvr_id =data["info"]["server"]["userid"]
        nvr_password = data["info"]["server"]["password"]
        nvr_ip = data["info"]["server"]["ip"]
        auth = HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
        event_post = f'http://{nvr_ip}/api/sources'


        request_data = event_post
        r = requests.get(request_data,auth=auth)
        camera_info = r.json()
        
        for i in camera_info["sources"]:
            id = i["id"]
            ip = i["address"]

            data["info"]["cameras"].append({"group_no": -1,
                                            "image": {},
                                            "is_connected": 1,
                                            "property": {
                                                "ip": f"{ip}",
                                                "mac": "mac1",
                                                "name": f"\uce74\uba54\ub77c {id}",
                                                "no": f"Camera {id}",
                                                "password": "",
                                                "port": "554",
                                                "stream_no": "Stream 2",
                                                "userid": ""
                                            },
                                            "roi": []})
            
    return data

def refresh_NVR_camera_info(data):
    nvr_id =data["info"]["server"]["userid"]
    nvr_password = data["info"]["server"]["password"]
    nvr_ip = data["info"]["server"]["ip"]
    auth = HTTPBasicAuth(nvr_id, nvr_password) # NVR에 대한 ID / PW
    event_post = f'http://{nvr_ip}/api/sources'


    request_data = event_post
    r = requests.get(request_data,auth=auth)
    NVR_camera_info = r.json()

    for i in NVR_camera_info["sources"]:
        id = i["id"]
        ip = i["address"]
        new_camera_check_flag = 0

        
        for j in range(len(data["info"]["cameras"])):

            if data["info"]["cameras"][j]["property"]["ip"] == ip and str(data["info"]["cameras"][j]["property"]["no"].split(" ")[-1]) == str(id):
                new_camera_check_flag = 1
                break

        if new_camera_check_flag == 0:
            # print(f"add {id}")
            data["info"]["cameras"].append({"group_no": -1,
                                            "image": {},
                                            "is_connected": 1,
                                            "property": {
                                                "ip": f"{ip}",
                                                "mac": "mac1",
                                                "name": f"\uce74\uba54\ub77c {id}",
                                                "no": f"Camera {id}",
                                                "password": "",
                                                "port": "554",
                                                "stream_no": "Stream 2",
                                                "userid": ""
                                            },
                                            "roi": []})
    return data

        
def restart_NVR_camera(camera_info_dict, nvr_ip, nvr_id, nvr_password):
    auth = HTTPBasicAuth(nvr_id, nvr_password)

    for camera_id, camera_info in camera_info_dict.items():
        # print(camera_id)
        event_post = f'http://{nvr_ip}/api/cameras/{str(camera_id)}'
        headers = {
            "Content-Type": "application/json",
            }
        data = {
            "reboot": True,
            }
        request_data = event_post
        r = requests.put(request_data, headers=headers, json=data, auth=auth)

    time.sleep(1)
