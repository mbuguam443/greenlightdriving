from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_portal', '0003_studentdocument_student_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300)),
                ('message', models.TextField()),
                ('notification_type', models.CharField(choices=[('lesson', 'Lesson Update'), ('payment', 'Payment Reminder'), ('general', 'General')], default='general', max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='notifications', to='students.student')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
