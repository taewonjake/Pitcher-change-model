# EC2 + Docker + GitHub Actions + Nginx + Certbot 배포 가이드

이 프로젝트는 `Flask(backend)` + `Streamlit(frontend)` 구조입니다.
아래 순서로 설정하면 `SpringBoot 배포 글`과 같은 방식으로 운영할 수 있습니다.

## 1. EC2 초기 설정 (Ubuntu 기준)

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
mkdir -p ~/bullpen-deploy
```

보안 그룹 인바운드:
- `22` (SSH)
- `80` (HTTP)
- `443` (HTTPS)

## 2. DNS 설정

- 도메인 `A 레코드`를 EC2 퍼블릭 IP로 연결합니다.
- 예: `yourdomain.com`, `www.yourdomain.com`

## 3. GitHub Secrets 설정

리포지토리 `Settings > Secrets and variables > Actions`에 아래 값을 추가하세요.

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `EC2_HOST`
- `EC2_USER` (예: `ubuntu`)
- `EC2_SSH_KEY` (EC2 접속용 private key)

## 4. 자동 배포 동작

`main` 브랜치에 push 하면:
1. 백엔드/프론트 이미지를 Docker Hub에 push
2. 배포 파일을 EC2로 복사
3. EC2에서 `docker compose`로 최신 컨테이너 재기동

워크플로 파일:
- `.github/workflows/deploy.yml`

## 5. HTTPS 발급 (최초 1회)

EC2에서 아래를 실행하세요.

```bash
cd ~/bullpen-deploy
chmod +x deploy/scripts/enable-https.sh
./deploy/scripts/enable-https.sh yourdomain.com you@example.com
```

실행 후:
- Certbot이 인증서 발급
- `deploy/nginx/nginx.conf`가 HTTPS 설정으로 교체
- Nginx 재시작

## 6. 서비스 접속

- 프론트: `https://yourdomain.com`
- 백엔드 API: `https://yourdomain.com/api/health`

## 7. 참고

- 프론트는 `API_URL` 환경변수를 읽도록 수정되어, Docker 환경에서 자동으로 `http://backend:5000` 사용
- 백엔드는 Gunicorn으로 실행됨 (`backend/Dockerfile`)
