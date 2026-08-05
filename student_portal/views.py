from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils import timezone


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'STUDENT'


class PortalDashboardView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from admissions.models import Admission
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None

        admission = Admission.objects.filter(email=request.user.email).order_by('-created_at').first()

        context = {
            'student': student,
            'student_profile': student,
            'admission': admission,
        }

        if student:
            from payments.models import Payment
            from lessons.models import PracticalLesson
            from ntsa.models import NTSARecord

            payments = Payment.objects.filter(student=student, status='COMPLETED')
            all_lessons = PracticalLesson.objects.filter(student=student)
            completed_lessons = all_lessons.filter(status='COMPLETED')

            context['recent_payments'] = payments[:5]
            context['lessons'] = all_lessons[:10]
            context['upcoming_lessons'] = all_lessons.filter(date__gte=timezone.now().date()).order_by('date')[:5]
            context['ntsa'] = NTSARecord.objects.filter(student=student).first()
            context['lessons_completed'] = completed_lessons.count()
            context['progress_percentage'] = student.progress_percentage
            context['balance'] = student.balance
            context['ntsa_status'] = context['ntsa'].pdl_status.title() if context['ntsa'] else 'N/A'

        return render(request, 'student_portal/dashboard.html', context)


class PortalScheduleView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from lessons.models import PracticalLesson, TheoryLesson
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None
        
        tab = request.GET.get('tab', 'practical')
        practical = PracticalLesson.objects.filter(student=student).select_related('lesson_item', 'instructor', 'vehicle') if student else []
        theory = TheoryLesson.objects.filter(student=student).select_related('instructor') if student else []
        
        return render(request, 'student_portal/schedule.html', {
            'practical_lessons': practical,
            'theory_lessons': theory,
            'student': student,
            'tab': tab,
        })


class PortalLessonsView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from lessons.models import PracticalLesson, TheoryLesson
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return render(request, 'student_portal/lessons.html', {'lessons': [], 'student': None})
        
        practical = PracticalLesson.objects.filter(student=student).select_related('lesson_item', 'instructor__user', 'vehicle')
        theory = TheoryLesson.objects.filter(student=student).select_related('instructor__user')
        
        completed_p = sum(1 for l in practical if l.status == 'COMPLETED')
        total_p = practical.count() or 0
        completed_t = sum(1 for l in theory if l.status == 'COMPLETED')
        total_t = theory.count() or 0
        total_all = total_p + total_t
        completed_all = completed_p + completed_t
        
        return render(request, 'student_portal/lessons.html', {
            'student': student,
            'practical_lessons': practical,
            'theory_lessons': theory,
            'completed_count': completed_all,
            'total_count': total_all,
            'progress_percentage': round((completed_all / total_all * 100)) if total_all else 0,
        })


class PortalPaymentsView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from payments.models import Payment
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None

        payments = Payment.objects.filter(student=student, status='COMPLETED') if student else []
        total_paid = sum(p.amount for p in payments) if student else 0
        total_fees = student.total_fees if student else 0
        balance = total_fees - total_paid

        return render(request, 'student_portal/payments.html', {
            'payments': payments,
            'student': student,
            'total_paid': total_paid,
            'total_fees': total_fees,
            'balance': balance,
        })


class PortalProgressView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from lessons.models import PracticalLesson, TheoryLesson
        from ntsa.models import NTSARecord
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None
        
        context = {'student': student}
        if student:
            practical = PracticalLesson.objects.filter(student=student).select_related('lesson_item')
            theory = TheoryLesson.objects.filter(student=student)
            completed_p = practical.filter(status='COMPLETED').count()
            total_p = practical.count()
            completed_t = theory.filter(status='COMPLETED').count()
            total_t = theory.count()
            total_all = total_p + total_t
            completed_all = completed_p + completed_t
            
            context['lessons'] = practical
            context['lesson_progress'] = practical
            context['ntsa_status'] = NTSARecord.objects.filter(student=student).first()
            context['completed_lessons'] = completed_all
            context['total_lessons'] = total_all
            context['total_hours'] = completed_p
            context['lesson_completion_rate'] = round((completed_all / total_all * 100)) if total_all else 0
            context['overall_progress'] = context['lesson_completion_rate']
        
        return render(request, 'student_portal/progress.html', context)


