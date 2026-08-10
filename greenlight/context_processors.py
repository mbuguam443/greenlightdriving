from students.models import Student
from student_portal.models import Notification


def student_balance(request):
    """Add balance reminder info for logged-in students."""
    balance = None
    show_reminder = False
    unread_count = 0
    if request.user.is_authenticated and request.user.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            if student.payment_reminder and student.balance > 0:
                balance = student.balance
                show_reminder = True
            unread_count = Notification.objects.filter(student=student, is_read=False).count()
        except Student.DoesNotExist:
            pass
    return {
        'student_balance': balance,
        'show_reminder': show_reminder,
        'unread_notifications': unread_count,
    }


def admin_notifications(request):
    """Count student replies that admin hasn't seen."""
    admin_reply_count = 0
    if request.user.is_authenticated and request.user.role in ('SUPER_ADMIN', 'MANAGER', 'RECEPTIONIST'):
        admin_reply_count = Notification.objects.filter(reply__isnull=False).exclude(reply='').count()
    return {'admin_reply_count': admin_reply_count}
