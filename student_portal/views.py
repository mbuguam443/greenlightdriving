from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.conf import settings
import os
import json

from .push import send_push


def pwa_manifest(request):
    path = os.path.join(str(settings.BASE_DIR), 'static', 'pwa', 'manifest.webmanifest')
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return HttpResponse(json.dumps(data, indent=2), content_type='application/manifest+json')


def pwa_service_worker(request):
    path = os.path.join(str(settings.BASE_DIR), 'static', 'pwa', 'sw.js')
    with open(path, encoding='utf-8') as f:
        content = f.read()
    response = HttpResponse(content, content_type='text/javascript; charset=utf-8')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache'
    return response


class StudentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role == 'STUDENT'


class PortalDashboardView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from admissions.models import Admission
        from lessons.models import PracticalLesson, TheoryLesson, LessonItem
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
        from lessons.models import PracticalLesson, TheoryLesson, LessonItem
        from django.contrib import messages
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
        
        # Auto-mark lesson notifications as read
        from .models import Notification
        Notification.objects.filter(student=student, notification_type='lesson', is_read=False).update(is_read=True)
        
        return render(request, 'student_portal/lessons.html', {
            'student': student,
            'practical_lessons': practical,
            'theory_lessons': theory,
            'completed_count': completed_all,
            'total_count': total_all,
            'progress_percentage': round((completed_all / total_all * 100)) if total_all else 0,
            'lesson_items': LessonItem.objects.filter(is_active=True),
        })

    def post(self, request):
        from students.models import Student
        from lessons.models import PracticalLesson, TheoryLesson, LessonItem
        from django.contrib import messages
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return redirect('student_portal:lessons')
        
        item_id = request.POST.get('lesson_item')
        lesson_date = request.POST.get('lesson_date', timezone.now().date())
        if not item_id:
            messages.error(request, 'Please select a lesson.')
            return redirect('student_portal:lessons')
        
        item = get_object_or_404(LessonItem, pk=item_id, is_active=True)
        
        if item.lesson_type == 'PRACTICAL':
            if PracticalLesson.objects.filter(student=student, lesson_item=item).exists():
                messages.warning(request, 'This practical lesson already exists.')
                return redirect('student_portal:lessons')
            PracticalLesson.objects.create(
                student=student, lesson_item=item, date=lesson_date,
                status='NOT_STARTED', submitted_by_student=True, is_approved=False,
            )
            from core.models import DailyLog
            DailyLog.objects.create(title=f'Student Submitted: {student.user.full_name}', description=f'Lesson: {item.name}. Date: {lesson_date}. Pending approval.', log_date=timezone.now().date())
        else:
            if TheoryLesson.objects.filter(student=student, lesson_item=item).exists():
                messages.warning(request, 'This theory lesson already exists.')
                return redirect('student_portal:lessons')
            TheoryLesson.objects.create(
                student=student, lesson_item=item, topic=item.name, date=lesson_date,
                time_start='08:00', time_end='09:00', status='NOT_STARTED',
            )
        
        messages.success(request, f'"{item.name}" submitted for approval.')
        return redirect('student_portal:lessons')


