#!/bin/bash
echo "Starting deployment..."

# 1. Install dependencies
echo "Installing requirements..."
pip3 install -r requirements.txt || pip install -r requirements.txt

echo "Preparing database directory..."
mkdir -p data

echo "Migrating database..."
python manage.py migrate

# 3. Create Superuser (Automated)
# Using a python script to safely create admin if not exists
cat <<EOF > create_cloud_admin.py
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_server.settings')
django.setup()

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin888')
    print("Superuser 'admin' created.")
else:
    print("Superuser 'admin' already exists.")
EOF
python create_cloud_admin.py

# 4. Run Server
echo "Server starting on port 8000..."
python manage.py runserver 0.0.0.0:8000
