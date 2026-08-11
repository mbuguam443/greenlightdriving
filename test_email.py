#!/usr/bin/env python3
"""SMTP email diagnostic script. Run via cPanel Python App to see what's failing."""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()

from django.core.mail import send_mail, get_connection
from django.conf import settings

TO_EMAIL = os.environ.get('EMAIL_TEST_TO', settings.EMAIL_HOST_USER)
FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

print("=" * 50)
print("  Email Diagnostic Test")
print("=" * 50)
print(f"  Backend: {settings.EMAIL_BACKEND}")
print(f"  Host: {settings.EMAIL_HOST}")
print(f"  Port: {settings.EMAIL_PORT}")
print(f"  TLS: {settings.EMAIL_USE_TLS}")
print(f"  SSL: {settings.EMAIL_USE_SSL}")

# Test 1: file-based (always works)
print("\n  [Test 1] File-based backend (baseline)...")
try:
    with get_connection('django.core.mail.backends.filebased.EmailBackend', file_path=os.path.join(settings.BASE_DIR, 'sent_emails')) as conn:
        send_mail('Test Email', 'This is a test from Green Light.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ✓ File-based OK — email saved to sent_emails/")
except Exception as e:
    print(f"  ✗ File-based FAILED: {e}")

# Test 2: SMTP on localhost:25 (cPanel default)
print("\n  [Test 2] SMTP localhost:25 (no auth)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend', host='localhost', port=25, use_tls=False, use_ssl=False) as conn:
        send_mail('Test Email', 'This is a test from Green Light.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False, )
    print("  ✓ SMTP localhost:25 OK — email sent!")
except Exception as e:
    print(f"  ✗ SMTP localhost:25 FAILED: {e}")

# Test 3: SMTP on localhost:587 (TLS)
print("\n  [Test 3] SMTP localhost:587 (TLS)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend', host='localhost', port=587, use_tls=True, use_ssl=False) as conn:
        send_mail('Test Email', 'Test.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ✓ SMTP localhost:587 OK!")
except Exception as e:
    print(f"  ✗ SMTP localhost:587 FAILED: {e}")

print("\n" + "=" * 50)
print("  DIAGNOSTIC COMPLETE")
print("  Check the configured recipient inbox and spam folder")
print("  Also check sent_emails/ folder for file-based backup")
print("=" * 50)

# Test 6: configured SMTP (Gmail when EMAIL_HOST=smtp.gmail.com)
print("\n  [Test 6] Gmail SMTP (app password)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend',
            host=settings.EMAIL_HOST, port=settings.EMAIL_PORT,
            use_tls=settings.EMAIL_USE_TLS, use_ssl=settings.EMAIL_USE_SSL,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD) as conn:
        send_mail('Test Email', 'Test from configured SMTP.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False)
    print("  OK: configured SMTP accepted the message!")
except Exception as e:
    print(f"  FAILED: configured SMTP: {e}")

print("\n" + "=" * 50)
print("  ALL TESTS COMPLETE")
print("=" * 50)
