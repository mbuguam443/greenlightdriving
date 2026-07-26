from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "SUPER_ADMIN")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ("SUPER_ADMIN", "Super Admin"),
        ("MANAGER", "Manager"),
        ("RECEPTIONIST", "Receptionist"),
        ("INSTRUCTOR", "Instructor"),
        ("ACCOUNTANT", "Accountant"),
        ("STUDENT", "Student"),
    ]

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("OTHER", "Other"),
    ]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="STUDENT")
    passport_photo = models.ImageField(upload_to="passports/", blank=True)
    national_id = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    branch = models.ForeignKey(
        "core.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name or self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def is_super_admin(self):
        return self.role == "SUPER_ADMIN"

    def is_manager(self):
        return self.role == "MANAGER"

    def is_receptionist(self):
        return self.role == "RECEPTIONIST"

    def is_instructor(self):
        return self.role == "INSTRUCTOR"

    def is_accountant(self):
        return self.role == "ACCOUNTANT"

    def is_student(self):
        return self.role == "STUDENT"
