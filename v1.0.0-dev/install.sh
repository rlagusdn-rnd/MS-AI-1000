#!/bin/bash

mkdir ~/workspace/MS-AI_1000_v1.0/install

cd ~/workspace/MS-AI_1000_v1.0/install

# sh 기반 파일을 생성합니다.
echo "python3 ~/workspace/MS-AI_1000_v1.0/FRONT/front_main.py" > ms-ai.sh

# 생성한 sh 파일을 실행하는 .desktop 파일을 생성합니다.
echo "[Desktop Entry]
Encoding=UTF-8
Name=MS-AI_1000_v1.0
Type=Application
Path=/home/$USER/workspace/MS-AI_1000_v1.0/install
Icon=/home/$USER/workspace/MS-AI_1000_v1.0/FRONT/HTML/images/icon2.png
Exec=sh ms-ai.sh
Terminal=true" > ms-ai.desktop

# 생성한 .desktop 파일을 /usr/share/applications 경로로 복사합니다.
sudo cp ms-ai.desktop /usr/share/applications/
