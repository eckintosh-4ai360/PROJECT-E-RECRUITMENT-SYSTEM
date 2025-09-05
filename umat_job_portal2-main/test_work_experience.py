#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced work experience extraction functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.work_experience_analyzer import extract_work_experience

# Sample resume texts with different date formats
sample_resumes = [
    {
        "name": "Structured Resume with Clear Dates",
        "text": """
        John Smith
        Software Engineer
        john.smith@email.com | (555) 123-4567
        
        WORK EXPERIENCE
        
        Senior Software Engineer
        Google Inc
        January 2020 - Present
        • Developed scalable microservices using Python and Go
        • Led a team of 5 engineers on cloud infrastructure projects
        • Improved system performance by 40%
        
        Software Engineer
        Microsoft Corporation  
        June 2017 - December 2019
        • Built web applications using React and Node.js
        • Collaborated with cross-functional teams
        • Implemented CI/CD pipelines
        
        Junior Developer
        StartupXYZ
        March 2016 - May 2017
        • Developed mobile applications using React Native
        • Participated in agile development process
        
        EDUCATION
        Bachelor of Computer Science
        University of Technology
        2016
        """
    },
    {
        "name": "Resume with Various Date Formats",
        "text": """
        Jane Doe
        Data Scientist
        
        PROFESSIONAL EXPERIENCE
        
        Lead Data Scientist | TechCorp | 01/2021 - Current
        - Advanced machine learning model development
        - Team leadership and project management
        
        Data Analyst | DataSolutions | 2019 - 2020
        - Statistical analysis and reporting
        - Database management and optimization
        
        Research Assistant | University Lab | Sep 2017 to Aug 2018
        - Conducted research on AI algorithms
        - Published 3 research papers
        
        SKILLS: Python, R, SQL, TensorFlow, Pandas
        """
    },
    {
        "name": "Resume with Experience Statement",
        "text": """
        Mark Johnson
        Full Stack Developer
        
        SUMMARY
        Experienced full-stack developer with 5+ years of experience in web development.
        Proficient in JavaScript, Python, and cloud technologies.
        
        SKILLS
        • Frontend: React, Vue.js, HTML, CSS
        • Backend: Node.js, Python, Django
        • Database: MongoDB, PostgreSQL
        • Cloud: AWS, Docker, Kubernetes
        
        PROJECTS
        E-commerce Platform (2020-2023)
        - Built scalable web application serving 10K+ users
        - Implemented microservices architecture
        """
    },
    {
        "name": "Resume with Overlapping Employment",
        "text": """
        Sarah Wilson
        Project Manager
        
        WORK HISTORY
        
        Senior Project Manager
        ABC Consulting
        Mar 2020 - Present
        • Managing multiple client projects simultaneously
        
        Freelance Consultant
        Self-Employed
        Jan 2019 - June 2021
        • Providing project management consulting services
        
        Project Coordinator
        XYZ Company
        June 2017 - February 2020
        • Coordinated cross-functional project teams
        
        Assistant Manager
        RetailCorp
        2015 - 2017
        • Managed daily operations and staff
        """
    }
]

def main():
    print("=" * 80)
    print("ENHANCED WORK EXPERIENCE EXTRACTION DEMONSTRATION")
    print("=" * 80)
    
    for i, resume in enumerate(sample_resumes, 1):
        print(f"\n{'='*20} RESUME {i}: {resume['name']} {'='*20}")
        print(f"\nRESUME TEXT:\n{resume['text'][:300]}...")
        
        # Extract work experience
        try:
            result = extract_work_experience(resume['text'])
            
            print(f"\n{'─'*60}")
            print("EXTRACTION RESULTS:")
            print(f"{'─'*60}")
            
            # Basic stats
            print(f"Total Experience: {result['total_years']} years ({result['total_months']} months)")
            print(f"Experience Level: {result['experience_level'].upper()}")
            print(f"Extraction Method: {result.get('extraction_method', 'N/A')}")
            
            if result.get('earliest_start_date') and result.get('latest_end_date'):
                print(f"Career Span: {result['earliest_start_date']} to {result['latest_end_date']}")
            
            # Individual work experiences
            work_experiences = result.get('work_experiences', [])
            if work_experiences:
                print(f"\nWORK EXPERIENCES FOUND: {len(work_experiences)}")
                print("─" * 40)
                
                for j, exp in enumerate(work_experiences, 1):
                    current_indicator = " (CURRENT)" if exp.get('is_current', False) else ""
                    print(f"{j}. {exp.get('position', 'Unknown Position')} at {exp.get('company', 'Unknown Company')}{current_indicator}")
                    print(f"   Duration: {exp.get('duration_months', 0)} months")
                    if hasattr(exp.get('start_date'), 'strftime'):
                        start_str = exp['start_date'].strftime('%b %Y')
                        end_str = exp['end_date'].strftime('%b %Y') if not exp.get('is_current') else 'Present'
                        print(f"   Period: {start_str} - {end_str}")
                    print()
            
            # Employment gaps
            gaps = result.get('gaps_detected', [])
            if gaps:
                print(f"EMPLOYMENT GAPS DETECTED: {len(gaps)}")
                for gap in gaps:
                    print(f"  • {gap['duration_months']} months gap between {gap['after_company']} and {gap['before_company']}")
            
            # Overlapping employment
            overlaps = result.get('overlaps_detected', [])
            if overlaps:
                print(f"OVERLAPPING EMPLOYMENT DETECTED: {len(overlaps)}")
                for overlap in overlaps:
                    print(f"  • {overlap['overlap_months']} months overlap between {overlap['company1']} and {overlap['company2']}")
            
            # Summary
            if result.get('experience_summary'):
                print(f"\nSUMMARY: {result['experience_summary']}")
            
            # Career timeline
            timeline = result.get('career_timeline', [])
            if timeline:
                print(f"\nCAREER TIMELINE:")
                for entry in timeline:
                    current_marker = " ← CURRENT" if entry.get('is_current') else ""
                    print(f"  • {entry['period']}: {entry['position']} at {entry['company']}{current_marker}")
                    
        except Exception as e:
            print(f"ERROR: Failed to extract work experience: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
