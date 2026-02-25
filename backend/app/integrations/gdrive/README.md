# Google Drive Integration (Backend)

This folder contains the Google Drive integration used by the backend to upload generated image results and return public links + QR URLs.

## Scope

This integration is responsible for:

- Creating/refreshing Google OAuth credentials.
- Uploading one file to Google Drive.
- Uploading multiple local result files with cache manifest support.
- Setting uploaded files to public read.
- Building QR URL endpoints for download links.
- Supporting API endpoints:
  - `POST /api/v1/drive/upload`
  - `POST /api/v1/drive/sync`
  - `GET /api/v1/drive/qr`

## Folder Contents

- `config.py`
  - Loads environment config and default paths.
  - Defines OAuth scope and target Drive folder.
- `client.py`
  - Handles OAuth token loading, refresh, and interactive authorization flow.
  - Builds Google Drive service client.
- `service.py`
  - Contains upload logic and manifest cache handling.
- `client_secrets.json`
  - Google OAuth client configuration (Desktop app client).
- `token.json`
  - Stored authorized user token/refresh token generated after consent.
- `uploads.json`
  - Optional local manifest cache for `upload_results_folder()`.

## High-Level Flow

1. API calls upload/sync logic.
2. `service.py` requests Drive client via `client.py`.
3. `client.py` attempts to:
   - load `token.json`
   - refresh if expired and refresh token exists
   - fallback to interactive browser auth if needed
4. File uploads to Drive (`files.create`), then permission set to `anyone/reader`.
5. API returns:
   - `file_id`
   - `drive_link`
   - `download_link`
   - `qr_url`

## Dependencies

Defined in `backend/requirements.txt`:

- `google-api-python-client`
- `google-auth`
- `google-auth-oauthlib`
- `qrcode`

Install (from repo root):

```powershell
.\backend\.venv\Scripts\pip install -r backend\requirements.txt
```

## Environment Configuration

Configured through `.env` and defaults in `config.py`.

Supported variables:

- `CLIENT_SECRETS_FILE`
  - Path to OAuth client secrets JSON.
  - Default: `app/integrations/gdrive/client_secrets.json`
- `TOKEN_FILE`
  - Path to token storage file.
  - Default: `app/integrations/gdrive/token.json`
- `TARGET_FOLDER_ID`
  - Google Drive destination folder ID.
- `LOCAL_FOLDER_PATH`
  - Optional local folder for batch upload scanning via `upload_results_folder()`.
  - If not set, falls back to backend static results folder.
- `DRIVE_UPLOAD_SOURCE`
  - Controls source file for job-based upload (`/drive/upload-job`, `/drive/sync`, auto upload after job done).
  - Allowed values: `compressed` or `results`.
  - Default: `compressed`.
- `OAUTHLIB_INSECURE_TRANSPORT`
  - `1` allows local HTTP callback for development.
- `API_BASE_URL`
  - Used for building QR endpoint URL.

## Google Cloud Setup (Required)

1. Create/select Google Cloud project.
2. Enable Google Drive API.
3. Configure OAuth consent screen.
4. Create OAuth client credentials of type Desktop app.
5. Download credentials JSON and place it as:
   - `backend/app/integrations/gdrive/client_secrets.json`

## Authorization (First-Time / Re-Authorization)

Use this when:

- first setup
- `invalid_grant`
- token expired and refresh failed
- `client_secrets.json` changed

### Steps

1. Delete old token file:

```powershell
Remove-Item backend/app/integrations/gdrive/token.json
```

2. Trigger credential creation once:

```powershell
cd backend
.\.venv\Scripts\python -c "from app.integrations.gdrive.client import get_credentials; c = get_credentials(); print('Authorized:', c.valid)"
```

3. Browser opens; login and consent.
4. New `token.json` is saved automatically.

## API Endpoints

### `POST /api/v1/drive/upload`

Uploads a single file to Drive.

- Request: multipart form-data with field `file`.
- Behavior:
  - Temporarily writes file to results folder.
  - Uploads to Google Drive.
  - Deletes temp local file.
- Response (example):

```json
{
  "file_id": "1AbCdEf",
  "name": "result.png",
  "drive_link": "https://drive.google.com/file/d/1AbCdEf/view?usp=sharing",
  "download_link": "https://drive.google.com/uc?id=1AbCdEf&export=download",
  "qr_url": "http://localhost:8000/api/v1/drive/qr?url=..."
}
```

### `POST /api/v1/drive/sync`

Syncs existing completed jobs that have result files.

- Query params:
  - `limit` (optional)
  - `force` (optional, default false)
- Uses `sync_drive_links()` from job service.
- Upload source follows `DRIVE_UPLOAD_SOURCE`:
  - `compressed`: tries `jobs.compressed_image_path`, fallback to `jobs.result_image_path`.
  - `results`: uses `jobs.result_image_path`.
- Updates job columns:
  - `drive_file_id`
  - `drive_link`
  - `download_link`
  - `qr_url`
  - `drive_uploaded_at`

### `GET /api/v1/drive/qr?url=<...>&size=<...>`

Returns PNG QR image for a URL.

## Service Functions

From `service.py`:

- `upload_file_to_drive(file_path, folder_id=None, service=None)`
  - Uploads one file and ensures public permission.
- `upload_results_folder(local_folder=None, folder_id=None, limit=None, force=False)`
  - Batch upload helper with manifest cache (`uploads.json`).
- `build_qr_url(value, size=360)`
  - Builds backend QR endpoint URL from link.

## Automatic Job Integration

Drive upload also runs automatically after successful job processing:

- `app/modules/jobs/service.py` -> `_attach_drive_info(...)`
- Called after job status becomes `done`.
- Upload source also follows `DRIVE_UPLOAD_SOURCE` (`compressed` or `results`).

If upload fails, job stays done, but Drive fields can remain empty.
You can later run `/api/v1/drive/sync`.

## Troubleshooting

### `POST /api/v1/drive/upload` returns 500

Most common causes:

1. Token and client secrets mismatch
   - Delete `token.json` and re-authorize.
2. Expired token + no valid refresh token
   - Re-authorize.
3. Invalid or missing `client_secrets.json`
   - Confirm JSON structure is valid Desktop OAuth config.
4. Drive API not enabled
   - Enable API in Google Cloud project.
5. OAuth consent/test user issue
   - Add your Google account as test user if app is in Testing mode.

### `redirect_uri_mismatch`

- Usually wrong OAuth client type.
- Use Desktop app OAuth client.

### `insufficientPermissions`

- Confirm scope includes Drive access (`https://www.googleapis.com/auth/drive`).
- Re-authorize after scope/client changes.

### Upload succeeded but link inaccessible

- Check `_ensure_public()` call success.
- Verify file permissions in Drive.

## Security Notes

- Never commit real secrets/tokens to git.
- Keep `client_secrets.json` and `token.json` out of source control.
- For production:
  - use HTTPS callback flow
  - avoid `OAUTHLIB_INSECURE_TRANSPORT=1`
  - consider restricted scopes and service-account-based strategy (if architecture allows)

## Quick Health Checklist

- `client_secrets.json` exists and valid.
- `token.json` exists and matches current client.
- `TARGET_FOLDER_ID` points to valid Drive folder.
- Backend can access internet and Google APIs.
- `POST /api/v1/drive/upload` returns non-empty `file_id`.

## Maintenance Tips

- If you rotate OAuth client credentials, delete `token.json` and re-auth.
- If Drive folder changes, update `TARGET_FOLDER_ID` in `.env`.
- If QR domain is wrong, update `API_BASE_URL` in `.env`.
