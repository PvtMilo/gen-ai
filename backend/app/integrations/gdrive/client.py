import json
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
