import os
import sys


USERNAME = 'TWOJ_LOGIN'
PROJECT_DIR = f'/home/{USERNAME}/paint_projj'

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'przyjazna_lapa.settings')


os.environ.setdefault('PAINT_SECRET_KEY', 'CHANGE-ME-pythonanywhere-free-secret-key')
os.environ.setdefault('PAINT_DEBUG', 'False')
os.environ.setdefault('PAINT_ALLOWED_HOSTS', f'{USERNAME}.pythonanywhere.com,.pythonanywhere.com')
os.environ.setdefault('PAINT_CSRF_TRUSTED_ORIGINS', f'https://{USERNAME}.pythonanywhere.com')
os.environ.setdefault('PAINT_SECURE_SSL_REDIRECT', 'True')

from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
