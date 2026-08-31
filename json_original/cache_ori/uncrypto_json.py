from cryptography.fernet import Fernet
import json

# 키 생성
KEY = "FBRBdZIbc_ULGN_qOlZjdMLDLPPzdRJ2Nb63kX3wuDI="

# 암호화 엔진 생성
fernet = Fernet(KEY)

file_name = "setting_info"

# JSON 파일 읽기
with open(f"../{file_name}.json", "rb") as f:
    file = f.read()
    file_tran = fernet.decrypt(file)
    uncrypted_data =  json.loads(file_tran.decode())

# 암호화된 데이터를 파일에 저장
with open(f"./{file_name}.json", "w", encoding="UTF-8") as f:
    f.write(json.dumps(uncrypted_data, indent=4))