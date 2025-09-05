#!/usr/bin/env python3
"""
Test script for enhanced skills extraction
Tests the skills mentioned in the user's example:
Swift, Objective-C, XCode, Cocoa Touch, SQLite, Plist, NSUserDefaults, XML, JSON, REST, SOAP
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_enhanced_skills_extraction():
    """Test the enhanced skills extraction with iOS development skills."""
    
    # Test resume text with iOS development skills
    test_resume_text = """
    iOS Developer with 5 years of experience
    
    TECHNICAL SKILLS:
    Programming Languages: Swift, Objective-C
    Tools: XCode
    Frameworks: Cocoa Touch
    Data Storage: SQLite, Plist, NSUserDefaults
    Parsing Techniques: XML, JSON
    Web Services: REST, SOAP
    
    WORK EXPERIENCE:
    Senior iOS Developer at TechCorp
    January 2020 - Present
    - Developed iOS applications using Swift and Objective-C
    - Used XCode for development and debugging
    - Implemented Cocoa Touch frameworks for UI development
    - Worked with SQLite databases and Plist files
    - Integrated REST and SOAP web services
    - Parsed XML and JSON data formats
    
    EDUCATION:
    Bachelor of Computer Science
    University of Technology
    2016
    """
    
    print("=" * 80)
    print("ENHANCED SKILLS EXTRACTION TEST")
    print("=" * 80)
    print(f"\nTest Resume Text:\n{test_resume_text}")
    
    try:
        # Test the enhanced skills extraction
        from app.resume_analyzer import ResumeAnalyzer
        
        analyzer = ResumeAnalyzer()
        skills = analyzer.extract_skills(test_resume_text)
        
        print(f"\n{'─'*60}")
        print("EXTRACTION RESULTS:")
        print(f"{'─'*60}")
        
        if skills:
            for category, skill_list in skills.items():
                if skill_list:
                    print(f"\n{category.upper()}:")
                    for skill in skill_list:
                        print(f"  - {skill}")
        else:
            print("No skills extracted!")
            
        # Check for specific skills mentioned in the user's example
        expected_skills = {
            "programming_languages": ["swift", "objective-c"],
            "development_tools": ["xcode"],
            "mobile_development": ["cocoa touch"],
            "databases": ["sqlite", "plist", "nsuserdefaults"],
            "parsing_techniques": ["xml", "json"],
            "web_services": ["rest", "soap"]
        }
        
        print(f"\n{'─'*60}")
        print("EXPECTED SKILLS CHECK:")
        print(f"{'─'*60}")
        
        all_extracted_skills = []
        for category_skills in skills.values():
            all_extracted_skills.extend([skill.lower() for skill in category_skills])
        
        for category, expected_list in expected_skills.items():
            print(f"\n{category.upper()}:")
            for expected_skill in expected_list:
                if expected_skill in all_extracted_skills:
                    print(f"  ✓ {expected_skill} - FOUND")
                else:
                    print(f"  ✗ {expected_skill} - MISSING")
        
        # Test the enhanced work experience extraction
        print(f"\n{'─'*60}")
        print("WORK EXPERIENCE EXTRACTION:")
        print(f"{'─'*60}")
        
        experience = analyzer.extract_experience(test_resume_text)
        print(f"Total Years: {experience.get('years', 0)}")
        print(f"Experience Level: {experience.get('level', 'unknown')}")
        print(f"Extraction Method: {experience.get('extraction_method', 'unknown')}")
        
        if experience.get('work_experiences'):
            print(f"\nWork Experiences Found: {len(experience['work_experiences'])}")
            for i, exp in enumerate(experience['work_experiences'], 1):
                print(f"{i}. {exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')}")
                print(f"   Duration: {exp.get('duration_months', 0)} months")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_skills_extraction()
