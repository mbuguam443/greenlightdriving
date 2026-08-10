from django.db import models


class Student(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('GRADUATED', 'Graduated'),
        ('DROPPED', 'Dropped'),
        ('SUSPENDED', 'Suspended'),
    ]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='student_profile')
    admission = models.OneToOneField('admissions.Admission', on_delete=models.SET_NULL, null=True, blank=True)
    student_number = models.CharField(max_length=20, unique=True)
    PACKAGE_CHOICES = [
        ('FULL', 'Full Course'),
        ('HALF', 'Half Course'),
        ('TEST', 'Test Only'),
    ]

    category = models.ForeignKey('website.CourseCategory', on_delete=models.CASCADE)
    course = models.ForeignKey('website.Course', on_delete=models.CASCADE)
    package_choice = models.CharField(max_length=10, choices=PACKAGE_CHOICES, default='FULL')
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE)
    instructor = models.ForeignKey('instructors.Instructor', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    enrollment_date = models.DateField(auto_now_add=True)
    expected_graduation = models.DateField(null=True, blank=True)
    payment_reminder = models.BooleanField(default=False, help_text='Show balance alert to student')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student_number} - {self.user.full_name}"

    def save(self, *args, **kwargs):
        if not self.student_number:
            last = Student.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.student_number = f"GLS-STU-{num:05d}"
        super().save(*args, **kwargs)

    @property
    def lessons_completed(self):
        from lessons.models import PracticalLesson
        return PracticalLesson.objects.filter(student=self, status='COMPLETED').count()

    @property
    def total_lessons(self):
        from lessons.models import PracticalLesson
        return PracticalLesson.objects.filter(student=self).count()

    @property
    def progress_percentage(self):
        total = self.total_lessons
        if total == 0:
            return 0
        return round((self.lessons_completed / total) * 100)

    @property
    def total_fees(self):
        course_fee = 0
        if self.course:
            prices = {
                'FULL': self.course.full_course_price,
                'HALF': self.course.half_course_price,
                'TEST': self.course.test_only_price,
            }
            course_fee = prices.get(self.package_choice, 0)
        # Add exam fee from school settings
        from core.models import SiteSettings
        try:
            settings = SiteSettings.load()
            course_fee += settings.exam_fee
        except Exception:
            pass
        return course_fee

    @property
    def amount_paid(self):
        from payments.models import Payment
        payments = Payment.objects.filter(student=self, status='COMPLETED')
        return sum(p.amount for p in payments)

    @property
    def balance(self):
        return self.total_fees - self.amount_paid
