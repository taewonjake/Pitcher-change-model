# AWS 포트폴리오 실행 계획 (확정 아키텍처 기준)

## 1) 목표
- 우리 프로젝트를 `EC2 + Docker Compose` 기반으로 안정 운영한다.
- 여기에 `CloudFront + SSM + RDS + S3`를 단계적으로 붙여 실무형 클라우드 역량을 증명한다.
- 모든 단계에서 비용 리스크를 통제한다.

## 2) 확정 아키텍처
- 컴퓨팅: EC2 1대 (backend/frontend/nginx/certbot, Docker Compose)
- 배포: GitHub Actions (`.github/workflows/deploy.yml`)
- 엣지: CloudFront (EC2 오리진 앞단)
- 비밀/설정값: SSM Parameter Store
- 데이터 저장: RDS PostgreSQL (예측 이벤트 저장)
- 아카이브: S3 (예측 JSON 백업)
- 모니터링: CloudWatch + AWS Budgets + 프리 티어 사용량 알림

## 3) 사전 준비 체크
- [ ] AWS 계정 결제 알림 수신 이메일 확인
- [ ] GitHub Actions 시크릿 등록 권한 확인
- [ ] EC2 SSH 접속 가능 상태 확인
- [ ] 현재 `main` 브랜치 배포가 정상 동작하는지 확인

## 4) 2주 상세 실행 계획

### Week 1: 운영 기반 고정 + CloudFront/SSM 연결

#### 1일차: 비용 가드레일...
- 행동
1. AWS 콘솔 `결제 및 비용 관리 > 예산 > 예산 생성`
2. `0 USD`, `1 USD`, `3 USD` 월별 비용 예산 생성
3. 각 예산에 `실제 비용 100% 도달` 이메일 알림 추가
4. `결제 기본 설정`에서 `프리 티어 사용량 알림 수신` 체크
- 검증
1. 예산 3개가 `활성` 상태인지 확인
2. 알림 메일 수신 확인
- 산출물
1. 예산 설정 스크린샷
2. `docs/cost-estimate.md`에 현재 알림 정책 반영

#### 2일차: EC2 인프라 고정
- 행동
1. EC2 인스턴스 1대만 운영(타입/리전 확정)
2. 보안 그룹 인바운드 규칙 정리: `22(내 IP)`, `80`, `443`
3. EBS 용량 확인, 미사용 스냅샷/볼륨 정리
4. 미연결 Elastic IP가 있으면 해제
- 검증
1. `EC2 > 인스턴스` 실행 중 1대 확인
2. 보안 그룹 규칙이 의도대로 반영되었는지 확인
- 산출물
1. 인프라 점검표(인스턴스/SG/EBS/EIP)

#### 3일차: 배포 파이프라인 점검
- 행동
1. 테스트 커밋 푸시로 GitHub Actions 배포 실행
2. EC2에서 `docker ps`로 컨테이너 상태 확인
3. `/health` 호출로 API 정상 확인
4. 실패 시 이전 이미지로 롤백 리허설
- 검증
1. 배포 성공 시간(시작~완료) 기록
2. 롤백 후 서비스 정상 동작 확인
- 산출물
1. 롤백 절차 초안 (`docs/runbook.md` 반영)

#### 4일차: HTTPS/도메인/CloudFront 연결
- 행동
1. Certbot 갱신 테스트 실행
2. Nginx 설정 확인 및 재시작 테스트
3. CloudFront 배포 생성 후 EC2를 오리진으로 연결
4. CloudFront 도메인으로 접속 테스트
- 검증
1. HTTPS 인증서 정상/만료일 확인
2. CloudFront 경유 접속 시 앱 정상 동작 확인
- 산출물
1. `docs/architecture.md`에 CloudFront 경로 반영

#### 5일차: SSM 연동
- 행동
1. SSM Parameter Store에 운영 파라미터 등록
2. 파라미터 네이밍을 프로젝트 규칙으로 통일
3. EC2 역할(IAM)에 SSM 읽기 권한 부여
4. `SSM_ENABLED=true`로 배포 후 `/infra/status` 확인
- 검증
1. `/infra/status`에서 `ssm.loaded` 값 확인
2. 앱이 기존 기능과 동일하게 동작하는지 확인
- 산출물
1. `docs/cloud-extensions-setup.md`에 실제 파라미터명 기록

