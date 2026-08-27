from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.db import models
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.decorators import method_decorator
from .models import Payment, Receipt, MpesaTransaction
from .forms import PaymentForm
from .mpesa_utils import initiate_stk_push, format_phone


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'ACCOUNTANT', 'RECEPTIONIST', 'READ_ONLY_ADMIN')


class PaymentListView(StaffTestMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = Payment.objects.select_related('student', 'student__user')
        method = self.request.GET.get('method')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        if method:
            queryset = queryset.filter(method=method)
        if status:
            queryset = queryset.filter(status=status)
        if search:
            queryset = queryset.filter(
                models.Q(receipt_number__icontains=search) |
                models.Q(student__student_number__icontains=search) |
                models.Q(student__user__first_name__icontains=search) |
                models.Q(student__user__last_name__icontains=search) |
                models.Q(reference_number__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['method_choices'] = Payment.METHOD_CHOICES
        context['status_choices'] = Payment.STATUS_CHOICES
        context['method_filter'] = self.request.GET.get('method', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['date_from'] = self.request.GET.get('date_from', '')
        context['date_to'] = self.request.GET.get('date_to', '')
        context['total_amount'] = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
        context['completed_count'] = Payment.objects.filter(status='COMPLETED').count()
        context['pending_count'] = Payment.objects.filter(status='PENDING').count()
        context['failed_count'] = Payment.objects.filter(status='FAILED').count()
        return context


class PaymentCreateView(StaffTestMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'payments/payment_form.html'
    success_url = reverse_lazy('payments:list')

    def get_initial(self):
        initial = super().get_initial()
        student_id = self.request.GET.get('student')
        if student_id:
            initial['student'] = student_id
        enrollment_id = self.request.GET.get('enrollment')
        if enrollment_id:
            initial['enrollment'] = enrollment_id
        return initial

    def get_success_url(self):
        student_id = self.request.GET.get('student') or self.request.POST.get('student')
        if student_id:
            return reverse('students:detail', kwargs={'pk': student_id})
        return reverse('payments:list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        from students.models import StudentEnrollment
        student_id = self.request.GET.get('student') or self.request.POST.get('student')
        form.fields['enrollment'].queryset = StudentEnrollment.objects.filter(
            student_id=student_id
        ).select_related('course') if student_id else StudentEnrollment.objects.none()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from students.models import Student
        context['students'] = Student.objects.filter(status='ACTIVE').select_related('user')
        from students.models import StudentEnrollment
        context['enrollments'] = StudentEnrollment.objects.select_related('course', 'student__user')
        student_id = self.request.GET.get('student') or self.request.POST.get('student')
        if student_id:
            try:
                context['selected_student'] = Student.objects.select_related('user').get(pk=student_id)
            except (Student.DoesNotExist, ValueError):
                pass
        return context

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user
        response = super().form_valid(form)
        from core.models import DailyLog
        from django.utils import timezone
        p = form.instance
        DailyLog.objects.create(title=f'Payment: {p.student.user.full_name}', description=f'KES {p.amount:,.0f} via {p.get_method_display()}. Receipt: {p.receipt_number}', log_date=timezone.now().date(), created_by=self.request.user)
        messages.success(self.request, 'Payment recorded successfully.')
        return response


class PaymentDetailView(StaffTestMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'


class PaymentStatusUpdateView(StaffTestMixin, View):
    def get(self, request, pk, status):
        payment = get_object_or_404(Payment, pk=pk)
        if status in dict(Payment.STATUS_CHOICES):
            payment.status = status
            payment.save(update_fields=['status'])
            messages.success(request, f'Payment {payment.receipt_number} marked as {payment.get_status_display()}.')
        return redirect('payments:detail', pk=payment.pk)


class ReceiptView(StaffTestMixin, View):
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        receipt, created = Receipt.objects.get_or_create(
            payment=payment,
            defaults={'receipt_number': payment.receipt_number, 'issued_by': request.user}
        )
        from django.templatetags.static import static
        return render(request, 'payments/receipt_standalone.html', {
            'payment': payment,
            'logo_url': request.build_absolute_uri(static('images/logo.png')),
        })


class PaymentDeleteView(StaffTestMixin, DeleteView):
    model = Payment
    success_url = reverse_lazy('payments:list')

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Payment deleted.')
        return super().form_valid(form)


# ==================== M-PESA STAFF VIEWS ====================

class MpesaTransactionListView(StaffTestMixin, View):
    def get(self, request):
        txs = MpesaTransaction.objects.select_related('student', 'student__user')
        status = request.GET.get('status', '')
        search = request.GET.get('search', '')
        if status:
            txs = txs.filter(status=status)
        if search:
            txs = txs.filter(
                models.Q(phone_number__icontains=search) |
                models.Q(mpesa_receipt__icontains=search) |
                models.Q(account_reference__icontains=search) |
                models.Q(student__student_number__icontains=search) |
                models.Q(student__user__first_name__icontains=search) |
                models.Q(student__user__last_name__icontains=search)
            )

        total_success = txs.filter(status='SUCCESS').aggregate(total=Sum('amount'))['total'] or 0
        total_pending = txs.filter(status='PENDING').count()
        total_failed = txs.filter(status='FAILED').count()

        from django.core.paginator import Paginator
        paginator = Paginator(txs, 20)
        page = request.GET.get('page', 1)
        txs_page = paginator.get_page(page)

        return render(request, 'payments/mpesa_transactions.html', {
            'transactions': txs_page,
            'status_filter': status,
            'search_query': search,
            'total_success': total_success,
            'total_pending': total_pending,
            'total_failed': total_failed,
            'total_count': txs.count(),
        })


class MpesaTransactionQueryView(StaffTestMixin, View):
    def get(self, request, pk):
        from django.http import JsonResponse
        import logging
        logger = logging.getLogger(__name__)

        tx = get_object_or_404(MpesaTransaction, pk=pk)
        if tx.status != 'PENDING' or not tx.checkout_request_id:
            return JsonResponse({'success': False, 'message': 'Only pending transactions can be queried.'})

        from .mpesa_utils import query_stk_push_status
        logger.info(f"Querying STK Push status for tx {pk}: checkout={tx.checkout_request_id}")
        result = query_stk_push_status(tx.checkout_request_id)
        logger.info(f"STK Push query result: {result}")

        if not result['success']:
            return JsonResponse({'success': False, 'message': result.get('message', 'Query failed.')})

        data = result['data']
        result_code = data.get('ResultCode', '')
        result_desc = data.get('ResultDesc', '')

        if str(result_code) == '0':
            tx.status = 'SUCCESS'
            tx.result_code = str(result_code)
            tx.result_desc = result_desc

            # Extract receipt from response metadata if available
            metadata = data.get('ResultMetadata', [])
            if isinstance(metadata, list):
                for item in metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        tx.mpesa_receipt = item.get('Value', '')

            tx.save(update_fields=['status', 'result_code', 'result_desc', 'mpesa_receipt', 'updated_at'])

            # Create Payment record if not already linked
            if not tx.payment:
                payment = Payment.objects.create(
                    student=tx.student,
                    amount=tx.amount,
                    method='MPESA',
                    reference_number=tx.mpesa_receipt or tx.result_code,
                    status='COMPLETED',
                    recorded_by=self.request.user,
                    description=f'M-Pesa STK Push (queried). Receipt: {tx.mpesa_receipt}',
                )
                tx.payment = payment
                tx.save(update_fields=['payment', 'updated_at'])
        elif str(result_code) == '1032':
            tx.status = 'FAILED'
            tx.result_code = str(result_code)
            tx.result_desc = result_desc
            tx.save(update_fields=['status', 'result_code', 'result_desc', 'updated_at'])
        elif str(result_code) == '1037':
            tx.result_code = str(result_code)
            tx.result_desc = result_desc
            tx.save(update_fields=['result_code', 'result_desc', 'updated_at'])

        return JsonResponse({
            'success': True,
            'new_status': tx.status,
            'result_code': result_code,
            'result_desc': result_desc,
        })


# ==================== M-PESA STUDENT VIEWS ====================

class MpesaPaymentView(LoginRequiredMixin, View):
    """Student M-Pesa payment page — STK Push."""
    def get(self, request):
        from students.models import Student
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.error(request, 'No student profile found.')
            return redirect('student_portal:dashboard')

        balance = student.balance
        return render(request, 'payments/mpesa_payment.html', {
            'student': student,
            'balance': balance,
            'phone': request.user.phone_number if hasattr(request.user, 'phone_number') else '',
        })

    def post(self, request):
        from students.models import Student
        from django.conf import settings as django_settings
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.error(request, 'No student profile found.')
            return redirect('student_portal:dashboard')

        phone = request.POST.get('phone', '').strip()
        amount = request.POST.get('amount', '').strip()

        # Validate
        errors = []
        if not phone:
            errors.append('Phone number is required.')
        if not amount:
            errors.append('Amount is required.')
        else:
            try:
                amount = float(amount)
                if amount <= 0:
                    errors.append('Amount must be greater than zero.')
                if amount > student.balance:
                    errors.append(f'Amount exceeds your balance of KES {student.balance:,.0f}.')
            except ValueError:
                errors.append('Invalid amount.')
                amount = 0

        if errors:
            return render(request, 'payments/mpesa_payment.html', {
                'student': student,
                'balance': student.balance,
                'phone': phone,
                'errors': errors,
            })

        # Create pending transaction
        account_ref = f"GLS-{student.student_number}"
        transaction = MpesaTransaction.objects.create(
            student=student,
            phone_number=format_phone(phone),
            amount=amount,
            account_reference=account_ref,
            status='PENDING',
        )

        # Initiate STK Push
        result = initiate_stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=account_ref,
            transaction_desc=f'Fee payment for {student.user.get_full_name()}',
        )

        if result['success']:
            transaction.checkout_request_id = result.get('checkout_request_id', '')
            transaction.merchant_request_id = result.get('merchant_request_id', '')
            transaction.save()
            messages.success(request, f"STK Push sent to {format_phone(phone)}. Check your phone to complete payment.")
            return redirect('payments:mpesa_status', pk=transaction.pk)
        else:
            transaction.status = 'FAILED'
            transaction.result_desc = result.get('message', '')
            transaction.save()
            messages.error(request, f"Payment failed: {result.get('message', 'Unknown error')}")
            return render(request, 'payments/mpesa_payment.html', {
                'student': student,
                'balance': student.balance,
                'phone': phone,
                'errors': [result.get('message', 'Payment failed.')],
            })


class MpesaStatusView(LoginRequiredMixin, View):
    """Show M-Pesa transaction status."""
    def get(self, request, pk):
        transaction = get_object_or_404(MpesaTransaction, pk=pk, student__user=request.user)
        return render(request, 'payments/mpesa_status.html', {
            'transaction': transaction,
        })


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(View):
    """Safaricom M-Pesa callback — receives STK Push result."""
    def post(self, request):
        import json
        import logging
        logger = logging.getLogger(__name__)

        try:
            body = json.loads(request.body)
            logger.info(f"M-Pesa callback received: {json.dumps(body, default=str)[:500]}")

            stk_callback = body.get('Body', {}).get('stkCallback', {})
            result_code = str(stk_callback.get('ResultCode', ''))
            result_desc = stk_callback.get('ResultDesc', '')
            checkout_id = stk_callback.get('CheckoutRequestID', '')
            merchant_id = stk_callback.get('MerchantRequestID', '')

            logger.info(f"Callback: code={result_code}, checkout={checkout_id}, merchant={merchant_id}")

            # Find the transaction
            transaction = MpesaTransaction.objects.filter(checkout_request_id=checkout_id).first()

            if not transaction:
                transaction = MpesaTransaction.objects.filter(merchant_request_id=merchant_id).first()

            if not transaction:
                logger.warning(f"Transaction not found for checkout={checkout_id} merchant={merchant_id}")
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Transaction not found'})

            if result_code == '0':
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                mpesa_receipt = ''
                amount_paid = 0
                phone_paid = ''

                for item in callback_metadata:
                    if item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt = item.get('Value', '')
                    elif item.get('Name') == 'Amount':
                        amount_paid = item.get('Value', 0)
                    elif item.get('Name') == 'PhoneNumber':
                        phone_paid = str(item.get('Value', ''))

                logger.info(f"Payment success: receipt={mpesa_receipt}, amount={amount_paid}")

                transaction.status = 'SUCCESS'
                transaction.result_code = result_code
                transaction.result_desc = result_desc
                transaction.mpesa_receipt = mpesa_receipt
                transaction.save()

                # Create the actual Payment record
                payment = transaction.payment or Payment.objects.create(
                    student=transaction.student,
                    amount=transaction.amount,
                    method='MPESA',
                    reference_number=mpesa_receipt,
                    status='COMPLETED',
                    recorded_by=None,
                    description=f'M-Pesa STK Push. Receipt: {mpesa_receipt}',
                )
                transaction.payment = payment
                transaction.save()

                logger.info(f"Payment record created: {payment.receipt_number}")

            else:
                # Payment failed
                transaction.status = 'FAILED'
                transaction.result_code = result_code
                transaction.result_desc = result_desc
                transaction.save()
                logger.info(f"Payment failed: code={result_code}, desc={result_desc}")

        except Exception as e:
            logger.error(f"M-Pesa callback error: {e}", exc_info=True)

        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})

    def get(self, request):
        return JsonResponse({'status': 'M-Pesa callback endpoint active'})


class MpesaCheckStatusView(LoginRequiredMixin, View):
    """AJAX endpoint to check M-Pesa transaction status."""
    def get(self, request, pk):
        transaction = get_object_or_404(MpesaTransaction, pk=pk, student__user=request.user)
        return JsonResponse({
            'status': transaction.status,
            'mpesa_receipt': transaction.mpesa_receipt,
            'result_desc': transaction.result_desc,
            'amount': str(transaction.amount),
        })
