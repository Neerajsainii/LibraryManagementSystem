import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
try:
    user = User.objects.get(username='admin')
    user.set_password('admin123')
    user.save()
    print("Admin password set successfully!")
except User.DoesNotExist:
    print("Admin user does not exist. Creating...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Admin user created with password 'admin123'")
