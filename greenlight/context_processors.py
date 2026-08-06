from students.models import Student


def student_balance(request):
    """Add balance to template context for logged-in students."""
    balance = None
    if request.user.is_authenticated and request.user.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            balance = student.balance
        except Student.DoesNotExist:
            pass
    return {'student_balance': balance}