class PortalPaymentsView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from payments.models import Payment
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            student = None

        payments = Payment.objects.filter(student=student) if student else []
        total_paid = sum(p.amount for p in payments.filter(status='COMPLETED')) if student else 0
        total_fees = student.total_fees if student else 0
        balance = total_fees - total_paid
        # Get exam fee for breakdown
        from core.models import SiteSettings
        exam_fee = 0
        try:
            exam_fee = SiteSettings.load().exam_fee
        except Exception:
            pass
        course_fee = total_fees - exam_fee

        return render(request, 'student_portal/payments.html', {
            'payments': payments,
            'student': student,
            'total_paid': total_paid,
            'total_fees': total_fees,
            'balance': balance,
            'course_fee': course_fee,
            'exam_fee': exam_fee,
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
        from students.models import Student
        from admissions.models import Admission
        try:
            student = Student.objects.select_related('user', 'course', 'branch', 'instructor__user', 'admission').get(user=request.user)
        except Student.DoesNotExist:
            student = None
        admission = student.admission if student else None
        return render(request, 'student_portal/profile.html', {
            'student_profile': student,
            'admission': admission,
            'user': request.user,
        })

    def post(self, request):
        from students.models import Student
        from admissions.models import Admission
        try:
            student = Student.objects.select_related('admission').get(user=request.user)
        except Student.DoesNotExist:
            return redirect('student_portal:profile')

        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save(update_fields=['first_name', 'last_name', 'phone'])

        national_id = request.POST.get('national_id', '')
        address = request.POST.get('address', '')
        dob = request.POST.get('date_of_birth') or None
        gender = request.POST.get('gender', '')

        if national_id or address or dob or gender:
            admission = student.admission
            if not admission:
                admission = Admission(
                    first_name=user.first_name, last_name=user.last_name,
                    email=user.email, phone=user.phone or '',
                    date_of_birth=dob or '2000-01-01',
                    gender=gender or 'M',
                    national_id=national_id, address=address,
                    category=student.category, course=student.course,
                    branch=student.branch, status='ENROLLED',
                )
            else:
                admission.national_id = national_id or admission.national_id
                admission.address = address or admission.address
                admission.date_of_birth = dob or admission.date_of_birth
                admission.gender = gender or admission.gender
            admission.save()
            student.admission = admission
            student.save(update_fields=['admission'])
            messages.success(request, 'Admission profile completed. Thank you!')
        else:
            messages.success(request, 'Profile updated.')

        return redirect('student_portal:profile')


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


class PortalAttendanceReportPDFView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from django.http import HttpResponse
        from .pdf_utils import generate_attendance_report
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return HttpResponse("No student profile", status=404)
        pdf = generate_attendance_report(student)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{student.student_number}.pdf"'
        return response


class PortalNotificationsView(StudentRequiredMixin, View):
    def get(self, request):
        from students.models import Student
        from .models import Notification
        try:
            student = Student.objects.get(user=request.user)
            notifications = Notification.objects.filter(student=student)
        except Student.DoesNotExist:
            notifications = []
        return render(request, 'student_portal/notifications.html', {'notifications': notifications})


class ReadNotificationView(StudentRequiredMixin, View):
    def get(self, request, pk):
        from .models import Notification
        from students.models import Student
        try:
            student = Student.objects.get(user=request.user)
            notification = get_object_or_404(Notification, pk=pk, student=student)
        except Student.DoesNotExist:
            return redirect('student_portal:dashboard')
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return redirect('student_portal:notifications')


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


class NotificationCreateView(StaffMixin, View):
    def get(self, request):
        from students.models import Student
        students = Student.objects.filter(status='ACTIVE').select_related('user')
        return render(request, 'student_portal/manage/notification_form.html', {'students': students})

    def post(self, request):
        from students.models import Student
        from .models import Notification
        from django.contrib import messages

        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        ntype = request.POST.get('notification_type', 'general')
        send_to_all = request.POST.get('send_to_all') == '1'
        student_ids = request.POST.getlist('student_ids')

        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return redirect('student_portal:manage_notification')

        if send_to_all:
            students = Student.objects.filter(status='ACTIVE')
            for s in students:
                Notification.objects.create(student=s, title=title, message=message, notification_type=ntype)
                send_push(s, title, message)
            messages.success(request, f'Notification sent to {students.count()} students.')
        elif student_ids:
            students = Student.objects.filter(pk__in=student_ids)
            for s in students:
                Notification.objects.create(student=s, title=title, message=message, notification_type=ntype)
                send_push(s, title, message)
            messages.success(request, f'Notification sent to {students.count()} selected students.')
        else:
            student_id = request.POST.get('student')
            if not student_id:
                messages.error(request, 'Please select a student.')
                return redirect('student_portal:manage_notification')
            student = get_object_or_404(Student, pk=student_id)
            Notification.objects.create(student=student, title=title, message=message, notification_type=ntype)
            send_push(student, title, message)
            messages.success(request, f'Notification sent to {student.user.full_name}.')

        return redirect('student_portal:manage_notification')



class NotificationHistoryView(StaffMixin, View):
    def get(self, request):
        from .models import Notification
        notifications = Notification.objects.select_related('student__user').all()[:50]
        return render(request, 'student_portal/manage/notification_history.html', {'notifications': notifications})



class StudentLessonRequestView(StudentRequiredMixin, View):
    def post(self, request):
        from students.models import Student
        from lessons.models import PracticalLesson, LessonItem
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return redirect('student_portal:lessons')
        
        item_id = request.POST.get('lesson_item')
        if not item_id:
            messages.error(request, 'Please select a lesson.')
            return redirect('student_portal:lessons')
        
        item = get_object_or_404(LessonItem, pk=item_id, is_active=True)
        if PracticalLesson.objects.filter(student=student, lesson_item=item).exists():
            messages.warning(request, 'This lesson already exists.')
            return redirect('student_portal:lessons')
        
        PracticalLesson.objects.create(
            student=student, lesson_item=item,
            date=request.POST.get('lesson_date', timezone.now().date()),
            status='NOT_STARTED', submitted_by_student=True, is_approved=False,
        )
        messages.success(request, f'Lesson "{item.name}" submitted for approval.')
        return redirect('student_portal:lessons')


class LessonApprovalView(StaffMixin, View):
    def get(self, request):
        from lessons.models import PracticalLesson
        pending = PracticalLesson.objects.filter(submitted_by_student=True, is_approved=False).select_related('student__user', 'lesson_item')
        attendance = PracticalLesson.objects.filter(attended=True, is_approved=False).select_related('student__user', 'lesson_item')
        return render(request, 'student_portal/manage/lesson_approval.html', {
            'pending_lessons': pending,
            'attendance_requests': attendance,
        })


class ApproveLessonView(StaffMixin, View):
    def get(self, request, pk):
        from lessons.models import PracticalLesson
        lesson = get_object_or_404(PracticalLesson, pk=pk, submitted_by_student=True)
        lesson.is_approved = True
        lesson.save(update_fields=['is_approved'])
        messages.success(request, f'Lesson "{lesson.lesson_item.name}" approved for {lesson.student.user.full_name}.')
        return redirect('student_portal:lesson_approval')



class MarkAttendedView(StudentRequiredMixin, View):
    def get(self, request, pk):
        from lessons.models import PracticalLesson, TheoryLesson
        from students.models import Student
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return redirect('student_portal:lessons')
        lesson = PracticalLesson.objects.filter(pk=pk, student=student).first()
        is_practical = lesson is not None
        if not lesson:
            lesson = get_object_or_404(TheoryLesson, pk=pk, student=student)
        return render(request, 'student_portal/attendance_date.html', {
            'lesson': lesson,
            'is_practical': is_practical,
        })

    def post(self, request, pk):
        from lessons.models import PracticalLesson, TheoryLesson
        from students.models import Student
        from datetime import datetime
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return redirect('student_portal:lessons')
        attendance_date = request.POST.get('attendance_date', '').strip()
        try:
            selected_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            messages.error(request, 'Please select a valid attendance date.')
            return redirect('student_portal:mark_attended', pk=pk)

        lesson = PracticalLesson.objects.filter(pk=pk, student=student).first()
        if lesson:
            lesson.attended = True
            lesson.is_approved = False
            lesson.date = selected_date
            lesson.save(update_fields=['attended', 'is_approved', 'date'])
            messages.success(request, 'Attendance submitted for approval.')
            from core.models import DailyLog
            DailyLog.objects.create(title=f'Student Attendance: {student.user.full_name}', description=f'Marked {lesson.lesson_item.name} attended on {selected_date}. Pending approval.', log_date=timezone.now().date())
        else:
            lesson = get_object_or_404(TheoryLesson, pk=pk, student=student)
            lesson.attended = True
            lesson.date = selected_date
            lesson.save(update_fields=['attended', 'date'])
            messages.success(request, 'Attendance recorded.')
        return redirect('student_portal:lessons')



class ApproveAttendanceView(StaffMixin, View):
    def get(self, request, pk):
        from lessons.models import PracticalLesson
        lesson = get_object_or_404(PracticalLesson, pk=pk)
        lesson.is_approved = True
        lesson.status = 'COMPLETED'
        lesson.save(update_fields=['is_approved', 'status'])
        messages.success(request, f'Attendance approved for {lesson.student.user.full_name} - {lesson.lesson_item.name}.')
        return redirect('student_portal:lesson_approval')


class RejectAttendanceView(StaffMixin, View):
    def get(self, request, pk):
        from lessons.models import PracticalLesson
        lesson = get_object_or_404(PracticalLesson, pk=pk)
        lesson.attended = False
        lesson.is_approved = False
        lesson.save(update_fields=['attended', 'is_approved'])
        messages.success(request, f'Attendance rejected for {lesson.student.user.full_name}.')
        return redirect('student_portal:lesson_approval')



class PortalReceiptView(StudentRequiredMixin, View):
    def get(self, request, pk):
        from payments.models import Payment
        from django.templatetags.static import static
        try:
            from students.models import Student
            student = Student.objects.get(user=request.user)
            payment = get_object_or_404(Payment, pk=pk, student=student)
        except Student.DoesNotExist:
            return redirect('student_portal:dashboard')
        return render(request, 'payments/receipt_standalone.html', {
            'payment': payment,
            'logo_url': request.build_absolute_uri(static('images/logo.png')),
        })



class ReplyNotificationView(StudentRequiredMixin, View):
    def post(self, request, pk):
        from .models import Notification
        from students.models import Student
        from django.utils import timezone
        try:
            student = Student.objects.get(user=request.user)
            notification = get_object_or_404(Notification, pk=pk, student=student)
        except Student.DoesNotExist:
            return redirect('student_portal:dashboard')
        notification.reply = request.POST.get('reply', '').strip()
        notification.replied_at = timezone.now()
        notification.is_read = True
        notification.save(update_fields=['reply', 'replied_at', 'is_read'])
        messages.success(request, 'Reply sent.')
        return redirect('student_portal:notifications')


class ChatStaffMixin(LoginRequiredMixin):
    """Allow any staff role (anything except STUDENT) into staff chat."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.role == 'STUDENT':
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


def _chat_context(request, post_url, messages_url):
    from .models import ChatMessage
    chat_messages = list(ChatMessage.objects.select_related('user').order_by('-created_at')[:200])
    chat_messages.reverse()
    return {'chat_messages': chat_messages, 'chat_post_url': post_url, 'chat_messages_url': messages_url}


class PortalChatView(StudentRequiredMixin, View):
    def get(self, request):
        ctx = _chat_context(request, reverse('student_portal:chat'), reverse('student_portal:chat_messages'))
        return render(request, 'student_portal/chat.html', ctx)

    def post(self, request):
        content = request.POST.get('content', '').strip()
        if content:
            from .models import ChatMessage
            ChatMessage.objects.create(user=request.user, content=content[:2000])
        return redirect('student_portal:chat')


class StaffChatView(ChatStaffMixin, View):
    def get(self, request):
        ctx = _chat_context(request, reverse('student_portal:staff_chat'), reverse('student_portal:staff_chat_messages'))
        return render(request, 'student_portal/manage/chat.html', ctx)

    def post(self, request):
        content = request.POST.get('content', '').strip()
        if content:
            from .models import ChatMessage
            ChatMessage.objects.create(user=request.user, content=content[:2000])
        return redirect('student_portal:staff_chat')


class ChatMessagesJSONView(LoginRequiredMixin, View):
    def get(self, request):
        from .models import ChatMessage
        from django.http import JsonResponse
        data = []
        qs = ChatMessage.objects.select_related('user').order_by('-created_at')[:200]
        for m in reversed(list(qs)):
            u = m.user
            data.append({
                'user': u.get_full_name() or u.username,
                'role': u.get_role_display(),
                'is_staff': u.role != 'STUDENT',
                'content': m.content,
                'time': timezone.localtime(m.created_at).strftime('%H:%M'),
                'date': timezone.localtime(m.created_at).strftime('%a %d %b'),
                'is_me': u.id == request.user.id,
            })
        return JsonResponse({'messages': data})
