#!/usr/bin/env python3
"""SMTP email diagnostic script. Run via cPanel Python App to see what's failing."""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()

from django.core.mail import send_mail, get_connection
from django.conf import settings

TO_EMAIL = 'mbuguanjane@gmail.com'
FROM_EMAIL = 'info@greenlight-driving-defensive.schones-heim-builders.co.ke'

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

# Test 4: SMTP on greenlight-...:465 (SSL)
print("\n  [Test 4] SMTP domain:465 (SSL with auth)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend',
            host='greenlight-driving-defensive.schones-heim-builders.co.ke', port=465, use_ssl=True,
            username='noreply@greenlight-driving-defensive.schones-heim-builders.co.ke',
            password='Me32323383#&') as conn:
        send_mail('Test Email', 'Test.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ✓ SMTP domain:465 OK!")
except Exception as e:
    print(f"  ✗ SMTP domain:465 FAILED: {e}")

# Test 5: SMTP on domain:587 (TLS with auth)
print("\n  [Test 5] SMTP domain:587 (TLS with auth)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend',
            host='greenlight-driving-defensive.schones-heim-builders.co.ke', port=587, use_tls=True,
            username='noreply@greenlight-driving-defensive.schones-heim-builders.co.ke',
            password='Me32323383#&') as conn:
        send_mail('Test Email', 'Test.', FROM_EMAIL, [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ✓ SMTP domain:587 OK!")
except Exception as e:
    print(f"  ✗ SMTP domain:587 FAILED: {e}")

print("\n" + "=" * 50)
print("  DIAGNOSTIC COMPLETE")
print("  Check your inbox (mbuguanjane@gmail.com) and spam folder")
print("  Also check sent_emails/ folder for file-based backup")
print("=" * 50)

# Test 6: Gmail SMTP with App Password
print("\n  [Test 6] Gmail SMTP (app password)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend',
            host='smtp.gmail.com', port=587, use_tls=True,
            username='mbuguanjane@gmail.com',
            password='syhgujomdcnofene') as conn:
        send_mail('Test Email', 'Test from Gmail SMTP.', 'mbuguanjane@gmail.com', [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ? Gmail SMTP OK!")
except Exception as e:
    print(f"  ? Gmail SMTP FAILED: {e}")

# Test 7: Gmail SMTP on port 465 (SSL)
print("\n  [Test 7] Gmail SMTP port 465 (SSL)...")
try:
    with get_connection('django.core.mail.backends.smtp.EmailBackend',
            host='smtp.gmail.com', port=465, use_ssl=True,
            username='mbuguanjane@gmail.com',
            password='syhgujomdcnofene') as conn:
        send_mail('Test Email', 'Test from Gmail SMTP SSL.', 'mbuguanjane@gmail.com', [TO_EMAIL], connection=conn, fail_silently=False)
    print("  ? Gmail SMTP SSL OK!")
except Exception as e:
    print(f"  ? Gmail SMTP SSL FAILED: {e}")

print("\n" + "=" * 50)
print("  ALL TESTS COMPLETE")
print("=" * 50)
