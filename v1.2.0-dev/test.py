# # from back.ms_labeler_main import train




# # train(NVR_IP = "117.17.159.143")

# from requests.auth import HTTPBasicAuth
# import requests


# nvr_ip = "192.168.0.249"
# nvr_id = "USER"
# nvr_pw = "Admin13579"

# auth = HTTPBasicAuth(nvr_id, nvr_pw) # NVR에 대한 ID / PW
# camera_post = f'http://{nvr_ip}/api/cameras'
# # try:
# r = requests.get(camera_post,auth=auth, timeout= 3)
# # "<Response [200]>"
# print(str(r))
# print(str(r) == str("<Response [200]>"))


import time

# 테스트용 리스트 생성
my_list = list(range(1000000))

# enumerate() 사용
start_time = time.time()
for index, value in enumerate(my_list):
    pass
print(f"enumerate() duration: {time.time() - start_time} seconds")

# range(len()) 사용
start_time = time.time()
for i in range(len(my_list)):
    _ = my_list[i]
print(f"range(len()) duration: {time.time() - start_time} seconds")