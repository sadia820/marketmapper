import csv
import io
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import Business, Job
from app.schemas import BusinessOut, BusinessPage, JobOut, UploadResult
from app.services.ingest import IngestError, parse_upload
from app.worker.queue import enqueue_businesses

router = APIRouter(prefix="/jobs", tags=["jobs"])

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
EXPORT_COLUMNS = ["business_name", "website", "city", "country", "status", "industry", "summary",
                  "size_estimate", "gaps", "recommended_offers", "offer_reasons", "priority",
                  "outreach_angle", "confidence"]


def _get_job(db: DbSession, job_id: str) -> Job:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


def _export_row(b: Business) -> list[str]:
    offers = b.offers or []
    return [
        b.business_name, b.final_url or b.website, b.city, b.country, b.site_status or b.status.value,
        b.industry or "", b.summary or "", b.size_estimate or "", "; ".join(b.gaps or []),
        "; ".join(o["name"] for o in offers),
        " | ".join(f"{o['name']}: {o.get('reason', '')}" for o in offers),
        b.priority or "", b.outreach_angle or "", b.confidence or "",
    ]


@router.post("", response_model=UploadResult, status_code=status.HTTP_201_CREATED)
def create_job(
    db: DbSession, user: CurrentUser, file: Annotated[UploadFile, File()]
) -> UploadResult:
    settings = get_settings()
    content = file.file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            f"File is larger than {settings.max_upload_mb} MB")
    try:
        parsed = parse_upload(file.filename or "upload.csv", content, settings.max_rows_per_upload)
    except IngestError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    job = Job(owner_id=user.id, filename=file.filename or "upload", total=len(parsed.rows))
    job.businesses = [
        Business(position=i, **vars(row)) for i, row in enumerate(parsed.rows, start=1)
    ]
    db.add(job)
    db.commit()

    enqueue_businesses([b.id for b in job.businesses])
    db.refresh(job)
    return UploadResult(job=JobOut.model_validate(job), ignored_columns=parsed.ignored_columns)


@router.get("", response_model=list[JobOut])
def list_jobs(db: DbSession, _: CurrentUser, limit: int = Query(50, le=200)) -> list[Job]:
    return list(db.scalars(select(Job).order_by(Job.created_at.desc()).limit(limit)))


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: DbSession, _: CurrentUser) -> Job:
    return _get_job(db, job_id)


@router.get("/{job_id}/businesses", response_model=BusinessPage)
def list_businesses(
    job_id: str,
    db: DbSession,
    _: CurrentUser,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> BusinessPage:
    _get_job(db, job_id)
    base = select(Business).where(Business.job_id == job_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(base.order_by(Business.position).offset(offset).limit(limit))
    return BusinessPage(items=[BusinessOut.model_validate(b) for b in items], total=total)


@router.get("/{job_id}/export.csv")
def export_csv(job_id: str, db: DbSession, _: CurrentUser) -> StreamingResponse:
    job = _get_job(db, job_id)
    rows = sorted(
        db.scalars(select(Business).where(Business.job_id == job_id)),
        key=lambda b: (PRIORITY_ORDER.get(b.priority or "", 3), b.position),
    )
    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM so Excel opens UTF-8 correctly
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)
    writer.writerows(_export_row(b) for b in rows)
    name = job.filename.rsplit(".", 1)[0] + "-results.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: DbSession, _: CurrentUser) -> None:
    db.delete(_get_job(db, job_id))
    db.commit()
