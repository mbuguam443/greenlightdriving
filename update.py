#!/usr/bin/env python3
"""
Green Light Driving School - Update Script
Run this after uploading a zip update:
  1. Upload zip via cPanel File Manager
  2. Extract into /home/wlsihszp/greenlight/
  3. Run: python update.py
"""
import os
import sys
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

print("=" * 50)
print("  Green Light Driving School - Update")
print("=" * 50)

project_dir = os.path.dirname(os.path.abspath(__file__))

# 1. Setup Django
import django
django.setup()
from django.core.management import call_command

# 2. Migrations
print("\n[1/4] Running migrations...")
call_command('migrate', '--run-syncdb', verbosity=1)
print("      Done!")

# 3. Ensure media directories exist
print("\n[2/4] Setting up media directories...")
media_dir = os.path.join(project_dir, 'media')
os.makedirs(media_dir, exist_ok=True)
os.chmod(media_dir, 0o755)
for sub in ['courses', 'site', 'gallery', 'testimonials', 'blog', 'admissions/passports', 'admissions/ids', 'vehicles', 'student_documents', 'student_documents/other']:
    sub_dir = os.path.join(media_dir, sub)
    os.makedirs(sub_dir, exist_ok=True)
    os.chmod(sub_dir, 0o755)
for root, dirs, files in os.walk(media_dir):
    os.chmod(root, 0o755)
    for f in files:
        os.chmod(os.path.join(root, f), 0o644)
print("      Media directories ready")

# 4. Collect static
print("\n[3/4] Collecting static files...")
call_command('collectstatic', '--noinput', verbosity=1)
# Sync staticfiles/ -> static/ for Apache
staticfiles_dir = os.path.join(project_dir, 'staticfiles')
static_dir = os.path.join(project_dir, 'static')
if os.path.isdir(staticfiles_dir):
    for item in os.listdir(staticfiles_dir):
        src = os.path.join(staticfiles_dir, item)
        dst = os.path.join(static_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print("      Static files synced to static/")
print("      Done!")

# 5. Fix permissions
print("\n[4/4] Fixing file permissions...")
for root, dirs, files in os.walk(project_dir):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', 'staticfiles', 'node_modules')]
    try:
        os.chmod(root, 0o755)
    except OSError:
        pass
    for f in files:
        try:
            os.chmod(os.path.join(root, f), 0o644)
        except OSError:
            pass
print("      Permissions fixed")

print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
