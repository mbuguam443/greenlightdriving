#!/bin/bash
# Run this after uploading to cPanel via SSH or Terminal
# Navigate to project directory first: cd greenlight-driving-defensive.schones-heim-builders.co.ke

echo "=== Setting up Green Light Driving School ==="

# Create virtual environment
python3 -m venv virtualenv
source virtualenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (interactive)
echo "Creating superuser..."
python manage.py createsuperuser --noinput
export DJANGO_SUPERUSER_PASSWORD='admin1234'
python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'greenlight.settings'
django.setup()
from accounts.models import User
if not User.objects.filter(username='admin@greenlight.com').exists():
    User.objects.create_superuser('admin@greenlight.com', 'admin@greenlight.com', 'admin1234', role='SUPER_ADMIN')
    print('Superuser created: admin@greenlight.com / admin1234')
else:
    print('Superuser already exists')
"

# Seed data
python manage.py shell -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'greenlight.settings'
django.setup()
from core.models import SiteSettings
if not SiteSettings.objects.exists():
    SiteSettings.objects.create(
        school_name='Greenlight Defensive Driving School',
        phone='+254 700 000 000',
        email='info@greenlightdriving.co.ke',
        address='Nairobi, Kenya'
    )
    print('Site settings created')
"

echo "=== Setup complete ==="
echo "Login: admin@greenlight.com / admin1234"
echo "URL: http://greenlight-driving-defensive.schones-heim-builders.co.ke"
