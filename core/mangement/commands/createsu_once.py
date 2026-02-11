import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a superuser once, controlled by env vars."

    def handle(self, *args, **options):
        if os.environ.get("CREATE_SUPERUSER") != "1":
            self.stdout.write("CREATE_SUPERUSER!=1, skipping.")
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not username or not password:
            self.stdout.write("Missing DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"email": email})
        if not created:
            self.stdout.write("Superuser already exists, skipping.")
            return

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write("Superuser created successfully.")
