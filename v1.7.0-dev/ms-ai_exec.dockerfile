# 베이스 이미지로 Ubuntu 24.04 사용
FROM nvcr.io/nvidia/tensorrt:25.03-py3

RUN echo "Asia/Seoul" | tee /etc/timezone

RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
ENV DEBIAN_FRONTEND=noninteractive

ENV TORCH_CUDA_ARCH_LIST="8.6"

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
    ufw \
    libgtk2.0-dev \
    libgtk-3-dev \
    pkg-config \
    build-essential \
    git
    

RUN pip install --upgrade pip setuptools


RUN pip install ninja \
            packaging \
            opencv-python

RUN pip install --no-cache-dir --ignore-installed \
								ultralytics \
                boxmot \
                fastapi \
                uvicorn \
                transformers==4.57.3\
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
                bitsandbytes \
                qwen-vl-utils[decord] \
                autoawq \
                solapi

# RUN git clone https://github.com/facebookresearch/sam2.git 
# RUN CMAKE_GENERATOR=Ninja pip install -e ./sam2/

RUN git clone https://github.com/Gy920/segment-anything-2-real-time.git
RUN pip install --no-build-isolation -e ./segment-anything-2-real-time/

RUN apt-get install libturbojpeg && pip install -U git+https://github.com/lilohuang/PyTurboJPEG.git

RUN pip install --no-cache-dir vllm==0.12.0

RUN pip install torch==2.9.0 torchvision==0.24.0 torchaudio==2.9.0 --index-url https://download.pytorch.org/whl/cu129

RUN pip install numpy==2.2.6 scipy==1.15.3
# RUN MAX_JOBS=2 pip install flash-attn --no-build-isolation
# ENV USE_FLASH_ATTENTION=1
RUN pip install https://github.com/mjun0812/flash-attention-prebuild-wheels/releases/download/v0.4.17/flash_attn-2.8.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl


RUN echo 'export DISPLAY=:0' >> /root/.bashrc

EXPOSE 65432

WORKDIR /root/workspace/MS-AI-1000/v1.7.0-dev

CMD ["python", "main.py"]
