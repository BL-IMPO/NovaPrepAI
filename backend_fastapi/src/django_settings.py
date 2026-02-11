import os
import sys
from pathlib import Path


current_file = Path(__file__).resolve()

local_django_path = current_file.parent.parent.parent / 'backend_core' / 'src'

docker_django_path = Path('/app/backend_core/src')

if docker_django_path.exists():
    sys.path.insert(0, str(docker_django_path))
    print(f"Using Docker Django path: {docker_django_path}")
elif local_django_path.exists():
    sys.path.insert(0, str(local_django_path))
    print(f"Using Local Django path: {local_django_path}")
else:
    print("WARNING: Could not find Django project path!")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')

# Initialize Django
import django
try:
    django.setup()
    print("Django initialized successfully")
except Exception as e:
    print(f"Error initializing django: {e}")
    raise

# Add the Django project to the path
#django_project_path = Path(__file__).resolve().parent.parent.parent / 'backend_core' / 'src'
#sys.path.insert(0, str(django_project_path))

# Set Django settings module
#os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend_core.settings')


