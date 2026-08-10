from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.http import HttpResponse
from .models import DailyLog, SiteSettings


class StaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class DailyLogListView(StaffMixin, View):
    def get(self, request):
        from datetime import date
        from django.core.paginator import Paginator
        logs = DailyLog.objects.select_related('created_by').all()
        filter_date = request.GET.get('date', '')
        if filter_date:
            logs = logs.filter(log_date=filter_date)
        paginator = Paginator(logs, 15)
        page = request.GET.get('page', 1)
        return render(request, 'core/daily_log_list.html', {
            'logs': paginator.get_page(page),
            'filter_date': filter_date or str(date.today()),
        })


class DailyLogCreateView(StaffMixin, View):
    def post(self, request):
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        log_date = request.POST.get('log_date', '')
        if title:
            DailyLog.objects.create(title=title, description=description, log_date=log_date)
            messages.success(request, 'Activity logged.')
        return redirect('core:daily_log')


class DailyLogUpdateView(StaffMixin, View):
    def post(self, request, pk):
        log = get_object_or_404(DailyLog, pk=pk)
        log.title = request.POST.get('title', log.title)
        log.description = request.POST.get('description', log.description)
        log.log_date = request.POST.get('log_date', log.log_date)
        log.save()
        messages.success(request, 'Updated.')
        return redirect('core:daily_log')


class DailyLogDeleteView(StaffMixin, View):
    def get(self, request, pk):
        get_object_or_404(DailyLog, pk=pk).delete()
        messages.success(request, 'Deleted.')
        return redirect('core:daily_log')


class DailyLogPDFView(StaffMixin, View):
    def get(self, request):
        from datetime import date
        import io, os
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image, PageBreak

        logs = DailyLog.objects.select_related('created_by').all()
        filter_date = request.GET.get('date', '')
        if filter_date:
            logs = logs.filter(log_date=filter_date)
        filter_date = filter_date or str(date.today())

        GREEN = colors.HexColor('#2E7D32')
        DARK = colors.HexColor('#1B5E20')
        GREEN_LIGHT = colors.HexColor('#E8F5E9')
        GREY = colors.HexColor('#666666')

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=25*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()

        story = []
        # Logo + Title in header table
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images', 'logo.png')
        hdr_img = Image(logo_path, width=42, height=42) if os.path.isfile(logo_path) else Paragraph("GLS", styles['Normal'])
        hdr_title = Paragraph("DAILY ACTIVITY REPORT", ParagraphStyle('HdrTitle', parent=styles['Title'], fontSize=16, textColor=DARK, fontName='Helvetica-Bold', leading=20))
        hdr_sub = Paragraph(f"{filter_date}", ParagraphStyle('HdrSub', parent=styles['Normal'], fontSize=8, textColor=GREY))
        
        hdr_data = [[hdr_img, [hdr_title, hdr_sub]]]
        hdr_table = Table(hdr_data, colWidths=[50, None])
        hdr_table.setStyle(TableStyle([('VALIGN',(0,0),(0,0),'TOP'),('TOPPADDING',(0,0),(0,0),0)]))
        story.append(hdr_table)
        story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=10))

        desc_style = ParagraphStyle('Desc', parent=styles['Normal'], fontSize=8, leading=11, wordWrap='CJK')
        time_style = ParagraphStyle('Time', parent=styles['Normal'], fontSize=8, textColor=GREY)

        data = [['Time', 'Activity', 'Details']]
        for l in logs:
            data.append([
                Paragraph(f"{l.created_at.strftime('%I:%M %p')}", time_style),
                Paragraph(f"<b>{l.title}</b>", ParagraphStyle('Title', parent=styles['Normal'], fontSize=9, leading=12)),
                Paragraph(l.description or '—', desc_style),
            ])

        t = Table(data, colWidths=[50, 180, None], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), GREEN),
            ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('FONTNAME',(0,0),(-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0), 8),
            ('BOTTOMPADDING',(0,0),(-1,0), 8),
            ('TOPPADDING',(0,0),(-1,0), 8),
            ('GRID',(0,0),(-1,-1), 0.3, colors.Color(0.9,0.9,0.9)),
            ('FONTSIZE',(0,1),(-1,-1), 8),
            ('VALIGN',(0,0),(-1,-1), 'TOP'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.white, GREEN_LIGHT]),
            ('TOPPADDING',(0,1),(-1,-1), 8),
            ('BOTTOMPADDING',(0,1),(-1,-1), 8),
            ('LEFTPADDING',(0,0),(-1,-1), 8),
            ('RIGHTPADDING',(0,0),(-1,-1), 8),
            ('LINEBELOW',(0,0),(-1,-1), 0.3, colors.Color(0.9,0.9,0.9)),
        ]))
        story.append(t)

        story.append(Spacer(1, 8*mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN, spaceAfter=4))
        summary = Paragraph(
            f"<b>Total Activities: {len(logs)}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Greenlight Defensive Driving School &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Kimbo | Ruiru | Waithaka",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=GREY, alignment=1)
        )
        story.append(summary)

        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')




class SiteSettingsView(StaffMixin, View):
    def get(self, request):
        settings = SiteSettings.load()
        return render(request, 'core/site_settings.html', {'settings': settings})

    def post(self, request):
        settings = SiteSettings.load()
        settings.exam_fee = request.POST.get('exam_fee', 3100)
        settings.save(update_fields=['exam_fee'])
        messages.success(request, f'Exam fee updated to KES {settings.exam_fee}.')
        return redirect('core:site_settings')

