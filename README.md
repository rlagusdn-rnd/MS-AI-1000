# MS-AI-1000 — 지능형 CCTV 실시간 영상분석 엔진

> **원 저장소:** https://github.com/diddytpq/MS-AI-1000 (선임 개발자 주도 개발)
> 본 저장소는 팀 프로젝트 참여 이력 정리를 위한 사본입니다. 기여 범위는 아래 참조.

NVR/RTSP 다채널 영상에서 **배회·침입·쓰러짐·싸움 등 이상행동을 실시간 탐지**하고
관제 클라이언트로 알람을 전송하는 온프레미스 AI 분석 서버.
㈜마이크로시스템 상용 제품(MS-AI1000)의 분석 서버 코어이며, 코드 원저작권은 회사에 있습니다.

---

## 참여 범위

2인 팀 프로젝트로 **주 개발은 선임 개발자**가 담당했습니다.
당시 팀은 공유 서버에서 작업하고 **커밋을 선임 계정으로 일원화**하는 방식이라,
개별 기여가 git 히스토리에 분리되어 남아 있지 않습니다.

### 본 저장소 코드에 반영된 기여

| 영역 | 내용 | 위치 |
|---|---|---|
| **RTSP/GStreamer 파이프라인 안정화** | `rtspsrc` caps 명시(`application/x-rtp,media=video,encoding-name=H264`)로 스트림 협상 실패 해결. NVR 경유 → 카메라 직결(`:554/stream1`) 경로 전환 | `v1.7.0-dev/back/ms_ai_main.py` |
| **SigLIP 입력 전처리 개선** | crop 최소 해상도 224 → 448 상향. bbox 면적비(2% / 5%) 기반 **3단계 적응형 패딩** 적용으로 소형 객체 인식 품질 개선 | `v1.7.0-dev/back/HAR.py` `adjust_coordinates_and_crop` |
| **transformers 버전 호환성 대응** | `get_text_features` / `get_image_features` 반환 타입 분기 처리 (`pooler_output` 폴백) | `v1.7.0-dev/back/ms_ai_main.py` |

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
NVR / RTSP 카메라
      │  (GStreamer / OpenCV)
      ▼
  프레임 수집  ──►  YOLO 객체 탐지  ──►  BoxMot 추적 (Track ID 유지)
                                            │
                                            ▼
                                     이벤트 판정 로직
                          (ROI 폴리곤 · 체류시간 · 행동분류 HAR · SigLIP)
                                            │
                                            ▼
                        알람 전송  ──►  NVR / 관제 클라이언트
```

## 주요 구성 (v1.7.0-dev)

| 파일 | 줄수 | 역할 |
|---|---:|---|
| `back/ms_ai_main.py` | 1,524 | 분석 엔진 메인 루프 — 프레임 수집·탐지·추적·이벤트 판정 |
| `back/ms_labeler_utils.py` | 1,165 | 라벨링/학습 데이터 처리 |
| `AI_core_main.py` | 1,002 | AI 코어 프로세스 관리 · 다채널 디스패치 |
| `back/utils.py` | 982 | ROI 판정, IOU, 알람 전송, 카메라 정보 갱신 |
| `main.py` | 914 | 서버 진입점 · 소켓 통신 |
| `back/HAR.py` | 502 | 행동인식(Human Activity Recognition) |
| `back/ms_trash_back_tracking.py` | 298 | 무단투기 역추적 |

## 탐지 이벤트

배회 · 침입 · 방화 · 무단투기 · 쓰러짐 · 싸움

## 기술 스택

Python 3.10 · PyTorch · Ultralytics YOLO · BoxMot · SigLIP · VLM · OpenCV · GStreamer · Docker

## 실행

```bash
docker build -f ms-ai.dockerfile -t ms-ai:1.7.0 .
docker run -it --gpus all --network host --ipc host \
  -v $HOME/workspace:/root/workspace ms-ai:1.7.0
python main.py
```

## 버전

`v1.0.0-dev` ~ `v1.7.0-dev` — 제품 버전별 개발 이력.
