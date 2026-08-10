from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone', 
                  'role', 'gender', 'date_of_birth', 'national_id', 'branch',
                  'address', 'passport_photo', 'password1', 'password2')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone',
                  'role', 'gender', 'date_of_birth', 'national_id', 'branch',
                  'address', 'passport_photo', 'is_active')


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email Address', 'autofocus': True
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'gender', 'date_of_birth',
                  'address', 'passport_photo')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'passport_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'phone',
                  'role', 'gender', 'date_of_birth', 'national_id', 'branch',
                  'address', 'passport_photo', 'is_active', 'is_staff')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'passport_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class StudentRegistrationForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Last Name'
    }))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Phone Number'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Create Password'
    }))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm Password'
    }))

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User(
            username=data['email'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data['phone'],
            role='STUDENT',
        )
        user.set_password(data['password'])
        user.save()
        return user


from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm


class CustomPasswordResetForm(DjangoPasswordResetForm):
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('No account found with this email address.')
        return email
