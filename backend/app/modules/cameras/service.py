import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import CAPTURED_DIR, DIGICAM_ORIGINAL_DIR
from app.integrations.digicamcontrol_client import get_latest_file, trigger_capture

__all__ = ["capture_and_save_photo"]

DEFAULT_TIMEOUT_SECONDS = 5.0
POLL_INTERVAL_SECONDS = 0.5


def capture_and_save_photo(
    original_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> str:
    """
    1. Trigger capture di digiCamControl (kamera jepret)
    2. Tunggu file baru muncul di folder original_dir (folder digiCamControl)
    3. Copy file baru itu ke output_dir (backend/static/captured)
    4. Return nama file (bukan path lengkap)

    original_dir: folder tempat digiCamControl menyimpan foto asli
    output_dir: folder tujuan untuk file final yang diakses web
    """
    source_dir = original_dir or DIGICAM_ORIGINAL_DIR
    dest_dir = output_dir or CAPTURED_DIR

    if not source_dir.exists():
        raise RuntimeError(f"Original directory does not exist: {source_dir}")

    before_file = get_latest_file(source_dir)
    before_mtime = before_file.stat().st_mtime if before_file else None

    trigger_capture()

    latest_file: Optional[Path] = None
    deadline = time.time() + DEFAULT_TIMEOUT_SECONDS

    while time.time() < deadline:
        time.sleep(POLL_INTERVAL_SECONDS)
        candidate = get_latest_file(source_dir)
        if not candidate:
            continue

        if before_mtime is None or candidate.stat().st_mtime > before_mtime:
            latest_file = candidate
            break

    if latest_file is None:
        raise RuntimeError("No new file detected in digiCamControl folder after capture")

    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp_prefix = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    dest_name = f"{timestamp_prefix}_{latest_file.name}"
    dest_path = dest_dir / dest_name

    shutil.copy2(latest_file, dest_path)

    return dest_name
