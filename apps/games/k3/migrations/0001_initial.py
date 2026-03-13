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
            name='K3Round',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('round_number', models.BigIntegerField(unique=True)),
                ('status', models.CharField(
                    choices=[('OPEN', 'Open'), ('LOCKED', 'Locked'), ('COMPLETED', 'Completed')],
                    default='OPEN', max_length=12)),
                ('dice1', models.IntegerField(blank=True, null=True)),
                ('dice2', models.IntegerField(blank=True, null=True)),
                ('dice3', models.IntegerField(blank=True, null=True)),
                ('total', models.IntegerField(blank=True, null=True)),
                ('result_tags', models.JSONField(blank=True, default=list)),
                ('seed_hash', models.CharField(blank=True, max_length=64)),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'k3_rounds',
                'ordering': ['-round_number'],
            },
        ),
        migrations.CreateModel(
            name='K3Bet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('bet_type', models.CharField(
                    choices=[
                        ('TOTAL', 'Total Sum'),
                        ('SIZE', 'Big/Small'),
                        ('PARITY', 'Odd/Even'),
                        ('SPECIFIC_TRIPLE', 'Specific Triple'),
                        ('ANY_TRIPLE', 'Any Triple'),
                        ('SPECIFIC_DOUBLE', 'Specific Double'),
                        ('TWO_DIFFERENT', 'Two Different Dice'),
                        ('THREE_DIFFERENT', 'All Different'),
                    ],
                    max_length=20)),
                ('bet_value', models.CharField(max_length=32)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('potential_payout', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('is_winner', models.BooleanField(blank=True, null=True)),
                ('payout_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True)),
                ('settled_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='k3_bets',
                    to=settings.AUTH_USER_MODEL)),
                ('round', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bets',
                    to='k3.k3round')),
            ],
            options={
                'db_table': 'k3_bets',
            },
        ),
        migrations.AddConstraint(
            model_name='k3bet',
            constraint=models.UniqueConstraint(
                fields=['user', 'round', 'bet_type', 'bet_value'],
                name='unique_k3_bet_per_round'),
        ),
        migrations.AddIndex(
            model_name='k3bet',
            index=models.Index(fields=['user', '-created_at'], name='k3_bet_user_date_idx'),
        ),
    ]
