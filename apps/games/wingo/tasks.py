import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('apps')


def _run_cycle_for_mode(mode: str):
    """Core logic: settle expired rounds and ensure open round exists for a mode."""
    from .models import WingoRound
    from .services import settle_round, get_or_create_current_round

    now = timezone.now()
    expired_rounds = WingoRound.objects.filter(
        mode=mode,
        status=WingoRound.Status.OPEN,
        ends_at__lte=now
    )
    for round_obj in expired_rounds:
        logger.info(f"Settling expired Wingo[{mode}] round #{round_obj.round_number}")
        settle_round(round_obj.id)

    # Ensure there's always an open round
    get_or_create_current_round(mode=mode)


@shared_task(bind=True, max_retries=3, name='apps.games.wingo.tasks.run_wingo_1min_cycle')
def run_wingo_1min_cycle(self):
    """Celery beat task for 1-minute Wingo rounds."""
    try:
        _run_cycle_for_mode('1MIN')
    except Exception as exc:
        logger.error(f"Wingo 1MIN cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3, name='apps.games.wingo.tasks.run_wingo_3min_cycle')
def run_wingo_3min_cycle(self):
    """Celery beat task for 3-minute Wingo rounds."""
    try:
        _run_cycle_for_mode('3MIN')
    except Exception as exc:
        logger.error(f"Wingo 3MIN cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)


@shared_task(bind=True, max_retries=3, name='apps.games.wingo.tasks.run_wingo_5min_cycle')
def run_wingo_5min_cycle(self):
    """Celery beat task for 5-minute Wingo rounds."""
    try:
        _run_cycle_for_mode('5MIN')
    except Exception as exc:
        logger.error(f"Wingo 5MIN cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)


# Keep backward-compat alias
@shared_task(bind=True, max_retries=3)
def run_wingo_round_cycle(self):
    try:
        _run_cycle_for_mode('1MIN')
    except Exception as exc:
        logger.error(f"Wingo cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)
