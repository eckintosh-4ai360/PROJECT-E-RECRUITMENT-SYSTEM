#!/usr/bin/env python3
"""
Test script to verify admin functionality
"""

from app import create_app, db
from app.models import User, Application, Interview, InterviewLevel, InterviewLevelStatus
from datetime import datetime, timedelta

def test_admin_functionality():
    app = create_app()
    
    with app.app_context():
        # Check if there are any admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        print(f"Found {len(admin_users)} admin users:")
        for user in admin_users:
            print(f"  - {user.email} (ID: {user.user_id})")
        
        # Check if there are any applications with interviews
        all_applications = Application.query.all()
        applications_with_interviews = []
        
        for app in all_applications:
            if app.interview:
                applications_with_interviews.append(app)
        
        print(f"\nFound {len(applications_with_interviews)} applications with interviews:")
        for app in applications_with_interviews:
            print(f"  - Application ID: {app.application_id}")
            print(f"    Job: {app.job.title}")
            print(f"    Status: {app.status.value}")
            print(f"    Interview: {app.interview.interview_level.value} Level - {app.interview.level_status.value}")
        
        # Check if there are any interviews at all
        all_interviews = Interview.query.all()
        print(f"\nTotal interviews in database: {len(all_interviews)}")
        
        if all_interviews:
            print("Sample interview details:")
            for interview in all_interviews[:3]:  # Show first 3
                print(f"  - ID: {interview.interview_id}")
                print(f"    Level: {interview.interview_level.value}")
                print(f"    Status: {interview.level_status.value}")
                print(f"    Date: {interview.scheduled_date}")
                print(f"    Application ID: {interview.application_id}")

if __name__ == "__main__":
    test_admin_functionality()
