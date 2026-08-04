from django.db import models
from django.utils.text import slugify
import uuid


class Admission(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('ENROLLED', 'Enrolled'),
    ]
    SCHEDULE_CHOICES = [
        ('MORNING', 'Morning (8AM-12PM)'),
        ('AFTERNOON', 'Afternoon (1PM-5PM)'),
        ('EVENING', 'Evening (5PM-8PM)'),
        ('WEEKEND', 'Weekend'),
    ]

    admission_number = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=6, choices=[('M', 'Male'), ('F', 'Female'), ('OTHER', 'Other')])
    national_id = models.CharField(max_length=30, verbose_name='National ID Number')
    address = models.TextField()

    passport_photo = models.ImageField(upload_to='admissions/passports/')
    national_id_image = models.ImageField(upload_to='admissions/ids/', verbose_name='National ID Image')

    PACKAGE_CHOICES = [
        ('FULL', 'Full Course'),
        ('HALF', 'Half Course'),
        ('TEST', 'Test Only'),
    ]

    category = models.ForeignKey('website.CourseCategory', on_delete=models.CASCADE)
    course = models.ForeignKey('website.Course', on_delete=models.CASCADE)
    package_choice = models.CharField(max_length=10, choices=PACKAGE_CHOICES, default='FULL')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE)
    preferred_schedule = models.CharField(max_length=20, choices=SCHEDULE_CHOICES, default='MORNING')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admission_number} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.admission_number:
            year = self.created_at.year if self.created_at else __import__('datetime').datetime.now().year
            prefix = f"GLS-{year}-"
            last = Admission.objects.filter(admission_number__startswith=prefix).order_by('-admission_number').first()
            if last:
                num = int(last.admission_number.split('-')[-1]) + 1
            else:
                num = 1
            self.admission_number = f"{prefix}{num:04d}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class WalkInInquiry(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    course = models.ForeignKey('website.Course', on_delete=models.SET_NULL, null=True, blank=True)
    feedback = models.TextField(blank=True, help_text='What they said, interested in, etc.')
    followed_up = models.BooleanField(default=False)
    converted = models.BooleanField(default=False, help_text='Converted to admission/student?')
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Walk-in Inquiry'
        verbose_name_plural = 'Walk-in Inquiries'

    def __str__(self):
        return f"{self.name} - {self.phone} ({self.created_at.strftime('%d/%m/%Y')})"
