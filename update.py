#!/usr/bin/env python3
"""
Green Light Driving School - Update Script
Run this after uploading new/changed files to apply migrations and collect static.
Does NOT re-seed data — use deploy.py for fresh installs.
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

import django
django.setup()

from django.core.management import call_command
import shutil

print("=" * 50)
print("  Green Light Driving School - Update")
print("=" * 50)

# 1. Migrations
print("\n[1/3] Running migrations...")
call_command('migrate', '--run-syncdb', verbosity=1)
print("      Done!")

# 1b. Ensure media directory permissions
media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media')
os.makedirs(media_dir, exist_ok=True)
os.chmod(media_dir, 0o755)
for sub in ['courses', 'site', 'gallery', 'testimonials', 'blog', 'admissions', 'vehicles']:
    sub_dir = os.path.join(media_dir, sub)
    os.makedirs(sub_dir, exist_ok=True)
    os.chmod(sub_dir, 0o755)
print("      Media directories ready")

# 2. Collect static
print("\n[2/3] Collecting static files...")
call_command('collectstatic', '--noinput', verbosity=1)
print("      Done!")

# 3. Sync staticfiles -> static for Apache
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
print("      Done!")

print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
