"""Background tasks run by RQ workers (`rq worker research`)."""
import logging
from datetime import UTC, datetime

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models import Business, BusinessStatus, Job, JobStatus
from app.services.research.pipeline import run_research
from app.services.research.types import BusinessInput

log = logging.getLogger(__name__)
FINAL_STATES = {BusinessStatus.done, BusinessStatus.failed}


def _now() -> datetime:
    return datetime.now(UTC)


def research_business(business_id: int) -> None:
    """Research a single business and record progress on its job.

    Safe to retry: a business that already finished is skipped, and job counters
    are updated with atomic SQL increments so many workers can run in parallel.
    """
    with SessionLocal() as db:
        business = db.get(Business, business_id)
        if business is None or business.status in FINAL_STATES:
            return

        business.status = BusinessStatus.researching
        db.execute(
            update(Job)
            .where(Job.id == business.job_id, Job.status == JobStatus.queued)
            .values(status=JobStatus.running, started_at=_now())
        )
        db.commit()

        failed = False
        try:
            site, analysis = run_research(BusinessInput(
                business_name=business.business_name, website=business.website,
                city=business.city, country=business.country, notes=business.notes,
            ))
            business.final_url = site.url or None
            business.site_status = site.status
            business.pages_read = site.pages_read
            business.industry = analysis.industry
            business.summary = analysis.summary
            business.services = analysis.services
            business.size_estimate = analysis.size_estimate
            business.gaps = analysis.gaps
            business.offers = analysis.offers
            business.priority = analysis.priority
            business.outreach_angle = analysis.outreach_angle
            business.confidence = analysis.confidence
            business.mode = analysis.mode
            business.status = BusinessStatus.done
        except Exception as exc:
            log.exception("Research failed for business %s", business_id)
            failed = True
            business.status = BusinessStatus.failed
            business.error = str(exc)[:500]

        db.execute(
            update(Job)
            .where(Job.id == business.job_id)
            .values(processed=Job.processed + 1, failed_count=Job.failed_count + int(failed))
        )
        db.execute(
            update(Job)
            .where(Job.id == business.job_id, Job.processed >= Job.total,
                   Job.status != JobStatus.completed)
            .values(status=JobStatus.completed, finished_at=_now())
        )
        db.commit()
