from django.db import models


class Instructor(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='instructor_profile')
    license_number = models.CharField(max_length=30, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=200, blank=True, help_text='e.g. Class B, Commercial')
    bio = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} ({self.license_number})"

    @property
    def assigned_students_count(self):
        from students.models import Student
        return Student.objects.filter(instructor=self, status='ACTIVE').count()

    @property
    def assigned_vehicle(self):
        from vehicles.models import Vehicle
        try:
            return Vehicle.objects.get(assigned_instructor=self)
        except Vehicle.DoesNotExist:
            return None
