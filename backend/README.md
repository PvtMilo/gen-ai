# AI Generative Backend

Backend for AI Generative services.

## Event Maintenance (Bulk Delete)

- Endpoints:
  - `POST /api/v1/event-maintenance/preview-delete`
  - `POST /api/v1/event-maintenance/execute-delete`
- Current password: `event-cleanup-admin`
- Password source: hardcoded `EVENT_CLEANUP_PASSWORD` in
  `backend/app/api/v1/endpoints/event_maintenance.py`
