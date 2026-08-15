from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_portal', '0005_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='replied_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='reply',
            field=models.TextField(blank=True),
        ),
    ]
