from django.db import models


class Instructor(models.Model):
    LICENSE_CLASS_CHOICES = [
        ('A1', 'A1 - Motorcycle'),
        ('A2', 'A2 - Motorcycle Advanced'),
        ('B1', 'B1 - Saloon Car'),
        ('B2', 'B2 - SUV/Jeep'),
        ('C1', 'C1 - Light Commercial'),
        ('C2', 'C2 - Heavy Commercial'),
        ('D1', 'D1 - Light PSV'),
        ('D2', 'D2 - Heavy PSV'),
        ('CE', 'CE - Articulated'),
        ('ALL', 'ALL - All Classes'),
    ]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='instructor_profile')
    phone = models.CharField(max_length=20, blank=True)
    license_number = models.CharField(max_length=30, unique=True)
    license_class = models.CharField(max_length=20, choices=LICENSE_CLASS_CHOICES, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=200, blank=True, help_text='e.g. Class B, Commercial')
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='instructors')
    photo = models.ImageField(upload_to='instructors/', blank=True)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
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
