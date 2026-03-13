import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WingoRound',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('round_number', models.BigIntegerField(unique=True)),
                ('status', models.CharField(
                    choices=[('OPEN', 'Open for Bets'), ('LOCKED', 'Locked (Processing)'), ('COMPLETED', 'Completed')],
                    default='OPEN', max_length=12)),
                ('result_number', models.IntegerField(blank=True, null=True)),
                ('result_color', models.CharField(blank=True, max_length=16)),
                ('result_size', models.CharField(blank=True, max_length=8)),
                ('seed_hash', models.CharField(blank=True, max_length=64)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'wingo_rounds',
                'ordering': ['-round_number'],
            },
        ),
        migrations.AddIndex(
            model_name='wingoround',
            index=models.Index(fields=['-round_number'], name='wingo_round_num_idx'),
        ),
        migrations.CreateModel(
            name='WingoBet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bet_type', models.CharField(
                    choices=[('NUMBER', 'Number (0-9)'), ('COLOR', 'Color'), ('SIZE', 'Big/Small')],
                    max_length=10)),
                ('bet_value', models.CharField(max_length=16)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('potential_payout', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('is_winner', models.BooleanField(blank=True, null=True)),
                ('payout_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('settled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='wingo_bets',
                    to=settings.AUTH_USER_MODEL)),
                ('round', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bets',
                    to='wingo.wingoround')),
            ],
            options={
                'db_table': 'wingo_bets',
            },
        ),
        migrations.AddConstraint(
            model_name='wingobet',
            constraint=models.UniqueConstraint(
                fields=['user', 'round', 'bet_type', 'bet_value'],
                name='unique_wingo_bet_per_round'),
        ),
        migrations.AddIndex(
            model_name='wingobet',
            index=models.Index(fields=['user', '-created_at'], name='wingo_bet_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='wingobet',
            index=models.Index(fields=['round', 'is_winner'], name='wingo_bet_round_winner_idx'),
        ),
    ]
