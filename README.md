<<<<<<< HEAD
# UMaT Job Portal - Final Year Project

This project is a web-based job portal for the University of Mines and Technology (UMaT), featuring user management (candidates, admins), job postings, resume uploads, and an AI-powered resume analysis module to match candidates with suitable Computer Science department jobs.

## Features

*   **User Roles:** Candidate and Admin roles with distinct functionalities.
*   **Authentication:** Secure registration and login for users.
*   **Candidate Profile:** Users can manage their profile information.
*   **Resume Management:** Candidates can upload resumes (PDF, DOCX). Uploaded resumes are parsed to extract text.
*   **AI Job Matching:** An AI module analyzes parsed resume text against open Computer Science job descriptions using NLP (NLTK, spaCy) and TF-IDF/Cosine Similarity to calculate match scores.
*   **Job Listings:** Public view of open job positions.
*   **Admin Dashboard:** Admins can view basic site statistics and manage users/jobs (job management UI is basic).
*   **Database:** Uses SQLite for easy setup and development (switched from MySQL due to environment issues).

## Technology Stack

*   **Backend:** Python, Flask
*   **Database:** SQLite (using Flask-SQLAlchemy)
*   **Frontend:** HTML, CSS (Bootstrap 5), Jinja2 Templates
*   **Forms:** Flask-WTF, Flask-Bootstrap (for rendering forms with Bootstrap styles)
*   **Authentication:** Flask-Login
*   **Resume Parsing:** `pdfminer.six`, `python-docx`
*   **AI/NLP:** `nltk`, `spacy`, `scikit-learn`, `pandas`
*   **WSGI Server:** Gunicorn (for deployment)

## Setup and Running Locally

**Important:** If you previously installed dependencies, please delete your old virtual environment (`venv` folder) and follow these steps again to ensure all packages, including the newly added `Flask-Bootstrap`, are installed correctly.

1.  **Prerequisites:**
    *   Python 3.10 or higher
    *   `pip` (Python package installer)
    *   (Optional but recommended) `virtualenv` or `conda` for environment management

2.  **Clone/Download:** Obtain the project files (e.g., unzip the provided archive).

3.  **Create Virtual Environment (Recommended):**
    ```bash
    cd path/to/umat_job_portal
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Download NLP Models:**
    *   **spaCy:**
        ```bash
        python -m spacy download en_core_web_sm
        ```
    *   **NLTK:** The application attempts to download required NLTK data (`punkt`, `stopwords`, `wordnet`, `averaged_perceptron_tagger`) on first run if missing. If this fails due to network issues or permissions, you can download them manually:
        ```python
        import nltk
        nltk.download("punkt")
        nltk.download("stopwords")
        nltk.download("wordnet")
        nltk.download("averaged_perceptron_tagger")
        ```

6.  **Initialize Database & Run:**
    The `run.py` script will automatically create the SQLite database (`app.db`) and add a default admin user and a sample job posting if they don't exist.
    ```bash
    python run.py
    ```

7.  **Access the Application:**
    Open your web browser and navigate to `http://127.0.0.1:5000` or `http://localhost:5000`.

8.  **Default Admin Login:**
    *   **Email:** `admin@umat.edu.gh`
    *   **Password:** `adminpassword` (Change this immediately if deploying!)

## Deployment Guidance (Permanent Hosting)

This application is configured for deployment using a WSGI server like Gunicorn. Here's general guidance for common platforms:

**1. Environment Variables:**
   Before deploying, you **MUST** set the following environment variables on your hosting platform:
   *   `SECRET_KEY`: A long, random string for Flask session security. Generate one using `python -c "import secrets; print(secrets.token_hex())"`.
   *   `DATABASE_URL` (Optional, if switching database): If you switch back to PostgreSQL or MySQL in production, set this variable to the correct database connection string (e.g., `postgresql://user:password@host:port/database`). If you continue using SQLite (not recommended for most production scenarios due to concurrency limitations), ensure the file path is appropriate for your hosting environment.
   *   `FLASK_ENV` (Optional): Set to `production` to disable debug mode.

