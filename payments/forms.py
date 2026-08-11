from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'enrollment', 'amount', 'method', 'reference_number', 'status', 'description']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'enrollment': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned = super().clean()
        student = cleaned.get('student')
        enrollment = cleaned.get('enrollment')
        if student and enrollment and enrollment.student_id != student.pk:
            self.add_error('enrollment', 'Select an enrollment belonging to this student.')
        return cleaned
