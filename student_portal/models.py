from django.db import models
from django.utils import timezone


class StudentDocument(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('theory', 'Theory Materials'),
        ('forms', 'Forms'),
        ('certificates', 'Certificates'),
        ('guidelines', 'Guidelines'),
        ('ntsa', 'NTSA Documents'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='student_documents/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'title']

    def __str__(self):
        return self.title

    @property
    def file_extension(self):
        return self.file.name.split('.')[-1].upper() if self.file else ''

    @property
    def file_size_display(self):
        if not self.file:
            return ''
        size = self.file.size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('ntsa_test', 'NTSA Driving Test'),
        ('ntsa_exam', 'NTSA Theory Exam'),
        ('school_event', 'School Event'),
        ('holiday', 'Holiday / Closure'),
        ('orientation', 'New Student Orientation'),
        ('workshop', 'Safety Workshop'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='school_event')
    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    branch = models.ForeignKey('core.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=300, blank=True, help_text='Physical location or online link')
    is_active = models.BooleanField(default=True)
    is_important = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date', 'event_time']

    def __str__(self):
        return f"{self.title} ({self.event_date})"

    @property
    def is_upcoming(self):
        return self.event_date >= timezone.now().date()

    @property
    def category_badge_class(self):
        mapping = {
            'ntsa_test': 'bg-danger',
            'ntsa_exam': 'bg-warning text-dark',
            'school_event': 'bg-success',
            'holiday': 'bg-info text-dark',
            'orientation': 'bg-primary',
            'workshop': 'bg-secondary',
            'other': 'bg-dark',
        }
        return mapping.get(self.category, 'bg-secondary')

    @property
    def days_until(self):
        delta = self.event_date - timezone.now().date()
        return delta.days if delta.days >= 0 else 0
