# 아키텍처 (AWS 프리 티어 + 포트폴리오 확장)

## 기본 구성 (상시 운영)
- 사용자 -> Nginx(EC2) -> frontend(Streamlit) / backend(Flask)
- 단일 EC2 인스턴스에서 Docker Compose 운영
- GitHub Actions 배포 파이프라인 사용 (`.github/workflows/deploy.yml`)
- Certbot 기반 HTTPS 운영

## 추가한 클라우드 구성요소
- CloudFront: EC2 오리진 앞단 CDN 및 TLS 엣지 엔드포인트
- SSM Parameter Store: 백엔드 런타임 환경변수 소스
- RDS PostgreSQL: 예측 이벤트 영속 저장
- S3: 예측 결과 JSON 아카이브 저장

## 런타임 동작
1. 백엔드가 시작되면 `.env` 환경변수를 먼저 로드
2. `SSM_ENABLED=true`이면 SSM에서 추가 값을 조회해 환경변수로 반영
3. `DATABASE_URL`이 있으면 예측 이벤트를 RDS에 저장
4. `S3_BUCKET_NAME`이 있으면 예측 이벤트 JSON을 S3에도 저장
5. 선택 연동이 일부 실패해도 API 응답은 계속 처리(best effort)

## 추가 API
- `GET /infra/status`: SSM/RDS/S3 준비 상태와 오류 확인
- `GET /infra/predictions?limit=20`: RDS에 저장된 최근 예측 이벤트 조회

## 트레이드오프
- 장점: 저비용을 유지하면서 실무형 클라우드 연동 경험을 보여줄 수 있음
- 한계: 단일 EC2 구조라 완전한 고가용성(HA) 아키텍처는 아님
