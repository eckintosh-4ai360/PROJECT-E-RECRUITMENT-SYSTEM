#!/usr/bin/env python3
"""
Script to fix the interview relationship from one-to-one to one-to-many
"""

from app import create_app, db
from app.models import Application, Interview
from sqlalchemy import text

def fix_interview_relationship():
    app = create_app()
    
    with app.app_context():
        print("Fixing interview relationship...")
        
        # First, let's see the current state
        applications = Application.query.all()
        interviews = Interview.query.all()
        
        print(f"Current state:")
        print(f"  Applications: {len(applications)}")
        print(f"  Interviews: {len(interviews)}")
        
        for app in applications:
            if app.interview:
                print(f"  Application {app.application_id} has interview {app.interview.interview_id}")
        
        # The issue is that the relationship is defined as uselist=False (one-to-one)
        # but we need one-to-many for multiple interview levels
        # We need to update the model and create a migration
        
        print("\nTo fix this, we need to:")
        print("1. Update the Application model to use uselist=True")
        print("2. Update the template to use application.interviews instead of application.interview")
        print("3. Create a database migration")
        
        return True

if __name__ == "__main__":
    fix_interview_relationship()
