import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()

DATA_PROVIDER_GROUP = "data_provider"


class Command(BaseCommand):
    help = "Seed the database with roles and an initial data-provider user."

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=DATA_PROVIDER_GROUP)

        username = os.environ.get("SEED_PROVIDER_USERNAME", "dataprovider")
        password = os.environ.get("SEED_PROVIDER_PASSWORD", "ProviderPass123!")

        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Created user '{username}'"))
        else:
            self.stdout.write(f"User '{username}' already exists")

        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f"User '{username}' has role '{DATA_PROVIDER_GROUP}'"))
