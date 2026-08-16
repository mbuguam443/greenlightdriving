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

# 0. Sync code from GitHub
print("\n[0/6] Syncing code from GitHub...")
git_dir = os.path.join(project_dir, '.git')

ZIP_URL = 'https://codeload.github.com/mbuguam443/greenlightdriving/zip/refs/heads/main'


def sync_from_zip(project_dir):
    """Download the latest code as a ZIP and replace the working tree.
    Returns True if anything changed. Works even when git is broken/missing.
    Server data (media/, staticfiles/, .env, db.sqlite3, email_config.py,
    settings_local.py, .git, node_modules, sent_emails/) is never touched."""
    import io
    import zipfile
    import urllib.request

    keep_top = {'.git', 'media', 'staticfiles', 'node_modules', 'sent_emails', '__pycache__'}
    keep_files = {'.env', 'db.sqlite3', 'email_config.py', 'settings_local.py'}

    print("      Downloading latest code from GitHub (ZIP)...")
    req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'greenlight-updater'})
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = resp.read()
    zf = zipfile.ZipFile(io.BytesIO(data))
    root = zf.namelist()[0].split('/')[0]

    changed = False
    zip_files = set()
    for n in zf.namelist():
        rel = n[len(root) + 1:] if n.startswith(root + '/') else n
        rel = rel.replace('\\', '/')
        if not rel or rel.endswith('/'):
            continue
        if rel.split('/')[0] in keep_top:
            continue
        if os.path.basename(rel) in keep_files:
            continue
        zip_files.add(rel)
        dst = os.path.join(project_dir, rel)
        if os.path.isdir(dst):
            continue
        os.makedirs(os.path.dirname(dst) or project_dir, exist_ok=True)
        new_bytes = zf.read(n)
        if not os.path.exists(dst) or open(dst, 'rb').read() != new_bytes:
            with open(dst, 'wb') as f:
                f.write(new_bytes)
            changed = True

    # Remove stale files that no longer exist in the new ZIP (kept files stay)
    for walk_root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in keep_top]
        rel_dir = os.path.relpath(walk_root, project_dir).replace('\\', '/')
        for fn in files:
            rel = (rel_dir + '/' + fn) if rel_dir != '.' else fn
            if rel in zip_files:
                continue
            if os.path.basename(rel) in keep_files:
                continue
            if rel.split('/')[0] in keep_top:
                continue
            try:
                os.remove(os.path.join(walk_root, fn))
                changed = True
            except OSError:
                pass
    return changed


def git_rev_parse(project_dir):
    try:
        r = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, cwd=project_dir
        )
        return r.stdout.strip() or None
    except Exception:
        return None


def git_update(project_dir):
    """Fast path using git. Returns True if code was updated (re-exec'd)."""
    before = git_rev_parse(project_dir)
    fetch = subprocess.run(
        ['git', 'fetch', 'origin', 'main'],
        capture_output=True, text=True, timeout=60, cwd=project_dir
    )
    if fetch.returncode != 0:
        print(f"      Git fetch failed: {fetch.stderr.strip()}")
        return False
    reset = subprocess.run(
        ['git', 'reset', '--hard', 'origin/main'],
        capture_output=True, text=True, timeout=60, cwd=project_dir
    )
    if reset.returncode != 0:
        print(f"      Git reset failed: {reset.stderr.strip()}")
        return False
    subprocess.run(['git', 'clean', '-fd'], capture_output=True, text=True, timeout=60, cwd=project_dir)
    after = git_rev_parse(project_dir)
    if before != after:
        print(f"      Code updated ({before[:7] or '?'} -> {after[:7] or '?'}). Re-running with new version...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    print("      Already up to date.")
    return True


git_available = False
try:
    subprocess.run(['git', '--version'], capture_output=True, check=True)
    git_available = True
except Exception:
    pass

git_ok = False
if git_available and os.path.isdir(git_dir):
    git_ok = git_update(project_dir)

if not git_ok:
    print("      Using ZIP download instead of git...")
    try:
        if sync_from_zip(project_dir):
            print("      Code updated from ZIP. Re-running with new version...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print("      Already up to date.")
    except Exception as e:
        print(f"      ZIP download failed: {e}")
        print("      Continuing with existing code...")

# 1. Ensure Python dependencies are installed
print("\n[0/6] Checking Python dependencies...")
missing = []
for mod in ('rest_framework', 'rest_framework_simplejwt', 'corsheaders',
            'django_filters', 'PIL', 'reportlab', 'pymysql', 'requests'):
    try:
        __import__(mod)
    except Exception:
        missing.append(mod)
if missing:
    print(f"      Missing packages: {', '.join(missing)}. Installing requirements.txt...")
    req_file = os.path.join(project_dir, 'requirements.txt')
    if not os.path.isfile(req_file):
        print("      requirements.txt not found - skipping")
    else:
        r = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '-r', req_file],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f"      pip install failed: {r.stderr.strip()[-500:]}")
        else:
            print("      Dependencies installed")
else:
    print("      All dependencies present")

