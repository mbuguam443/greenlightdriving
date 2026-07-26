from django.contrib import admin
from .models import NTSARecord


@admin.register(NTSARecord)
class NTSARecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'pdl_status', 'theory_exam_status', 'practical_exam_status', 'driving_test_status', 'licence_issued')
    list_filter = ('pdl_status', 'theory_exam_status', 'practical_exam_status', 'driving_test_status', 'licence_issued')
    search_fields = ('student__student_number', 'student__user__first_name', 'student__user__last_name')
