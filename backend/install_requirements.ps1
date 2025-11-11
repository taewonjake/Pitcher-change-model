# Windows PowerShell 스크립트: 패키지 설치 (문제 해결 버전)

Write-Host "=== 패키지 설치 시작 ===" -ForegroundColor Green

# pip 업그레이드
Write-Host "`n1. pip 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# setuptools와 wheel 업그레이드 (빌드 도구)
Write-Host "`n2. 빌드 도구 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade setuptools wheel

# 기본 패키지 먼저 설치 (의존성 해결)
Write-Host "`n3. 기본 패키지 설치 중..." -ForegroundColor Yellow
python -m pip install numpy
python -m pip install pandas
python -m pip install scikit-learn

# 나머지 패키지 설치
Write-Host "`n4. 나머지 패키지 설치 중..." -ForegroundColor Yellow
python -m pip install flask flask-cors
python -m pip install tensorflow
python -m pip install joblib
python -m pip install "kagglehub[pandas-datasets]"

Write-Host "`n=== 설치 완료! ===" -ForegroundColor Green
Write-Host "설치 확인: python -c 'import pandas, sklearn, flask, tensorflow; print(\"모든 패키지 설치 완료!\")'" -ForegroundColor Cyan




