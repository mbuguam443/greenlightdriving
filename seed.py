#!/usr/bin/env python3
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date

User = get_user_model()

print("=" * 50)
print("  Green Light Driving School - Seeding Data")
print("=" * 50)

# 1. Branches
print("\n[1/7] Branches...")
from core.models import Branch
branches_data = [
    {'name': 'Kimbo', 'slug': 'kimbo', 'address': 'Kimbo Town, Ruiru Road', 'town': 'Kimbo', 'phone': '+254 700 000 001', 'latitude': -1.1736, 'longitude': 36.834},
    {'name': 'Ruiru', 'slug': 'ruiru', 'address': 'Ruiru Town, Kiambu County', 'town': 'Ruiru', 'phone': '+254 700 000 002', 'latitude': -1.1466, 'longitude': 36.9614},
    {'name': 'Waithaka', 'slug': 'waithaka', 'address': 'Waithaka Road, Nairobi', 'town': 'Nairobi', 'phone': '+254 700 000 003', 'latitude': -1.2921, 'longitude': 36.744},
]
for b in branches_data:
    Branch.objects.get_or_create(slug=b['slug'], defaults=b)
print(f"      {Branch.objects.count()} branches ready")

# 2. Course Categories & Courses
print("\n[2/7] Courses...")
from website.models import CourseCategory, Course, FAQ

# Only add/update — NEVER delete existing data
categories_data = [
    {'name': 'A1', 'slug': 'a1', 'description': 'Motorcycle (A1)', 'order': 1},
    {'name': 'A2', 'slug': 'a2', 'description': 'Motorcycle (A2)', 'order': 2},
    {'name': 'A3', 'slug': 'a3', 'description': 'Tuk-tuk / Three-wheeler', 'order': 3},
    {'name': 'B1', 'slug': 'b1', 'description': 'Saloon Car (B1)', 'order': 4},
    {'name': 'B2', 'slug': 'b2', 'description': 'Light Vehicle (B2)', 'order': 5},
    {'name': 'C1', 'slug': 'c1', 'description': 'Light Truck (C1)', 'order': 6},
    {'name': 'C2', 'slug': 'c2', 'description': 'Medium Truck (C2)', 'order': 7},
    {'name': 'D', 'slug': 'd', 'description': 'Minibus / Bus (D1 & D2)', 'order': 8},
    {'name': 'CE', 'slug': 'ce', 'description': 'Trailer Truck (CE)', 'order': 9},
    {'name': 'Combined', 'slug': 'combined', 'description': 'Combined B Light / C1', 'order': 10},
]
for c in categories_data:
    CourseCategory.objects.update_or_create(slug=c['slug'], defaults=c)
print(f"      {CourseCategory.objects.count()} categories ready")

