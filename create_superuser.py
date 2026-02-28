#!/usr/bin/env python
"""
Create superuser automatically for Render deployment.
Place this file in the backend folder.
Usage: python backend/create_superuser.py
"""

import os
import sys
import django
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_django():
    """Setup Django environment"""
    # Get the directory containing this script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Add the backend directory to Python path (though we're already there)
    sys.path.append(BASE_DIR)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myClinicproject.settings')
    
    # Setup Django
    django.setup()
    
    logging.info(f"Django setup complete. BASE_DIR: {BASE_DIR}")

def create_superuser():
    """Create superuser if it doesn't exist"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get credentials from environment variables (Render's environment)
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'rukia')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@rukia.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '12345')
    
    # If no password in env, check if we should generate one
    if not password:
        # For production, you should ALWAYS set this in environment
        if os.environ.get('RENDER', False):  # Running on Render
            logging.error("DJANGO_SUPERUSER_PASSWORD environment variable not set!")
            logging.error("Please set it in Render's environment variables.")
            sys.exit(1)
        else:
            # Local development fallback
            password = 'admin123'
            logging.warning(f"Using default password '{password}' for local development. NOT SAFE FOR PRODUCTION!")
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        logging.info(f"Superuser '{username}' already exists. Skipping creation.")
        return
    
    # Create superuser
    try:
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        logging.info(f"✅ Superuser '{username}' created successfully!")
        
        # Log email but not password
        logging.info(f"📧 Email: {email}")
        if os.environ.get('RENDER', False):
            logging.info("🔐 Password is set from environment variable")
        else:
            logging.info("🔐 Password is set (check your env or default)")
            
    except Exception as e:
        logging.error(f"❌ Failed to create superuser: {e}")
        sys.exit(1)

def main():
    """Main function"""
    try:
        logging.info("Starting superuser creation script...")
        setup_django()
        create_superuser()
        logging.info("Superuser script completed successfully!")
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()