# 2. Setup Django
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

    # Ensure submitted_by_student column
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lessons_practicallesson' AND column_name='submitted_by_student'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE lessons_practicallesson ADD COLUMN submitted_by_student TINYINT(1) DEFAULT 0 NOT NULL")
        print("      Added missing column lessons_practicallesson.submitted_by_student")

    # Ensure is_approved column
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='lessons_practicallesson' AND column_name='is_approved'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE lessons_practicallesson ADD COLUMN is_approved TINYINT(1) DEFAULT 0 NOT NULL")
        print("      Added missing column lessons_practicallesson.is_approved")

    # Convert theory lessons that should now be practical (after lesson type update)
    c.execute("""
        SELECT tl.id, tl.student_id, tl.lesson_item_id, tl.instructor_id, tl.date, tl.time_start, tl.time_end, tl.status, tl.notes, tl.attended
        FROM lessons_theorylesson tl
        INNER JOIN lessons_lessonitem li ON tl.lesson_item_id = li.id
        WHERE li.lesson_type = 'PRACTICAL'
    """)
    bad_theory = c.fetchall()
    if bad_theory:
        for row in bad_theory:
            c.execute("""
                INSERT IGNORE INTO lessons_practicallesson (student_id, lesson_item_id, instructor_id, vehicle_id, date, status, remarks, attended, submitted_by_student, is_approved, created_at, completed_at)
                VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, 0, 0, NOW(), NULL)
            """, [row[1], row[2], row[3], row[4], row[7], row[8] or '', int(row[9] or 0)])
            c.execute("DELETE FROM lessons_theorylesson WHERE id = %s", [row[0]])
        print(f"      Converted {len(bad_theory)} theory lessons to practical (type mismatch)")

    # Fake lessons migration if columns exist
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='lessons' AND name='0006_practicallesson_is_approved_and_more'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('lessons', '0006_practicallesson_is_approved_and_more', NOW())")
        print("      Faked migration lessons.0006_practicallesson_is_approved_and_more")

    # Ensure OTP columns exist
    c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='core_dailylog'")
    if not c.fetchone()[0]:
        c.execute("""
            CREATE TABLE core_dailylog (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(300) NOT NULL,
                description LONGTEXT,
                log_date DATE NOT NULL,
                created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6)
            )
        """)
        print("      Created core_dailylog table")
    else:
        # Drop FK column if it exists (simplified model)
        c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='core_dailylog' AND column_name='recorded_by_id'")
        if c.fetchone()[0]:
            c.execute("ALTER TABLE core_dailylog DROP FOREIGN KEY fk_dailylog_user")
            c.execute("ALTER TABLE core_dailylog DROP COLUMN recorded_by_id")
            print("      Dropped recorded_by_id from core_dailylog")
        # Ensure created_by_id column
        c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='core_dailylog' AND column_name='created_by_id'")
        if not c.fetchone()[0]:
            c.execute("ALTER TABLE core_dailylog ADD COLUMN created_by_id BIGINT NULL, ADD CONSTRAINT fk_dailylog_user FOREIGN KEY (created_by_id) REFERENCES accounts_user(id) ON DELETE SET NULL")
            print("      Added created_by_id column to core_dailylog")
        else:
            # Fake migration
            c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core' AND name='0004_dailylog_created_by'")
            if not c.fetchone()[0]:
                c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('core', '0004_dailylog_created_by', NOW())")
                print("      Faked migration core.0004_dailylog_created_by")

    # Ensure exam_fee column exists
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='core_sitesettings' AND column_name='exam_fee'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE core_sitesettings ADD COLUMN exam_fee DECIMAL(10,2) DEFAULT 3100 NOT NULL")
        print("      Added exam_fee column to core_sitesettings")

    # Fake exam_fee migration
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core' AND name='0003_sitesettings_exam_fee'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('core', '0003_sitesettings_exam_fee', NOW())")
        print("      Faked migration core.0003_sitesettings_exam_fee")

    # Fake the daily log migration if table exists
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='core' AND name='0002_dailylog'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('core', '0002_dailylog', NOW())")
        print("      Faked migration core.0002_dailylog")

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

    # Ensure discount columns exist
    for col in ('discount', 'discount_reason'):
        c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='students_student' AND column_name=%s", (col,))
        if not c.fetchone()[0]:
            col_type = "DECIMAL(10,2) DEFAULT 0" if col == 'discount' else "VARCHAR(200) DEFAULT ''"
            c.execute(f"ALTER TABLE students_student ADD COLUMN {col} {col_type} NOT NULL")
            print(f"      Added missing column students_student.{col}")
    # Fake the discount migration if columns already exist (avoids duplicate error)
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='students' AND name='0004_student_discount_student_discount_reason_and_more'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('students', '0004_student_discount_student_discount_reason_and_more', NOW())")
        print("      Faked migration students.0004_student_discount_student_discount_reason_and_more")

    # Ensure discount_description column exists
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='students_student' AND column_name='discount_description'")
    if not c.fetchone()[0]:
        c.execute("ALTER TABLE students_student ADD COLUMN discount_description LONGTEXT NOT NULL")
        print("      Added missing column students_student.discount_description")
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='students' AND name='0005_student_discount_description'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('students', '0005_student_discount_description', NOW())")
        print("      Faked migration students.0005_student_discount_description")

    # Ensure notification table exists
    c.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='student_portal_notification'")
    if not c.fetchone()[0]:
        c.execute("""
            CREATE TABLE student_portal_notification (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                student_id BIGINT NOT NULL,
                title VARCHAR(300) NOT NULL,
                message LONGTEXT NOT NULL,
                notification_type VARCHAR(20) DEFAULT 'general',
                is_read TINYINT(1) DEFAULT 0,
                created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6),
                CONSTRAINT fk_notification_student FOREIGN KEY (student_id) REFERENCES students_student(id) ON DELETE CASCADE
            )
        """)
        print("      Created student_portal_notification table")

    # Fake the notification migration if table exists but migration isn't recorded
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='student_portal' AND name='0005_notification'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('student_portal', '0005_notification', NOW())")
        print("      Faked migration student_portal.0005_notification")

    # Ensure reply columns exist
    for col in ['reply', 'replied_at']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='student_portal_notification' AND column_name='{col}'")
        if not c.fetchone()[0]:
            c.execute(f"ALTER TABLE student_portal_notification ADD COLUMN {col} {'LONGTEXT' if col == 'reply' else 'DATETIME(6) NULL'}")
            print(f"      Added {col} to student_portal_notification")

    # Fake reply migration
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='student_portal' AND name='0006_notification_replied_at_notification_reply'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('student_portal', '0006_notification_replied_at_notification_reply', NOW())")
        print("      Faked migration student_portal.0006_notification_reply")

    # Ensure OTP columns exist
    for col in ['otp', 'is_verified']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='accounts_user' AND column_name='{col}'")
        if not c.fetchone()[0]:
            c.execute(f"ALTER TABLE accounts_user ADD COLUMN {col} {'VARCHAR(6)' if col == 'otp' else 'TINYINT(1) DEFAULT 0'} NOT NULL")
            print(f"      Added {col} to accounts_user")

    # Fake OTP migration
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='accounts' AND name='0002_user_is_verified_user_otp'")
    if not c.fetchone()[0]:
        c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('accounts', '0002_user_is_verified_user_otp', NOW())")
        print("      Faked migration accounts.0002_user_is_verified_user_otp")

    # Ensure sent_emails directory exists for file-based email
    sent_emails_dir = os.path.join(project_dir, 'sent_emails')
    if not os.path.isdir(sent_emails_dir):
        os.makedirs(sent_emails_dir, exist_ok=True)
        print("      Created sent_emails/ directory")

    # The course price migration may have been applied directly by an older
    # repair script. Fake it when the final columns already exist, otherwise
    # Django will try to drop the missing legacy price column.
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='website_course' AND column_name='price'")
    has_legacy_price = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='website_course' AND column_name IN ('full_course_price', 'half_course_price', 'test_only_price')")
    final_price_columns = c.fetchone()[0] == 3
    if not has_legacy_price and final_price_columns:
        c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='website' AND name='0003_remove_course_price_course_full_course_price_and_more'")
        if not c.fetchone()[0]:
            c.execute("INSERT INTO django_migrations (app, name, applied) VALUES ('website', '0003_remove_course_price_course_full_course_price_and_more', NOW())")
            print("      Faked website price migration (schema already repaired)")

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

