from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.jobs.model import Job

router = APIRouter(prefix="/gallery", tags=["gallery"])


@router.get("")
def list_gallery(limit: Optional[int] = 100, db: Session = Depends(get_db)):
    query = (
        db.query(Job)
        .filter(
            Job.status == "done",
            or_(Job.compressed_image_path.isnot(None), Job.result_image_path.isnot(None)),
        )
        .order_by(Job.id.desc())
    )

    if limit and limit > 0:
        query = query.limit(limit)

    items = []
    for job in query.all():
        image_url = job.compressed_image_path or job.result_image_path
        if not image_url:
            continue
        items.append(
            {
                "id": job.id,
                "url": image_url,
                "drive_link": job.drive_link,
                "download_link": job.download_link,
                "qr_url": job.qr_url,
            }
        )

    return items