#### 6일차: RDS 연동
- 행동
1. RDS PostgreSQL 인스턴스 생성
2. DB 보안 그룹에서 EC2 -> RDS 접근 허용
3. `DATABASE_URL` 시크릿 설정 후 재배포
4. `/predict` 호출 후 `/infra/predictions`로 저장 확인
- 검증
1. `/infra/status`에서 `rds.ready=true` 확인
2. DB에 예측 이벤트가 적재되는지 확인
- 산출물
1. RDS 연결/보안 구성 문서화

#### 7일차: S3 연동
- 행동
1. S3 버킷 생성(공개 차단 기본)
2. EC2 역할(IAM)에 `s3:PutObject` 권한 부여
3. `S3_BUCKET_NAME`, `S3_PREDICTION_PREFIX` 설정 후 재배포
4. `/predict` 호출 후 S3 경로에 JSON 생성 확인
- 검증
1. `/infra/status`에서 `s3.ready=true` 확인
2. S3 객체 생성 시간/경로 확인
- 산출물
1. 저장 경로 규칙 문서화

### Week 2: 운영 안정화 + 포트폴리오 완성

#### 8일차: 장애 리허설 1 (앱 중단)
- 행동
1. backend 컨테이너 의도적 중단
2. 감지 -> 재시작 -> 복구 절차 수행
- 검증
1. 감지 시간, 복구 시간(MTTR) 측정
- 산출물
1. `docs/runbook.md` 절차 업데이트

#### 9일차: 장애 리허설 2 (오배포/롤백)
- 행동
1. 의도적으로 잘못된 설정 배포
2. 이전 정상 버전으로 롤백
- 검증
1. 사용자 영향 시간 측정
- 산출물
1. 배포 실패 대응 절차 확정

#### 10일차: 모니터링/알람 최소셋 완성
- 행동
1. CloudWatch 알람 구성(상태체크, CPU)
2. `/health`, `/infra/status` 점검 루틴 정리
3. 알람 발생 시 대응 담당/절차 명시
- 검증
1. 테스트 알람 발생/복구 플로우 확인
- 산출물
1. 운영 체크리스트 확정

#### 11일차: 성능/비용 점검
- 행동
1. 간단 부하 테스트 수행
2. 응답시간/에러율 기록
3. 로그 보관주기/리소스 크기 점검
- 검증
1. 기준치 대비 개선 여부 확인
- 산출물
1. 성능/비용 요약표

#### 12일차: README 포트폴리오화
- 행동
1. 아키텍처 다이어그램 추가
2. 배포 흐름, 장애 대응, 관측성 섹션 작성
3. 정량 지표(배포시간, MTTR, 월비용) 반영
- 검증
1. 제3자가 README만 보고 재현 가능한지 점검
- 산출물
1. 최종 README 초안

#### 13일차: 문서 정합성 검토
- 행동
1. `docs/architecture.md`, `runbook.md`, `cost-estimate.md`, `cloud-extensions-setup.md` 교차 검토
2. 실제 운영 상태와 문서 불일치 수정
- 검증
1. 문서와 실제 설정값 일치 여부 확인
- 산출물
1. 문서 최종본

#### 14일차: 면접 대비 패키지 완성
- 행동
1. 아키텍처 선택 이유/트레이드오프 정리
2. 장애 대응 사례 2건 요약
3. 비용 통제 사례(알림/정리 정책) 정리
- 검증
1. 3분/10분 설명 버전 각각 리허설
- 산출물
1. 면접 Q&A 시트

## 5) 완료 기준 (Definition of Done)
- [ ] CloudFront 도메인으로 서비스 정상 접속
- [ ] `SSM_ENABLED=true`에서 파라미터 로드 확인
- [ ] RDS에 예측 이벤트 저장 확인
- [ ] S3에 예측 JSON 저장 확인
- [ ] 배포 실패 시 롤백 절차 1회 이상 검증
- [ ] CloudWatch + Budget 알림 정상 동작
- [ ] README/운영문서/면접노트까지 최종 반영

