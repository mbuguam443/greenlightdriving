from django.db import models


class Vehicle(models.Model):
    CATEGORY_CHOICES = [
        ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'),
        ('B1', 'B1'), ('B2', 'B2'),
        ('C1', 'C1'), ('C2', 'C2'),
        ('D1', 'D1'), ('D2', 'D2'), ('CE', 'CE'),
    ]
    
    registration_number = models.CharField(max_length=20, unique=True)
    category = models.CharField(max_length=5, choices=CATEGORY_CHOICES)
    make = models.CharField(max_length=100, help_text='e.g. Toyota, Nissan')
    model_name = models.CharField(max_length=100, help_text='e.g. Vitz, Note')
    year = models.PositiveIntegerField()
    color = models.CharField(max_length=50, blank=True)
    insurance_expiry = models.DateField()
    service_due = models.DateField()
    assigned_instructor = models.OneToOneField(
        'instructors.Instructor', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_vehicle'
    )
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='vehicles/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['registration_number']

    def __str__(self):
        return f"{self.registration_number} ({self.category})"

    @property
    def is_insurance_valid(self):
        from datetime import date
        return self.insurance_expiry >= date.today()

    @property
    def is_service_due(self):
        from datetime import date
        return self.service_due <= date.today()
