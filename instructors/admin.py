from django.contrib import admin
from .models import Instructor


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'license_number', 'experience_years', 'specialization', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('user__first_name', 'user__last_name', 'license_number')
