# Python 버전 호환성 안내

## 문제: Python 3.13과 pandas 2.1.4 호환성 문제

**오류 원인:**
- Python 3.13은 2024년 10월에 출시된 매우 최신 버전입니다.
- pandas 2.1.4는 Python 3.13을 지원하지 않습니다 (Python 3.9-3.12까지만 지원).
- Python 3.13의 내부 API 변경으로 인해 빌드 오류가 발생합니다.

## 해결 방법

### 방법 1: pandas를 최신 버전으로 업그레이드 (권장)

Python 3.13을 사용하는 경우, pandas 2.2.0 이상을 사용해야 합니다:

```bash
python -m pip install --upgrade pandas>=2.2.0 numpy>=1.26.0
```

이미 `requirements.txt`를 업데이트했습니다.

### 방법 2: Python 버전을 다운그레이드

Python 3.12 또는 3.11을 사용하는 것을 권장합니다:

1. Python 3.12 또는 3.11 다운로드 및 설치
2. 가상환경 재생성:
   ```bash
   # 기존 가상환경 삭제
   Remove-Item .venv -Recurse -Force
   
   # Python 3.12로 새 가상환경 생성
   py -3.12 -m venv .venv
   
   # 가상환경 활성화
   .venv\Scripts\Activate.ps1
   
   # 패키지 설치
   python -m pip install -r requirements.txt
   ```

## 현재 설정

- **Python 버전**: 3.13
- **pandas 버전**: >=2.2.0 (Python 3.13 지원)
- **numpy 버전**: >=1.26.0 (Python 3.13 지원)

## 참고

- Python 3.13은 매우 최신 버전이므로 일부 패키지가 아직 완전히 지원하지 않을 수 있습니다.
- 프로덕션 환경에서는 Python 3.11 또는 3.12 사용을 권장합니다.
- pandas 2.2.0 이상은 Python 3.13을 공식적으로 지원합니다.











