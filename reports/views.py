from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.db.models import Sum, Count, Q
from datetime import date, timedelta


class StaffTestMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'ACCOUNTANT')


class ReportIndexView(StaffTestMixin, View):
    def get(self, request):
        from payments.models import Payment
        from students.models import Student
        from admissions.models import Admission, WalkInInquiry
        from instructors.models import Instructor
        from vehicles.models import Vehicle
        from lessons.models import PracticalLesson, TheoryLesson
        from datetime import date
        
        today = date.today()
        month_start = today.replace(day=1)
        
        # Enquiry stats
        enquiries = WalkInInquiry.objects.all()
        enquiry_pending = enquiries.filter(followed_up=False, converted=False).count()
        enquiry_converted = enquiries.filter(converted=True).count()
        
        # Lesson stats
        lessons_today = PracticalLesson.objects.filter(date=today).count()
        lessons_completed = PracticalLesson.objects.filter(status='COMPLETED').count()
        lessons_total = PracticalLesson.objects.count()
        
        context = {
            'total_students': Student.objects.filter(status='ACTIVE').count(),
            'total_revenue': Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0,
            'month_revenue': Payment.objects.filter(status='COMPLETED', created_at__date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0,
            'total_admissions': Admission.objects.count(),
            'pending_admissions': Admission.objects.filter(status='PENDING').count(),
            'total_instructors': Instructor.objects.filter(is_active=True).count(),
            'total_vehicles': Vehicle.objects.count(),
            'enquiry_total': enquiries.count(),
            'enquiry_pending': enquiry_pending,
            'enquiry_converted': enquiry_converted,
            'lessons_today': lessons_today,
            'lessons_completed': lessons_completed,
            'lessons_total': lessons_total,
        }
        return render(request, 'reports/index.html', context)


class RevenueReportView(StaffTestMixin, View):
    def get(self, request):
        from payments.models import Payment
        from django.db.models import Sum
        from datetime import date
        
        period = request.GET.get('period', 'month')
        today = date.today()
        
        if period == 'today':
            payments = Payment.objects.filter(created_at__date=today, status='COMPLETED')
        elif period == 'week':
            week_start = today - timedelta(days=today.weekday())
            payments = Payment.objects.filter(created_at__date__gte=week_start, status='COMPLETED')
        elif period == 'year':
            year_start = today.replace(month=1, day=1)
            payments = Payment.objects.filter(created_at__date__gte=year_start, status='COMPLETED')
        else:
            month_start = today.replace(day=1)
            payments = Payment.objects.filter(created_at__date__gte=month_start, status='COMPLETED')
        
        total = payments.aggregate(total=Sum('amount'))['total'] or 0
        by_method = payments.values('method').annotate(total=Sum('amount')).order_by('-total')
        
        context = {
            'payments': payments[:100],
            'total': total,
            'by_method': by_method,
            'current_period': period,
        }
        return render(request, 'reports/revenue.html', context)


class AdmissionReportView(StaffTestMixin, View):
    def get(self, request):
        from admissions.models import Admission
        from students.models import Student
        from django.db.models import Count
        
        by_status = Admission.objects.values('status').annotate(count=Count('id')).order_by('status')
        by_category = Admission.objects.values('category__name').annotate(count=Count('id')).order_by('-count')
        by_branch = Admission.objects.values('branch__name').annotate(count=Count('id')).order_by('-count')
        
        context = {
            'by_status': by_status,
            'by_category': by_category,
            'by_branch': by_branch,
            'total': Admission.objects.count(),
        }
        return render(request, 'reports/admissions.html', context)


class OutstandingBalanceView(StaffTestMixin, View):
    def get(self, request):
        from students.models import Student
        
        active_students = Student.objects.filter(
            status='ACTIVE'
        ).select_related('user', 'course')
        
        students_with_balance = [s for s in active_students if s.balance > 0]
        students_with_balance.sort(key=lambda s: s.balance, reverse=True)
        
        total_outstanding = sum(s.balance for s in students_with_balance)
        
        context = {
            'students': students_with_balance,
            'total_outstanding': total_outstanding,
        }
        return render(request, 'reports/outstanding.html', context)


class InstructorPerformanceView(StaffTestMixin, View):
    def get(self, request):
        from instructors.models import Instructor
        from students.models import Student
        from lessons.models import PracticalLesson
        
        instructors = Instructor.objects.all()
        data = []
        for inst in instructors:
            students = Student.objects.filter(instructor=inst, status='ACTIVE')
            completed = PracticalLesson.objects.filter(instructor=inst, status='COMPLETED').count()
            data.append({
                'instructor': inst,
                'active_students': students.count(),
                'lessons_completed': completed,
            })
        
        return render(request, 'reports/instructor_performance.html', {'data': data})


class VehicleUtilizationView(StaffTestMixin, View):
    def get(self, request):
        from vehicles.models import Vehicle
        from lessons.models import PracticalLesson
        
        vehicles = Vehicle.objects.all()
        data = []
        for v in vehicles:
            lessons = PracticalLesson.objects.filter(vehicle=v).count()
            data.append({
                'vehicle': v,
                'total_lessons': lessons,
            })
        
        return render(request, 'reports/vehicle_utilization.html', {'data': data})


class BranchPerformanceView(StaffTestMixin, View):
    def get(self, request):
        from core.models import Branch
        from students.models import Student
        from admissions.models import Admission
        from payments.models import Payment
        from django.db.models import Sum, Count
        
        branches = Branch.objects.filter(is_active=True)
        data = []
        for b in branches:
            students = Student.objects.filter(branch=b, status='ACTIVE').count()
            admissions = Admission.objects.filter(branch=b).count()
            revenue = Payment.objects.filter(student__branch=b, status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
            data.append({
                'branch': b,
                'students': students,
                'admissions': admissions,
                'revenue': revenue,
            })
        
        return render(request, 'reports/branch_performance.html', {'data': data})


class StudentProgressReportView(StaffTestMixin, View):
    def get(self, request):
        from students.models import Student
        
        students = Student.objects.filter(status='ACTIVE').select_related('user', 'course', 'instructor')
        
        context = {
            'students': students,
        }
        return render(request, 'reports/student_progress.html', context)


class ActivityReportView(StaffTestMixin, View):
    def get(self, request):
        from payments.models import Payment
        from admissions.models import WalkInInquiry
        from lessons.models import PracticalLesson, TheoryLesson
        from students.models import Student
        from datetime import date

        # Recent payments
        recent_payments = Payment.objects.select_related('student__user').order_by('-created_at')[:20]
        
        # Recent enquiries
        recent_enquiries = WalkInInquiry.objects.all().order_by('-created_at')[:20]
        
        # Lessons per student (top 10)
        student_lessons = Student.objects.filter(status='ACTIVE').annotate(
            practical_count=Count('practical_lessons', distinct=True),
            completed_count=Count('practical_lessons', filter=Q(practical_lessons__status='COMPLETED'), distinct=True),
        ).order_by('-practical_count')[:10]
        
        # Payments per student
        student_payments = Student.objects.filter(status='ACTIVE').annotate(
            total_paid=Sum('payments__amount', filter=Q(payments__status='COMPLETED')),
            payment_count=Count('payments', filter=Q(payments__status='COMPLETED')),
        ).order_by('-total_paid')[:10]
        
        return render(request, 'reports/activity.html', {
            'recent_payments': recent_payments,
            'recent_enquiries': recent_enquiries,
            'student_lessons': student_lessons,
            'student_payments': student_payments,
        })



class BackupView(StaffTestMixin, View):
    def get(self, request):
        from django.core.management import call_command
        from django.http import HttpResponse
        import io
        import gzip
        from datetime import datetime

        buf = io.StringIO()
        call_command('dumpdata', '--exclude', 'auth.permission', '--exclude', 'contenttypes',
                     '--exclude', 'admin.logentry', '--exclude', 'sessions.session',
                     stdout=buf)
        response = HttpResponse(buf.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="greenlight_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json"'
        messages.success(request, 'Backup downloaded successfully.')
        return response



class PaymentReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from payments.models import Payment
        from .pdf_reports import generate_payment_report
        from django.http import HttpResponse
        
        payments = Payment.objects.select_related('student__user').all().order_by('-created_at')
        pdf = generate_payment_report(payments)
        return HttpResponse(pdf, content_type='application/pdf')


class EnquiryReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from admissions.models import WalkInInquiry
        from .pdf_reports import generate_enquiry_report
        from django.http import HttpResponse
        
        enquiries = WalkInInquiry.objects.all().order_by('-created_at')
        pdf = generate_enquiry_report(enquiries)
        return HttpResponse(pdf, content_type='application/pdf')


class StudentReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from students.models import Student
        from .pdf_reports import generate_student_report
        from django.http import HttpResponse
        
        students = Student.objects.select_related('user', 'course').all()
        pdf = generate_student_report(students)
        return HttpResponse(pdf, content_type='application/pdf')


class LessonReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from lessons.models import PracticalLesson
        from .pdf_reports import generate_lesson_report
        from django.http import HttpResponse
        
        lessons = PracticalLesson.objects.select_related('student__user', 'lesson_item', 'instructor__user', 'vehicle').all()
        pdf = generate_lesson_report(lessons)
        return HttpResponse(pdf, content_type='application/pdf')
