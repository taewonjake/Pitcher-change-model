@echo off
REM Windows 배치 파일: 간단한 패키지 설치

echo === 패키지 설치 시작 ===

echo.
echo 1. pip 업그레이드 중...
python -m pip install --upgrade pip

echo.
echo 2. 빌드 도구 업그레이드 중...
python -m pip install --upgrade setuptools wheel

echo.
echo 3. 패키지 설치 중 (순차적으로)...
python -m pip install numpy
python -m pip install pandas
python -m pip install scikit-learn
python -m pip install flask flask-cors
python -m pip install tensorflow
python -m pip install joblib
python -m pip install "kagglehub[pandas-datasets]"

echo.
echo === 설치 완료! ===
pause




