from cryptography.fernet import Fernet
import json

# 키 생성
KEY = "FBRBdZIbc_ULGN_qOlZjdMLDLPPzdRJ2Nb63kX3wuDI="

# 암호화 엔진 생성
fernet = Fernet(KEY)

file_name = "admin_info"

# JSON 파일 읽기
with open(f"./{file_name}.json", "rb") as file:
    # file_data = json.load(file)
    file_data = file.read()

# 파일 데이터 암호화
encrypted_data = fernet.encrypt(file_data)

# 암호화된 데이터를 파일에 저장
# with open(f"../{file_name}.json", "wb") as file:
#     file.write(encrypted_data)
with open(f"./init/{file_name}.json", "wb") as file:
    file.write(encrypted_data)