courses_data = [
    # A-category
    {'cat_slug': 'a1', 'name': 'A1 – Motorcycle', 'slug': 'a1-motorcycle', 'description': 'Motorcycle riding course for beginners. Learn balance, control, traffic navigation, and safety gear usage.', 'short_description': '18 years & above', 'duration': 'Training Period', 'full_course_price': 8500, 'half_course_price': 7000, 'test_only_price': 5000, 'features': 'Balance and control\nTraffic navigation\nSafety gear usage\nNTSA test prep'},
    {'cat_slug': 'a2', 'name': 'A2 – Motorcycle Advanced', 'slug': 'a2-motorcycle', 'description': 'Advanced motorcycle riding for experienced riders.', 'short_description': '18 years & above', 'duration': 'Training Period', 'full_course_price': 8500, 'half_course_price': 7000, 'test_only_price': 5000, 'features': 'Advanced control\nHighway riding\nDefensive techniques\nNTSA test prep'},
    {'cat_slug': 'a3', 'name': 'A3 – Tuk-tuk', 'slug': 'a3-tuktuk', 'description': 'Three-wheeler (Tuk-tuk) driving course.', 'short_description': '18 years & above', 'duration': 'Training Period', 'full_course_price': 8500, 'half_course_price': 7000, 'test_only_price': 5000, 'features': 'Vehicle handling\nPassenger safety\nTraffic navigation\nNTSA test prep'},
    # B-category
    {'cat_slug': 'b1', 'name': 'B1 – Saloon Car', 'slug': 'b1-saloon', 'description': 'Comprehensive saloon car driving course for beginners covering all road rules and practical skills.', 'short_description': '18 years & above', 'duration': 'Training Period', 'full_course_price': 12800, 'half_course_price': 9500, 'test_only_price': 6500, 'features': 'Road rules theory\nPractical driving\nModel town board\nDefensive driving\nHighway driving\nNTSA test prep'},
    {'cat_slug': 'b2', 'name': 'B2 – Light Vehicle', 'slug': 'b2-light', 'description': 'Light vehicle driving including SUVs and vans.', 'short_description': '18 years & above', 'duration': 'Training Period', 'full_course_price': 12800, 'half_course_price': 8500, 'test_only_price': 6500, 'features': 'Vehicle handling\nParking maneuvers\nCity & highway driving\nNTSA test prep'},
    # Combined
    {'cat_slug': 'combined', 'name': 'Combined B Light / C1', 'slug': 'combined-b-c1', 'description': 'Combined course covering both B Light (saloon/SUV) and C1 (light truck) categories.', 'short_description': 'Dual category training', 'duration': 'Training Period', 'full_course_price': 15800, 'half_course_price': 10000, 'test_only_price': 9000, 'features': 'B Light training\nC1 Light truck training\nDual exam preparation'},
    # C-category
    {'cat_slug': 'c1', 'name': 'C1 – Light Truck', 'slug': 'c1-light-truck', 'description': 'Light commercial truck driving course.', 'short_description': '22 years & above', 'duration': 'Training Period', 'full_course_price': 12500, 'half_course_price': 9000, 'test_only_price': 7000, 'features': 'Commercial regulations\nLoad management\nRoute planning\nNTSA test prep'},
    {'cat_slug': 'c2', 'name': 'C2 – Medium Truck', 'slug': 'c2-medium-truck', 'description': 'Medium commercial truck driving course.', 'short_description': '24 years & above', 'duration': 'Training Period', 'full_course_price': 13000, 'half_course_price': 9000, 'test_only_price': 7000, 'features': 'Heavy vehicle handling\nLoad management\nSafety regulations\nNTSA test prep'},
    # D-category (Test Only)
    {'cat_slug': 'd', 'name': 'D1 & D2 – Minibus / Bus', 'slug': 'd-minibus-bus', 'description': 'Minibus and bus driving test preparation. Requires 4 years driving experience.', 'short_description': '4 years driving experience required', 'duration': 'Test Only', 'full_course_price': 0, 'half_course_price': 0, 'test_only_price': 8000, 'features': 'Test preparation only\nNTSA driving test prep\nRequires 4 years driving experience'},
    # CE (Test Only)
    {'cat_slug': 'ce', 'name': 'CE – Trailer Truck', 'slug': 'ce-trailer', 'description': 'Articulated trailer truck driving test preparation.', 'short_description': 'Test Only', 'duration': 'Test Only', 'full_course_price': 0, 'half_course_price': 0, 'test_only_price': 15000, 'features': 'Trailer handling\nArticulated vehicle control\nNTSA test prep'},
]
for c in courses_data:
    cat = CourseCategory.objects.get(slug=c.pop('cat_slug'))
    Course.objects.update_or_create(slug=c['slug'], defaults={**c, 'category': cat})
print(f"      {Course.objects.count()} courses ready")

# 3. Lesson Items (no CoursePackage)
print("\n[3/7] Lesson Items...")
from lessons.models import LessonItem
LessonItem.objects.all().delete()

