from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='google_calendar_event_id',
            field=models.CharField(blank=True, help_text='Google Calendar Event ID for synced appointments', max_length=255, null=True),
        ),
    ]
