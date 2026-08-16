from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0005_student_discount_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='push_token',
            field=models.CharField(blank=True, default='', help_text="Expo push token for this student's phone", max_length=300),
        ),
    ]
