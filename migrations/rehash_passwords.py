"""
Script to rehash existing passwords to use SHA-256 instead of scrypt.
This should be run once after updating the code to use the new hashing mechanism.

Usage:
python -m migrations.rehash_passwords

Note: This script creates a new admin user with known credentials if no users can be authenticated.
"""

import sys
import os
import traceback
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User, UserRole
from app.utils import generate_password_hash

def rehash_passwords():
    """
    This function rehashes all user passwords using the new SHA-256 algorithm.
    Since we can't decrypt the existing hashes, we'll set a known password for all users
    and print out the list so administrators can communicate the temporary passwords.
    """
    try:
        print("Starting password rehashing process...")
        app = create_app()
        with app.app_context():
            print("Acquired app context")
            users = User.query.all()
            print(f"Found {len(users)} users in the database")
            
            if not users:
                print("No users found in the database.")
                return
            
            # Create a temporary admin account with known credentials
            admin_exists = User.query.filter_by(role=UserRole.admin).first()
            if not admin_exists:
                print("Creating a default admin account...")
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    role=UserRole.admin,
                    first_name="Admin",
                    last_name="User"
                )
                admin.password_hash = generate_password_hash("admin123")
                db.session.add(admin)
                db.session.commit()
                print("Default admin account created:")
                print("Email: admin@example.com")
                print("Password: admin123")
                print("IMPORTANT: Change this password immediately after logging in!")
            
            print("Setting temporary passwords for all users...")
            
            #! Reset all user passwords to a known temporary value
            temp_password = "UMaT2024!"
            password_hash = generate_password_hash(temp_password)
            
            for user in users:
                # Check if the hash is already in our new format
                if user.password_hash.startswith('sha256:'):
                    print(f"User {user.username} already has SHA-256 hash - skipping")
                    continue
                    
                # Update to new hash format
                print(f"Rehashing password for user: {user.username} ({user.email})")
                user.password_hash = password_hash
            
            db.session.commit()
            print("\nPassword rehashing completed.")
            print(f"All users now have the temporary password: {temp_password}")
            print("Please advise users to change their passwords immediately after logging in.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    rehash_passwords() 