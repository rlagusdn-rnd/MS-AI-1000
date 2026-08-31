import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import numpy as np
import json
import xml.etree.ElementTree as ET
import time

# enevt_svg='http://117.17.159.143:80/api/events/svg' # 이벤트 주소
# event_post='http://117.17.159.143:80/api/events' # 이벤트 주소



enevt_svg='http://117.17.159.2:80/api/events/svg' # 이벤트 주소
event_post='http://117.17.159.2:80/api/events' # 이벤트 주소
ip = "117.17.159.146"
camera_num = 3
# ip = "117.17.159.140"

# svg_data = '''<svg id="posco-ai" source-address={} viewBox="0 0 1920 1080"> 
#             <polygon style="fill-opacity:0; 
#                     stroke:rgb(255, 0, 255); 
#                     stroke-opacity:0.8; 
#                     stroke-width:5.0" points=" 330,229 24,569 27,1055 675,1064 912,488  " /> 

#             <polygon style="fill-opacity:0;
#                     stroke:rgb(255, 0, 255);
#                     stroke-opacity:0.8;
#                     stroke-width:5.0"
#                     points=" 915,499 696,1055 1851,1075  " /> '''.format(ip)
svg_data = '''<svg id="posco-ai" channels="{}" viewBox="0 0 1920 1080"> 
            <polygon style="fill-opacity:0; 
                    stroke:rgb(0, 0, 255); 
                    stroke-opacity:0.8; 
                    stroke-width:5.0" points=" 330,229 24,569 27,1055 675,1064 912,488  " /> 

            <polygon style="fill-opacity:0;
                    stroke:rgb(255, 0, 255);
                    stroke-opacity:0.8;
                    stroke-width:5.0"
                    points=" 915,499 696,1055 1851,1075  " /> '''.format(camera_num)

auth=HTTPBasicAuth("admin", 1234)

#/api/events?types=33&since=2017-02-20
r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))
print(r)


# while True:
    # r = requests.post(enevt_svg,auth=auth, data="".join(svg_data+'''</svg>'''))
#     request_data = event_post + f"?types=33&since=2023-07-07:00:00:00&until=2023-07-08:19:00:00&total=True"
# nvr_ip = "117.17.159.143"
# event_post = f'http://{nvr_ip}/api/cameras/{str(1)}'
# request_data = event_post
# r = requests.get(request_data,auth=auth)
# print("--------------")
# print(r.json())

    # time.sleep(1)


# enevt_svg='http://117.17.159.147:80/api/events/svg' # 이벤트 주소
# event_post='http://117.17.159.143:80/api/events' # 이벤트 주소
# event_post='http://192.168.0.102:80/api/events' # 이벤트 주소

# alarm_type = 0

# alarm_msg = {
#             "type": 1,
#             "source_address": "117.17.159.147" ,
#             # "devices": [ 15 ],
#             "micro_ai": {
#                 "type": alarm_type,
#                 "object" : 1
#             }
#         }

# r = requests.post(event_post,auth=auth, data=alarm_msg)

# print(r)

# nvr_ip = "192.168.0.102"
# camera_id = 10
# # event_post = f'http://{nvr_ip}/api/cameras/{str(camera_id)}'
# # event_post='http://192.168.0.102:80/api/events' # 이벤트 주소
# event_post='http://117.17.159.143:80/api/events' # 이벤트 주소

# request_data = 'http://117.17.159.143:80/api/events' # 이벤트 주소
# alarm_type = 6

# headers = {
#     "Content-Type": "application/json",
# }
# # data = {
# #     "reboot": True,
# # }

# data = {
#             "type": 70,
#             "source_address": "117.17.159.147" ,
#             # "devices": [ 15 ],
#             "micro_ai": {
#                 "type": alarm_type,
#                 "object" : 1
#             }
#         }

# data = {"type": 70, "source_address": "117.17.159.147", "micro_ai": {"type": 6, "object": 1}}

# r = requests.put(request_data, headers=headers, json=data, auth=auth)

# print(r.json())
# print(r.status_code)
# print(r.text)