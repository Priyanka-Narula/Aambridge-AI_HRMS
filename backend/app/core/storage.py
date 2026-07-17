import io
import logging
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from uuid import uuid4

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = logging.getLogger(__name__)


class MinioStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            logger.info("Created MinIO bucket: %s", self.bucket)

    def upload_cv(self, pdf_bytes: bytes, original_filename: str) -> dict[str, str]:
        object_key = f"cvs/{uuid4()}/{_sanitize_filename(original_filename)}"
        self.client.put_object(
            self.bucket,
            object_key,
            io.BytesIO(pdf_bytes),
            length=len(pdf_bytes),
            content_type="application/pdf",
        )
        logger.info("Stored CV in MinIO: %s/%s", self.bucket, object_key)
        return {
            "bucket": self.bucket,
            "object_key": object_key,
            "storage_uri": f"s3://{self.bucket}/{object_key}",
        }

    def download_cv(self, object_key: str) -> bytes:
        response = self.client.get_object(self.bucket, object_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


def object_key_from_storage_uri(storage_uri: str) -> str | None:
    if not storage_uri.startswith("s3://"):
        return None
    _, _, object_key = storage_uri[5:].partition("/")
    return object_key or None


def _sanitize_filename(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[^\w.\-]", "_", name)
    return name or "resume.pdf"


_storage: MinioStorage | None = None


def get_storage() -> MinioStorage:
    global _storage
    if _storage is None:
        _storage = MinioStorage()
    return _storage


def _minio_reachable(endpoint: str, timeout: float = 1.5) -> bool:
    if ":" not in endpoint:
        return False
    host, port_str = endpoint.rsplit(":", 1)
    if not port_str.isdigit():
        return False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, int(port_str)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def init_storage() -> None:
    """Ensure the CV bucket exists. Retries briefly; never blocks API startup."""
    endpoint = settings.MINIO_ENDPOINT
    if not _minio_reachable(endpoint):
        logger.warning("Skipping MinIO bucket init (not reachable at %s)", endpoint)
        return

    for attempt in range(1, 4):
        ex = ThreadPoolExecutor(max_workers=1)
        try:
            fut = ex.submit(get_storage().ensure_bucket)
            fut.result(timeout=5.0)
            logger.info("MinIO bucket ready: %s", settings.MINIO_BUCKET)
            return
        except FuturesTimeoutError:
            logger.warning(
                "MinIO bucket init attempt %s/3 timed out (endpoint %s)",
                attempt,
                endpoint,
            )
        except S3Error:
            logger.exception("MinIO bucket initialization failed (attempt %s/3)", attempt)
        except Exception:
            logger.exception(
                "MinIO bucket initialization failed unexpectedly (attempt %s/3)",
                attempt,
            )
        finally:
            ex.shutdown(wait=False)
        if attempt < 3:
            time.sleep(2)

    logger.warning(
        "MinIO bucket init did not complete; uploads/downloads may fail until MinIO is healthy"
    )
