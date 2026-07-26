#!/usr/bin/env python3
"""
Green Light Driving School - Update Script
Run this from cPanel Python App > Run > update.py
Pulls latest code from GitHub, runs migrations, collects static.
Does NOT re-seed data — use deploy.py for fresh installs.
"""
import os
import sys
import subprocess
import shutil

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

print("=" * 50)
print("  Green Light Driving School - Update")
print("=" * 50)

# 0. Pull latest code from GitHub
print("\n[0/5] Pulling latest code from GitHub...")
project_dir = os.path.dirname(os.path.abspath(__file__))
try:
    result = subprocess.run(
        ['git', 'pull', 'origin', 'main'],
        cwd=project_dir,
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        print(result.stdout.strip())
        print("      Code updated!")
    else:
        print("      Git pull failed (this is OK if not a git repo)")
        print("      " + result.stderr.strip()[:200])
except FileNotFoundError:
    print("      Git not available — skipping pull")
    print("      Upload files manually via File Manager or FTP")
except subprocess.TimeoutExpired:
    print("      Git pull timed out — skipping")

# 1. Setup Django
import django
django.setup()
from django.core.management import call_command

# 2. Migrations
print("\n[1/5] Running migrations...")
call_command('migrate', '--run-syncdb', verbosity=1)
print("      Done!")

# 2b. Ensure media directory permissions
media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
os.makedirs(media_dir, exist_ok=True)
os.chmod(media_dir, 0o755)
for sub in ['courses', 'site', 'gallery', 'testimonials', 'blog', 'admissions', 'vehicles', 'student_documents']:
    sub_dir = os.path.join(media_dir, sub)
    os.makedirs(sub_dir, exist_ok=True)
    os.chmod(sub_dir, 0o755)
for root, dirs, files in os.walk(media_dir):
    os.chmod(root, 0o755)
    for f in files:
        os.chmod(os.path.join(root, f), 0o644)
print("      Media directories ready")

# 3. Collect static
print("\n[2/5] Collecting static files...")
call_command('collectstatic', '--noinput', verbosity=1)
print("      Done!")

# 4. Sync staticfiles -> static for Apache
print("\n[3/5] Syncing static files for Apache...")
staticfiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'staticfiles')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if os.path.isdir(staticfiles_dir):
    for item in os.listdir(staticfiles_dir):
        src = os.path.join(staticfiles_dir, item)
        dst = os.path.join(static_dir, item)
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print("      Static files synced to static/")

# 5. Fix permissions on all project files
print("\n[4/5] Fixing file permissions...")
for root, dirs, files in os.walk(project_dir):
    if '__pycache__' in root or '.git' in root:
        continue
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

print("\n[5/5] Done!")
print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
