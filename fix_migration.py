#!/usr/bin/env python3
"""
Fix inconsistent migration history caused by renamed/regenerated migration files.
Run this once, then run update.py normally.
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()
from django.db import connection

print("Fixing migration history...")

with connection.cursor() as c:
    c.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Remove inconsistent migration records
    c.execute("DELETE FROM django_migrations WHERE app IN ('lessons','admissions','students') AND name LIKE '0002_%'")
    print("  Cleared inconsistent migration records.")

    # Drop old tables (order matters: drop junction table first)
    tables = ['lessons_lessonitem_packages', 'lessons_coursepackage']
    for t in tables:
        c.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{t}'")
        if c.fetchone()[0]:
            c.execute(f"DROP TABLE IF EXISTS {t}")
            print(f"  Dropped old table: {t}")

    # Drop old columns that reference the old model
    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='students_student' AND column_name='package_id'")
    if c.fetchone()[0]:
        c.execute("ALTER TABLE students_student DROP COLUMN package_id")
        print("  Dropped old students_student.package_id column")

    c.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='admissions_admission' AND column_name='package_id'")
    if c.fetchone()[0]:
        c.execute("ALTER TABLE admissions_admission DROP COLUMN package_id")
        print("  Dropped old admissions_admission.package_id column")

    c.execute("SET FOREIGN_KEY_CHECKS = 1")

print("\nMigration history fixed. Now run: python update.py")
