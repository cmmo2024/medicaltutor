"""
WSGI config for medicaltutordjproject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from dotenv import load_dotenv

project_dir = Path(__file__).resolve().parent.parent
env_file = project_dir / '.env'

# Load environment variables from .env file
load_dotenv(env_file)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medicaltutordjproject.settings")

application = get_wsgi_application()

