#!/usr/bin/env python3
"""
Fresh Start - Fixes all migration issues and rebuilds the database.
Run once: python fresh_start.py
It will fix migrations, then run update.py and seed.py automatically.
"""
import os, sys, subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()
from django.db import connection

print("=" * 50)
print("  Green Light - Fresh Start")
print("=" * 50)

with connection.cursor() as c:
    c.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 1. Clear inconsistent migration records
    c.execute("DELETE FROM django_migrations WHERE app IN ('lessons','admissions','students') AND name LIKE '0002_%'")
    print("[1/6] Cleared old migration records")

    # 2. Drop FK constraints on package_id columns
    for table, col in [('students_student', 'package_id'), ('admissions_admission', 'package_id')]:
        c.execute(f"""
            SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'
        """)
        row = c.fetchone()
        if row:
            c.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {row[0]}")
            print(f"      Dropped FK on {table}.{col}")

    # 3. Drop old columns
    for table, col in [('students_student', 'package_id'), ('admissions_admission', 'package_id')]:
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'")
        if c.fetchone()[0]:
            c.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
            print(f"      Dropped {table}.{col}")

    # 4. Drop old junction table first, then coursepackage
    for t in ['lessons_lessonitem_packages', 'lessons_coursepackage']:
        c.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{t}'")
        if c.fetchone()[0]:
            c.execute(f"DROP TABLE IF EXISTS {t}")
            print(f"      Dropped table {t}")

    c.execute("SET FOREIGN_KEY_CHECKS = 1")

print("[2/6] Running migrations...")
result = subprocess.run([sys.executable, 'update.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("ERROR during update.py:")
    print(result.stderr)
    sys.exit(1)

print("[3/6] Seeding data...")
result = subprocess.run([sys.executable, 'seed.py'], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("ERROR during seed.py:")
    print(result.stderr)
    sys.exit(1)

print("[4/6] Checking collectstatic...")
from django.core.management import call_command
call_command('collectstatic', '--noinput', verbosity=0)
print("      Done!")

print("\n" + "=" * 50)
print("  FRESH START COMPLETE!")
print("  Site should be working now.")
print("=" * 50)