# Remove locally-generated migration files that are not tracked in the repo.
# (Schema changes on this project are handled by the repair step above, which
#  records the migration names in django_migrations directly. Running
#  makemigrations would regenerate conflicting files, so it is disabled and any
#  leftover generated files must not be re-applied by migrate.)
try:
    tracked = set(subprocess.run(
        ['git', 'ls-files', '*/migrations/*.py'],
        capture_output=True, text=True, cwd=project_dir
    ).stdout.splitlines())
    if tracked:
        for root, dirs, files in os.walk(project_dir):
            root = os.path.normpath(root)
            parts = root.replace('\\', '/').split('/')
            if 'migrations' not in parts:
                continue
            for fn in files:
                if not fn.endswith('.py'):
                    continue
                rel = os.path.relpath(os.path.join(root, fn), project_dir).replace('\\', '/')
                if rel not in tracked and fn != '__init__.py':
                    try:
                        os.remove(os.path.join(root, fn))
                        print(f"      Removed stale migration {rel}")
                    except OSError:
                        pass
except Exception:
    pass

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

# 7. Seed course data (skip in production — run manually if needed)
# seed_script = os.path.join(project_dir, 'seed.py')
# if os.path.isfile(seed_script):
#     import subprocess as sp
#     sp.run([sys.executable, seed_script], cwd=project_dir)
#     print("      Done!")
# else:
#     print("      seed.py not found")

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

# $9. Purge dummy seed data (disabled — production mode)
# print("\n[8/6] Purging dummy data...")
# purge_script = os.path.join(project_dir, 'purge_dummy.py')
# if os.path.isfile(purge_script):
#     import subprocess as sp
#     sp.run([sys.executable, purge_script], cwd=project_dir)
#     print("      Done!")
# else:
#     print("      purge_dummy.py not found")

# 10. Seed study materials
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
