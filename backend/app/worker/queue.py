"""Job queue. Each business is its own task, so N workers research N sites in parallel."""
from functools import lru_cache

from redis import Redis
from rq import Queue, Retry

from app.core.config import get_settings


@lru_cache
def get_queue() -> Queue:
    settings = get_settings()
    return Queue(settings.queue_name, connection=Redis.from_url(settings.redis_url))


def enqueue_businesses(business_ids: list[int]) -> None:
    from app.worker.tasks import research_business  # local import avoids a cycle

    if get_settings().run_jobs_inline:
        for business_id in business_ids:
            research_business(business_id)
        return

    queue = get_queue()
    for business_id in business_ids:
        queue.enqueue(
            research_business,
            business_id,
            job_timeout=180,
            retry=Retry(max=1, interval=10),
        )