class PortalCertificatesView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from .models import StudentDocument
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None
        
        certificates = StudentDocument.objects.none()
        if student:
            from django.db.models import Q
            certificates = StudentDocument.objects.filter(
                is_active=True, category='certificates'
            ).filter(
                Q(student=student) | Q(student__isnull=True)
            )[:5]
        
        return render(request, 'student_portal/certificates.html', {
            'student': student,
            'certificates': certificates,
        })


class PortalProfileView(StudentRequiredMixin, View):
    def get(self, request):
        return render(request, 'student_portal/profile.html', {'user': request.user})


class PortalDocumentsView(StudentRequiredMixin, View):
    def get(self, request):
        from .models import StudentDocument
        from students.models import Student
        from django.db.models import Q

        category = request.GET.get('category', '')
        student = Student.objects.filter(user=request.user).first()
        docs = StudentDocument.objects.filter(is_active=True).filter(
            Q(student__isnull=True) | Q(student=student)
        )
        if category:
            docs = docs.filter(category=category)
        categories = StudentDocument.CATEGORY_CHOICES
        return render(request, 'student_portal/documents.html', {
            'documents': docs,
            'categories': categories,
            'current_category': category,
        })


class StaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role not in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST'):
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


from django.views.generic import ListView, CreateView, UpdateView, DeleteView


class DocListView(StaffMixin, ListView):
    from .models import StudentDocument
    model = StudentDocument
    template_name = 'student_portal/manage/doc_list.html'
    context_object_name = 'documents'
    paginate_by = 20

    def get_queryset(self):
        from .models import StudentDocument
        from django.db.models import Q
        queryset = StudentDocument.objects.all()
        q = self.request.GET.get('q', '').strip()
        cat = self.request.GET.get('category', '')
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if cat:
            queryset = queryset.filter(category=cat)
        return queryset


class DocCreateView(StaffMixin, CreateView):
    from .models import StudentDocument
    model = None
    template_name = 'student_portal/manage/doc_form.html'
    fields = ['title', 'description', 'file', 'category', 'is_active']
    success_url = reverse_lazy('student_portal:manage_documents')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from .models import StudentDocument
        self.model = StudentDocument

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import StudentDocument
        from students.models import Student
        context['categories'] = StudentDocument.CATEGORY_CHOICES
        context['all_students'] = Student.objects.select_related('user').all()
        return context

    def post(self, request, *args, **kwargs):
        from .models import StudentDocument
        from django.contrib import messages

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'theory')
        is_active = request.POST.get('is_active') == 'on'
        student_id = request.POST.get('student') or None
        files = request.FILES.getlist('files')

        if not title:
            messages.error(request, 'Title is required.')
            return self.form_invalid(self.get_form())

        if not files:
            messages.error(request, 'At least one file is required.')
            return self.form_invalid(self.get_form())

        created = 0
        for f in files:
            StudentDocument.objects.create(
                title=title if len(files) == 1 else f"{title} - {f.name}",
                description=description,
                file=f,
                category=category,
                student_id=student_id,
                is_active=is_active,
            )
            created += 1

        messages.success(request, f'{created} document(s) uploaded successfully.')
        return redirect(self.success_url)


class DocUpdateView(StaffMixin, UpdateView):
    from .models import StudentDocument
    model = None
    template_name = 'student_portal/manage/doc_form.html'
    fields = ['title', 'description', 'file', 'category', 'is_active']
    success_url = reverse_lazy('student_portal:manage_documents')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from .models import StudentDocument
        self.model = StudentDocument


