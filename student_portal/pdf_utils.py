import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings

GREEN = HexColor('#2E7D32')
LIGHT_GREEN = HexColor('#66BB6A')
DARK = HexColor('#333333')
GRAY = HexColor('#666666')
LIGHT_BG = HexColor('#f8f9fa')


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        'SchoolName', parent=styles['Title'],
        fontSize=18, textColor=GREEN, spaceAfter=2, alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'SchoolTagline', parent=styles['Normal'],
        fontSize=9, textColor=GRAY, spaceAfter=12, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=14, textColor=DARK, spaceBefore=6, spaceAfter=14, alignment=TA_CENTER,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontSize=11, textColor=GREEN, spaceBefore=14, spaceAfter=6,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'InfoLabel', parent=styles['Normal'],
        fontSize=9, textColor=GRAY,
    ))
    styles.add(ParagraphStyle(
        'InfoValue', parent=styles['Normal'],
        fontSize=10, textColor=DARK, fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'NormalBold', parent=styles['Normal'],
        fontSize=10, textColor=DARK, fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        'SmallGray', parent=styles['Normal'],
        fontSize=8, textColor=GRAY, alignment=TA_CENTER,
    ))
    return styles


def _get_logo():
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        return Image(logo_path, width=50 * mm, height=25 * mm)
    return None


def _header(styles, title):
    elements = []
    logo = _get_logo()
    if logo:
        logo.hAlign = 'CENTER'
        elements.append(logo)
        elements.append(Spacer(1, 4))
    elements.append(Paragraph('GREENLIGHT DEFENSIVE DRIVING SCHOOL', styles['SchoolName']))
    elements.append(Paragraph('Drive Safe, Drive Smart &middot; NTSA Certified', styles['SchoolTagline']))
    elements.append(HRFlowable(width='100%', thickness=1.5, color=GREEN, spaceAfter=10))
    elements.append(Paragraph(title, styles['ReportTitle']))
    return elements


def _footer(styles):
    return [
        Spacer(1, 20),
        HRFlowable(width='100%', thickness=0.5, color=LIGHT_GREEN, spaceAfter=6),
        Paragraph(
            'This is a computer-generated document from Greenlight Defensive Driving School. '
            'For enquiries, call +254 700 000 000 or email info@greenlightschool.co.ke',
            styles['SmallGray']
        ),
    ]


