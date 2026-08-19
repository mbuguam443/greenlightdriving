from django.shortcuts import render, redirect
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
            'outstanding_balance': sum(
                s.balance for s in Student.objects.filter(status='ACTIVE') if s.balance > 0
            ),
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
        ).select_related('user', 'course', 'admission')
        
        outstanding_list = []
        fully_paid_count = 0
        total_outstanding = 0
        for s in active_students:
            total_fees = s.total_fees
            amount_paid = s.amount_paid
            balance = s.balance
            if balance > 0:
                total_outstanding += balance
                outstanding_list.append({
                    'student': s,
                    'total_fees': total_fees,
                    'amount_paid': amount_paid,
                    'balance': balance,
                    'balance_percentage': round(balance * 100 / total_fees) if total_fees else 0,
                })
            else:
                fully_paid_count += 1
        
        outstanding_list.sort(key=lambda item: item['balance'], reverse=True)
        
        context = {
            'outstanding_list': outstanding_list,
            'students_with_balance': len(outstanding_list),
            'fully_paid_count': fully_paid_count,
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
        from datetime import date, timedelta

        vehicles_qs = Vehicle.objects.select_related('assigned_instructor__user').all()
        week_ago = date.today() - timedelta(days=7)
        vehicles = []
        for v in vehicles_qs:
            total = PracticalLesson.objects.filter(vehicle=v).count()
            weekly = PracticalLesson.objects.filter(vehicle=v, date__gte=week_ago).count()
            v.total_lessons = total
            v.weekly_lessons = weekly
            v.utilization_rate = min(100, int((weekly / 20) * 100)) if weekly else 0
            vehicles.append(v)

        return render(request, 'reports/vehicle_utilization.html', {
            'vehicles': vehicles,
            'total_vehicles': len(vehicles),
            'available_vehicles': sum(1 for v in vehicles if v.is_available),
            'unavailable_vehicles': sum(1 for v in vehicles if not v.is_available),
        })


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
            inst = v.assigned_instructor.user.full_name if v.assigned_instructor else '�'
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
            br = i.branch.name if i.branch else '�'
            data.append([i.user.full_name, i.phone or '�', i.license_number, i.get_license_class_display() or '�',
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
            data.append([a.admission_number, a.full_name, a.phone, a.course.name if a.course else '�',
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
        from lessons.models import PracticalLesson, TheoryLesson
        from django.http import HttpResponse
        import io
        from datetime import date
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

        practical = PracticalLesson.objects.select_related('student__user', 'lesson_item', 'instructor__user').all()
        theory = TheoryLesson.objects.select_related('student__user', 'instructor__user').all()
        
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=28*mm, bottomMargin=22*mm)
        styles = getSampleStyleSheet()
        story = [Paragraph("Attendance Report", ParagraphStyle('T', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#2E7D32'), fontName='Helvetica-Bold')),
                 Paragraph(f'Generated: {date.today().strftime("%d %B %Y")}', ParagraphStyle('S', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#666666'))),
                 HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=8)]

        story.append(Paragraph("<b>Practical Lessons</b>", ParagraphStyle('H', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2E7D32'))))
        story.append(Spacer(1, 3*mm))

        pdata = [['Student', 'Lesson Item', 'Date', 'Instructor', 'Attended', 'Status']]
        for l in practical:
            pdata.append([l.student.user.full_name if l.student else '-',
                         l.lesson_item.name if l.lesson_item else '-',
                         l.date.strftime('%d/%m/%y'),
                         l.instructor.user.full_name if l.instructor else '-',
                         'Present' if l.attended else 'Absent',
                         l.get_status_display()])
        t = Table(pdata, colWidths=[90, 110, 50, 90, 45, 60], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.Color(0.85,0.85,0.85)), ('FONTSIZE',(0,0),(-1,-1),7.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#E8F5E9')]),
        ]))
        story.append(t)
        p_present = sum(1 for l in practical if l.attended)
        story.append(Paragraph(f"Practical: {p_present}/{len(practical)} present", ParagraphStyle('Sum', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#1B5E20'))))
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph("<b>Theory Lessons</b>", ParagraphStyle('H', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2E7D32'))))
        story.append(Spacer(1, 3*mm))

        tdata = [['Student', 'Topic', 'Date', 'Instructor', 'Attended', 'Status']]
        for l in theory:
            tdata.append([l.student.user.full_name if l.student else '-',
                         l.topic, l.date.strftime('%d/%m/%y'),
                         l.instructor.user.full_name if l.instructor else '-',
                         'Present' if l.attended else 'Absent',
                         l.get_status_display()])
        t2 = Table(tdata, colWidths=[90, 130, 50, 90, 45, 60], repeatRows=1)
        t2.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.Color(0.85,0.85,0.85)), ('FONTSIZE',(0,0),(-1,-1),7.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#E8F5E9')]),
        ]))
        story.append(t2)
        t_present = sum(1 for l in theory if l.attended)
        story.append(Paragraph(f"Theory: {t_present}/{len(theory)} present", ParagraphStyle('Sum', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#1B5E20'))))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(f"<b>Total Attendance: {p_present+t_present}/{len(practical)+len(theory)} ({round((p_present+t_present)/(len(practical)+len(theory))*100) if (len(practical)+len(theory)) else 0}%)</b>",
                               ParagraphStyle('Sum', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#1B5E20'))))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')



class StudentAttendancePDFView(StaffTestMixin, View):
    def get(self, request, pk):
        from students.models import Student
        from lessons.models import PracticalLesson, TheoryLesson
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        import io
        from datetime import date
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

        student = get_object_or_404(Student, pk=pk)
        practical = PracticalLesson.objects.filter(student=student).select_related('lesson_item', 'instructor__user')
        theory = TheoryLesson.objects.filter(student=student).select_related('instructor__user')

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=28*mm, bottomMargin=22*mm)
        styles = getSampleStyleSheet()

        story = [Paragraph(f"Attendance - {student.user.full_name}", ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#2E7D32'), fontName='Helvetica-Bold')),
                 Paragraph(f'{student.student_number} | Generated: {date.today().strftime("%d %B %Y")}', ParagraphStyle('S', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#666666'))),
                 HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=8)]

        p_present = sum(1 for l in practical if l.attended)
        story.append(Paragraph(f"<b>Practical: {p_present}/{practical.count()} attended</b> | <b>Theory: {sum(1 for l in theory if l.attended)}/{theory.count()} attended</b>",
                               ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1B5E20'))))
        story.append(Spacer(1, 5*mm))

        pdata = [['Date', 'Lesson', 'Instructor', 'Attended', 'Status']]
        for l in practical:
            pdata.append([l.date.strftime('%d/%m/%y'), l.lesson_item.name if l.lesson_item else '-',
                         l.instructor.user.full_name if l.instructor else '-',
                         'Yes' if l.attended else 'No', l.get_status_display()])

        t = Table(pdata, colWidths=[48, 140, 100, 45, 65], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.Color(0.85,0.85,0.85)), ('FONTSIZE',(0,0),(-1,-1),7.5),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#E8F5E9')]),
        ]))
        story.append(t)

        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')



class PurgeDummyView(StaffTestMixin, View):
    def get(self, request):
        import subprocess, os, sys
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'purge_dummy.py')
        if os.path.isfile(script):
            subprocess.run([sys.executable, script])
        messages.success(request, 'Dummy data purged. Real data untouched.')
        return redirect('reports:index')



class ArrearsReportPDFView(StaffTestMixin, View):
    def get(self, request):
        from students.models import Student
        from django.http import HttpResponse
        import io, os
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image

        students = Student.objects.filter(status='ACTIVE').select_related('user', 'course')
        arrears = [s for s in students if s.balance > 0]
        arrears.sort(key=lambda s: s.balance, reverse=True)

        GREEN = colors.HexColor('#2E7D32')
        GREEN_LIGHT = colors.HexColor('#E8F5E9')
        RED = colors.HexColor('#DC3545')

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=25*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story = []
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'logo.png')
        img = Image(logo_path, width=42, height=42) if os.path.isfile(logo_path) else Paragraph("GLS", styles['Normal'])
        hdr = Paragraph("STUDENTS WITH ARREARS", ParagraphStyle('T', parent=styles['Title'], fontSize=16, textColor=GREEN, fontName='Helvetica-Bold'))
        hdr_sub = Paragraph(f"Report generated by {request.user.full_name}", ParagraphStyle('S', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#666666')))
        hdr_data = [[img, [hdr, hdr_sub]]]
        ht = Table(hdr_data, colWidths=[50, None])
        ht.setStyle(TableStyle([('VALIGN',(0,0),(0,0),'TOP')]))
        story.append(ht)
        story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=8))

        total_arrears = sum(s.balance for s in arrears)
        story.append(Paragraph(f"Total Outstanding: <font color='#DC3545'><b>KES {total_arrears:,.0f}</b></font> | {len(arrears)} student(s)",
                               ParagraphStyle('Sum', parent=styles['Normal'], fontSize=10)))
        story.append(Spacer(1, 5*mm))

        data = [['Student', 'Number', 'Course', 'Phone', 'Paid', 'Balance']]
        for s in arrears:
            data.append([s.user.full_name, s.student_number, s.course.name if s.course else '-',
                         s.user.phone or '-', f'{s.amount_paid:,.0f}', f'{s.balance:,.0f}'])

        t = Table(data, colWidths=[90, 60, 80, 70, 55, 55], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), GREEN), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('FONTNAME',(0,0),(-1,0), 'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,0), 9),
            ('GRID',(0,0),(-1,-1),0.3,colors.Color(0.9,0.9,0.9)),
            ('FONTSIZE',(0,1),(-1,-1),8), ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, GREEN_LIGHT]),
            ('TOPPADDING',(0,1),(-1,-1),6), ('BOTTOMPADDING',(0,1),(-1,-1),6),
        ]))
        story.append(t)
        story.append(Spacer(1, 6*mm))
        story.append(Paragraph("Greenlight Defensive Driving School | Kimbo | Ruiru | Waithaka",
                               ParagraphStyle('Foot', parent=styles['Normal'], fontSize=7, textColor=colors.HexColor('#999999'), alignment=1)))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')
