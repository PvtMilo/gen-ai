import json
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import CLIENT_SECRETS_FILE, SCOPES, TOKEN_FILE


def _save_credentials(creds: Credentials) -> None:
    token_path = Path(TOKEN_FILE)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")


def _load_credentials() -> Credentials | None:
    token_path = Path(TOKEN_FILE)
    if not token_path.exists():
        return None

    try:
        return Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except (ValueError, json.JSONDecodeError):
        return None


def _to_utc_iso(dt: datetime | None) -> str | None:
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def get_credentials() -> Credentials:
    creds = _load_credentials()

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)
        return creds

    # Fallback to interactive auth flow (dev)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080)
    _save_credentials(creds)
    return creds


def get_drive_service():
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


def get_credentials_status() -> dict:
    checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    token_path = Path(TOKEN_FILE)

    if not token_path.exists():
        return {
            "ok": False,
            "status": "missing_token",
            "message": "Google Drive token not found. Please authorize Google Drive first.",
            "expiry": None,
            "has_refresh_token": False,
            "refreshed": False,
            "checked_at": checked_at,
        }

    creds = _load_credentials()
    if not creds:
        return {
            "ok": False,
            "status": "invalid_token_file",
            "message": "Google Drive token file is invalid. Re-authorize Google Drive.",
            "expiry": None,
            "has_refresh_token": False,
            "refreshed": False,
            "checked_at": checked_at,
        }

    refreshed = False

    if not creds.valid and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_credentials(creds)
            refreshed = True
        except Exception as exc:
            return {
                "ok": False,
                "status": "refresh_failed",
                "message": f"Google Drive token refresh failed: {exc}",
                "expiry": _to_utc_iso(creds.expiry),
                "has_refresh_token": bool(creds.refresh_token),
                "refreshed": False,
                "checked_at": checked_at,
            }

    if creds.valid:
        return {
            "ok": True,
            "status": "authorized",
            "message": "Google Drive is authorized.",
            "expiry": _to_utc_iso(creds.expiry),
            "has_refresh_token": bool(creds.refresh_token),
            "refreshed": refreshed,
            "checked_at": checked_at,
        }

    if creds.expired and not creds.refresh_token:
        return {
            "ok": False,
            "status": "expired_no_refresh_token",
            "message": "Google Drive token is expired and missing refresh token. Re-authorize required.",
            "expiry": _to_utc_iso(creds.expiry),
            "has_refresh_token": False,
            "refreshed": False,
            "checked_at": checked_at,
        }

    return {
        "ok": False,
        "status": "unauthorized",
        "message": "Google Drive is not authorized. Re-authorize required.",
        "expiry": _to_utc_iso(creds.expiry),
        "has_refresh_token": bool(creds.refresh_token),
        "refreshed": False,
        "checked_at": checked_at,
    }
