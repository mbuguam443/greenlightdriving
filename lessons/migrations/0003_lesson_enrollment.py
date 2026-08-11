from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('lessons', '0002_lessonitem_lesson_type_theorylesson_lesson_item'),
        ('students', '0003_studentenrollment'),
    ]

    operations = [
        migrations.AddField(
            model_name='practicallesson',
            name='enrollment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='practical_lessons', to='students.studentenrollment'),
        ),
        migrations.AddField(
            model_name='theorylesson',
            name='enrollment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='theory_lessons', to='students.studentenrollment'),
        ),
        migrations.AlterUniqueTogether(
            name='practicallesson',
            unique_together={('student', 'lesson_item', 'enrollment')},
        ),
    ]
