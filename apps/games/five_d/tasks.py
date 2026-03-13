import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('apps')


@shared_task(bind=True, max_retries=3)
def run_fived_round_cycle(self):
    from .models import FiveDRound
    from .services import settle_round, get_or_create_current_round
    try:
        now = timezone.now()
        expired = FiveDRound.objects.filter(status=FiveDRound.Status.OPEN, ends_at__lte=now)
        for round_obj in expired:
            settle_round(round_obj.id)
        get_or_create_current_round()
    except Exception as exc:
        logger.error(f"5D cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)
