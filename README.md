# MS-AI-1000 (지능형 CCTV 실시간 영상분석 엔진)

> 본 저장소는 팀 프로젝트 참여 이력 정리를 위한 사본입니다. 기여 범위는 아래 참조.

NVR/RTSP 다채널 영상에서 **배회·침입·쓰러짐·싸움 등 이상행동을 실시간 탐지**하고 관제 클라이언트로 알람을 전송하는 AI 분석 서버

---

## 역할 및 참여범위

3인 팀 프로젝트로 RTSP 기반 카메라 입출력 파이프라인, 행동 탐지 파이프라인 구현, 평가 및 검증 담당
사내 서버PC에서 작업 후 일괄 업로드하는 방식으로 협업 수행

### 본 저장소 코드에 반영된 기여

| 영역 | 내용 | 위치 |
|---|---|---|
| **RTSP/GStreamer 파이프라인 안정화** | `rtspsrc` caps 명시(`application/x-rtp,media=video,encoding-name=H264`)로 스트림 협상 실패 해결. NVR 경유 → 카메라 직결(`:554/stream1`) 경로 전환 | `v1.7.0-dev/back/ms_ai_main.py` |
| **SigLIP 입력 전처리 개선** | crop 최소 해상도 224 → 448 상향. bbox 면적비(2% / 5%) 기반 **3단계 적응형 패딩** 적용으로 소형 객체 인식 품질 개선 | `v1.7.0-dev/back/HAR.py` `adjust_coordinates_and_crop` |

### 별도 주도한 작업

- **KISA 지능형 CCTV 성능인증 대응**
  인증 규격 러너 신규 개발(880줄, 신규 함수 35개 — ROI 폴리곤 판정, 맵파일 파서, 규격 결과 XML 생성, 배치 러너).
  KISA 공식 채점식(F1 = 100 × 2pr/(p+r), 정상검출 시간창 GT −2초 ~ +10초) 구현.
  배회 30건 + 침입 30건 = **시험영상 60건 검증**. GStreamer / OpenCV 파이프라인 2종 비교.
  폐쇄망 환경 대응(오프라인 모델 로딩, 의존성 로컬 벤더링).

- **낙상/싸움 탐지 프로토타입 및 다중스트림 처리 검증**
  YOLO 추적 → SigLIP 제로샷 분류 → 통합 파이프라인 → **16채널 멀티프로세싱** 확장까지 단계적 개발.

---

## 아키텍처

```
┌────────────────────────────────────────────────────────────────────┐
│                         NVR (RTSP 서버)                            │
└───────────────────────────────┬────────────────────────────────────┘
                                │ RTSP Stream
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Main Server (FastAPI :65432)                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • REST API Endpoints                                        │  │
│  │  • 스케줄러 (APScheduler)                                     │  │
│  │  • 프로세스 관리                                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬────────────────────────────────────┘
                                │ Process Spawn
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
     │ AI Process  │     │ AI Process  │     │ AI Process  │
     │ (4 cameras) │     │ (4 cameras) │     │ (4 cameras) │
     │ ┌─────────┐ │     │ ┌─────────┐ │     │ ┌─────────┐ │
     │ │  YOLO   │ │     │ │  YOLO   │ │     │ │  YOLO   │ │
     │ │ BotSort │ │     │ │ BotSort │ │     │ │ BotSort │ │
     │ │ SigLip  │ │     │ │ SigLip  │ │     │ │ SigLip  │ │
     │ └─────────┘ │     │ └─────────┘ │     │ └─────────┘ │
     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │ BaseManager 공유 메모리
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                   AI Core Server (FastAPI :1206)                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  • VLM (Qwen3-VL) QnA                                        │  │
│  │  • SAM2 쓰레기 검출                                           │  │
│  │  • GPU 메모리 관리                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## 기술적 구현 및 문제 해결

### 1. RTSP 프레임 지연 해소 — 수집 계층 재설계

**문제**
Opencv기반 디코딩 방식은 프레임을 FIFO 큐에 쌓고 가장 오래된 1장을 반환 -> 실시간 다채널 환경에서 아래 문제 발생
- 지연 누적 : 추론속도가 입력 속도(30fps)보다 느릴경우 지연이 누적됨 

**해결**
GStreamer 활용
-> 오래된 프레임 폐기 & 비동기적 방법 활용 (지연 누적 해결)
-> GPU 디코딩 (nvh264dec)으로 CPU 부하 제거


**결과**
16채널 CCTV 실시간 입력·분석 구현


## 주요 구성 (v1.7.0-dev)

MS-AI-1000/v1.7.0-dev/
├── main.py                 # FastAPI 메인 서버 (REST API, 스케줄러)
├── AI_core_main.py         # VLM/SAM2 AI 코어 서버
├── utils.py                # 공통 유틸리티 (암호화, 데이터 모델)
├── logging_config.py       # 로깅 설정 (RotatingFileHandler)
├── test_falldown_detect.py # 낙상 검출 테스트 모듈
├── ms-ai.dockerfile        # Docker 빌드 설정
├── back/
│   ├── ms_ai_main.py       # AI 분석 엔진 (핵심 로직)
│   ├── ms_labeler_main.py  # 자동 라벨링 모듈
│   ├── ms_labeler_utils.py # 라벨링 유틸리티
│   ├── HAR.py              # 사람 정보 관리 (Human Action Recognition)
│   └── utils.py            # 백엔드 유틸리티
└── cache/                  # 설정 파일 (암호화된 JSON)

## 탐지 이벤트

배회 · 침입 · 방화 · 무단투기 · 쓰러짐 · 싸움

## 기술 스택

Python 3.10 · PyTorch · Ultralytics YOLO · BoxMot · SigLIP · VLM · OpenCV · GStreamer · Docker

## Docker 배포
```
FROM nvcr.io/nvidia/tensorrt:25.03-py3
# CUDA 12.9 + TensorRT + vLLM + Flash Attention
# 하드웨어 가속 GStreamer (nvh264dec)
RUN pip install ultralytics boxmot transformers vllm
```

## 실행

```bash
docker build -f ms-ai.dockerfile -t ms-ai:1.7.0 .
docker run -it --gpus all --network host --ipc host \
  -v $HOME/workspace:/root/workspace ms-ai:1.7.0
python main.py
```

## 버전

`v1.0.0-dev` ~ `v1.7.0-dev` — 제품 버전별 개발 이력.
