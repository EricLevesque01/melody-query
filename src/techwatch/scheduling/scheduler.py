"""Scheduling engine — APScheduler integration for watch execution."""

from __future__ import annotations

import json
import logging
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from techwatch.config import get_settings
from techwatch.models import SearchQuery, Watch, WatchTrigger
from techwatch.models.enums import CanonicalCondition, WatchStatus
from techwatch.persistence.database import get_session, init_db
from techwatch.persistence.repos import OfferRepo, WatchRepo

logger = logging.getLogger(__name__)


def execute_watch(watch_id: str) -> str:
    """Execute a single watch run: search -> score -> detect deals -> alert.

    Returns a status string: 'completed', 'not_found', 'not_active', or 'error'.
    """
    from techwatch.agents.deal_analyst import evaluate_watch_triggers
    from techwatch.agents.orchestrator import SearchOrchestrator

    init_db()
    started_at = datetime.utcnow()

    with get_session() as session:
        watch_repo = WatchRepo(session)
        offer_repo = OfferRepo(session)

        row = watch_repo.get(watch_id)
        if not row:
            logger.info("Watch %s not found", watch_id)
            return "not_found"
        if row.status != WatchStatus.ACTIVE.value:
            logger.info("Watch %s is not active (status=%s), skipping", watch_id, row.status)
            return "not_active"

        logger.info("Executing watch %s: %s", watch_id, row.raw_query)

        # Build search query from watch config
        conditions = [CanonicalCondition(c) for c in row.get_conditions()]
        query = SearchQuery(
            raw_query=row.raw_query,
            budget=row.budget,
            country=row.country,
            postal_code=row.postal_code,
            currency=row.currency,
            conditions=conditions or list(CanonicalCondition),
            top_n=row.top_n,
        )

        # Execute search
        settings = get_settings()
        has_openai = bool(settings.openai_api_key.get_secret_value())
        orchestrator = SearchOrchestrator(skip_llm=not has_openai)

        try:
            response = orchestrator.search(query)
        except Exception as e:
            logger.error("Watch %s search failed: %s", watch_id, e)
            watch_repo.log_run(
                watch_id, started_at, datetime.utcnow(),
                results_count=0, alerts_fired=False,
                errors=[str(e)],
            )
            return "error"
        finally:
            orchestrator.close()

        # Evaluate triggers
        watch_model = Watch(
            watch_id=watch_id,
            raw_query=row.raw_query,
            triggers=[
                WatchTrigger(**t) for t in row.get_triggers()
            ],
        )

        alert = evaluate_watch_triggers(watch_model, response.results, offer_repo)

        # Send digest if alert triggered
        if alert.should_alert and row.email:
            try:
                _send_digest(row, alert, response.results)
            except Exception as e:
                logger.error("Digest send failed for watch %s: %s", watch_id, e)

        # Log the run
        watch_repo.update_last_run(watch_id, datetime.utcnow())
        watch_repo.log_run(
            watch_id, started_at, datetime.utcnow(),
            results_count=len(response.results),
            alerts_fired=alert.should_alert,
            errors=response.errors or None,
        )

        logger.info(
            "Watch %s complete: %d results, alerts=%s",
            watch_id, len(response.results), alert.should_alert,
        )

        return "completed"


def _send_digest(watch_row, alert, results) -> None:
    """Send an email digest for triggered alerts."""
    from techwatch.email.renderer import render_digest
    from techwatch.email.smtp import send_email
    from techwatch.models.narrative import DigestEntry, DigestPayload

    entries = []
    for r in results[:10]:
        if r.offer.offer_id in alert.top_offer_ids:
            entries.append(DigestEntry(
                offer_id=r.offer.offer_id,
                title=r.product.title,
                headline=r.analysis.explanation or "Deal found",
                price_display=f"{r.offer.pricing.currency} {r.offer.pricing.total_landed_cost:.2f}",
                condition_display=r.offer.condition.canonical.value,
                trigger_reason=alert.triggered_rules[0] if alert.triggered_rules else "",
                url=r.offer.url,
            ))

    payload = DigestPayload(
        watch_id=watch_row.watch_id,
        watch_query=watch_row.raw_query,
        entries=entries,
        summary=alert.summary,
        generated_at_display=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )

    subject, body = render_digest(payload)
    send_email(to=watch_row.email, subject=subject, body=body)


def start_daemon() -> None:
    """Start the blocking scheduler daemon."""
    init_db()
    scheduler = BlockingScheduler()

    # Load active watches
    with get_session() as session:
        watch_repo = WatchRepo(session)
        watches = watch_repo.list_active()

    for watch in watches:
        try:
            trigger = CronTrigger.from_crontab(watch.schedule)
            scheduler.add_job(
                execute_watch,
                trigger=trigger,
                args=[watch.watch_id],
                id=f"watch_{watch.watch_id}",
                replace_existing=True,
                misfire_grace_time=300,
            )
            logger.info("Scheduled watch %s: %s", watch.watch_id, watch.schedule)
        except Exception as e:
            logger.error("Failed to schedule watch %s: %s", watch.watch_id, e)

    if not scheduler.get_jobs():
        logger.warning("No active watches to schedule")
        return

    # Graceful shutdown
    def _shutdown(sig, frame):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Daemon started with %d watches", len(scheduler.get_jobs()))
    scheduler.start()
