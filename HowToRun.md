# ⚾ 투수 교체 예측 시스템 (Streamlit Edition)

투수 교체 타이밍을 데이터로 예측하는 AI 프로젝트입니다.

경기 상황(이닝, 투구 수, 구속 하락, 실점, 구종, 투수 손, 타자 타석 방향 등)을 입력하면 교체 권장 확률과 주요 요인을 시각화하여 보여주는 시스템입니다.

## 🎯 주요 기능

- **AI 기반 예측**: RandomForest와 LSTM 모델을 앙상블하여 투수 교체 시점 예측
- **실시간 대시보드**: Streamlit 기반 사용자 친화적 인터페이스
- **시각화**: 교체 확률 게이지 차트 및 모델별 비교 차트
- **RESTful API**: Flask 기반 백엔드 API

## 📁 프로젝트 구조

```
.
├── backend/
│   ├── api/
│   │   └── app.py              # Flask API 서버
│   ├── model/
│   │   ├── rf_pitch_model.pkl  # RandomForest 모델
│   │   └── lstm_pitch_model.h5 # LSTM 모델
│   ├── data/
│   │   └── train_pitch_replacement.csv  # 학습 데이터
│   ├── train_models.py         # 모델 학습 스크립트
│   ├── download_kaggle_data.py # Kaggle 데이터 다운로드
│   └── requirements.txt        # 백엔드 의존성
├── frontend/
│   ├── app.py                  # Streamlit 대시보드
│   └── requirements.txt        # 프론트엔드 의존성
└── README.md
```

## 🚀 설치 및 실행

### 1. 저장소 클론 및 디렉토리 이동

```bash
cd "E:\datasci fin pro base"
```

### 2. 백엔드 설정

#### 방법 1: 일반 설치 (문제 없을 때)

```bash
cd backend

# Windows PowerShell/CMD에서 (권장)
python -m pip install -r requirements.txt
# 또는
py -m pip install -r requirements.txt

# Linux/Mac 또는 pip가 PATH에 있는 경우
pip install -r requirements.txt
```

#### 방법 2: 문제 해결 설치 (pandas 설치 오류 시)

**PowerShell 사용:**
```powershell
cd backend
. .\install_requirements.ps1
```

**CMD 사용:**
```cmd
cd backend
install_requirements_simple.bat
```

**또는 수동으로 순차 설치:**
```bash
cd backend

# 1. pip 및 빌드 도구 업그레이드
python -m pip install --upgrade pip setuptools wheel

# 2. 기본 패키지 먼저 설치
python -m pip install numpy
python -m pip install pandas
python -m pip install scikit-learn

# 3. 나머지 패키지 설치
python -m pip install flask flask-cors tensorflow joblib
python -m pip install "kagglehub[pandas-datasets]"
```

**참고**: 
- Windows에서 `pip` 명령이 인식되지 않으면 `python -m pip` 또는 `py -m pip`를 사용하세요.
- `metadata-generation-failed` 오류가 발생하면 방법 2를 사용하세요.
- **Python 3.13 사용 시**: pandas 2.2.0 이상이 필요합니다 (이미 requirements.txt에 반영됨).
- **Python 버전 확인**: `python --version`으로 확인하세요.
- Python 3.13은 매우 최신 버전이므로, 일부 패키지 호환성 문제가 있을 수 있습니다. Python 3.11 또는 3.12 사용을 권장합니다.

### 3. 데이터 준비 및 모델 학습 (선택사항)

#### 방법 1: 자동 다운로드 (kagglehub 사용 - 권장)

```bash
# kagglehub 설치 (API 토큰 설정 불필요!)
python -m pip install kagglehub[pandas-datasets]
# 또는: py -m pip install kagglehub[pandas-datasets]

# 데이터 자동 다운로드
python download_kaggle_data.py

# 모델 학습
python train_models.py
```

**장점**: API 토큰 설정이 필요 없어서 가장 간단합니다!

#### 방법 1-2: 자동 다운로드 (기존 Kaggle API 사용)

```bash
# Kaggle API 설치
python -m pip install kaggle
# 또는: py -m pip install kaggle

# Kaggle API 토큰 설정
# 1. https://www.kaggle.com/account 접속
# 2. API 토큰 다운로드 (kaggle.json)
# 3. Windows: C:\Users\[사용자명]\.kaggle\kaggle.json 에 저장

# 데이터 자동 다운로드
python download_kaggle_data.py

# 모델 학습
python train_models.py
```

#### 방법 2: 수동 다운로드

```bash
# 1. https://www.kaggle.com/datasets/pschale/mlb-pitch-data-20152018 에서 데이터 다운로드
# 2. 다운로드한 파일을 backend/data/ 폴더에 넣기
# 3. 데이터 전처리 실행
python download_kaggle_data.py

# 모델 학습
python train_models.py
```

#### 방법 3: 합성 데이터 사용 (가장 간단)

```bash
# 합성 데이터로 모델 학습 (Kaggle 데이터 불필요)
python train_models.py
```

