# 장애 대응 런북

## 장애 유형 1: 백엔드 5xx 급증
1. `/health`, `/infra/status` 상태 확인
2. EC2에서 `backend` 컨테이너 로그 확인
3. 신규 배포 원인일 경우 이전 이미지 태그로 롤백
4. `/health`와 주요 사용자 플로우로 복구 확인

## 장애 유형 2: RDS 저장 실패
1. `/infra/status`의 `rds.error` 확인
2. `DATABASE_URL`, 보안 그룹, 네트워크 경로 점검
3. AWS 콘솔에서 RDS 인스턴스 상태 확인
4. DB 연동 없이도 예측은 가능하므로 서비스는 유지하고 DB 경로 복구

## 장애 유형 3: S3 업로드 실패
1. `/infra/status`의 `s3.error` 확인
2. IAM 권한(`s3:PutObject`)과 버킷 이름 확인
3. 버킷 리전과 애플리케이션 리전 일치 여부 확인

## 장애 유형 4: SSM 로드 실패
1. `/infra/status`의 `ssm.errors` 확인
2. `SSM_PARAMETER_PATH` 또는 `SSM_PARAMETER_NAMES` 값 점검
3. IAM 권한(`ssm:GetParameters`, `ssm:GetParametersByPath`) 확인
4. 파라미터 수정 후 백엔드 재시작

## 롤백 절차
1. 이전 backend/frontend 이미지로 재배포
2. 원인 확인 전까지 선택 기능(SSM/RDS/S3)은 비활성화 유지
3. 복구 후 SSM -> RDS -> S3 순서로 다시 활성화
