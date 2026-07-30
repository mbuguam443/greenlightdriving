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
import tempfile
import glob

REPO_URL = 'https://github.com/mbuguam443/greenlightdriving.git'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

print("=" * 50)
print("  Green Light Driving School - Update")
print("=" * 50)

project_dir = os.path.dirname(os.path.abspath(__file__))

# 0. Git setup / pull
print("\n[0/6] Syncing code from GitHub...")
git_dir = os.path.join(project_dir, '.git')
git_available = False

try:
    subprocess.run(['git', '--version'], capture_output=True, check=True)
    git_available = True
except Exception:
    pass

if git_available:
    if os.path.isdir(git_dir):
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            capture_output=True, text=True, timeout=60, cwd=project_dir
        )
        if result.returncode == 0:
            print(f"      {result.stdout.strip() or 'Already up to date.'}")
        else:
            print(f"      Git pull failed: {result.stderr.strip()}")
            print("      Continuing with existing code...")
    else:
        print("      Cloning repository for the first time...")
        tmp = tempfile.mkdtemp()
        clone_result = subprocess.run(
            ['git', 'clone', REPO_URL, tmp],
            capture_output=True, text=True, timeout=120
        )
        if clone_result.returncode == 0:
            # Copy all files from clone to project dir (except media, staticfiles, .git)
            exclude_dirs = {'media', 'staticfiles', '.git'}
            for item in os.listdir(tmp):
                if item in exclude_dirs:
                    continue
                src = os.path.join(tmp, item)
                dst = os.path.join(project_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst, symlinks=True)
                else:
                    shutil.copy2(src, dst)
            # Copy .git directory too
            shutil.copytree(os.path.join(tmp, '.git'), git_dir, symlinks=True)
            shutil.rmtree(tmp)
            print("      Repository cloned. Re-running update with fresh code...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print(f"      Clone failed: {clone_result.stderr.strip()}")
            print("      Continuing with existing code...")
else:
    print("      Git not found on this server.")
    print("      To enable automatic updates, install git or set up GitHub deployment.")
    print("      Continuing with existing code...")

# 1. Setup Django
import django
django.setup()
from django.core.management import call_command
from django.db import connection

# 2. Clean stale columns (from partially-applied old migrations)
print("\n[1/6] Cleaning stale database columns...")
with connection.cursor() as c:
    for table, col in [
        ('lessons_lessonitem', 'lesson_type'),
        ('students_student', 'package_id'),
        ('admissions_admission', 'package_id'),
    ]:
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'")
        if c.fetchone()[0]:
            c.execute(f"SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'")
            row = c.fetchone()
            if row:
                c.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {row[0]}")
            c.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
            print(f"      Dropped stale column {table}.{col}")
    # Drop old junction table if it exists
    for t in ['lessons_lessonitem_packages', 'lessons_coursepackage']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{t}'")
        if c.fetchone()[0]:
            c.execute(f"DROP TABLE {t}")
            print(f"      Dropped stale table {t}")
print("      Database cleanup done")

# 3. Migrations
print("\n[2/6] Running migrations...")
call_command('makemigrations', interactive=False, verbosity=1)
call_command('migrate', interactive=False, verbosity=1)
print("      Done!")

# 3. Ensure media directories exist
print("\n[3/6] Setting up media directories...")
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
print("\n[4/6] Collecting static files...")
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
print("\n[5/6] Clearing Python cache and fixing permissions...")
for pycache_dir in glob.glob(os.path.join(project_dir, '**', '__pycache__'), recursive=True):
    if os.path.isdir(pycache_dir):
        shutil.rmtree(pycache_dir, ignore_errors=True)
        print(f"      Cleared {pycache_dir}")
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
print("      Permissions fixed, cache cleared")

# 6. Restart Passenger (touch passenger_wsgi.py to reload the app)
print("\n[6/6] Restarting Python app...")
passenger_file = os.path.join(project_dir, 'passenger_wsgi.py')
if os.path.isfile(passenger_file):
    os.utime(passenger_file, None)
    print("      App restarted (passenger_wsgi.py touched)")
else:
    print("      passenger_wsgi.py not found — skipping restart")

# 7. Seed check
print("\n[6/6] Checking if seed data needed...")
try:
    from website.models import Course
    if Course.objects.count() == 0:
        print("      Courses not found. Run python seed.py to seed data.")
    else:
        print(f"      {Course.objects.count()} course(s) already exist — skipping seed.")
except Exception:
    print("      Could not check seed status.")

print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
