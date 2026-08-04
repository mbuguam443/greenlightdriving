from django.db import models


class LessonItem(models.Model):
    LESSON_TYPE_CHOICES = [
        ('THEORY', 'Theory'),
        ('PRACTICAL', 'Practical'),
        ('ASSESSMENT', 'Assessment'),
    ]

    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES, default='PRACTICAL')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class PracticalLesson(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('NEEDS_PRACTICE', 'Needs Practice'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='practical_lessons')
    lesson_item = models.ForeignKey(LessonItem, on_delete=models.CASCADE)
    instructor = models.ForeignKey('instructors.Instructor', on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED', blank=True)
    remarks = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'lesson_item__order']
        unique_together = ['student', 'lesson_item']

    def __str__(self):
        return f"{self.student} - {self.lesson_item.name}"


class TheoryLesson(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
    ]
    
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='theory_lessons')
    lesson_item = models.ForeignKey(LessonItem, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=300)
    instructor = models.ForeignKey('instructors.Instructor', on_delete=models.SET_NULL, null=True)
    date = models.DateField()
    time_start = models.TimeField()
    time_end = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'time_start']

    def __str__(self):
        return f"{self.student} - {self.topic}"
