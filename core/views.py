from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views import View
from django.http import HttpResponse
from .models import DailyLog


class StaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST')


class DailyLogListView(StaffMixin, View):
    def get(self, request):
        from datetime import date
        logs = DailyLog.objects.select_related('recorded_by').all()
        filter_date = request.GET.get('date', '')
        if filter_date:
            logs = logs.filter(log_date=filter_date)
        return render(request, 'core/daily_log_list.html', {
            'logs': logs[:50],
            'filter_date': filter_date or str(date.today()),
        })


class DailyLogCreateView(StaffMixin, View):
    def post(self, request):
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        log_date = request.POST.get('log_date', '')
        if title:
            DailyLog.objects.create(title=title, description=description, log_date=log_date, recorded_by=request.user)
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
        import io
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable

        logs = DailyLog.objects.select_related('recorded_by').all()
        filter_date = request.GET.get('date', '')
        if filter_date:
            logs = logs.filter(log_date=filter_date)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=28*mm, bottomMargin=22*mm)
        styles = getSampleStyleSheet()

        story = [Paragraph("Daily Activity Report", ParagraphStyle('T', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#2E7D32'), fontName='Helvetica-Bold')),
                 Paragraph(f"Date: {filter_date or str(date.today())}", ParagraphStyle('S', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#666666'))),
                 HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2E7D32'), spaceAfter=8)]

        data = [['Time', 'Title', 'Description', 'By']]
        for l in logs:
            data.append([l.created_at.strftime('%H:%M'), l.title, l.description or '—',
                         l.recorded_by.full_name if l.recorded_by else '—'])

        t = Table(data, colWidths=[45, 120, None, 70], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#2E7D32')), ('TEXTCOLOR',(0,0),(-1,0), colors.white),
            ('GRID',(0,0),(-1,-1),0.4,colors.Color(0.85,0.85,0.85)), ('FONTSIZE',(0,0),(-1,-1),8),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#E8F5E9')]),
        ]))
        story.append(t)
        story.append(Spacer(1,4*mm))
        story.append(Paragraph(f"<b>Total: {len(logs)} activities</b>", ParagraphStyle('Sum', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#1B5E20'))))
        doc.build(story)
        buf.seek(0)
        return HttpResponse(buf, content_type='application/pdf')
