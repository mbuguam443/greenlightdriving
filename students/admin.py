from django.contrib import admin
from django.utils.html import format_html

from .models import Student


class BalanceFilter(admin.SimpleListFilter):
    title = 'Balance'
    parameter_name = 'balance'

    def lookups(self, request, model_admin):
        return (
            ('owing', 'Has outstanding balance'),
            ('clear', 'Paid in full'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'owing':
            ids = [s.id for s in queryset if s.balance > 0]
            return queryset.filter(id__in=ids)
        if self.value() == 'clear':
            ids = [s.id for s in queryset if s.balance <= 0]
            return queryset.filter(id__in=ids)
        return queryset


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    change_list_template = 'admin/students/student/change_list.html'
    list_display = ('student_number', 'get_full_name', 'course', 'branch', 'status',
                    'enrollment_date', 'get_total_fees', 'get_amount_paid', 'get_discount',
                    'get_balance', 'get_reminder')
    list_filter = ('status', 'category', 'branch', BalanceFilter)
    search_fields = ('student_number', 'user__first_name', 'user__last_name', 'user__email',
                     'discount_reason', 'discount_description')
    readonly_fields = ('student_number', 'enrollment_date', 'created_at', 'updated_at')
    raw_id_fields = ('user', 'admission', 'instructor', 'vehicle')

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        my_urls = [
            path('remind-all/', self.admin_site.admin_view(self.remind_all_view), name='students_student_remind_all'),
            path('clear-reminders/', self.admin_site.admin_view(self.clear_reminders_view), name='students_student_clear_reminders'),
        ]
        return my_urls + urls

    def remind_all_view(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        if request.method == 'POST':
            ids = [s.id for s in Student.objects.all() if s.balance > 0]
            Student.objects.filter(id__in=ids).update(payment_reminder=True)
            messages.success(request, f'Payment reminders enabled for {len(ids)} student(s).')
        return redirect('admin:students_student_changelist')

    def clear_reminders_view(self, request):
        from django.contrib import messages
        from django.shortcuts import redirect
        if request.method == 'POST':
            Student.objects.update(payment_reminder=False)
            messages.success(request, 'All payment reminders cleared.')
        return redirect('admin:students_student_changelist')

    def get_full_name(self, obj):
        return obj.user.full_name
    get_full_name.short_description = 'Name'

    def get_total_fees(self, obj):
        return f"KES {obj.total_fees:,.0f}"
    get_total_fees.short_description = 'Total fees'

    def get_amount_paid(self, obj):
        return f"KES {obj.amount_paid:,.0f}"
    get_amount_paid.short_description = 'Paid'

    def get_discount(self, obj):
        if obj.discount:
            return format_html("<span style='color:#1565C0;font-weight:bold'>KES {}</span>", f"{obj.discount:,.0f}")
        return "-"
    get_discount.short_description = 'Discount'

    def get_balance(self, obj):
        balance = obj.balance
        if balance > 0:
            return format_html("<span style='color:#D32F2F;font-weight:bold'>KES {}</span>", f"{balance:,.0f}")
        return f"KES {balance:,.0f}"
    get_balance.short_description = 'Balance'

    def get_reminder(self, obj):
        if obj.payment_reminder:
            return format_html("<span style='color:#2E7D32;font-weight:bold;'>ON</span>")
        return format_html("<span style='color:#999;'>OFF</span>")
    get_reminder.short_description = 'Reminder'