**2. Platform-as-a-Service (PaaS - e.g., Heroku):**
   *   The included `Procfile` (`web: gunicorn wsgi:app`) tells Heroku how to run the application using Gunicorn.
   *   Ensure your `requirements.txt` includes `gunicorn` and `Flask-Bootstrap`.
   *   Deploy using the Heroku CLI or Git integration.
   *   Set the required environment variables in the Heroku dashboard (Settings -> Config Vars).
   *   **Database:** Heroku's free/hobby tier often uses PostgreSQL. You would need to:
        *   Add `psycopg2-binary` to `requirements.txt`.
        *   Provision a Heroku Postgres database.
        *   Heroku automatically sets the `DATABASE_URL` environment variable.
        *   Update `config.py` to use `DATABASE_URL` if provided, falling back to SQLite otherwise.
        *   Run database migrations/creations on Heroku (e.g., `heroku run python -c "from app import db; db.create_all()"`).

**3. Virtual Private Server (VPS - e.g., DigitalOcean, AWS EC2):**
   *   Install Python, pip, and your database (e.g., PostgreSQL or MySQL) on the server.
   *   Clone your project code.
   *   Set up a virtual environment and install dependencies (`pip install -r requirements.txt`).
   *   Configure environment variables (e.g., using a `.env` file loaded by your application or system environment variables).
   *   Run the application using Gunicorn directly:
     ```bash
     gunicorn --bind 0.0.0.0:5000 wsgi:app 
     ```
     (Adjust the port as needed).
   *   **Reverse Proxy (Recommended):** Set up Nginx or Apache as a reverse proxy to handle incoming requests, manage SSL, and serve static files efficiently. Configure the proxy to forward requests to Gunicorn (e.g., running on `127.0.0.1:5000`).
   *   **Process Management:** Use a process manager like `systemd` or `supervisor` to ensure Gunicorn runs reliably and restarts automatically if it crashes.

**4. NLP Model Downloads:**
   *   Ensure the deployment environment has network access to download the spaCy and NLTK models during the build process or on first run.
   *   Alternatively, you can package the models with your application code, but this increases the deployment size.

**5. Static Files & Uploads:**
   *   For better performance, configure your web server (Nginx/Apache) or use a CDN to serve static files directly.
   *   The `uploads` directory needs to be persistent. On platforms like Heroku, the filesystem is ephemeral, so uploaded files will be lost on restart. Use a cloud storage service (like AWS S3, Google Cloud Storage) for resume uploads in production.

## Notes & Limitations

*   **Database:** Switched to SQLite for easy development setup. Consider PostgreSQL for production deployments.
*   **NLTK WordNet:** The development environment had issues downloading `wordnet`. Ensure your deployment environment can download it or handle the potential minor impact on lemmatization.
*   **Background Tasks:** Resume analysis is synchronous. Use Celery/RQ for background processing in production.
*   **Error Handling & UI:** Basic implementation; can be enhanced.
*   **Features:** Job application, advanced admin controls, and profile editing are placeholders.

## Project Structure

```
umat_job_portal/
├── app/                    # Main application package
│   ├── static/             # Static files (CSS, JS, images)
│   ├── templates/          # HTML templates (Jinja2)
│   ├── __init__.py         # Application factory
│   ├── ai_analyzer.py      # AI resume analysis and matching logic
│   ├── forms.py            # WTForms definitions
│   ├── models.py           # SQLAlchemy database models
│   ├── routes.py           # Application routes (views)
│   └── utils.py            # Utility functions (e.g., resume parsing)
├── uploads/                # Directory for uploaded resumes (created automatically)
├── venv/                   # Virtual environment directory (if created)
├── .env.example            # Example environment variables (copy to .env)
├── app.db                  # SQLite database file (created automatically)
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── run.py                  # Script to run the Flask application locally
├── wsgi.py                 # WSGI entry point for Gunicorn
├── Procfile                # For Heroku/PaaS deployment
└── README.md               # This file
```

