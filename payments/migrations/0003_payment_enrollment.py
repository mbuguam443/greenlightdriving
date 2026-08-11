from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('payments', '0002_mpesatransaction'),
        ('students', '0003_studentenrollment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='enrollment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='students.studentenrollment'),
        ),
    ]
