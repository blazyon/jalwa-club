from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('five_d', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fivedround',
            name='forced_digits',
            field=models.CharField(
                max_length=20, blank=True, null=True,
                help_text='Admin override: 5 comma-separated digits e.g. "1,2,3,4,5" (each 0-9)'
            ),
        ),
    ]
