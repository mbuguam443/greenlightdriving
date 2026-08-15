from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_studentenrollment'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='payment_reminder',
            field=models.BooleanField(default=False, help_text='Show balance alert to student'),
        ),
    ]
