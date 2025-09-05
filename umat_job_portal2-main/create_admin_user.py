#!/usr/bin/env python3
"""
Script to create an admin user for testing
"""

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        existing_admin = User.query.filter_by(email='admin@umat.edu.gh').first()
        if existing_admin:
            print(f"Admin user already exists: {existing_admin.email}")
            return existing_admin
        
        # Create admin user
        admin_user = User(
            email='admin@umat.edu.gh',
            username='admin',
            first_name='Admin',
            last_name='User',
            password_hash=generate_password_hash('admin123'),
            is_admin=True,
            is_verified=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created successfully: {admin_user.email}")
            print("Login credentials:")
            print("  Email: admin@umat.edu.gh")
            print("  Password: admin123")
            return admin_user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
            return None

if __name__ == "__main__":
    create_admin_user()
