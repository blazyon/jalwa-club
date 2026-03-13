from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Adds forced_color field to WingoRound.
    Admin can now pre-set both a result number AND a result color.
    Neither triggers early settlement — both are applied by Celery when timer ends.
    """

    dependencies = [
        # adjust this to your last wingo migration
        ('wingo', '0003_alter_wingoround_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wingoround',
            name='forced_color',
            field=models.CharField(
                max_length=16,
                blank=True,
                null=True,
                choices=[
                    ('GREEN',  'Green'),
                    ('RED',    'Red'),
                    ('VIOLET', 'Violet'),
                ],
                help_text=(
                    'Admin override: force result COLOR (Green / Red / Violet). '
                    'Applied when the round timer ends. Leave blank to auto-derive from number.'
                ),
            ),
        ),
    ]
