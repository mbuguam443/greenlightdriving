#!/usr/bin/env python3
"""
Green Light Driving School - Auto Deploy Script
Run this from cPanel Python App > Run > deploy.py
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')

import django
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 50)
print("  Green Light Driving School - Deployment")
print("=" * 50)

# 1. Migrations
print("\n[1/6] Running migrations...")
call_command('migrate', '--run-syncdb', verbosity=1)
print("      Done!")

# 2. Collect static
print("\n[2/6] Collecting static files...")
call_command('collectstatic', '--noinput', verbosity=1)
print("      Done!")

# 2b. Symlink staticfiles -> static for Apache serving
import shutil
staticfiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'staticfiles')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
if os.path.isdir(staticfiles_dir):
    # Copy staticfiles content into static/ so Apache serves it from /static/
    for item in os.listdir(staticfiles_dir):
        src = os.path.join(staticfiles_dir, item)
        dst = os.path.join(static_dir, item)
        if os.path.isdir(src):
            if not os.path.exists(dst):
                shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print("      Static files synced to static/")

# 3. Superuser
print("\n[3/6] Creating superuser...")
if not User.objects.filter(username='admin@greenlight.com').exists():
    u = User(username='admin@greenlight.com', email='admin@greenlight.com', first_name='Admin', last_name='User', role='SUPER_ADMIN', is_staff=True, is_superuser=True)
    u.set_password('admin1234')
    u.save()
    print("      Superuser created!")
else:
    print("      Already exists")
print("      Credentials: admin@greenlight.com / admin1234")

# 4. Site settings & Branches
print("\n[4/6] Creating site settings and branches...")
from core.models import SiteSettings, Branch
if not SiteSettings.objects.exists():
    SiteSettings.objects.create(
        site_name='Greenlight Defensive Driving School',
        tagline='Drive Safe, Drive Smart',
        phone_primary='+254 700 000 000',
        phone_secondary='+254 711 000 000',
        email='info@greenlightdriving.co.ke',
        address='Nairobi, Kenya',
        working_hours='Mon-Sat: 7:00 AM - 6:00 PM',
    )
    print("      SiteSettings created")

branches_data = [
    {'name': 'Kimbo', 'slug': 'kimbo', 'address': 'Kimbo Town, Ruiru Road', 'town': 'Kimbo', 'phone': '+254 700 000 001', 'latitude': -1.1736, 'longitude': 36.834},
    {'name': 'Ruiru', 'slug': 'ruiru', 'address': 'Ruiru Town, Kiambu County', 'town': 'Ruiru', 'phone': '+254 700 000 002', 'latitude': -1.1466, 'longitude': 36.9614},
    {'name': 'Waithaka', 'slug': 'waithaka', 'address': 'Waithaka Road, Nairobi', 'town': 'Nairobi', 'phone': '+254 700 000 003', 'latitude': -1.2921, 'longitude': 36.744},
]
for b in branches_data:
    Branch.objects.get_or_create(slug=b['slug'], defaults=b)
print(f"      {Branch.objects.count()} branches ready")

# 5. Course Categories, Courses, Lesson Items, FAQs, Events
print("\n[5/6] Seeding courses, lessons, FAQs, events...")
from website.models import CourseCategory, Course, FAQ
from lessons.models import LessonItem
from student_portal.models import Event

categories_data = [
    {'name': 'A1', 'slug': 'a1', 'description': 'Motorcycle', 'order': 1},
    {'name': 'A2', 'slug': 'a2', 'description': 'Motorcycle Advanced', 'order': 2},
    {'name': 'B1', 'slug': 'b1', 'description': 'Saloon Cars', 'order': 3},
    {'name': 'B2', 'slug': 'b2', 'description': 'SUVs and Vans', 'order': 4},
    {'name': 'C1', 'slug': 'c1', 'description': 'Light Commercial', 'order': 5},
    {'name': 'C2', 'slug': 'c2', 'description': 'Heavy Commercial', 'order': 6},
    {'name': 'D1', 'slug': 'd1', 'description': 'Light PSV', 'order': 7},
    {'name': 'D2', 'slug': 'd2', 'description': 'Heavy PSV', 'order': 8},
    {'name': 'CE', 'slug': 'ce', 'description': 'Articulated Vehicles', 'order': 9},
    {'name': 'F', 'slug': 'f', 'description': 'Special Vehicles', 'order': 10},
    {'name': 'G', 'slug': 'g', 'description': 'Earth Moving Equipment', 'order': 11},
]
for c in categories_data:
    CourseCategory.objects.get_or_create(slug=c['slug'], defaults=c)
print(f"      {CourseCategory.objects.count()} categories ready")

courses_data = [
    {'cat_slug': 'b1', 'name': 'Basic Driving Course', 'slug': 'basic-driving', 'description': 'Comprehensive driving course for beginners covering all road rules and practical skills.', 'short_description': 'Perfect for first-time drivers', 'duration': '4 Weeks', 'price': 25000, 'features': 'Road rules theory\nPractical driving lessons\nDefensive driving\nHighway driving'},
    {'cat_slug': 'b1', 'name': 'Intensive Driving Course', 'slug': 'intensive-driving', 'description': 'Fast-track driving course for those who want to learn quickly.', 'short_description': 'Learn to drive in 2 weeks', 'duration': '2 Weeks', 'price': 35000, 'features': 'Daily driving sessions\nTheory included\nMock NTSA test\nCertificate'},
    {'cat_slug': 'b2', 'name': 'SUV & Van Training', 'slug': 'suv-van-training', 'description': 'Specialized training for larger vehicles.', 'short_description': 'Handle bigger vehicles with confidence', 'duration': '3 Weeks', 'price': 30000, 'features': 'Vehicle handling\nParking maneuvers\nOff-road basics'},
    {'cat_slug': 'a1', 'name': 'Motorcycle Basic', 'slug': 'motorcycle-basic', 'description': 'Basic motorcycle riding course.', 'short_description': 'Get your motorcycle license', 'duration': '2 Weeks', 'price': 15000, 'features': 'Balance and control\nTraffic navigation\nSafety gear usage'},
    {'cat_slug': 'c1', 'name': 'Commercial Driving', 'slug': 'commercial-driving', 'description': 'Commercial vehicle driving for logistics and delivery.', 'short_description': 'Drive for business', 'duration': '6 Weeks', 'price': 45000, 'features': 'Commercial regulations\nLoad management\nRoute planning'},
]
for c in courses_data:
    cat = CourseCategory.objects.get(slug=c.pop('cat_slug'))
    Course.objects.get_or_create(slug=c['slug'], defaults={**c, 'category': cat})
print(f"      {Course.objects.count()} courses ready")

lessons_data = [
    'Vehicle Controls & Cockpit Drill', 'Starting and Stopping', 'Steering Techniques',
    'Gear Changing', 'Roundabouts', 'Junctions & Intersections',
    'Reversing & Parking', 'Emergency Stops', 'Dual Carriageway Driving',
    'Night Driving', 'Defensive Driving', 'Eco-Driving',
    'Hill Starts', 'Overtaking', 'City Driving',
]
for i, name in enumerate(lessons_data):
    LessonItem.objects.get_or_create(name=name, defaults={'order': i + 1})
print(f"      {LessonItem.objects.count()} lesson items ready")

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

from datetime import timedelta
from django.utils import timezone
today = timezone.now().date()

events_data = [
    {'title': 'NTSA Driving Test - Kimbo', 'category': 'ntsa_test', 'date': today + timedelta(days=14), 'location': 'Kimbo Branch'},
    {'title': 'NTSA Theory Exam - Ruiru', 'category': 'ntsa_exam', 'date': today + timedelta(days=21), 'location': 'Ruiru Branch'},
    {'title': 'New Student Orientation', 'category': 'orientation', 'date': today + timedelta(days=7), 'location': 'All Branches'},
    {'title': 'Road Safety Workshop', 'category': 'workshop', 'date': today + timedelta(days=30), 'location': 'Waithaka Branch'},
    {'title': 'School Holiday Closure', 'category': 'holiday', 'date': today + timedelta(days=45), 'end_date': today + timedelta(days=48), 'location': 'All Branches'},
    {'title': 'NTSA Driving Test - Waithaka', 'category': 'ntsa_test', 'date': today + timedelta(days=35), 'location': 'Waithaka Branch'},
]
for e in events_data:
    d = e.pop('date')
    ed = e.pop('end_date', None)
    Event.objects.get_or_create(title=e['title'], defaults={
        **e, 'event_date': d, 'end_date': ed,
        'is_important': e['category'] in ('ntsa_test', 'ntsa_exam'),
    })
print(f"      {Event.objects.count()} events ready")

# 6. Student accounts, instructors, vehicles
print("\n[6/6] Creating student accounts, instructors, vehicles...")
from accounts.models import User as UserModel
from instructors.models import Instructor
from vehicles.models import Vehicle
from students.models import Student
from django.utils import timezone as tz

students_info = [
    {'username': 'james.mwangi@student.com', 'first_name': 'James', 'last_name': 'Mwangi', 'email': 'james.mwangi@student.com'},
    {'username': 'sarah.omondi@student.com', 'first_name': 'Sarah', 'last_name': 'Omondi', 'email': 'sarah.omondi@student.com'},
    {'username': 'peter.kamau@student.com', 'first_name': 'Peter', 'last_name': 'Kamau', 'email': 'peter.kamau@student.com'},
]
for s in students_info:
    if not UserModel.objects.filter(username=s['username']).exists():
        user = UserModel(username=s['username'], email=s['email'], first_name=s['first_name'], last_name=s['last_name'], role='STUDENT')
        user.set_password('student1234')
        user.save()
        print(f"      Created: {s['username']}")

instructors_info = [
    {'username': 'instructor1@greenlight.com', 'first_name': 'David', 'last_name': 'Ochieng', 'license': 'INS-001', 'exp': 8, 'spec': 'Class B, Commercial'},
    {'username': 'instructor2@greenlight.com', 'first_name': 'Grace', 'last_name': 'Wanjiku', 'license': 'INS-002', 'exp': 5, 'spec': 'Class B, Class A'},
    {'username': 'instructor3@greenlight.com', 'first_name': 'Peter', 'last_name': 'Otieno', 'license': 'INS-003', 'exp': 12, 'spec': 'Commercial, PSV'},
]
instructors = []
for inst in instructors_info:
    user, created = UserModel.objects.get_or_create(
        username=inst['username'],
        defaults={'first_name': inst['first_name'], 'last_name': inst['last_name'], 'email': inst['username'], 'role': 'INSTRUCTOR'},
    )
    if created:
        user.set_password('instructor123')
        user.save()
    instructor, _ = Instructor.objects.get_or_create(
        user=user,
        defaults={'license_number': inst['license'], 'experience_years': inst['exp'], 'specialization': inst['spec']},
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
vehicle_objs = []
from datetime import date
for v in vehicles_info:
    vehicle, _ = Vehicle.objects.get_or_create(
        registration_number=v['reg'],
        defaults={
            'category': v['cat'], 'make': v['make'], 'model_name': v['model'],
            'year': v['year'], 'color': v['color'],
            'insurance_expiry': date(2027, 12, 31), 'service_due': date(2026, 12, 31),
        }
    )
    vehicle_objs.append(vehicle)
print(f"      {Vehicle.objects.count()} vehicles ready")

# Create student profiles
cat_b1 = CourseCategory.objects.get(slug='b1')
course_basic = Course.objects.get(slug='basic-driving')
branch_kimbo = Branch.objects.get(slug='kimbo')

student_users = UserModel.objects.filter(role='STUDENT')
for su in student_users:
    Student.objects.get_or_create(
        user=su,
        defaults={
            'student_number': f'GLS-{su.id:04d}',
            'category': cat_b1,
            'course': course_basic,
            'branch': branch_kimbo,
            'instructor': instructors[0] if instructors else None,
            'vehicle': vehicle_objs[0] if vehicle_objs else None,
            'status': 'ACTIVE',
            'expected_graduation': tz.now().date() + timedelta(days=90),
        }
    )
print(f"      {Student.objects.count()} student profiles ready")

print("\n" + "=" * 50)
print("  DEPLOYMENT COMPLETE!")
print("=" * 50)
print("\n  URL: http://greenlight-driving-defensive.schones-heim-builders.co.ke")
print("  Admin: admin@greenlight.com / admin1234")
print("  Students:")
print("    james.mwangi@student.com / student1234")
print("    sarah.omondi@student.com / student1234")
print("    peter.kamau@student.com  / student1234")
print("  Instructors:")
print("    instructor1@greenlight.com / instructor123")
print("    instructor2@greenlight.com / instructor123")
print("    instructor3@greenlight.com / instructor123")
print("=" * 50)
