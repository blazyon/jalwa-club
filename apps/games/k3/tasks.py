import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('apps')


@shared_task(bind=True, max_retries=3)
def run_k3_round_cycle(self):
    from .models import K3Round
    from .services import settle_round, get_or_create_current_round
    try:
        now = timezone.now()
        expired = K3Round.objects.filter(status=K3Round.Status.OPEN, ends_at__lte=now)
        for round_obj in expired:
            settle_round(round_obj.id)
        get_or_create_current_round()
    except Exception as exc:
        logger.error(f"K3 cycle error: {exc}")
        raise self.retry(exc=exc, countdown=5)