def _info_table(styles, rows):
    data = []
    for label, value in rows:
        data.append([
            Paragraph(label, styles['InfoLabel']),
            Paragraph(str(value), styles['InfoValue']),
        ])
    t = Table(data, colWidths=[45 * mm, 120 * mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return t


def _table(headers, rows, col_widths=None):
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    t.setStyle(TableStyle(style))
    return t


def generate_progress_report(student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    styles = _get_styles()
    story = []
    story.extend(_header(styles, 'Student Progress Report'))
    story.append(Spacer(1, 6))

    story.append(_info_table(styles, [
        ('Student Name:', student.user.get_full_name()),
        ('Student Number:', student.student_number),
        ('Admission No.:', student.admission.admission_number if student.admission else 'N/A'),
        ('Course:', f'{student.category.name} - {student.course.name}'),
        ('Branch:', student.branch.name),
        ('Enrollment Date:', student.enrollment_date.strftime('%d %B %Y') if student.enrollment_date else 'N/A'),
        ('Report Date:', student.progress_percentage),
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph('Lesson Progress', styles['SectionHead']))
    from lessons.models import PracticalLesson
    all_lessons = PracticalLesson.objects.filter(student=student).select_related('lesson_item', 'instructor')
    completed = all_lessons.filter(status='COMPLETED')
    total = all_lessons.count()
    headers = ['Lesson', 'Instructor', 'Date', 'Status']
    rows = []
    for l in all_lessons[:20]:
        rows.append([
            l.lesson_item.name if l.lesson_item else '-',
            l.instructor.user.get_full_name() if l.instructor else '-',
            l.date.strftime('%d %b %Y') if l.date else '-',
            l.get_status_display() if hasattr(l, 'get_status_display') else l.status,
        ])
    if rows:
        story.append(_table(headers, rows, col_widths=[55*mm, 40*mm, 35*mm, 35*mm]))
    else:
        story.append(Paragraph('No lessons recorded yet.', styles['InfoLabel']))

    story.append(Spacer(1, 8))
    story.append(Paragraph('Summary', styles['SectionHead']))
    total_hrs = sum((getattr(l, 'duration', 0) or 0) for l in completed)
    pct = student.progress_percentage
    story.append(_info_table(styles, [
        ('Total Lessons:', total),
        ('Completed:', completed.count()),
        ('Pending:', total - completed.count()),
        ('Hours Completed:', f'{total_hrs:.1f} hrs'),
        ('Overall Progress:', f'{pct}%'),
        ('Balance Due:', f'KES {student.balance:,.0f}'),
    ]))

    story.extend(_footer(styles))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_payment_report(student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    styles = _get_styles()
    story = []
    story.extend(_header(styles, 'Payment Summary Report'))
    story.append(Spacer(1, 6))

    story.append(_info_table(styles, [
        ('Student Name:', student.user.get_full_name()),
        ('Student Number:', student.student_number),
        ('Course:', f'{student.category.name} - {student.course.name}'),
        ('Report Date:', student.progress_percentage),
    ]))
    story.append(Spacer(1, 8))

    story.append(Paragraph('Payment History', styles['SectionHead']))
    from payments.models import Payment
    payments = Payment.objects.filter(student=student).order_by('-created_at')
    headers = ['Receipt No.', 'Date', 'Amount', 'Method', 'Status']
    rows = []
    total_paid = 0
    for p in payments:
        rows.append([
            p.receipt_number,
            p.created_at.strftime('%d %b %Y') if p.created_at else '-',
            f'KES {p.amount:,.0f}',
            p.get_method_display() if hasattr(p, 'get_method_display') else p.method,
            p.get_status_display() if hasattr(p, 'get_status_display') else p.status,
        ])
        if p.status == 'COMPLETED':
            total_paid += p.amount
    if rows:
        story.append(_table(headers, rows, col_widths=[35*mm, 30*mm, 30*mm, 35*mm, 30*mm]))
    else:
        story.append(Paragraph('No payments recorded yet.', styles['InfoLabel']))

    story.append(Spacer(1, 8))
    story.append(Paragraph('Summary', styles['SectionHead']))
    course_fee = student.course.price if student.course else 0
    story.append(_info_table(styles, [
        ('Course Fee:', f'KES {course_fee:,.0f}'),
        ('Total Paid:', f'KES {total_paid:,.0f}'),
        ('Balance Due:', f'KES {student.balance:,.0f}'),
        ('Total Transactions:', payments.count()),
    ]))

    story.extend(_footer(styles))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_enrollment_report(student):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                            leftMargin=2 * cm, rightMargin=2 * cm)
    styles = _get_styles()
    story = []
    story.extend(_header(styles, 'Enrollment Details'))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Personal Information', styles['SectionHead']))
    story.append(_info_table(styles, [
        ('Full Name:', student.user.get_full_name()),
        ('Email:', student.user.email),
        ('Phone:', student.user.phone_number if hasattr(student.user, 'phone_number') else 'N/A'),
        ('Student Number:', student.student_number),
        ('Admission No.:', student.admission.admission_number if student.admission else 'N/A'),
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Course Details', styles['SectionHead']))
    story.append(_info_table(styles, [
        ('Category:', student.category.name if student.category else 'N/A'),
        ('Course:', student.course.name if student.course else 'N/A'),
        ('Course Fee:', f'KES {student.course.price:,.0f}' if student.course else 'N/A'),
        ('Branch:', student.branch.name if student.branch else 'N/A'),
        ('Instructor:', student.instructor.user.get_full_name() if student.instructor and student.instructor.user else 'Not Assigned'),
        ('Vehicle:', f'{student.vehicle.make} {student.vehicle.model} ({student.vehicle.reg_number})' if student.vehicle else 'Not Assigned'),
    ]))
    story.append(Spacer(1, 6))

    story.append(Paragraph('Enrollment Details', styles['SectionHead']))
    story.append(_info_table(styles, [
        ('Enrollment Date:', student.enrollment_date.strftime('%d %B %Y') if student.enrollment_date else 'N/A'),
        ('Expected Graduation:', student.expected_graduation.strftime('%d %B %Y') if student.expected_graduation else 'N/A'),
        ('Status:', student.get_status_display() if hasattr(student, 'get_status_display') else student.status),
        ('Notes:', student.notes if student.notes else 'None'),
    ]))

    from ntsa.models import NTSARecord
    ntsa = NTSARecord.objects.filter(student=student).first()
    if ntsa:
        story.append(Spacer(1, 6))
        story.append(Paragraph('NTSA Status', styles['SectionHead']))
        story.append(_info_table(styles, [
            ('PDL Status:', ntsa.get_pdl_status_display() if hasattr(ntsa, 'get_pdl_status_display') else ntsa.pdl_status),
            ('Licence Issued:', 'Yes' if ntsa.licence_issued else 'No'),
        ]))

    story.extend(_footer(styles))
    doc.build(story)
    buffer.seek(0)
    return buffer
