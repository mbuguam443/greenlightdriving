#!/usr/bin/env python3
"""Seed study materials from study_materials/ into StudentDocument records."""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greenlight.settings')
import django
django.setup()

from student_portal.models import StudentDocument
from django.core.files import File

project_dir = os.path.dirname(os.path.abspath(__file__))
materials_dir = os.path.join(project_dir, 'study_materials')

if not os.path.isdir(materials_dir):
    print("      study_materials/ folder not found")
    sys.exit(0)

materials = [
    {'title': 'Road Signs', 'category': 'theory', 'prefix': 'sign_', 'desc': 'Common road signs for NTSA theory exam'},
    {'title': 'NTSA Theory Notes', 'category': 'theory', 'prefix': 'ntsa_theory_', 'desc': 'NTSA theory exam preparation materials'},
]

created = 0
for mat in materials:
    prefix = mat['prefix']
    existing = StudentDocument.objects.filter(title__startswith=mat['title'], category=mat['category']).count()
    if existing > 0:
        print(f"      {mat['title']}: already seeded ({existing} docs) — skipping")
        continue

    files = sorted([f for f in os.listdir(materials_dir) if f.startswith(prefix)])
    for i, fname in enumerate(files):
        filepath = os.path.join(materials_dir, fname)
        doc_title = mat['title'] if len(files) == 1 else f'{mat["title"]} - {i + 1}'
        rel_path = f'student_documents/{fname}'
        doc = StudentDocument(
            title=doc_title,
            description=mat['desc'],
            category=mat['category'],
            is_active=True,
        )
        with open(filepath, 'rb') as f:
            doc.file.save(fname, File(f), save=True)
        created += 1
        print(f"      {doc_title}")

if created:
    print(f"   {created} study material(s) seeded")
else:
    print("      All materials already seeded")
