import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _to_env_key(parameter_name: str) -> str:
    # Example: /bullpen/prod/database_url -> DATABASE_URL
    key = parameter_name.strip().split("/")[-1]
    return key.upper().replace("-", "_")


class CloudRuntime:
    def __init__(self) -> None:
        self.ssm_report: Dict[str, Any] = {
            "enabled": _as_bool(os.getenv("SSM_ENABLED", "false")),
            "loaded": 0,
            "source": "env",
            "errors": [],
        }
        self._db_engine = None
        self._db_error: Optional[str] = None
        self._s3_client = None
        self._s3_error: Optional[str] = None
        self._init_optional_integrations()

    def _init_optional_integrations(self) -> None:
        self.load_env_from_ssm()
        self._init_db_engine()
        self._init_s3_client()

    def load_env_from_ssm(self) -> Dict[str, Any]:
        if not self.ssm_report["enabled"]:
            return self.ssm_report

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
        except Exception as exc:  # pragma: no cover
            self.ssm_report["errors"].append(f"boto3 unavailable: {exc}")
            return self.ssm_report

        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "ap-northeast-2"
        override_existing = _as_bool(os.getenv("SSM_OVERRIDE_ENV", "false"))
        parameter_names = [
            n.strip()
            for n in os.getenv("SSM_PARAMETER_NAMES", "").split(",")
            if n.strip()
        ]
        parameter_path = os.getenv("SSM_PARAMETER_PATH", "").strip()
        decrypt = _as_bool(os.getenv("SSM_WITH_DECRYPTION", "true"))

        if not parameter_names and not parameter_path:
            self.ssm_report["errors"].append("No SSM_PARAMETER_NAMES or SSM_PARAMETER_PATH configured.")
            return self.ssm_report

        client = boto3.client("ssm", region_name=region)
        loaded_count = 0

        try:
            if parameter_path:
                paginator = client.get_paginator("get_parameters_by_path")
                for page in paginator.paginate(
                    Path=parameter_path,
                    Recursive=True,
                    WithDecryption=decrypt,
                ):
                    for param in page.get("Parameters", []):
                        env_key = _to_env_key(param["Name"])
                        if override_existing or not os.getenv(env_key):
                            os.environ[env_key] = param.get("Value", "")
                            loaded_count += 1
            else:
                response = client.get_parameters(
                    Names=parameter_names,
                    WithDecryption=decrypt,
                )
                for param in response.get("Parameters", []):
                    env_key = _to_env_key(param["Name"])
                    if override_existing or not os.getenv(env_key):
                        os.environ[env_key] = param.get("Value", "")
                        loaded_count += 1

                invalid = response.get("InvalidParameters", [])
                if invalid:
                    self.ssm_report["errors"].append(f"Invalid parameters: {', '.join(invalid)}")

            self.ssm_report["loaded"] = loaded_count
            self.ssm_report["source"] = "ssm"
        except (BotoCoreError, ClientError) as exc:
            self.ssm_report["errors"].append(str(exc))

        return self.ssm_report

    def _init_db_engine(self) -> None:
        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            return

        try:
            from sqlalchemy import create_engine, text

            self._db_engine = create_engine(database_url, pool_pre_ping=True, future=True)
            with self._db_engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS prediction_events (
                            id VARCHAR(64) PRIMARY KEY,
                            created_at TIMESTAMP NOT NULL,
                            request_json TEXT NOT NULL,
                            response_json TEXT NOT NULL
                        )
                        """
                    )
                )
        except Exception as exc:
            self._db_error = str(exc)
            self._db_engine = None

    def _init_s3_client(self) -> None:
        bucket = os.getenv("S3_BUCKET_NAME", "").strip()
        if not bucket:
            return

        try:
            import boto3

            region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
            self._s3_client = boto3.client("s3", region_name=region)
        except Exception as exc:
            self._s3_error = str(exc)
            self._s3_client = None

    def status(self) -> Dict[str, Any]:
        return {
            "cloudfront_domain": os.getenv("CLOUDFRONT_DOMAIN", "").strip(),
            "ssm": self.ssm_report,
            "rds": {
                "enabled": bool(os.getenv("DATABASE_URL", "").strip()),
                "ready": self._db_engine is not None,
                "error": self._db_error,
            },
            "s3": {
                "enabled": bool(os.getenv("S3_BUCKET_NAME", "").strip()),
                "ready": self._s3_client is not None,
                "bucket": os.getenv("S3_BUCKET_NAME", "").strip(),
                "error": self._s3_error,
            },
        }

    def save_prediction(self, request_payload: Dict[str, Any], response_payload: Dict[str, Any]) -> None:
        event_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        request_json = json.dumps(request_payload, ensure_ascii=False)
        response_json = json.dumps(response_payload, ensure_ascii=False)

        if self._db_engine is not None:
            try:
                from sqlalchemy import text

                with self._db_engine.begin() as conn:
                    conn.execute(
                        text(
                            """
                            INSERT INTO prediction_events (id, created_at, request_json, response_json)
                            VALUES (:id, :created_at, :request_json, :response_json)
                            """
                        ),
                        {
                            "id": event_id,
                            "created_at": created_at,
                            "request_json": request_json,
                            "response_json": response_json,
                        },
                    )
            except Exception as exc:
                self._db_error = str(exc)

        if self._s3_client is not None:
            bucket = os.getenv("S3_BUCKET_NAME", "").strip()
            prefix = os.getenv("S3_PREDICTION_PREFIX", "predictions").strip("/")
            key = f"{prefix}/{created_at.strftime('%Y/%m/%d')}/{event_id}.json"
            body = json.dumps(
                {
                    "id": event_id,
                    "created_at": created_at.isoformat(),
                    "request": request_payload,
                    "response": response_payload,
                },
                ensure_ascii=False,
            ).encode("utf-8")
            try:
                self._s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=body,
                    ContentType="application/json",
                )
            except Exception as exc:
                self._s3_error = str(exc)

    def recent_predictions(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self._db_engine is None:
            return []

        safe_limit = max(1, min(limit, 100))
        try:
            from sqlalchemy import text

            with self._db_engine.connect() as conn:
                rows = conn.execute(
                    text(
                        """
                        SELECT id, created_at, request_json, response_json
                        FROM prediction_events
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"limit": safe_limit},
                ).mappings()
                return [
                    {
                        "id": row["id"],
                        "created_at": str(row["created_at"]),
                        "request": json.loads(row["request_json"]),
                        "response": json.loads(row["response_json"]),
                    }
                    for row in rows
                ]
        except Exception as exc:
            self._db_error = str(exc)
            return []
