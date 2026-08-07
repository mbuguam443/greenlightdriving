#!/usr/bin/env python3
"""
Purge test/dummy data. Keeps all real production data.
Deletes ONLY records created by seed — identified by email domain patterns.
"""
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# --- SEED STUDENTS ---
print("Cleaning seed students...")
dummy_students = User.objects.filter(role='STUDENT', email__endswith='@student.com')
count = dummy_students.count()
dummy_students.delete()
print(f"   {count} seed student(s) removed")

# --- SEED INSTRUCTORS (keep Simon Mureithi) ---
print("Cleaning seed instructors...")
dummy_inst = User.objects.filter(role='INSTRUCTOR', email__endswith='@greenlight.com').exclude(email='simon@greenlight.com')
c2 = dummy_inst.count()
dummy_inst.delete()
print(f"   {c2} seed instructor(s) removed")

# --- DUMMY VEHICLES (from seed) ---
from vehicles.models import Vehicle
print("Cleaning seed vehicles...")
seed_regs = ['KDG 100A', 'KDH 200B', 'KDJ 300C', 'KDK 400D', 'KDE 500E']
c3 = Vehicle.objects.filter(registration_number__in=seed_regs).delete()[0]
print(f"   {c3} seed vehicle(s) removed")

print("\nPurge complete. Your real data is untouched.")
