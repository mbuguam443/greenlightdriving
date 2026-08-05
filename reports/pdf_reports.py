"""Beautiful PDF report generation for Green Light Driving School."""
import io
import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image

GREEN = colors.HexColor('#2E7D32')
GREEN_LIGHT = colors.HexColor('#E8F5E9')
GREEN_MED = colors.HexColor('#66BB6A')
DARK = colors.HexColor('#1B5E20')
WHITE = colors.white
GREY = colors.HexColor('#666666')

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'logo.png')
LIGHT_GREY = colors.HexColor('#F5F5F5')


def _header_footer(canvas, doc):
    w, h = A4
    canvas.saveState()
    # Top green bar
    canvas.setFillColor(GREEN)
    canvas.rect(0, h - 20, w, 20, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 7)
    canvas.drawString(25, h - 15, "GREENLIGHT DEFENSIVE DRIVING SCHOOL")
    canvas.drawRightString(w - 25, h - 15, "Kimbo | Ruiru | Waithaka")
    # Footer
    canvas.setFillColor(GREY)
    canvas.setFont('Helvetica', 7)
    canvas.drawString(25, 15, "Generated: " + date.today().strftime('%d %B %Y'))
    canvas.drawRightString(w - 25, 15, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _make_table(data, col_widths, total_text=""):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), GREEN),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('BACKGROUND', (0, 1), (-1, -1), WHITE),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.Color(0.85, 0.85, 0.85)),
        ('FONTSIZE', (0, 1), (-1, -1), 7.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 1), (-1, -1), 5),
    ]
    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 1:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), GREEN_LIGHT))
    t.setStyle(TableStyle(style_cmds))
    return t


def _title(title_text, subtitle=""):
    styles = getSampleStyleSheet()
    els = []
    # Logo + title in a table
    logo_table_data = [[
        Image(LOGO_PATH, width=40, height=40) if os.path.isfile(LOGO_PATH) else Paragraph("", styles['Normal']),
        Paragraph(title_text, ParagraphStyle('PDFTitle', parent=styles['Title'], fontSize=18, textColor=DARK,
                                              spaceAfter=2, fontName='Helvetica-Bold'))
    ]]
    logo_table = Table(logo_table_data, colWidths=[50, None])
    logo_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 10),
    ]))
    els.append(logo_table)
    if subtitle:
        els.append(Paragraph(subtitle, ParagraphStyle(
            'PDFSub', parent=styles['Normal'], fontSize=9, textColor=GREY, spaceAfter=8
        )))
    els.append(HRFlowable(width="100%", thickness=1.5, color=GREEN, spaceAfter=8))
    return els


def generate_payment_report(payments):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=28*mm, bottomMargin=22*mm)
    story = _title("Payment Report", f"All recorded payments — {date.today().strftime('%d %B %Y')}")

    total = 0
    data = [['Receipt', 'Student', 'Amount', 'Method', 'Status', 'Date']]
    for p in payments:
        total += p.amount
        data.append([p.receipt_number, p.student.user.full_name if p.student else '—',
                     f'{p.amount:,.0f}', p.get_method_display(),
                     p.get_status_display(), p.created_at.strftime('%d/%m/%y')])

    story.append(_make_table(data, col_widths=[62, None, 52, 45, 50, 48]))
    story.append(Spacer(1, 5*mm))
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"<b>Total Payments: {len(payments)} | Total Revenue: KES {total:,.0f}</b>",
                           ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=DARK)))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_enquiry_report(enquiries):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=28*mm, bottomMargin=22*mm)
    story = _title("Walk-in Enquiry Report", f"All customer enquiries — {date.today().strftime('%d %B %Y')}")

    data = [['Date', 'Name', 'Phone', 'Course Interest', 'Status']]
    for e in enquiries:
        status = 'Converted' if e.converted else ('Followed Up' if e.followed_up else 'Pending')
        data.append([e.created_at.strftime('%d/%m/%y'), e.name, e.phone,
                     e.course.name if e.course else '—', status])

    story.append(_make_table(data, col_widths=[48, 100, 75, 100, 60]))
    story.append(Spacer(1, 5*mm))
    styles = getSampleStyleSheet()
    pending = sum(1 for e in enquiries if not e.followed_up and not e.converted)
    converted = sum(1 for e in enquiries if e.converted)
    story.append(Paragraph(f"<b>Total: {len(enquiries)} | Pending: {pending} | Converted: {converted}</b>",
                           ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=DARK)))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_student_report(students):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=28*mm, bottomMargin=22*mm)
    story = _title("Student Enrollment Report", f"All registered students — {date.today().strftime('%d %B %Y')}")

    data = [['Number', 'Name', 'Phone', 'Course', 'Package', 'Status', 'Enrolled']]
    for s in students:
        data.append([s.student_number, s.user.full_name, s.user.phone or '—',
                     s.course.name if s.course else '—', s.get_package_choice_display(),
                     s.get_status_display(), s.enrollment_date.strftime('%d/%m/%y') if s.enrollment_date else '—'])

    story.append(_make_table(data, col_widths=[52, 90, 65, 85, 45, 50, 48]))
    story.append(Spacer(1, 5*mm))
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"<b>Total Students: {len(students)}</b>",
                           ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=DARK)))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf


def generate_lesson_report(lessons, title="Lesson Report"):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=28*mm, bottomMargin=22*mm)
    story = _title(title, f"All practical lessons — {date.today().strftime('%d %B %Y')}")

    data = [['Student', 'Lesson Item', 'Instructor', 'Vehicle', 'Date', 'Status']]
    for l in lessons:
        data.append([l.student.user.full_name if l.student else '—',
                     l.lesson_item.name if l.lesson_item else '—',
                     l.instructor.user.full_name if l.instructor else '—',
                     l.vehicle.registration_number if l.vehicle else '—',
                     l.date.strftime('%d/%m/%y'), l.get_status_display()])

    story.append(_make_table(data, col_widths=[85, 100, 85, 55, 48, 55]))
    story.append(Spacer(1, 5*mm))
    styles = getSampleStyleSheet()
    completed = sum(1 for l in lessons if l.status == 'COMPLETED')
    story.append(Paragraph(f"<b>Total: {len(lessons)} | Completed: {completed}</b>",
                           ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=DARK)))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf
