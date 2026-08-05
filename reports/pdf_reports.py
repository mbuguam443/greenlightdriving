"""PDF report generation using ReportLab."""
import io
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image


GREEN_DARK = colors.HexColor('#2E7D32')
GREEN_LIGHT = colors.HexColor('#66BB6A')
HEADER_BG = colors.HexColor('#2E7D32')


def _header_footer(canvas, doc):
    canvas.saveState()
    # Footer
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(30, 20, f"Greenlight Defensive Driving School | Generated: {date.today().strftime('%d %b %Y')}")
    canvas.drawRightString(A4[0] - 30, 20, f"Page {canvas.getPageNumber()}")
    # Header line
    canvas.setStrokeColor(GREEN_DARK)
    canvas.setLineWidth(2)
    canvas.line(30, A4[1] - 45, A4[0] - 30, A4[1] - 45)
    canvas.restoreState()


def _build_table(data, col_widths=None):
    if not data:
        return Paragraph("<i>No data available</i>", getSampleStyleSheet()['Normal'])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.9, 0.9, 0.9)),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.97, 0.95)]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return t


def generate_payment_report(payments):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=30*mm, bottomMargin=25*mm)
    styles = getSampleStyleSheet()
    story = []

    style_title = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, textColor=GREEN_DARK)
    story.append(Paragraph("Payment Report", style_title))
    story.append(Spacer(1, 6*mm))

    total = 0
    data = [['Receipt No.', 'Student', 'Amount (KES)', 'Method', 'Status', 'Date']]
    for p in payments:
        total += p.amount
        student_name = p.student.user.full_name if p.student else '—'
        data.append([p.receipt_number, student_name, f'{p.amount:,.0f}', p.get_method_display(), p.get_status_display(), p.created_at.strftime('%d/%m/%Y')])

    story.append(_build_table(data, col_widths=[70, None, 60, 55, 50, 60]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Total: KES {total:,.0f}</b> ({len(payments)} payment(s))", styles['Normal']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_enquiry_report(enquiries):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=30*mm, bottomMargin=25*mm)
    styles = getSampleStyleSheet()
    story = []

    style_title = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, textColor=GREEN_DARK)
    story.append(Paragraph("Walk-in Enquiry Report", style_title))
    story.append(Spacer(1, 6*mm))

    data = [['Date', 'Name', 'Phone', 'Course', 'Feedback', 'Status']]
    for e in enquiries:
        status = 'Converted' if e.converted else ('Followed' if e.followed_up else 'Pending')
        course_name = e.course.name if e.course else '—'
        data.append([e.created_at.strftime('%d/%m/%Y'), e.name, e.phone, course_name,
                     (e.feedback or '—')[:50], status])

    story.append(_build_table(data, col_widths=[50, 80, 65, 70, None, 50]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Total: {len(enquiries)} enquiry(ies)</b>", styles['Normal']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_student_report(students):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=30*mm, bottomMargin=25*mm)
    styles = getSampleStyleSheet()
    story = []

    style_title = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, textColor=GREEN_DARK)
    story.append(Paragraph("Student Enrollment Report", style_title))
    story.append(Spacer(1, 6*mm))

    data = [['Student No.', 'Name', 'Email', 'Phone', 'Course', 'Package', 'Status', 'Enrolled']]
    for s in students:
        data.append([
            s.student_number, s.user.full_name, s.user.email, s.user.phone or '—',
            s.course.name if s.course else '—', s.get_package_choice_display(),
            s.get_status_display(), s.enrollment_date.strftime('%d/%m/%Y') if s.enrollment_date else '—'
        ])

    story.append(_build_table(data, col_widths=[55, None, 90, 65, 75, 45, 50, 55]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Total: {len(students)} student(s)</b>", styles['Normal']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_lesson_report(lessons, title="Lesson Report"):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=30*mm, bottomMargin=25*mm)
    styles = getSampleStyleSheet()
    story = []

    style_title = ParagraphStyle('Title2', parent=styles['Title'], fontSize=16, textColor=GREEN_DARK)
    story.append(Paragraph(title, style_title))
    story.append(Spacer(1, 6*mm))

    data = [['Student', 'Lesson Item', 'Instructor', 'Date', 'Status', 'Vehicle']]
    for l in lessons:
        student = l.student.user.full_name if l.student else '—'
        inst = l.instructor.user.full_name if l.instructor else '—'
        veh = l.vehicle.registration_number if l.vehicle else '—'
        data.append([student, l.lesson_item.name if l.lesson_item else '—',
                     inst, l.date.strftime('%d/%m/%Y') if l.date else '—',
                     l.get_status_display(), veh])

    story.append(_build_table(data, col_widths=[70, 90, 70, 55, 60, 55]))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Total: {len(lessons)} lesson(s)</b>", styles['Normal']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf
