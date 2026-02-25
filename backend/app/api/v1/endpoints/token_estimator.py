from __future__ import annotations

import csv
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from io import StringIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.jobs.model import Job
from app.modules.sessions.model import PhotoSession
from app.modules.users.model import User

router = APIRouter(prefix="/token-estimator", tags=["token-estimator"])

try:
    WIB = ZoneInfo("Asia/Jakarta")
except ZoneInfoNotFoundError:
    # Windows environments may not have IANA tz database installed.
    WIB = timezone(timedelta(hours=7))
PRICE_PER_EVENT_REQ = Decimal("0.04")


class TokenEstimatorRowOut(BaseModel):
    id: int
    user_name: str
    user_id: int
    mode: str
    error: str | None = None
    price_per_req: float
    timestamp: str


class TokenEstimatorSummaryOut(BaseModel):
    total_requests: int
    price_per_req: float
    total_cost: float
    currency: str = "USD"


class TokenEstimatorReportOut(BaseModel):
    rows: list[TokenEstimatorRowOut]
    summary: TokenEstimatorSummaryOut


def _validate_range(start_date: date, end_date: date) -> None:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")


def _to_utc_naive_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    start_wib = datetime.combine(start_date, time.min, tzinfo=WIB)
    end_wib_exclusive = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=WIB)
    start_utc = start_wib.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_wib_exclusive.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def _to_wib_text(value: datetime | None) -> str:
    if value is None:
        value = datetime.utcnow()

    if value.tzinfo is None:
        utc_value = value.replace(tzinfo=timezone.utc)
    else:
        utc_value = value.astimezone(timezone.utc)

    return utc_value.astimezone(WIB).strftime("%Y-%m-%d %H:%M:%S")


def _query_rows(
    db: Session,
    *,
    start_utc: datetime,
    end_utc: datetime,
) -> list[TokenEstimatorRowOut]:
    query_rows = (
        db.query(Job, PhotoSession, User)
        .join(PhotoSession, Job.session_id == PhotoSession.id)
        .join(User, PhotoSession.user_id == User.id)
        .filter(
            Job.mode == "event",
            Job.status == "done",
            Job.error_message.is_(None),
            Job.created_at >= start_utc,
            Job.created_at < end_utc,
        )
        .order_by(Job.created_at.asc(), Job.id.asc())
        .all()
    )

    price = float(PRICE_PER_EVENT_REQ)

    return [
        TokenEstimatorRowOut(
            id=job.id,
            user_name=user.name,
            user_id=user.id,
            mode=job.mode,
            error=job.error_message,
            price_per_req=price,
            timestamp=_to_wib_text(job.created_at),
        )
        for job, _session, user in query_rows
    ]


def _build_summary(rows: list[TokenEstimatorRowOut]) -> TokenEstimatorSummaryOut:
    total_requests = len(rows)
    total_cost = float((Decimal(total_requests) * PRICE_PER_EVENT_REQ).quantize(Decimal("0.01")))
    return TokenEstimatorSummaryOut(
        total_requests=total_requests,
        price_per_req=float(PRICE_PER_EVENT_REQ),
        total_cost=total_cost,
    )


@router.get("/report", response_model=TokenEstimatorReportOut)
def get_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    _validate_range(start_date, end_date)
    start_utc, end_utc = _to_utc_naive_range(start_date, end_date)
    rows = _query_rows(db, start_utc=start_utc, end_utc=end_utc)
    summary = _build_summary(rows)
    return TokenEstimatorReportOut(rows=rows, summary=summary)


@router.get("/export.csv")
def export_csv(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
):
    _validate_range(start_date, end_date)
    start_utc, end_utc = _to_utc_naive_range(start_date, end_date)
    rows = _query_rows(db, start_utc=start_utc, end_utc=end_utc)
    summary = _build_summary(rows)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "user_name", "user_id", "mode", "error", "price_per_req", "timestamp"])
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.user_name,
                row.user_id,
                row.mode,
                row.error or "",
                f"{row.price_per_req:.2f}",
                row.timestamp,
            ]
        )

    writer.writerow([])
    writer.writerow(["total_requests", summary.total_requests])
    writer.writerow(["price_per_req", f"{summary.price_per_req:.2f}"])
    writer.writerow(["total_cost", f"{summary.total_cost:.2f}"])
    writer.writerow(["currency", summary.currency])

    filename = f"token_estimator_{start_date}_{end_date}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=buf.getvalue(), media_type="text/csv; charset=utf-8", headers=headers)
