from django.db import models


class NTSARecord(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SCHEDULED', 'Scheduled'),
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('COMPLETED', 'Completed'),
    ]
    
    PDL_STATUS = [
        ('NOT_APPLIED', 'Not Applied'),
        ('APPLIED', 'Applied'),
        ('ISSUED', 'Issued'),
    ]
    
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='ntsa_record')
    
    pdl_status = models.CharField(max_length=20, choices=PDL_STATUS, default='NOT_APPLIED')
    pdl_date = models.DateField(null=True, blank=True)
    pdl_number = models.CharField(max_length=30, blank=True)
    
    theory_exam_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    theory_exam_date = models.DateField(null=True, blank=True)
    theory_exam_score = models.PositiveIntegerField(null=True, blank=True)
    
    practical_exam_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    practical_exam_date = models.DateField(null=True, blank=True)
    
    driving_test_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    driving_test_date = models.DateField(null=True, blank=True)
    
    licence_issued = models.BooleanField(default=False)
    licence_number = models.CharField(max_length=30, blank=True)
    licence_issue_date = models.DateField(null=True, blank=True)
    licence_expiry_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NTSA - {self.student}"

    @property
    def overall_progress(self):
        steps = [
            self.pdl_status == 'ISSUED',
            self.theory_exam_status == 'PASSED',
            self.practical_exam_status == 'PASSED',
            self.driving_test_status == 'PASSED',
            self.licence_issued,
        ]
        return sum(steps)
