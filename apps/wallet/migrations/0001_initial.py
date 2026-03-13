import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('balance', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=14)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='wallet', to=settings.AUTH_USER_MODEL)),
            ],
            options={'db_table': 'wallets'},
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('tx_type', models.CharField(choices=[('CREDIT','Credit'),('DEBIT','Debit')], max_length=10)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('balance_after', models.DecimalField(decimal_places=2, max_digits=14)),
                ('reference', models.CharField(max_length=128, unique=True)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('category', models.CharField(
                    choices=[('SIGNUP_BONUS','Signup Bonus'),('ADMIN_CREDIT','Admin Credit'),
                             ('ADMIN_DEBIT','Admin Debit'),('BET_PLACED','Bet Placed'),
                             ('BET_WON','Bet Won'),('BET_REFUND','Bet Refund')],
                    default='ADMIN_CREDIT', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('wallet', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transactions', to='wallet.wallet')),
            ],
            options={
                'db_table': 'transactions',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['wallet', '-created_at'], name='tx_wallet_date_idx'),
                    models.Index(fields=['reference'], name='tx_reference_idx'),
                ],
            },
        ),
    ]
