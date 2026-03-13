from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('k3', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='k3round',
            name='forced_dice',
            field=models.CharField(
                max_length=16, blank=True, null=True,
                help_text='Admin override: comma-separated dice values e.g. "3,5,2" (each 1-6)'
            ),
        ),
    ]