<!-- ### sdf
Resume Analysis page 
I dont have the best idea but i want you to out of your best capability implement this, I want to add Candidates Resume Analysis page where:
1. candidate can view resume page (can use pdf.page) to view the resume uploaded.
2. display extraction of current skills from the candidate's resume
3. add resume tip and ideas (eg. check if there is no Professional summary in the resume tell the candidate to add professional summary or career objectives. do same for hobbies. and achievements and other relevant info that resume needs to have.)
4. add recommended courses for the user to better his career according to the resume uploaded using the courses.py file.
4. Add bonus videos for Resume Writing Tips from the youtube links provided
5. Add bonus videos for Interview tips 
make the ui for intuitive and modern. thank you.

you can you create the courses.py file for these: and import for implementation
"""Course recommendations and related functions"""

from utils.imports import *

# Course recommendations data
ds_course = [
    {"Course Name": "Python for Data Science and Machine Learning Bootcamp", "Link": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"},
    {"Course Name": "Machine Learning A-Z™: Hands-On Python & R In Data Science", "Link": "https://www.udemy.com/course/machinelearning/"},
    {"Course Name": "Data Science: Deep Learning in Python", "Link": "https://www.udemy.com/course/data-science-deep-learning-in-python/"},
]

web_course = [
    {"Course Name": "The Complete 2024 Web Development Bootcamp", "Link": "https://www.udemy.com/course/the-complete-web-development-bootcamp/"},
    {"Course Name": "The Web Developer Bootcamp 2024", "Link": "https://www.udemy.com/course/the-web-developer-bootcamp/"},
    {"Course Name": "JavaScript: Understanding the Weird Parts", "Link": "https://www.udemy.com/course/understand-javascript/"},
]

android_course = [
    {"Course Name": "Android App Development Masterclass using Kotlin", "Link": "https://www.udemy.com/course/android-oreo-kotlin-app-masterclass/"},
    {"Course Name": "The Complete Android 14 Developer Course", "Link": "https://www.udemy.com/course/complete-android-n-developer-course/"},
    {"Course Name": "Flutter & Dart - The Complete Guide", "Link": "https://www.udemy.com/course/learn-flutter-dart-to-build-ios-android-apps/"},
]

ios_course = [
    {"Course Name": "iOS & Swift - The Complete iOS App Development Bootcamp", "Link": "https://www.udemy.com/course/ios-13-app-development-bootcamp/"},
    {"Course Name": "SwiftUI Masterclass 2024", "Link": "https://www.udemy.com/course/swiftui-masterclass-course-ios-development-with-swift/"},
    {"Course Name": "iOS 14 & Swift 5 - The Complete iOS App Development Course", "Link": "https://www.udemy.com/course/ios-14-swift-5-the-complete-ios-app-development-course/"},
]

uiux_course = [
    {"Course Name": "UI/UX Design Patterns", "Link": "https://www.udemy.com/course/design-patterns-in-ui-ux-design/"},
    {"Course Name": "Complete Web & Mobile Designer in 2024: UI/UX, Figma", "Link": "https://www.udemy.com/course/complete-web-designer-mobile-designer-zero-to-mastery/"},
    {"Course Name": "User Experience Design Fundamentals", "Link": "https://www.udemy.com/course/user-experience-design-fundamentals/"},
]

def course_recommender(course_list):
    """Recommend courses based on user selection"""
    st.subheader("**Courses & Certificates Recommendations 🎓**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 5)
    
    # Use pandas DataFrame for better display
    df_courses = pd.DataFrame(course_list)
    df_courses = df_courses.sample(n=min(no_of_reco, len(df_courses)))
    
    for _, row in df_courses.iterrows():
        c += 1
        st.markdown(f"({c}) [{row['Course Name']}]({row['Link']})")
        rec_course.append(row['Course Name'])
    
    return rec_course

# Video recommendations
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

def display_video_section(videos, section_title):
    """Display video section with improved error handling"""
    st.header(f"**{section_title}💡**")
    try:
        video = random.choice(videos)
        title = fetch_yt_video(video)
        st.subheader(f"✅ **{title}**")
        try:
            st.video(video)
        except Exception as e:
            st.error(f"Could not display video. [Click here to watch]({video})")
    except Exception as e:
        st.info("Video content is temporarily unavailable. Please check back later.")  -->
=======
# umat-final-project
final year web app for ATS system 
>>>>>>> ac8878c0d5d7c0fd00bc07ad49392b3363bbb5e9
