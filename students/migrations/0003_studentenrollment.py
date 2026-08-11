from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
        ('instructors', '0002_rename_is_available_instructor_is_active_and_more'),
        ('students', '0002_student_package_choice'),
        ('vehicles', '0001_initial'),
        ('website', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('package_choice', models.CharField(choices=[('FULL', 'Full Course'), ('HALF', 'Half Course'), ('TEST', 'Test Only')], default='FULL', max_length=10)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')], default='ACTIVE', max_length=20)),
                ('enrollment_date', models.DateField(auto_now_add=True)),
                ('expected_graduation', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.branch')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='website.course')),
                ('instructor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='instructors.instructor')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='students.student')),
                ('vehicle', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicles.vehicle')),
            ],
            options={'ordering': ['-enrollment_date', '-id']},
        ),
        migrations.AddConstraint(
            model_name='studentenrollment',
            constraint=models.UniqueConstraint(fields=('student', 'course'), name='unique_student_enrollment_course'),
        ),
    ]
