#!/bin/bash

MS_AI_PATH="/home/$USER/workspace/MS-AI_1000/v1.2.0-dev"

mkdir $MS_AI_PATH/install

cd $MS_AI_PATH/install

# sh 기반 파일을 생성합니다.
echo "echo admin123 | xhost + local:docker
docker start ms-ai
docker exec -it ms-ai sh -c \"cd /root/workspace/MS-AI_1000/v1.2.0-dev && python3 main.py\"" > ms-ai.sh

# 생성한 sh 파일을 실행하는 .desktop 파일을 생성합니다.
echo "[Desktop Entry]
Encoding=UTF-8
Name=MS-AI_1000_v1.2
Type=Application
Path=$MS_AI_PATH/install
Icon=$MS_AI_PATH/front/ui/images/icon2.png
Exec=sh ms-ai.sh
Terminal=true" > ms-ai.desktop

# 생성한 .desktop 파일을 /usr/share/applications 경로로 복사합니다.
sudo cp ms-ai.desktop /usr/share/applications/
