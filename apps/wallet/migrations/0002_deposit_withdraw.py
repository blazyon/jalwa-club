import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DepositRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('utr_number', models.CharField(
                    max_length=64,
                    help_text='UTR / Transaction reference number provided by user'
                )),
                ('upi_id_used', models.CharField(
                    max_length=128, blank=True,
                    help_text='UPI ID the user sent money to'
                )),
                ('status', models.CharField(
                    max_length=16,
                    choices=[
                        ('PENDING', 'Pending Review'),
                        ('APPROVED', 'Approved'),
                        ('REJECTED', 'Rejected'),
                    ],
                    default='PENDING',
                    db_index=True,
                )),
                ('admin_note', models.CharField(max_length=255, blank=True)),
                ('reviewed_by', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    related_name='reviewed_deposits',
                )),
                ('reviewed_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wallet', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='wallet.wallet',
                    related_name='deposit_requests',
                )),
            ],
            options={
                'db_table': 'deposit_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WithdrawRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ('amount', models.DecimalField(max_digits=12, decimal_places=2)),
                ('upi_id', models.CharField(
                    max_length=128,
                    help_text='UPI ID to send money to'
                )),
                ('status', models.CharField(
                    max_length=16,
                    choices=[
                        ('PENDING', 'Pending Review'),
                        ('APPROVED', 'Approved'),
                        ('REJECTED', 'Rejected'),
                    ],
                    default='PENDING',
                    db_index=True,
                )),
                ('admin_note', models.CharField(max_length=255, blank=True)),
                ('reviewed_by', models.ForeignKey(
                    null=True, blank=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    related_name='reviewed_withdrawals',
                )),
                ('reviewed_at', models.DateTimeField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('wallet', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='wallet.wallet',
                    related_name='withdraw_requests',
                )),
            ],
            options={
                'db_table': 'withdraw_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='depositrequest',
            index=models.Index(fields=['wallet', '-created_at'], name='dep_wallet_date_idx'),
        ),
        migrations.AddIndex(
            model_name='withdrawrequest',
            index=models.Index(fields=['wallet', '-created_at'], name='wd_wallet_date_idx'),
        ),
    ]
