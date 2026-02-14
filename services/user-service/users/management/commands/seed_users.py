from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from users.models import User
import faker

class Command(BaseCommand):
    help = 'Seed the database with sample users'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=1000, help='Number of users to create')

    def handle(self, *args, **options):
        count = options['count']
        fake = faker.Faker()

        self.stdout.write(f'Creating {count} users...')

        users_created = 0
        max_attempts = count * 10  # Prevent infinite loops
        attempts = 0

        while users_created < count and attempts < max_attempts:
            # Generate unique username
            username = fake.user_name()
            email = fake.email()

            # Check if username or email already exists
            if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
                attempts += 1
                continue

            # Generate user data
            first_name = fake.first_name()
            last_name = fake.last_name()

            try:
                # Create user with hashed password
                User.objects.create(
                    username=username,
                    email=email,
                    password=make_password('password123'),  # Default password for all seeded users
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True
                )
                users_created += 1

                if users_created % 100 == 0:
                    self.stdout.write(f'Created {users_created} users...')

            except Exception as e:
                # If creation fails for any reason, continue
                attempts += 1
                continue

        if users_created < count:
            self.stdout.write(
                self.style.WARNING(f'Could only create {users_created} users out of {count} requested due to duplicate generation limits')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {users_created} users')
            )