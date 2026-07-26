from django.contrib import admin
from .models import StudentDocument, Event


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_size_display', 'is_active', 'uploaded_at')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'event_date', 'event_time', 'branch', 'is_active', 'is_important')
    list_filter = ('category', 'is_active', 'is_important')
    search_fields = ('title', 'description')
