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
        from django.db.models import Q
        
        payments = Payment.objects.select_related('student__user').all()
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        if search:
            payments = payments.filter(
                Q(receipt_number__icontains=search) |
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search)
            )
        if status:
            payments = payments.filter(status=status)
        payments = payments.order_by('-created_at')
        pdf = generate_payment_report(payments, exported_by=request.user.full_name)
        return HttpResponse(pdf, content_type='application/pdf')


class EnquiryReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from admissions.models import WalkInInquiry
        from .pdf_reports import generate_enquiry_report
        from django.http import HttpResponse
        
        enquiries = WalkInInquiry.objects.all()
        tab = request.GET.get('tab', '')
        if tab == 'pending':
            enquiries = enquiries.filter(followed_up=False, converted=False)
        elif tab == 'followed':
            enquiries = enquiries.filter(followed_up=True, converted=False)
        elif tab == 'converted':
            enquiries = enquiries.filter(converted=True)
        enquiries = enquiries.order_by('-created_at')
        pdf = generate_enquiry_report(enquiries, exported_by=request.user.full_name)
        return HttpResponse(pdf, content_type='application/pdf')


class StudentReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from students.models import Student
        from .pdf_reports import generate_student_report
        from django.http import HttpResponse
        from django.db.models import Q
        
        students = Student.objects.select_related('user', 'course').all()
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        if search:
            students = students.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(student_number__icontains=search)
            )
        if status:
            students = students.filter(status=status)
        pdf = generate_student_report(students, exported_by=request.user.full_name)
        return HttpResponse(pdf, content_type='application/pdf')


class LessonReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from lessons.models import PracticalLesson
        from .pdf_reports import generate_lesson_report
        from django.http import HttpResponse
        from django.db.models import Q
        
        lessons = PracticalLesson.objects.select_related('student__user', 'lesson_item', 'instructor__user', 'vehicle').all()
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status', '')
        date_f = request.GET.get('date', '')
        instructor_f = request.GET.get('instructor', '')
        if search:
            lessons = lessons.filter(
                Q(student__user__first_name__icontains=search) |
                Q(student__user__last_name__icontains=search) |
                Q(student__student_number__icontains=search)
            )
        if status:
            lessons = lessons.filter(status=status)
        if date_f:
            lessons = lessons.filter(date=date_f)
        if instructor_f:
            lessons = lessons.filter(instructor_id=instructor_f)
        pdf = generate_lesson_report(lessons, exported_by=request.user.full_name)
        return HttpResponse(pdf, content_type='application/pdf')



class VehicleReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from vehicles.models import Vehicle
        from .pdf_reports import generate_payment_report
        from django.http import HttpResponse
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        vehicles = Vehicle.objects.select_related('assigned_instructor__user').all()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=30*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("Vehicle Report", ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#2E7D32'))), Spacer(1, 6*mm)]

        data = [['Reg No.', 'Make', 'Model', 'Category', 'Year', 'Instructor', 'Available']]
        for v in vehicles:
            inst = v.assigned_instructor.user.full_name if v.assigned_instructor else 'ï¿½'
            data.append([v.registration_number, v.make, v.model_name, v.category, str(v.year), inst, 'Yes' if v.is_available else 'No'])

        t = Table(data, colWidths=[70, 55, 65, 45, 40, 80, 45], repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
             ('GRID',(0,0),(-1,-1),0.5,colors.Color(0.9,0.9,0.9)), ('FONTSIZE',(0,0),(-1,-1),8),
             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.Color(0.95,0.97,0.95)])]))
        story.append(t)
        story.append(Spacer(1,4*mm))
        story.append(Paragraph(f"<b>Total: {len(vehicles)} vehicle(s)</b>", styles['Normal']))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')


class InstructorReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from instructors.models import Instructor
        from django.http import HttpResponse
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        instructors = Instructor.objects.select_related('user', 'branch').all()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=30*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("Instructor Report", ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#2E7D32'))), Spacer(1, 6*mm)]

        data = [['Name', 'Phone', 'License No.', 'License Class', 'Experience', 'Branch', 'Active']]
        for i in instructors:
            br = i.branch.name if i.branch else 'ï¿½'
            data.append([i.user.full_name, i.phone or 'ï¿½', i.license_number, i.get_license_class_display() or 'ï¿½',
                         f'{i.experience_years} yrs', br, 'Active' if i.is_active else 'Inactive'])

        t = Table(data, colWidths=[80, 65, 65, 55, 45, 50, 40], repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
             ('GRID',(0,0),(-1,-1),0.5,colors.Color(0.9,0.9,0.9)), ('FONTSIZE',(0,0),(-1,-1),8),
             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.Color(0.95,0.97,0.95)])]))
        story.append(t)
        story.append(Spacer(1,4*mm))
        story.append(Paragraph(f"<b>Total: {len(instructors)} instructor(s)</b>", styles['Normal']))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')


class AdmissionReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from admissions.models import Admission
        from django.http import HttpResponse
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        admissions = Admission.objects.select_related('course').all()
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=30*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("Admission Report", ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#2E7D32'))), Spacer(1, 6*mm)]

        data = [['Adm No.', 'Name', 'Phone', 'Course', 'Package', 'Status', 'Date']]
        for a in admissions:
            data.append([a.admission_number, a.full_name, a.phone, a.course.name if a.course else 'ï¿½',
                         a.get_package_choice_display(), a.get_status_display(), a.created_at.strftime('%d/%m/%Y')])

        t = Table(data, colWidths=[55, 75, 65, 75, 45, 50, 55], repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
             ('GRID',(0,0),(-1,-1),0.5,colors.Color(0.9,0.9,0.9)), ('FONTSIZE',(0,0),(-1,-1),8),
             ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.Color(0.95,0.97,0.95)])]))
        story.append(t)
        story.append(Spacer(1,4*mm))
        story.append(Paragraph(f"<b>Total: {len(admissions)} admission(s)</b>", styles['Normal']))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')



class AttendanceReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from lessons.models import PracticalLesson
        from django.http import HttpResponse
        import io
        from datetime import date
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

        lessons = PracticalLesson.objects.select_related('student__user', 'lesson_item', 'instructor__user').all().order_by('date')
        
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=28*mm, bottomMargin=22*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("Attendance Report", ParagraphStyle('T', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#2E7D32'), fontName='Helvetica-Bold')),
                 Paragraph(f'Generated: {date.today().strftime("%d %B %Y")}', ParagraphStyle('S', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#666666'))),
                 HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=8)]

        data = [['Student', 'Lesson', 'Date', 'Instructor', 'Attended', 'Status']]
        for l in lessons:
            data.append([l.student.user.full_name if l.student else '—',
                         l.lesson_item.name if l.lesson_item else '—',
                         l.date.strftime('%d/%m/%y'),
                         l.instructor.user.full_name if l.instructor else '—',
                         'Present' if l.attended else 'Absent',
                         l.get_status_display()])

        t = Table(data, colWidths=[85, 100, 48, 85, 45, 55], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.Color(0.85,0.85,0.85)), ('FONTSIZE',(0,0),(-1,-1),7.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#E8F5E9')]),
        ]))
        story.append(t)
        story.append(Spacer(1,4*mm))
        present = sum(1 for l in lessons if l.attended)
        story.append(Paragraph(f"<b>Total: {len(lessons)} | Present: {present} | Absent: {len(lessons)-present}</b>",
                               ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1B5E20'))))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')
