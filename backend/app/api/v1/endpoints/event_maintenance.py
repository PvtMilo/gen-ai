from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import APP_DIR, RESULTS_DIR
from app.db.session import get_db
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.users.model import User

router = APIRouter(prefix="/event-maintenance", tags=["event-maintenance"])

try:
    WIB = ZoneInfo("Asia/Jakarta")
except ZoneInfoNotFoundError:
    # Windows environments may not have IANA tz database installed.
    WIB = timezone(timedelta(hours=7))
EVENT_CLEANUP_PASSWORD = "event-cleanup-admin"


class EventDeleteIn(BaseModel):
    start_date: date
    end_date: date
    password: str


class EventDeletePreviewOut(BaseModel):
    jobs_count: int
    result_files_count: int
    sessions_to_delete_count: int
    users_to_delete_count: int
    missing_files_count: int


class EventDeleteExecuteOut(BaseModel):
    jobs_deleted_count: int
    result_files_target_count: int
    result_files_deleted_count: int
    sessions_deleted_count: int
    users_deleted_count: int
    missing_files_count: int
    file_delete_warnings: list[str]


class _DeletePlan(BaseModel):
    job_ids: list[int]
    session_ids_to_delete: list[int]
    user_ids_to_delete: list[int]
    result_files: list[str]
    missing_files_count: int


def _validate_password(password: str) -> None:
    if password != EVENT_CLEANUP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid password")


def _validate_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")


def _to_utc_naive_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_wib = datetime.combine(start_date, time.min, tzinfo=WIB)
    end_wib_exclusive = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=WIB)
    return (
        start_wib.astimezone(timezone.utc).replace(tzinfo=None),
        end_wib_exclusive.astimezone(timezone.utc).replace(tzinfo=None),
    )


def _resolve_result_file(result_image_path: str) -> Path | None:
    if not result_image_path or not result_image_path.startswith("/static/results/"):
        return None

    abs_path = (APP_DIR / result_image_path.lstrip("/")).resolve()
    root = RESULTS_DIR.resolve()
    if root not in abs_path.parents:
        return None
    return abs_path


def _build_delete_plan(db: Session, *, start_utc: datetime, end_utc: datetime) -> _DeletePlan:
    jobs = (
        db.query(Job)
        .filter(
            Job.mode == "event",
            Job.created_at >= start_utc,
            Job.created_at < end_utc,
        )
        .order_by(Job.id.asc())
        .all()
    )

    job_ids = [job.id for job in jobs]
    session_ids = {job.session_id for job in jobs}

    result_files_set: set[str] = set()
    missing_files_count = 0

    for job in jobs:
        if not job.result_image_path:
            continue
        resolved = _resolve_result_file(job.result_image_path)
        if not resolved:
            continue
        result_files_set.add(str(resolved))

    for path_str in result_files_set:
        if not Path(path_str).exists():
            missing_files_count += 1

    session_ids_to_delete: set[int] = set()
    user_ids_to_delete: set[int] = set()

    if session_ids and job_ids:
        remaining_session_rows = (
            db.query(Job.session_id)
            .filter(Job.session_id.in_(session_ids), Job.id.notin_(job_ids))
            .distinct()
            .all()
        )
        remaining_sessions = {row[0] for row in remaining_session_rows}
        session_ids_to_delete = set(session_ids) - remaining_sessions

    if session_ids_to_delete:
        session_rows = (
            db.query(PhotoSession.id, PhotoSession.user_id)
            .filter(PhotoSession.id.in_(session_ids_to_delete))
            .all()
        )
        candidate_user_ids = {row[1] for row in session_rows}
        if candidate_user_ids:
            remaining_user_rows = (
                db.query(PhotoSession.user_id)
                .filter(
                    PhotoSession.user_id.in_(candidate_user_ids),
                    PhotoSession.id.notin_(list(session_ids_to_delete)),
                )
                .distinct()
                .all()
            )
            remaining_user_ids = {row[0] for row in remaining_user_rows}
            user_ids_to_delete = set(candidate_user_ids) - remaining_user_ids

    return _DeletePlan(
        job_ids=job_ids,
        session_ids_to_delete=sorted(session_ids_to_delete),
        user_ids_to_delete=sorted(user_ids_to_delete),
        result_files=sorted(result_files_set),
        missing_files_count=missing_files_count,
    )


@router.post("/preview-delete", response_model=EventDeletePreviewOut)
def preview_delete(payload: EventDeleteIn, db: Session = Depends(get_db)):
    _validate_password(payload.password)
    _validate_range(payload.start_date, payload.end_date)

    start_utc, end_utc = _to_utc_naive_range(payload.start_date, payload.end_date)
    plan = _build_delete_plan(db, start_utc=start_utc, end_utc=end_utc)

    return EventDeletePreviewOut(
        jobs_count=len(plan.job_ids),
        result_files_count=len(plan.result_files),
        sessions_to_delete_count=len(plan.session_ids_to_delete),
        users_to_delete_count=len(plan.user_ids_to_delete),
        missing_files_count=plan.missing_files_count,
    )


@router.post("/execute-delete", response_model=EventDeleteExecuteOut)
def execute_delete(payload: EventDeleteIn, db: Session = Depends(get_db)):
    _validate_password(payload.password)
    _validate_range(payload.start_date, payload.end_date)

    start_utc, end_utc = _to_utc_naive_range(payload.start_date, payload.end_date)
    plan = _build_delete_plan(db, start_utc=start_utc, end_utc=end_utc)

    jobs_deleted_count = 0
    sessions_deleted_count = 0
    users_deleted_count = 0

    if plan.job_ids:
        jobs_deleted_count = (
            db.query(Job)
            .filter(Job.id.in_(plan.job_ids))
            .delete(synchronize_session=False)
        )

    if plan.session_ids_to_delete:
        sessions_deleted_count = (
            db.query(PhotoSession)
            .filter(PhotoSession.id.in_(plan.session_ids_to_delete))
            .delete(synchronize_session=False)
        )

    if plan.user_ids_to_delete:
        users_deleted_count = (
            db.query(User)
            .filter(User.id.in_(plan.user_ids_to_delete))
            .delete(synchronize_session=False)
        )

    db.commit()

    file_deleted_count = 0
    missing_files_count = 0
    file_delete_warnings: list[str] = []

    for path_str in plan.result_files:
        path = Path(path_str)
        if not path.exists():
            missing_files_count += 1
            continue
        try:
            path.unlink()
            file_deleted_count += 1
        except Exception as e:
            file_delete_warnings.append(f"{path.name}: {e}")

    return EventDeleteExecuteOut(
        jobs_deleted_count=jobs_deleted_count,
        result_files_target_count=len(plan.result_files),
        result_files_deleted_count=file_deleted_count,
        sessions_deleted_count=sessions_deleted_count,
        users_deleted_count=users_deleted_count,
        missing_files_count=missing_files_count,
        file_delete_warnings=file_delete_warnings,
    )
