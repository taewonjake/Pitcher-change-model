# 클라우드 확장 설정 가이드 (CloudFront + SSM + RDS + S3)

## 1. GitHub Actions 시크릿 설정
`Settings -> Secrets and variables -> Actions`에서 아래 값을 등록합니다.

- `AWS_REGION` (예: `ap-northeast-2`)
- `SSM_ENABLED` (`true` 또는 `false`)
- `SSM_PARAMETER_PATH` (예: `/bullpen/prod/`)
- `SSM_PARAMETER_NAMES` (선택, 콤마로 구분)
- `SSM_WITH_DECRYPTION` (`true`)
- `SSM_OVERRIDE_ENV` (`false`)
- `DATABASE_URL` (예: `postgresql+psycopg2://user:pass@host:5432/dbname`)
- `S3_BUCKET_NAME` (예: `bullpen-prod-archive`)
- `S3_PREDICTION_PREFIX` (예: `predictions`)
- `CLOUDFRONT_DOMAIN` (예: `dxxxxx.cloudfront.net`)

## 2. SSM 파라미터 이름 규칙
백엔드는 파라미터 경로의 마지막 세그먼트를 환경변수 키로 매핑합니다.

예시:
- `/bullpen/prod/database_url` -> `DATABASE_URL`
- `/bullpen/prod/s3_bucket_name` -> `S3_BUCKET_NAME`
- `/bullpen/prod/thesportsdb_api_key` -> `THESPORTSDB_API_KEY`

## 3. IAM 권한 (EC2 역할)
다음 권한을 허용해야 합니다.
- `ssm:GetParameters`
- `ssm:GetParametersByPath`
- `s3:PutObject` (대상 버킷/프리픽스)
- `rds-db:connect`는 비밀번호 인증 방식에서는 필수가 아니지만, 보안 그룹/네트워크 경로는 반드시 열려 있어야 함

## 4. 검증 엔드포인트
- `GET /health`
- `GET /infra/status`
- `GET /infra/predictions?limit=10`

## 5. 안전한 적용 순서
1. 확장 기능을 모두 끈 상태로 배포
2. SSM만 활성화
3. RDS만 활성화
4. S3만 활성화
5. 마지막에 모두 활성화하고 `/infra/status`로 확인
