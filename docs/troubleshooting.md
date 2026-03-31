# 트러블슈팅 기록

## 배포 트러블슈팅

### 1) Docker Compose 미설치/버전 불일치
- 상황: GitHub Actions에서 EC2 배포 실행
- 증상: `Docker Compose is not installed on EC2`, `KeyError: 'ContainerConfig'`
- 원인: EC2의 Compose 설치/버전 상태가 배포 스크립트 기대와 다름
- 조치:
  - EC2에 `docker-compose` 설치
  - 스크립트에서 `docker compose`/`docker-compose` 자동 감지 처리
- 결과: 배포 단계 정상 통과, 컨테이너 기동 성공
- 교훈: 배포 스크립트는 런타임 차이를 흡수해야 재발이 줄어든다.

### 2) HTTPS 설정이 배포 때마다 초기화됨
- 상황: 새 배포 후 HTTPS가 깨지고 HTTP 설정으로 되돌아감
- 증상: `https://` 접속 실패, `https://localhost` 연결 문제
- 원인: 배포 시 `deploy/nginx/nginx.conf`가 기본(HTTP) 파일로 덮어써짐
- 조치:
  - `enable-https.sh` 개선 및 배포 후 HTTPS 자동 적용 로직 추가
  - `HTTPS_DOMAIN`, `HTTPS_EMAIL` 시크릿 기반 자동화
- 결과: 재배포 후에도 HTTPS 유지
- 교훈: 수동 조치가 필요한 설정은 배포 파이프라인에 편입해야 한다.

### 3) Let’s Encrypt 발급 실패
- 상황: 인증서 최초 발급 시도
- 증상: `Permission denied`, `too many certificates ... rate limit`
- 원인:
  - 스크립트 실행 권한 누락
  - 공유 도메인 레이트 리밋에 걸림
- 조치:
  - 스크립트 실행 권한 부여
  - 신규 도메인(`basegram.p-e.kr`)으로 재발급
  - `renew --dry-run`으로 갱신 리허설
- 결과: 인증서 발급/갱신 검증 완료
- 교훈: 인증서 자동화는 권한/도메인 정책(레이트 리밋)까지 고려해야 한다.

### 4) SSM 연동값 로드 실패(`loaded=0`)
- 상황: SSM 활성화 후 `/api/infra/status` 확인
- 증상: `ssm.enabled=true`, `source=ssm`인데 `loaded=0`
- 원인: 앱 조회 리전과 SSM 파라미터 생성 리전 불일치
- 조치:
  - 리전 통일(`ap-southeast-2`)
  - `SSM_PARAMETER_NAMES`에 대상 파라미터 명시
- 결과: `ssm.loaded=2` 확인
- 교훈: 클라우드 연동 문제는 기능보다 리전/계정/권한 정합성이 우선이다.

### 5) RDS 연결 실패(타임아웃 -> DB 없음)
- 상황: `DATABASE_URL` 설정 후 RDS 연동
- 증상:
  - 초기: `connection timed out`
  - 이후: `database "bullpen" does not exist`
- 원인:
  - EC2 -> RDS 네트워크 경로/SG 설정 미완성
  - DB 이름 미생성 상태에서 `/bullpen`으로 접속
- 조치:
  - RDS SG에 EC2 SG 소스 허용(5432)
  - `DATABASE_URL` DB명을 `/postgres`로 조정
- 결과: `rds.ready=true`, `/api/infra/predictions` 저장 성공
- 교훈: RDS 이슈는 네트워크와 DB 스키마 준비를 분리해서 점검해야 빠르다.

## 운영 트러블슈팅

### 6) CloudFront 경유 시 301/504 및 API 경로 불일치
- 상황: CloudFront를 오리진 앞단으로 붙인 직후
- 증상: API 호출이 301/504 또는 HTML 응답으로 반환
- 원인: 원본/프로토콜/동작(Behavior) 설정 불일치, 경로 라우팅 미정합
- 조치:
  - 오리진/프로토콜 정책 재설정
  - `/api/*` 확인 경로로 정상 응답 검증
- 결과: CloudFront 경유 `/api/health` 200 확인
- 교훈: CDN 연동은 경로 단위 라우팅 검증을 별도로 해야 한다.

### 7) Streamlit WebSocket 실패 및 무한 스켈레톤 로딩
- 상황: CloudFront 도메인으로 프론트 페이지 접속
- 증상: `/_stcore/stream` WebSocket 오류, 화면 로딩 정체
- 원인: WebSocket/타임아웃/동작 경로 설정 부족
- 조치:
  - Nginx에 WebSocket 안정 설정 추가(`Connection`, timeout)
  - CloudFront 동작 경로 보완(`/_stcore/*` 계열)
- 결과: 프론트 UI 정상 로드 및 API 상호작용 복구
- 교훈: Streamlit 운영 시 WebSocket 경로와 프록시 타임아웃이 핵심 안정 포인트다.

### 8) 로스터 실시간 수집 실패(`ROSTER_UNAVAILABLE`)
- 상황: Bullpen Dashboard에서 팀 로스터 조회
- 증상: `SessionNotCreatedException`, `ROSTER_UNAVAILABLE` 반복
- 원인: 운영 컨테이너에서 Selenium 기반 실시간 크롤링이 불안정
- 조치:
  - `KBO_ROSTER_ENABLED` 기본 OFF
  - 로스터 실패 시 503 대신 fallback 계산(합성 roster)으로 서비스 지속
  - Chromium/Chromedriver 설치 및 실행 환경 보강
- 결과: 로스터 수집 실패 시에도 핵심 지표/추천 기능 연속 제공
- 교훈: 운영 환경에서는 외부 실시간 크롤링 의존성을 낮추고 fallback이 필수다.

## 공통 재발 방지 체크리스트
- [ ] 배포 전 리전/권한/시크릿 값 정합성 확인
- [ ] 배포 후 `/api/health`, `/api/infra/status` 점검
- [ ] `/api/predict` 호출 후 RDS/S3 저장 성공 확인
- [ ] CloudFront 경유 API/프론트 경로 동작 확인
- [ ] 장애 시 롤백 절차(이전 이미지) 즉시 실행 가능 상태 유지
