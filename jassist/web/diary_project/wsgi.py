"""
WSGI config for diary_project project.
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Determine BASE_DIR consistently across the application
if getattr(sys, 'frozen', False):
    # If running in a PyInstaller bundle
    SCRIPT_DIR = Path(sys.executable).parent.resolve()
else:
    # If running as a normal Python script
    SCRIPT_DIR = Path(__file__).parent.parent.resolve()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diary_project.settings')

application = get_wsgi_application() 