import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR.parent.parent / "static" / "results"

ENV_PATH = BASE_DIR.parents[2] / ".env"
load_dotenv()

# GDRIVE
# Allow insecure transport for local development (http://localhost)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# OAuth token persistence (use absolute paths so uvicorn cwd tidak bermasalah)
TOKEN_FILE = os.getenv("TOKEN_FILE", str(BASE_DIR / "token.json"))
CLIENT_SECRETS_FILE = os.getenv("CLIENT_SECRETS_FILE", str(BASE_DIR / "client_secrets.json"))

# OAuth scopes
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Google Drive & local watcher defaults
TARGET_FOLDER_ID = os.getenv("TARGET_FOLDER_ID", "1PKm4EjaKmV6DM57i3Wzg7u2Cwc1zlQDY")
# default ke folder RESULT_DIR (absolute path) supaya watcher bekerja pasti
# LOCAL_FOLDER_PATH = os.getenv("LOCAL_FOLDER_PATH", str(RESULT_DIR))