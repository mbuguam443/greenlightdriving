from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'category', 'make', 'model_name', 'year', 'assigned_instructor', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('registration_number', 'make', 'model_name')
