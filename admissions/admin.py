from django.contrib import admin
from .models import Admission


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'full_name', 'email', 'phone', 'category', 'course', 'branch', 'status', 'created_at')
    list_filter = ('status', 'category', 'branch', 'gender', 'preferred_schedule')
    search_fields = ('admission_number', 'first_name', 'last_name', 'email', 'national_id')
    readonly_fields = ('admission_number', 'created_at', 'updated_at')
    list_editable = ('status',)
