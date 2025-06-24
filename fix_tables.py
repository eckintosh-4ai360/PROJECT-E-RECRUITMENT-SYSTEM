"""
Script to fix database tables.
"""

import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import User, Candidate, UserRole

def fix_database():
    print("Fixing database tables...")
    
    app = create_app()
    
    with app.app_context():
        print("Creating missing tables...")
        db.create_all()
        
        print("Checking users and creating candidate profiles...")
        # Create candidate profiles for users who don't have one
        users = User.query.filter_by(role=UserRole.candidate).all()
        created_count = 0
        
        for user in users:
            if not hasattr(user, 'candidate_profile') or user.candidate_profile is None:
                try:
                    print(f"Creating candidate profile for {user.username}")
                    candidate = Candidate(candidate_id=user.id)
                    db.session.add(candidate)
                    created_count += 1
                except Exception as e:
                    print(f"Error creating candidate profile for {user.username}: {e}")
                    db.session.rollback()
        
        if created_count > 0:
            db.session.commit()
            print(f"Created {created_count} candidate profiles")
        
        # Verify candidate profiles
        candidates = Candidate.query.all()
        print(f"Found {len(candidates)} candidate profiles after fix")
        
        # Set admin role for admin user
        admin = User.query.filter_by(username="admin").first()
        if admin:
            admin.role = UserRole.admin
            db.session.commit()
            print(f"Set admin role for user {admin.username}")
        
        print("Database fix completed")

if __name__ == "__main__":
    fix_database() 