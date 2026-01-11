from pathlib import Path
import uuid
import requests
from fastapi import UploadFile


def save_image_from_url(
    url: str,
    out_dir: Path,
    ext: str = ".jpg",
    *,
    attempts: int = 5,
    connect_timeout: int = 10,
    read_timeout: int = 180,
    log_prefix: str = "[DOWNLOAD]",
    progress_step: int = 10,   # print tiap 10%
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    out_path = out_dir / filename

    last_err = None

    for attempt in range(1, attempts + 1):
        try:
            with requests.get(
                url,
                stream=True,
                timeout=(connect_timeout, read_timeout),
            ) as r:
                r.raise_for_status()

                total = r.headers.get("Content-Length")
                total_bytes = int(total) if total and total.isdigit() else None

                downloaded = 0
                last_printed = -1

                if total_bytes:
                    print(f"{log_prefix} attempt {attempt}/{attempts} total={total_bytes} bytes")
                else:
                    print(f"{log_prefix} attempt {attempt}/{attempts} total=unknown")

                with out_path.open("wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 256):  # 256KB
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_bytes:
                            pct = int(downloaded * 100 / total_bytes)
                            # print tiap progress_step% (10%, 20%, ...)
                            if pct >= 100:
                                pct = 100
                            if pct // progress_step != last_printed // progress_step:
                                last_printed = pct
                                print(f"{log_prefix} {pct}%")
                        else:
                            # fallback kalau tidak ada Content-Length
                            # print tiap ~1MB
                            if downloaded % (1024 * 1024) < len(chunk):
                                mb = downloaded / (1024 * 1024)
                                print(f"{log_prefix} downloaded {mb:.1f} MB")

                # pastikan selalu ada 100% kalau total_bytes ada
                if total_bytes and last_printed < 100:
                    print(f"{log_prefix} 100%")

                print(f"{log_prefix} completed -> {out_path.name}")
                return out_path

        except Exception as e:
            last_err = e
            # backoff
            sleep_s = min(2 ** (attempt - 1), 10)
            print(f"{log_prefix} attempt {attempt}/{attempts} failed: {e} (retry in {sleep_s}s)")
            time.sleep(sleep_s)

            # hapus file partial sebelum retry
            try:
                if out_path.exists():
                    out_path.unlink()
            except Exception:
                pass

    raise RuntimeError(f"DOWNLOAD_FAILED_AFTER_RETRY: {last_err}")

def save_upload_file(file: UploadFile, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise ValueError("INVALID_FILE_TYPE")

    filename = f"{uuid.uuid4().hex}{ext}"
    out_path = out_dir / filename

    with out_path.open("wb") as f:
        f.write(file.file.read())

    return filename