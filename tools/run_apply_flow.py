import os
import sys
import django
from django.test import Client

# Ensure project root is on PYTHONPATH
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from grants.models import GrantApplication

# Create test user
username = 'testuser'
password = 'TestPass!123'
email = 'testuser@example.com'
if not User.objects.filter(username=username).exists():
    user = User.objects.create_user(username=username, email=email, password=password)
    print('Created user', username)
else:
    user = User.objects.get(username=username)
    print('User exists', username)

client = Client()
logged = client.login(username=username, password=password)
print('Login:', logged)

# Ensure no existing application
GrantApplication.objects.filter(user=user).delete()

# Submit application
resp = client.post('/grants/apply/', {
    'full_name': 'Test User',
    'email': 'testuser@example.com',
    'address': '123 Test St',
    'amount_requested': '1000',
}, follow=True, SERVER_NAME='127.0.0.1')

print('POST status code:', resp.status_code)
print('Redirect chain:', resp.redirect_chain)

# Check DB
app = GrantApplication.objects.filter(user=user).first()
if app:
    print('Application saved:', app.full_name, app.amount_requested, app.status)
else:
    print('No application found')

# Show content snippet
content = resp.content.decode('utf-8')
print('\n--- Response snippet ---\n')
print(content[:800])
