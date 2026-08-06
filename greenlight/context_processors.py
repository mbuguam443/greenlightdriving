from students.models import Student


def student_balance(request):
    """Add balance reminder info for logged-in students."""
    balance = None
    show_reminder = False
    if request.user.is_authenticated and request.user.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            if student.payment_reminder and student.balance > 0:
                balance = student.balance
                show_reminder = True
        except Student.DoesNotExist:
            pass
    return {'student_balance': balance, 'show_reminder': show_reminder}
