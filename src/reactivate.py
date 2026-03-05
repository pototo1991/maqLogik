import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
count = User.objects.filter(is_superuser=True).update(is_active=True)
print(f"[{count}] Superusuarios reactivados con éxito en la BD.")