class DocDeleteView(StaffMixin, DeleteView):
    from .models import StudentDocument
    model = None
    template_name = 'student_portal/manage/doc_confirm_delete.html'
    success_url = reverse_lazy('student_portal:manage_documents')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from .models import StudentDocument
        self.model = StudentDocument

    def delete(self, request, *args, **kwargs):
        from django.contrib import messages
        messages.success(request, 'Document deleted successfully.')
        return super().delete(request, *args, **kwargs)


class PortalEventsView(StudentRequiredMixin, View):
    def get(self, request):
        from .models import Event
        category = request.GET.get('category', '')
        events = Event.objects.filter(is_active=True)
        if category:
            events = events.filter(category=category)
        upcoming = events.filter(event_date__gte=timezone.now().date())
        past = events.filter(event_date__lt=timezone.now().date())

        return render(request, 'student_portal/events.html', {
            'upcoming_events': upcoming,
            'past_events': past,
            'categories': Event.CATEGORY_CHOICES,
            'current_category': category,
        })


class PortalProgressReportPDFView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from .pdf_utils import generate_progress_report
        student = Student.objects.get(user=request.user)
        pdf = generate_progress_report(student)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="progress_report_{student.student_number}.pdf"'
        return response


class PortalPaymentReportPDFView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from .pdf_utils import generate_payment_report
        student = Student.objects.get(user=request.user)
        pdf = generate_payment_report(student)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="payment_report_{student.student_number}.pdf"'
        return response


class PortalEnrollmentReportPDFView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from .pdf_utils import generate_enrollment_report
        student = Student.objects.get(user=request.user)
        pdf = generate_enrollment_report(student)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="enrollment_report_{student.student_number}.pdf"'
        return response


# ==================== EVENT MANAGEMENT (Staff) ====================

class EventListView(StaffMixin, View):
    def get(self, request):
        from .models import Event
        q = request.GET.get('q', '')
        cat = request.GET.get('category', '')
        events = Event.objects.all()
        if q:
            events = events.filter(title__icontains=q)
        if cat:
            events = events.filter(category=cat)

        return render(request, 'student_portal/manage/event_list.html', {
            'events': events,
            'categories': Event.CATEGORY_CHOICES,
            'search_query': q,
            'category_filter': cat,
        })


class EventCreateView(StaffMixin, View):
    def get(self, request):
        from .forms import EventForm
        form = EventForm()
        return render(request, 'student_portal/manage/event_form.html', {'form': form, 'is_edit': False})

    def post(self, request):
        from .forms import EventForm
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'Event created successfully.')
            return redirect('student_portal:manage_events')
        return render(request, 'student_portal/manage/event_form.html', {'form': form, 'is_edit': False})


class EventUpdateView(StaffMixin, View):
    def get(self, request, pk):
        from .models import Event
        from .forms import EventForm
        event = get_object_or_404(Event, pk=pk)
        form = EventForm(instance=event)
        return render(request, 'student_portal/manage/event_form.html', {'form': form, 'event': event, 'is_edit': True})

    def post(self, request, pk):
        from .models import Event
        from .forms import EventForm
        event = get_object_or_404(Event, pk=pk)
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'Event updated successfully.')
            return redirect('student_portal:manage_events')
        return render(request, 'student_portal/manage/event_form.html', {'form': form, 'event': event, 'is_edit': True})


class EventDeleteView(StaffMixin, View):
    def get(self, request, pk):
        from .models import Event
        event = get_object_or_404(Event, pk=pk)
        return render(request, 'student_portal/manage/event_confirm_delete.html', {'event': event})

    def post(self, request, pk):
        from .models import Event
        from django.contrib import messages
        event = get_object_or_404(Event, pk=pk)
        event.delete()
        messages.success(request, 'Event deleted successfully.')
        return redirect('student_portal:manage_events')