**참고**: 
- 모델 파일이 없어도 더미 모델로 동작합니다
- 실제 예측 정확도를 높이려면 실제 Kaggle 데이터로 학습하는 것을 권장합니다
- 합성 데이터로도 기본적인 예측 기능은 사용 가능합니다

### 4. 백엔드 서버 실행

```bash
.\.venv\Scripts\python.exe .\backend\api\app.py
python api/app.py
```

백엔드 서버가 `http://localhost:5000`에서 실행됩니다.

### 5. 프론트엔드 설정 및 실행

새 터미널에서:

```bash
.\.venv\Scripts\python.exe -m streamlit run .\frontend\app.py
cd frontend

# Windows PowerShell/CMD에서 (권장)
python -m pip install -r requirements.txt
# 또는
py -m pip install -r requirements.txt

# Linux/Mac 또는 pip가 PATH에 있는 경우
pip install -r requirements.txt

# Streamlit 실행
streamlit run app.py
# 또는
python -m streamlit run app.py
```

프론트엔드가 `http://localhost:8501`에서 실행됩니다.

## 📊 사용 방법

1. **백엔드 서버 실행 확인**
   - `http://localhost:5000/health` 접속하여 API 상태 확인

2. **Streamlit 대시보드 접속**
   - 브라우저에서 `http://localhost:8501` 접속

3. **입력 정보 입력**
   - 투수 상태: 이닝, 투구 수, 구속 감소량, 누적 실점
   - 매치업 정보: 구종, 투수 손 방향, 타자 타석 방향, 다음 타자 정보

4. **예측 결과 확인**
   - 교체 권장 확률 (앙상블)
   - RandomForest 및 LSTM 개별 확률
   - 시각화 차트

## 🔧 API 엔드포인트

### POST `/predict`

투수 교체 예측 요청

**Request Body:**
```json
{
  "inning": 6,
  "pitch_count": 90,
  "velocity_drop": 2.5,
  "earned_runs": 2,
  "pitcher_type": "선발투수",
  "pitcher_hand": "R",
  "batter_side": "R",
  "current_batter_ops": 0.8,
  "next_batter_side": "L",
  "next_batter_ops": 0.9
}
```

**Response:**
```json
{
  "rf_prob": 0.6234,
  "lstm_prob": 0.5891,
  "final_prob": 0.6100,
  "recommendation": "유지 가능",
  "status": "success"
}
```

### GET `/health`

API 상태 확인

**Response:**
```json
{
  "status": "healthy",
  "rf_model_loaded": true,
  "lstm_model_loaded": true
}
```

## 📈 모델 정보

### RandomForest
- 투수 상태 기반 교체 확률 예측
- 특징: 이닝, 투구 수, 구속 감소, 실점, 구종, 좌우 매치업 등

### LSTM (신경망)
- 시퀀스 기반 피로도 패턴 학습
- 실제로는 Dense 레이어 기반 신경망으로 구현

### 앙상블
- RandomForest (60%) + LSTM (40%) 가중 평균
- 최종 교체 권장 확률 계산

## 📝 데이터

