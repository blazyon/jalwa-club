from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wingo', '0001_initial'),
    ]

    operations = [
        # 1. Add mode field with default '1MIN'
        migrations.AddField(
            model_name='wingoround',
            name='mode',
            field=models.CharField(
                max_length=8,
                choices=[('1MIN', '1 Minute'), ('3MIN', '3 Minutes'), ('5MIN', '5 Minutes')],
                default='1MIN',
            ),
        ),
        # 2. Add forced_result field
        migrations.AddField(
            model_name='wingoround',
            name='forced_result',
            field=models.IntegerField(
                null=True, blank=True,
                help_text='Admin override: force this number (0-9) as result for this round'
            ),
        ),
        # 3. Remove old unique constraint on round_number alone
        migrations.AlterUniqueTogether(
            name='wingoround',
            unique_together=set(),
        ),
        # 4. Make round_number non-unique (will be unique per mode)
        migrations.AlterField(
            model_name='wingoround',
            name='round_number',
            field=models.BigIntegerField(),
        ),
        # 5. Add new unique_together (mode, round_number)
        migrations.AlterUniqueTogether(
            name='wingoround',
            unique_together={('mode', 'round_number')},
        ),
        # 6. Add new indexes
        migrations.AddIndex(
            model_name='wingoround',
            index=models.Index(fields=['mode', '-round_number'], name='wingo_mode_round_idx'),
        ),
        migrations.AddIndex(
            model_name='wingoround',
            index=models.Index(fields=['mode', 'status'], name='wingo_mode_status_idx'),
        ),
    ]
