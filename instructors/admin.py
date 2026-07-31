from django.contrib import admin
from .models import Instructor


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'license_class', 'experience_years', 'branch', 'is_active')
    list_filter = ('is_active', 'branch', 'license_class')
    search_fields = ('user__first_name', 'user__last_name', 'license_number', 'phone')
