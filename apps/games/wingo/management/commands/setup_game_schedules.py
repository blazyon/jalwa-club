from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Setup Celery beat schedules for all games (all Wingo modes + K3 + 5D)'

    def handle(self, *args, **options):

        # ── Wingo 1MIN: check every 10 seconds ───────────────────────
        s10, _ = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.update_or_create(
            name='Wingo 1MIN Round Cycle',
            defaults={
                'task': 'apps.games.wingo.tasks.run_wingo_1min_cycle',
                'interval': s10,
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        # ── Wingo 3MIN: check every 15 seconds ───────────────────────
        s15, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.update_or_create(
            name='Wingo 3MIN Round Cycle',
            defaults={
                'task': 'apps.games.wingo.tasks.run_wingo_3min_cycle',
                'interval': s15,
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        # ── Wingo 5MIN: check every 20 seconds ───────────────────────
        s20, _ = IntervalSchedule.objects.get_or_create(every=20, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.update_or_create(
            name='Wingo 5MIN Round Cycle',
            defaults={
                'task': 'apps.games.wingo.tasks.run_wingo_5min_cycle',
                'interval': s20,
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        # ── K3: check every 15 seconds ───────────────────────────────
        PeriodicTask.objects.update_or_create(
            name='K3 Round Cycle',
            defaults={
                'task': 'apps.games.k3.tasks.run_k3_round_cycle',
                'interval': s15,
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        # ── 5D: check every 30 seconds ───────────────────────────────
        s30, _ = IntervalSchedule.objects.get_or_create(every=30, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.update_or_create(
            name='5D Round Cycle',
            defaults={
                'task': 'apps.games.five_d.tasks.run_fived_round_cycle',
                'interval': s30,
                'args': json.dumps([]),
                'enabled': True,
            }
        )

        # Clean up old single Wingo task if exists
        PeriodicTask.objects.filter(name='Wingo Round Cycle').delete()

        self.stdout.write(self.style.SUCCESS(
            '✅ Game schedules configured:\n'
            '   Wingo 1MIN → every 10s\n'
            '   Wingo 3MIN → every 15s\n'
            '   Wingo 5MIN → every 20s\n'
            '   K3         → every 15s\n'
            '   5D         → every 30s\n'
        ))
