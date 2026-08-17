from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student_portal', '0003_studentdocument_student_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='chat_messages', to='accounts.user')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