### Kaggle 데이터셋
- **출처**: [MLB Pitch Data 2015-2018](https://www.kaggle.com/datasets/pschale/mlb-pitch-data-20152018)
- **용도**: 모델 학습용 데이터

### 데이터 컬럼
- `inning`: 이닝
- `pitch_count`: 투구 수
- `velocity_drop`: 구속 감소량 (km/h)
- `earned_runs`: 누적 실점
- `pitcher_type`: 투수 유형 ("선발투수" 또는 "불펜투수")
  - 선발투수: 100구/6이닝 기준 피로도
  - 불펜투수: 20구/1이닝 기준 피로도
- `pitcher_hand`: 투수 손 방향 (R/L)
- `batter_side`: 현재 타자 타석 방향 (R/L/S)
- `current_batter_ops`: 현재 타자 OPS (On-base Plus Slugging)
- `next_batter_side`: 다음 타자 타석 방향
- `next_batter_ops`: 다음 타자 OPS (On-base Plus Slugging)
- `matchup_type`: 좌우 매치업 타입
- `replace_decision`: 교체 여부 (0/1)

## 🛠️ 기술 스택

### Backend
- **Flask**: RESTful API 서버
- **scikit-learn**: RandomForest 모델
- **TensorFlow/Keras**: LSTM 모델
- **pandas/numpy**: 데이터 처리

### Frontend
- **Streamlit**: 웹 대시보드
- **Plotly**: 인터랙티브 차트
- **requests**: API 통신

## 📌 주의사항

1. **모델 파일**: 모델 파일이 없으면 더미 모델로 동작합니다. 실제 예측을 위해서는 `train_models.py`를 실행하여 모델을 학습하세요.

2. **Kaggle 데이터**: 실제 Kaggle 데이터를 사용하려면 Kaggle API 토큰 설정이 필요합니다.

3. **포트 충돌**: 백엔드(5000)와 프론트엔드(8501) 포트가 사용 중이면 변경하세요.

## 🔄 향후 개선 사항

- [ ] 실제 Kaggle 데이터 기반 모델 학습
- [ ] 더 정교한 특징 엔지니어링
- [ ] 모델 성능 평가 지표 추가
- [ ] 히스토리 저장 및 분석 기능
- [ ] 배치 예측 기능

## 📄 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 👥 기여

버그 리포트 및 기능 제안은 이슈로 등록해주세요.

---

**⚾ 투수 교체 예측 시스템 | AI Coach | Powered by RandomForest & LSTM**

---

### 1) 서비스 범위 확장: 불펜 운영 보조 기능 추가

- 기존 기능: `/predict` 기반 투수 교체 확률 예측
- 추가 기능: 팀 단위 불펜 상태 조회 + 상황별 추천 투수 제안
- 핵심 로직:
  - 불펜 에너지 지수(`energy_index`)
  - 위험도(`risk_level`)
  - 투수별 등판 가능성(`availability`)
  - 이닝/점수차/타자유형 반영 추천 점수(`recommendation_score`)

### 2) 백엔드 API 신규 엔드포인트

기존 `/predict`, `/health`는 유지되며, 아래 API가 추가되었습니다.

- `GET /teams`
  - KBO 팀 목록 조회
- `GET /bullpen/status?team=<team_name>`
  - 팀 불펜 요약 상태 조회 (에너지 지수/위험도/지표)
- `GET /bullpen/pitchers?team=<team_name>`
  - 팀 투수별 상태 목록 조회
  - 로스터 데이터 사용 불가 시 `503` + `ROSTER_UNAVAILABLE`
- `POST /bullpen/recommend`
  - 입력 상황(이닝/점수차/타자유형)에 맞는 추천 투수 반환

#### `POST /bullpen/recommend` 예시

Request:
```json
{
  "team": "LG Twins",
  "inning": 8,
  "score_diff": 1,
  "batter_side": "L",
  "count": 2
}
```

Response (요약):
```json
{
  "status": "success",
  "team": "LG Twins",
  "context": {
    "inning": 8,
    "score_diff": 1,
    "batter_side": "L"
  },
  "bullpen": {
    "energy_index": 67.4,
    "risk_level": "caution"
  },
  "recommendations": [
    {
      "name": "홍길동",
      "handed": "L",
      "recommendation_score": 0.81
    }
  ],
  "reasons": [
    "최근 3일 피로 지표 반영",
    "이닝/점수차 레버리지 반영",
    "좌우 매치업 반영"
  ]
}
```

### 3) 데이터 소스 계층 추가

- `backend/data_sources/thesportsdb_client.py`
  - TheSportsDB에서 팀/최근 경기 데이터 조회
  - 외부 API 실패 시 fallback 팀 목록 사용
- `backend/data_sources/kbodata_client.py`
  - `kbodata` 기반 팀 투수 로스터 조회
  - Selenium + ChromeDriver 사용
  - 타임아웃/캐시/오프시즌 fallback 고려

### 4) 프론트엔드 멀티페이지 확장

- 기존 메인 예측 화면: `frontend/app.py` (유지)
- 신규 페이지: `frontend/pages/1_Bullpen_Dashboard.py`
  - 팀 선택
  - 불펜 체력 시각화(bar chart + 테이블)
  - 상황별 추천 투수 출력

실행 시 Streamlit 사이드바/페이지 목록에서 불펜 대시보드를 함께 사용할 수 있습니다.

### 5) 신규 의존성 (백엔드)

기존 라이브러리에 더해 아래가 추가되었습니다.

- `requests`
- `kbodata`
- `selenium`
- `webdriver-manager`

`backend/requirements.txt` 재설치를 권장합니다.

```bash
cd backend
python -m pip install -r requirements.txt
```

### 6) 신규 환경변수 (선택/권장)

- `THESPORTSDB_API_KEY`
  - TheSportsDB API 키 (미설정 시 기본 공개 키 사용)
- `KBO_CHROMEDRIVER_PATH`
  - ChromeDriver 경로 직접 지정 시 사용
- `KBO_ROSTER_TIMEOUT_SEC`
  - 로스터 조회 타임아웃(초)
- `KBO_ROSTER_SCAN_LIMIT_SEC`
  - 과거 월 스캔 제한 시간(초)
- `KBO_ROSTER_CACHE_TTL_SEC`
  - 로스터 캐시 유지 시간(초)
- `FRONTEND_API_TIMEOUT_SEC`
  - 프론트엔드 API 호출 타임아웃(초)

### 7) 동작/장애 대응 참고

- 외부 데이터 연동 실패 시에도 일부 기능은 fallback 데이터로 동작합니다.
- 단, 팀별 투수 로스터가 확보되지 않으면 `/bullpen/pitchers`, `/bullpen/recommend`는 `503`을 반환할 수 있습니다.
- 이 경우 응답의 `error_code`, `roster_reason` 필드로 원인을 확인할 수 있습니다.
