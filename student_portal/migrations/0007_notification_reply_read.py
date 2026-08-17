from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('student_portal', '0006_notification_replied_at_notification_reply'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='reply_read',
            field=models.BooleanField(default=False),
        ),
    ]
