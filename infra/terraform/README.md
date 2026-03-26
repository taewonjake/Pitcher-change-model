# Terraform 구조 안내

## 구조
- `envs/dev`, `envs/prod`: 환경별 엔트리포인트
- `modules/network`: VPC/서브넷/라우팅
- `modules/security`: 보안 그룹/IAM
- `modules/ecr`: 이미지 저장소
- `modules/ecs`, `modules/alb`: 확장형 아키텍처(선택)
- `modules/edge`: CloudFront 배포
- `modules/ssm`: 파라미터 생성
- `modules/rds`: PostgreSQL 인스턴스
- `modules/s3`: 아카이브 버킷
- `modules/observability`: CloudWatch 리소스

## 프리 티어 우선 적용 순서
1. EC2 + Docker Compose만 먼저 운영
2. `ssm`, `s3` 추가
3. `edge`(CloudFront) 추가
4. 영속 저장 데모가 필요할 때만 `rds` 추가

## 참고
- 환경별 값은 `*.tfvars`로 분리
- 팀 작업 시 원격 상태 저장소(S3 + DynamoDB lock) 사용 권장
