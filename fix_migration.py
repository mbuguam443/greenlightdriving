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

    # Drop old FK constraints then columns
    for table, col in [('students_student', 'package_id'), ('admissions_admission', 'package_id')]:
        c.execute(f"""
            SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'
        """)
        row = c.fetchone()
        if row:
            fk = row[0]
            c.execute(f"ALTER TABLE {table} DROP FOREIGN KEY {fk}")
            print(f"  Dropped FK constraint {fk} on {table}")
        c.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{col}'")
        if c.fetchone()[0]:
            c.execute(f"ALTER TABLE {table} DROP COLUMN {col}")
            print(f"  Dropped old {table}.{col} column")

    c.execute("SET FOREIGN_KEY_CHECKS = 1")

print("\nMigration history fixed. Now run: python update.py")
