import json
import mimetypes
import os
from urllib.parse import quote
from datetime import datetime
from pathlib import Path
from typing import Iterable

from googleapiclient.http import MediaFileUpload

from .client import get_drive_service
from .config import RESULTS_DIR, TARGET_FOLDER_ID
from app.core.config import API_BASE_URL

MANIFEST_FILE = Path(__file__).resolve().parent / "uploads.json"


def _load_manifest() -> dict:
    if not MANIFEST_FILE.exists():
        return {}

    try:
        return json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_manifest(data: dict) -> None:
    MANIFEST_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _file_signature(path: Path) -> dict:
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
    }


def build_qr_url(value: str, size: int = 360) -> str:
    encoded = quote(value, safe="")
    base = API_BASE_URL.rstrip("/")
    return f"{base}/api/v1/drive/qr?url={encoded}&size={size}"


def _resolve_local_folder(local_folder: str | Path | None) -> Path:
    if local_folder:
        return Path(local_folder).resolve()

    env_folder = os.getenv("LOCAL_FOLDER_PATH")
    if env_folder:
        return Path(env_folder).resolve()

    return RESULTS_DIR.resolve()


def _iter_result_files(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []

    exts = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    files = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in exts
    ]
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def _ensure_public(service, file_id: str) -> None:
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()


def upload_file_to_drive(
    file_path: str | Path,
    *,
    folder_id: str | None = None,
    service=None,
) -> dict:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    folder_id = folder_id or TARGET_FOLDER_ID
    service = service or get_drive_service()

    mime_type, _ = mimetypes.guess_type(path.name)
    media = MediaFileUpload(str(path), mimetype=mime_type, resumable=True)

    file_meta = {"name": path.name}
    if folder_id:
        file_meta["parents"] = [folder_id]

    created = (
        service.files()
        .create(body=file_meta, media_body=media, fields="id, webViewLink, webContentLink")
        .execute()
    )

    file_id = created.get("id")
    if not file_id:
        raise RuntimeError("Google Drive upload failed (missing file id).")

    _ensure_public(service, file_id)

    info = (
        service.files()
        .get(fileId=file_id, fields="id, name, webViewLink, webContentLink")
        .execute()
    )

    drive_link = info.get("webViewLink") or info.get("webContentLink")
    if not drive_link:
        drive_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"

    download_link = info.get("webContentLink")
    if not download_link:
        download_link = f"https://drive.google.com/uc?id={file_id}&export=download"
    qr_target = download_link or drive_link
    qr_url = build_qr_url(qr_target)

    return {
        "file_id": file_id,
        "name": info.get("name") or path.name,
        "drive_link": drive_link,
        "download_link": download_link,
        "qr_url": qr_url,
    }


def upload_results_folder(
    *,
    local_folder: str | Path | None = None,
    folder_id: str | None = None,
    limit: int | None = None,
    force: bool = False,
) -> list[dict]:
    folder = _resolve_local_folder(local_folder)
    manifest = _load_manifest()
    service = get_drive_service()

    results: list[dict] = []

    for idx, path in enumerate(_iter_result_files(folder)):
        if limit and idx >= limit:
            break

        signature = _file_signature(path)
        cache_key = str(path)
        cached = manifest.get(cache_key)

        if cached and cached.get("signature") == signature and not force:
            results.append(cached["item"])
            continue

        uploaded = upload_file_to_drive(path, folder_id=folder_id, service=service)

        item = {
            "local_path": str(path),
            "name": path.name,
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
            "drive_file_id": uploaded["file_id"],
            "drive_link": uploaded["drive_link"],
            "download_link": uploaded.get("download_link"),
            "qr_url": uploaded.get("qr_url") or build_qr_url(uploaded["drive_link"]),
        }

        manifest[cache_key] = {
            "signature": signature,
            "item": item,
        }
        results.append(item)

    _save_manifest(manifest)
    return results
