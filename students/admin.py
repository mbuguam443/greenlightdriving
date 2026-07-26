from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_number', 'get_full_name', 'course', 'branch', 'instructor', 'status', 'enrollment_date')
    list_filter = ('status', 'category', 'branch')
    search_fields = ('student_number', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('student_number', 'enrollment_date', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'admission', 'instructor', 'vehicle')

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = 'Name'
