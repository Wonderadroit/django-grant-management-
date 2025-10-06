from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create or update admin user with specific credentials'
    
    def handle(self, *args, **options):
        username = 'wonderolabisi'
        password = 'Wonder419@'
        email = 'wonderolabisi@example.com'
        
        self.stdout.write('Setting up admin user...')
        
        # Check for existing admin users
        existing_admins = User.objects.filter(is_superuser=True)
        self.stdout.write(f'Found {existing_admins.count()} existing admin users:')
        for admin in existing_admins:
            self.stdout.write(f'  - {admin.username} ({admin.email})')
        
        # Try to get existing user or create new one
        try:
            admin_user = User.objects.get(username=username)
            self.stdout.write(f'Found existing user: {admin_user.username}')
            # Update existing user
            admin_user.set_password(password)
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.email = email
            admin_user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated existing user "{username}" with new password')
            )
        except User.DoesNotExist:
            # Create new admin user
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created new admin user: "{username}"')
            )
        
        # Verify the admin user
        self.stdout.write('\nAdmin user details:')
        self.stdout.write(f'  Username: {admin_user.username}')
        self.stdout.write(f'  Email: {admin_user.email}')
        self.stdout.write(f'  Is superuser: {admin_user.is_superuser}')
        self.stdout.write(f'  Is staff: {admin_user.is_staff}')
        
        # Show other admin users
        other_admins = User.objects.filter(is_superuser=True).exclude(username=username)
        if other_admins.exists():
            self.stdout.write(f'\nOther admin users ({other_admins.count()}):')
            for admin in other_admins:
                self.stdout.write(f'  - {admin.username} ({admin.email})')
            self.stdout.write('\nTo remove other admin users, you can delete them manually from the admin panel.')
        else:
            self.stdout.write('\nNo other admin users found.')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('ADMIN LOGIN CREDENTIALS:')
        self.stdout.write(f'URL: http://127.0.0.1:8000/admin/')
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write('='*50)