lessons_data = [
    ('Introduction', 'THEORY', ['test', 'half', 'full']),
    ('Theory Board Lanes', 'THEORY', ['test', 'half', 'full']),
    ('Theory Model Town Board', 'THEORY', ['test', 'half', 'full']),
    ('Identification of Road Signs', 'THEORY', ['test', 'half', 'full']),
    ('Starting the Car Drill', 'PRACTICAL', ['half', 'full']),
    ('Gear Changing Up and Down', 'PRACTICAL', ['half', 'full']),
    ('Road Positioning', 'PRACTICAL', ['half', 'full']),
    ('Turning Left', 'PRACTICAL', ['half', 'full']),
    ('Turning Right Procedure', 'PRACTICAL', ['half', 'full']),
    ('Hand Signal', 'PRACTICAL', ['half', 'full']),
    ('Clutch Control', 'PRACTICAL', ['full']),
    ('Three Point Turn', 'PRACTICAL', ['full']),
    ('Steering Control', 'PRACTICAL', ['full']),
    ('Reversing', 'PRACTICAL', ['full']),
    ('Hill Start', 'PRACTICAL', ['full']),
    ('Angle Parking', 'PRACTICAL', ['full']),
    ('Flash Parking', 'PRACTICAL', ['full']),
    ('Basic Mechanical', 'THEORY', ['test', 'half', 'full']),
    ('First Aid on Road', 'THEORY', ['test', 'half', 'full']),
    ('Assessment', 'ASSESSMENT', ['half', 'full']),
]
for i, (name, ltype, pkgs) in enumerate(lessons_data):
    LessonItem.objects.create(name=name, order=i + 1, lesson_type=ltype)
print(f"      {LessonItem.objects.count()} lesson items ready")

# 4. FAQs
print("\n[4/7] FAQs...")
faqs_data = [
    {'q': 'How long does it take to get a driving license?', 'a': 'The process typically takes 4-8 weeks depending on the course type and NTSA scheduling.', 'cat': 'general'},
    {'q': 'What documents do I need for admission?', 'a': 'You need a valid National ID or Passport, passport-sized photos, and a medical certificate.', 'cat': 'admission'},
    {'q': 'What payment methods do you accept?', 'a': 'We accept M-Pesa, cash, bank transfer, and cheque payments.', 'cat': 'payments'},
    {'q': 'Do you offer weekend classes?', 'a': 'Yes, we have Saturday classes available at all branches.', 'cat': 'courses'},
    {'q': 'How many lessons do I need?', 'a': 'Most students need 20-30 practical lessons. This varies based on your learning pace.', 'cat': 'courses'},
    {'q': 'What is the pass rate for NTSA tests?', 'a': 'Our pass rate is over 85%, thanks to our experienced instructors and comprehensive curriculum.', 'cat': 'exams'},
]
for i, f in enumerate(faqs_data):
    FAQ.objects.get_or_create(question=f['q'], defaults={'answer': f['a'], 'category': f['cat'], 'order': i + 1})
print(f"      {FAQ.objects.count()} FAQs ready")

# 5. Events
print("\n[5/7] Events...")
from student_portal.models import Event
today = timezone.now().date()
events_data = [
    {'title': 'NTSA Driving Test - Kimbo', 'category': 'ntsa_test', 'date': today + timedelta(days=14), 'location': 'Kimbo Branch', 'important': True},
    {'title': 'NTSA Theory Exam - Ruiru', 'category': 'ntsa_exam', 'date': today + timedelta(days=21), 'location': 'Ruiru Branch', 'important': True},
    {'title': 'New Student Orientation', 'category': 'orientation', 'date': today + timedelta(days=7), 'location': 'All Branches'},
    {'title': 'Road Safety Workshop', 'category': 'workshop', 'date': today + timedelta(days=30), 'location': 'Waithaka Branch'},
    {'title': 'School Holiday Closure', 'category': 'holiday', 'date': today + timedelta(days=45), 'end_date': today + timedelta(days=48), 'location': 'All Branches'},
    {'title': 'NTSA Driving Test - Waithaka', 'category': 'ntsa_test', 'date': today + timedelta(days=35), 'location': 'Waithaka Branch', 'important': True},
]
for e in events_data:
    d = e.pop('date')
    ed = e.pop('end_date', None)
    imp = e.pop('important', False)
    Event.objects.get_or_create(title=e['title'], defaults={**e, 'event_date': d, 'end_date': ed, 'is_important': imp})
print(f"      {Event.objects.count()} events ready")

# 6. Users: Students & Instructors
print("\n[6/7] Users...")
students_info = [
    {'username': 'james.mwangi@student.com', 'first_name': 'James', 'last_name': 'Mwangi'},
    {'username': 'sarah.omondi@student.com', 'first_name': 'Sarah', 'last_name': 'Omondi'},
    {'username': 'peter.kamau@student.com', 'first_name': 'Peter', 'last_name': 'Kamau'},
]
for s in students_info:
    if not User.objects.filter(username=s['username']).exists():
        u = User(username=s['username'], email=s['username'], first_name=s['first_name'], last_name=s['last_name'], role='STUDENT')
        u.set_password('student1234')
        u.save()
        print(f"      Created student: {s['username']}")

