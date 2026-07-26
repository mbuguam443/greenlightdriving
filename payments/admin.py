from django.contrib import admin
from .models import Payment, Receipt, MpesaTransaction


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'amount', 'method', 'status', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('receipt_number', 'student__student_number', 'reference_number')
    readonly_fields = ('receipt_number', 'created_at')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'payment', 'issued_date', 'issued_by')


@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'amount', 'status', 'mpesa_receipt', 'created_at')
    list_filter = ('status',)
    search_fields = ('phone_number', 'mpesa_receipt', 'checkout_request_id')
    readonly_fields = ('checkout_request_id', 'merchant_request_id', 'result_code', 'result_desc', 'created_at', 'updated_at')
