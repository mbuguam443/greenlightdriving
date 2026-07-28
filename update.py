#!/usr/bin/env python3
"""
Green Light Driving School - Update Script
Usage:
  1. Clone repo once: git clone https://github.com/mbuguam443/greenlightdriving.git .
  2. After that, just run: python update.py
  (Your code stays in sync with GitHub automatically)
"""
import os
import sys
import shutil
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

print("=" * 50)
print("  Green Light Driving School - Update")
print("=" * 50)

project_dir = os.path.dirname(os.path.abspath(__file__))

# 0. Git pull (if available)
print("\n[0/5] Pulling latest code from GitHub...")
git_dir = os.path.join(project_dir, '.git')
if os.path.isdir(git_dir):
    try:
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True, text=True, timeout=60, cwd=project_dir
        )
        if result.returncode == 0:
            print(f"      {result.stdout.strip() or 'Already up to date.'}")
        else:
            print(f"      Git pull failed: {result.stderr.strip()}")
            print("      Continuing with existing code...")
    except Exception as e:
        print(f"      Git not available or error: {e}")
        print("      Continuing with existing code...")
else:
    print("      Not a git repository. Clone once to enable auto-updates:")
    print("      git clone https://github.com/mbuguam443/greenlightdriving.git .")
    print("      Continuing with existing code...")

# 1. Setup Django
import django
django.setup()
from django.core.management import call_command

# 2. Migrations
print("\n[1/5] Running migrations...")
call_command('migrate', '--run-syncdb', verbosity=1)
print("      Done!")

# 3. Ensure media directories exist
print("\n[2/5] Setting up media directories...")
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
print("\n[3/5] Collecting static files...")
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
print("\n[4/5] Fixing file permissions...")
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

# 6. Seed check
print("\n[5/5] Checking if seed data needed...")
try:
    from lessons.models import CoursePackage
    if CoursePackage.objects.count() == 0:
        print("      Packages not found. Run python seed.py to seed data.")
    else:
        print(f"      {CoursePackage.objects.count()} package(s) already exist — skipping seed.")
except Exception:
    print("      Could not check seed status.")

print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
