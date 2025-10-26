from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import Profile


class Command(BaseCommand):
    help = 'Create missing profiles for existing users'

    def handle(self, *args, **kwargs):
        users_without_profile = []
        users_with_profile = []
        
        for user in User.objects.all():
            try:
                profile = user.profile
                users_with_profile.append(user.username)
            except Profile.DoesNotExist:
                # Create profile for user
                role = 'admin' if user.is_superuser else 'student'
                Profile.objects.create(user=user, role=role)
                users_without_profile.append(f"{user.username} (created as {role})")
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Profile Check Complete!\n'))
        
        if users_without_profile:
            self.stdout.write(self.style.WARNING(f'Created profiles for {len(users_without_profile)} user(s):'))
            for username in users_without_profile:
                self.stdout.write(f'  - {username}')
        else:
            self.stdout.write(self.style.SUCCESS('All users already have profiles!'))
        
        self.stdout.write(f'\nTotal users with profiles: {len(users_with_profile) + len(users_without_profile)}')
