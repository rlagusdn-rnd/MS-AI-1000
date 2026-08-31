# 베이스 이미지로 Ubuntu 24.04 사용
FROM nvcr.io/nvidia/tensorrt:24.12-py3

RUN echo "Asia/Seoul" | tee /etc/timezone

RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y \
    libgstreamer1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-vaapi \
    gstreamer1.0-tools \
    ninja-build \
    libxcb-shape0 \
    libxcb-shape0-dev \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb-render0 \
    libxcb-keysyms1 \
    libxcb-icccm4 \
    libxcb-xkb1 \
    libxcb-image0 \
    libxcb-randr0 \
    libxcb-util1 \
    fonts-nanum \
    python3 \
    python3-pip \
    xserver-xorg-video-mga \
    libgtk2.0-dev libgtk-3-dev pkg-config

RUN pip install --upgrade pip setuptools


RUN pip install ninja \
            packaging \
            opencv-python


RUN git clone https://github.com/facebookresearch/sam2.git 
RUN CMAKE_GENERATOR=Ninja pip install -e ./sam2/
            
RUN pip install --no-cache-dir --ignore-installed \
								numpy==1.26.4 \
								ultralytics \
                boxmot \
                fastapi \
                uvicorn \
                transformers\
                accelerate \
                einops \
                timm \
                sentencepiece \
                apscheduler \
                aiortc \
                protobuf \
                onnx \
                onnxslim \
                onnxruntime-gpu \
                dill \
                bitsandbytes

RUN apt-get install libturbojpeg && pip install -U git+https://github.com/lilohuang/PyTurboJPEG.git

RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126

RUN CMAKE_GENERATOR=Ninja pip install flash-attn --no-build-isolation
ENV USE_FLASH_ATTENTION=1

RUN echo 'export DISPLAY=:0' >> /root/.bashrc
