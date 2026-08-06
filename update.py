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
            output = result.stdout.strip()
            print(f"      {output or 'Already up to date.'}")
            if output and 'Already up to date' not in output:
                print("      Code updated. Re-running with new version...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
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

# 2. Repair database (handle missing/stale columns from old migrations)
print("\n[1/6] Repairing database schema...")
with connection.cursor() as c:
    # Drop old junction tables (these are truly stale, CoursePackage is gone)
    for t in ['lessons_lessonitem_packages', 'lessons_coursepackage']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{t}'")
        if c.fetchone()[0]:
            c.execute(f"DROP TABLE {t}")
            print(f"      Dropped stale table {t}")

    # Drop stale FK columns (package_id -> replaced by package_choice CharField)
    for table, col in [
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

    # Ensure lesson_type column exists (may have been dropped by a prior failed migration cycle)
    c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lessons_lessonitem' AND column_name='lesson_type'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE lessons_lessonitem ADD COLUMN lesson_type VARCHAR(20) DEFAULT 'PRACTICAL' NOT NULL")
        print("      Added missing column lessons_lessonitem.lesson_type")

    # Ensure inquiry converted column exists
    c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='admissions_walkininquiry' AND column_name='converted'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE admissions_walkininquiry ADD COLUMN converted TINYINT(1) DEFAULT 0 NOT NULL")
        print("      Added missing column admissions_walkininquiry.converted")

    # Ensure attended columns exist
    for table in ['lessons_practicallesson', 'lessons_theorylesson']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='attended'")
        if not c.fetchone()[0]:
            c.execute(f"ALTER TABLE {table} ADD COLUMN attended TINYINT(1) DEFAULT 0 NOT NULL")
            print(f"      Added missing column {table}.attended")

    # Ensure payment_reminder column exists
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='students_student' AND column_name='payment_reminder'")
    col_exists = c.fetchone()[0]
    if not col_exists:
        c.execute("ALTER TABLE students_student ADD COLUMN payment_reminder TINYINT(1) DEFAULT 0 NOT NULL")
        print("      Added missing column students_student.payment_reminder")
    else:
        # Fake the payment_reminder migration if column already exists (avoids duplicate error)
        c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='students' AND name='0003_student_payment_reminder'")
        if not c.fetchone()[0]:
            c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('students', '0003_student_payment_reminder', NOW())")
            print("      Faked migration students.0003_student_payment_reminder")

    # Ensure notification table exists
    c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='student_portal_notification'")
    if not c.fetchone()[0]:
        c.execute("""
            CREATE TABLE student_portal_notification (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                title VARCHAR(300) NOT NULL,
                message LONGTEXT NOT NULL,
                notification_type VARCHAR(20) DEFAULT 'general',
                is_read TINYINT(1) DEFAULT 0,
                created_at DATETIME(6) DEFAULT NOW(),
                CONSTRAINT fk_notification_student FOREIGN KEY (student_id) REFERENCES students_student(id) ON DELETE CASCADE
            )
        """)
        print("      Created student_portal_notification table")

    # Remove duplicate LessonItem records (seed run multiple times)
    c.execute("""
        SELECT t1.id, t2.id FROM lessons_lessonitem t1
        INNER JOIN lessons_lessonitem t2
        ON t1.name = t2.name AND t1.lesson_type = t2.lesson_type AND t1.id > t2.id
    """)
    dups = c.fetchall()
    if dups:
        for dup_id, keep_id in dups:
            c.execute("UPDATE lessons_practicallesson SET lesson_item_id = %s WHERE lesson_item_id = %s", [keep_id, dup_id])
            c.execute("UPDATE lessons_theorylesson SET lesson_item_id = %s WHERE lesson_item_id = %s", [keep_id, dup_id])
            c.execute("DELETE FROM lessons_lessonitem WHERE id = %s", [dup_id])
        print(f"      Removed {len(dups)} duplicate LessonItem record(s)")

    # Ensure lesson_item_id column exists
    c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lessons_theorylesson' AND column_name='lesson_item_id'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE lessons_theorylesson ADD COLUMN lesson_item_id INT NULL REFERENCES lessons_lessonitem(id)")
        print("      Added missing column lessons_theorylesson.lesson_item_id")

print("      Database repair done")

# 3. Migrations
print("\n[2/6] Running migrations...")
try:
    call_command('makemigrations', interactive=False, verbosity=1)
except Exception:
    call_command('makemigrations', '--merge', interactive=False, verbosity=1)
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

# 7. Seed course data
print("\n[6/6] Updating course pricing & categories...")
seed_script = os.path.join(project_dir, 'seed.py')
if os.path.isfile(seed_script):
    import subprocess as sp
    sp.run([sys.executable, seed_script], cwd=project_dir)
    print("      Done!")
else:
    print("      seed.py not found")

# 8. Setup Simon Mureithi as instructor
print("\n[7/6] Setting up Simon Mureithi as instructor...")
try:
    from instructors.models import Instructor
    from accounts.models import User

    if Instructor.objects.filter(user__first_name='Simon', user__last_name='Mureithi').exists():
        print("      Simon Mureithi already exists")
    else:
        Instructor.objects.all().delete()
        print("      Cleared all existing instructors")

        simon_user, created = User.objects.get_or_create(
            username='simon@greenlight.com',
            defaults={
                'email': 'simon@greenlight.com',
                'first_name': 'Simon',
                'last_name': 'Mureithi',
                'role': 'INSTRUCTOR',
            }
        )
        if created:
            simon_user.set_password('simon123')
            simon_user.save()
            print(f"      Created user: simon@greenlight.com / simon123")

        Instructor.objects.update_or_create(
            user=simon_user,
            defaults={
                'license_number': 'INS-SM001',
                'license_class': 'ALL',
                'experience_years': 10,
                'phone': '+254 700 000 000',
                'is_active': True,
            }
        )
        print("      Simon Mureithi set as instructor")
except Exception as e:
    print(f"      Error: {e}")

# 9. Seed study materials
print("\n[7/6] Seeding study materials...")
material_script = os.path.join(project_dir, 'seed_materials.py')
if os.path.isfile(material_script):
    import subprocess as sp
    sp.run([sys.executable, material_script], cwd=project_dir)
    print("      Done!")
else:
    print("      seed_materials.py not found")

print("\n" + "=" * 50)
print("  UPDATE COMPLETE!")
print("=" * 50)
print("  Visit: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("=" * 50)
