#!/usr/bin/env python3
"""
Restore a database backup created by the Backup Database button.
1. Upload your backup JSON file to the project folder
2. Rename it to backup.json (or change the filename in this script)
3. Run this script via cPanel Python App
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

BACKUP_FILE = 'backup.json'  # change this to your file name

import django
django.setup()
from django.core.management import call_command

print("=" * 50)
print("  Green Light Driving School - Restore Backup")
print("=" * 50)

filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), BACKUP_FILE)

if not os.path.isfile(filepath):
    print(f"\n  ERROR: {BACKUP_FILE} not found!")
    print(f"  Upload your backup file and rename it to {BACKUP_FILE}")
    print(f"  Or edit this script and change BACKUP_FILE")
    sys.exit(1)

print(f"\n  Restoring from: {BACKUP_FILE}")
call_command('loaddata', filepath, verbosity=1)
print("\n  RESTORE COMPLETE!")
print("=" * 50)
