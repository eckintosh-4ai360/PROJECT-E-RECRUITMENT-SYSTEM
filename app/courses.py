"""Course recommendations and related functions"""

# Course recommendations data
ds_course = [
    {
        "Course Name": "Data Science and Machine Learning Bootcamp",
        "Link": "https://www.coursera.org/specializations/data-science-python"
    },
    {
        "Course Name": "Applied Data Science with Python",
        "Link": "https://www.coursera.org/specializations/data-science-python"
    },
    {
        "Course Name": "Data Analysis with Python",
        "Link": "https://www.coursera.org/learn/data-analysis-with-python"
    }
]

web_course = [
    {
        "Course Name": "Full Stack Web Development",
        "Link": "https://www.coursera.org/specializations/full-stack-web-development"
    },
    {
        "Course Name": "Web Applications for Everybody",
        "Link": "https://www.coursera.org/specializations/web-applications"
    },
    {
        "Course Name": "React Specialization",
        "Link": "https://www.coursera.org/specializations/react"
    }
]

android_course = [
    {
        "Course Name": "Android App Development",
        "Link": "https://www.coursera.org/specializations/android-app-development"
    },
    {
        "Course Name": "Android Basics",
        "Link": "https://www.coursera.org/specializations/android-basics"
    },
    {
        "Course Name": "Advanced Android Development",
        "Link": "https://www.coursera.org/specializations/advanced-android-development"
    }
]

ios_course = [
    {
        "Course Name": "iOS App Development with Swift",
        "Link": "https://www.coursera.org/specializations/ios-development"
    },
    {
        "Course Name": "iOS Development for Creative Entrepreneurs",
        "Link": "https://www.coursera.org/specializations/ios-development"
    },
    {
        "Course Name": "Swift 5 iOS Application Developer",
        "Link": "https://www.coursera.org/specializations/swift-5-ios-app-developer"
    }
]

uiux_course = [
    {
        "Course Name": "UI/UX Design Specialization",
        "Link": "https://www.coursera.org/specializations/ui-ux-design"
    },
    {
        "Course Name": "User Interface Design",
        "Link": "https://www.coursera.org/learn/user-interface-design"
    },
    {
        "Course Name": "User Experience Research and Design",
        "Link": "https://www.coursera.org/specializations/user-experience-research"
    }
]

def course_recommender(resume_text):
    """
    Recommend courses based on skills found in the resume.
    Returns a dictionary of course categories and their corresponding courses.
    """
    resume_text = resume_text.lower()
    
    recommendations = {}
    
    # Data Science Keywords
    ds_keywords = ['python', 'r', 'statistics', 'machine learning', 'data analysis', 
                  'pandas', 'numpy', 'scipy', 'scikit-learn', 'tensorflow', 'keras',
                  'data science', 'big data', 'analytics']
                  
    # Web Development Keywords
    web_keywords = ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node',
                   'django', 'flask', 'php', 'ruby', 'web development', 'full stack',
                   'frontend', 'backend']
                   
    # Android Development Keywords
    android_keywords = ['android', 'kotlin', 'java', 'android studio', 'mobile development',
                       'mobile apps', 'gradle', 'android sdk']
                       
    # iOS Development Keywords
    ios_keywords = ['ios', 'swift', 'objective-c', 'xcode', 'cocoa', 'mobile development',
                   'mobile apps', 'app store']
                   
    # UI/UX Keywords
    uiux_keywords = ['ui', 'ux', 'user interface', 'user experience', 'figma', 'sketch',
                    'adobe xd', 'wireframe', 'prototype', 'design thinking']
    
    # Check for matches and add corresponding courses
    if any(keyword in resume_text for keyword in ds_keywords):
        recommendations["Data Science"] = ds_course
        
    if any(keyword in resume_text for keyword in web_keywords):
        recommendations["Web Development"] = web_course
        
    if any(keyword in resume_text for keyword in android_keywords):
        recommendations["Android Development"] = android_course
        
    if any(keyword in resume_text for keyword in ios_keywords):
        recommendations["iOS Development"] = ios_course
        
    if any(keyword in resume_text for keyword in uiux_keywords):
        recommendations["UI/UX"] = uiux_course
    
    # If no matches found, recommend web development as a default
    if not recommendations:
        recommendations["Web Development"] = web_course
    
    return recommendations

# Resume writing and interview tip video links
resume_videos = [
    "https://www.youtube.com/watch?v=y8YH0Qbu5h4",
    "https://www.youtube.com/watch?v=HQqqQx5BCFY",
    "https://www.youtube.com/watch?v=BYUy1yvjHxE",
    "https://www.youtube.com/watch?v=HQqqQx5BCFY",
]

interview_videos = [
    "https://www.youtube.com/watch?v=Ji46s5BHdr0",
    "https://www.youtube.com/watch?v=seVxXHi2YMs",
    "https://www.youtube.com/watch?v=9FgfsLa_SmY",
    "https://www.youtube.com/watch?v=2HQmjLu-6RQ",
] 