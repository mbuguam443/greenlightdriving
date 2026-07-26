from django.contrib import admin

from .models import Branch, SiteSettings


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "town", "phone", "is_active", "created_at")
    list_filter = ("is_active", "town")
    search_fields = ("name", "town", "address")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("site_name", "phone_primary", "email")

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
