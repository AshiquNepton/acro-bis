# scripts/hash_password.py
"""
Standalone utility — hash a plaintext password using Django's PBKDF2 hasher.
No DB connection needed. Just prints the hash so you can paste it manually.

Usage:
    python scripts/hash_password.py
"""
import os
import sys
import django

# Point to your settings module so Django's hasher config loads correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_project.settings.local')
django.setup()

from django.contrib.auth.hashers import make_password

if __name__ == '__main__':
    password = input("Enter password to hash: ").strip()
    if not password:
        print("No password entered.")
        sys.exit(1)

    hashed = make_password(password)
    print("\nHashed password (copy this into itemgroups.narration):\n")
    print(hashed)
    print()