instructors_info = [
    {'username': 'instructor1@greenlight.com', 'first_name': 'David', 'last_name': 'Ochieng'},
    {'username': 'instructor2@greenlight.com', 'first_name': 'Grace', 'last_name': 'Wanjiku'},
    {'username': 'instructor3@greenlight.com', 'first_name': 'Peter', 'last_name': 'Otieno'},
]
for inst in instructors_info:
    if not User.objects.filter(username=inst['username']).exists():
        u = User(username=inst['username'], email=inst['username'], first_name=inst['first_name'], last_name=inst['last_name'], role='INSTRUCTOR')
        u.set_password('instructor123')
        u.save()
        print(f"      Created instructor: {inst['username']}")
print(f"      {User.objects.count()} total users")

# 7. Instructors, Vehicles, Student Profiles
print("\n[7/7] Instructors, vehicles, student profiles...")
from instructors.models import Instructor
from vehicles.models import Vehicle
from students.models import Student

inst_data = [
    {'username': 'instructor1@greenlight.com', 'license': 'INS-001', 'exp': 8, 'spec': 'Class B, Commercial'},
    {'username': 'instructor2@greenlight.com', 'license': 'INS-002', 'exp': 5, 'spec': 'Class B, Class A'},
    {'username': 'instructor3@greenlight.com', 'license': 'INS-003', 'exp': 12, 'spec': 'Commercial, PSV'},
]
instructors = []
for inst in inst_data:
    user = User.objects.get(username=inst['username'])
    instructor, _ = Instructor.objects.get_or_create(
        user=user, defaults={'license_number': inst['license'], 'experience_years': inst['exp'], 'specialization': inst['spec']}
    )
    instructors.append(instructor)
print(f"      {Instructor.objects.count()} instructors ready")

vehicles_info = [
    {'reg': 'KDG 100A', 'cat': 'B1', 'make': 'Toyota', 'model': 'Vitz', 'year': 2020, 'color': 'White'},
    {'reg': 'KDH 200B', 'cat': 'B1', 'make': 'Toyota', 'model': 'Corolla', 'year': 2021, 'color': 'Silver'},
    {'reg': 'KDJ 300C', 'cat': 'B2', 'make': 'Nissan', 'model': 'X-Trail', 'year': 2022, 'color': 'Black'},
    {'reg': 'KDK 400D', 'cat': 'C1', 'make': 'Isuzu', 'model': 'NQR', 'year': 2019, 'color': 'White'},
    {'reg': 'KDE 500E', 'cat': 'A1', 'make': 'Honda', 'model': 'CB125', 'year': 2023, 'color': 'Red'},
]
vehicles = []
for v in vehicles_info:
    vehicle, _ = Vehicle.objects.get_or_create(
        registration_number=v['reg'],
        defaults={'category': v['cat'], 'make': v['make'], 'model_name': v['model'], 'year': v['year'], 'color': v['color'], 'insurance_expiry': date(2027, 12, 31), 'service_due': date(2026, 12, 31)}
    )
    vehicles.append(vehicle)
print(f"      {Vehicle.objects.count()} vehicles ready")

cat_b1 = CourseCategory.objects.get(slug='b1')
course_saloon = Course.objects.filter(category=cat_b1).first()
branch_kimbo = Branch.objects.get(slug='kimbo')

for su in User.objects.filter(role='STUDENT'):
    Student.objects.get_or_create(
        user=su,
        defaults={'student_number': f'GLS-{su.id:04d}', 'category': cat_b1, 'course': course_saloon, 'package_choice': 'FULL', 'branch': branch_kimbo, 'instructor': instructors[0], 'vehicle': vehicles[0], 'status': 'ACTIVE', 'expected_graduation': timezone.now().date() + timedelta(days=90)}
    )
print(f"      {Student.objects.count()} student profiles ready")

print("\n" + "=" * 50)
print("  SEED COMPLETE!")
print("=" * 50)
print("  Students: james.mwangi@student.com / student1234")
print("            sarah.omondi@student.com / student1234")
print("            peter.kamau@student.com  / student1234")
print("  Instructors: instructor1@greenlight.com / instructor123")
print("=" * 50)
