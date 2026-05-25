README.md

# UMaT Job Portal

# UMaT E-Recruitment System

A web-based career platform and e-recruitment system for the University of Mines and Technology (UMaT), featuring an AI-powered resume analysis module to intelligently match candidates with suitable job opportunities.
A Flask-based recruitment platform for the University of Mines and Technology (UMaT) that supports candidate applications, resume analysis, interview tracking, recruitment analytics, and role-based AI assistance for candidates, administrators, and portal visitors.

## Features

- **Role-based Authentication:** Secure access for Candidates and Administrators.
- **AI-Powered Resume Analysis:** Utilizes Groq AI (Llama 3) for fast and accurate resume parsing, skill extraction, and completeness feedback.
- **Semantic Job Matching:** Intelligent scoring system that aligns candidate skills and experiences with open job requirements.
- **Application Tracking:** Comprehensive pipeline to manage applications from submission through review, interview scheduling, and final outcome.
- **Admin Dashboard:** Recruitment analytics and metrics for streamlined hiring operations.
- **Candidate Profiles:** Personalized portals for users to manage their resumes, view matched jobs, and track applications.

## Overview

## Built With

- **Backend:** Python, Flask
- **Database:** PostgreSQL on Neon via `DATABASE_URL` (SQLite fallback for local-only use if no database URL is set)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2
- **AI/NLP:** Groq API (Llama-3.3-70b-versatile), spaCy, NLTK
- **Document Parsing:** pdfminer.six, python-docx
  This project brings the main recruitment workflow into one web application:

## Screenshots

- candidates can create profiles, upload resumes, discover jobs, apply, and track progress
- administrators can manage jobs, review applications, schedule interviews, and monitor hiring activity
- AI features help explain resume quality, job fit, cover letters, interview preparation, candidate comparisons, and portal FAQs

![Homepage Overview](screenshots/home.JPG)
_(Placeholder: Add your homepage screenshot here)_

## What The System Can Do

### Candidate experience

![Resume Analysis](screenshots/user%20profile.JPG)
![Resume Analysis](screenshots/resume%20coach.JPG)
![Resume Analysis](screenshots/resume%20analysis.JPG)
_(Placeholder: Add your admin dashboard screenshot here)_

- register and sign in as a candidate
- upload one or more resumes
- run AI-assisted resume analysis
- view job-match scores against open roles
- generate cover-letter drafts from resume and job context
- apply for jobs and track application status
- view scheduled interviews and interview progress
- use a Candidate Resume Coach for resume feedback, fit explanations, and interview prep

### Admin experience

![Admin Dashboard](screenshots/admin%20dashboard.JPG)
![Admin Dashboard](screenshots/admin%20dashboard2.JPG)

_(Placeholder: Add your resume analysis screenshot here)_

- create, edit, close, and delete job postings
- manage university events
- review all submitted applications
- schedule interviews and notify candidates
- update candidate status with feedback
- view dashboard analytics for users, jobs, resumes, applications, and pipeline flow
- use an Admin Recruitment Copilot for applicant summaries, candidate comparison, feedback drafting, shortlist reasoning, and interview prep notes

## Installation

### Public portal support

- browse open positions and event listings
- use a Portal Support Assistant for questions about applications, documents, events, and interview flow

## AI Features

The current AI layer is built around the app's real data rather than free-form chat alone.

- **Resume analysis:** section completeness, extracted skills, experience signals, and role relevance
- **Semantic job matching:** match scoring between resumes and open positions
- **Candidate Resume Coach:** explains weak matches, improvement areas, and likely next steps
- **Cover Letter Assistant:** drafts role-specific cover letters using resume and job context
- **Interview Prep Assistant:** helps candidates prepare for interviews with likely questions and talking points
- **Admin Recruitment Copilot:** summarizes applicant pools, compares candidates, drafts feedback, and prepares interview notes
- **Portal Support Assistant:** answers common workflow and navigation questions across the portal

## Guardrails

- candidate-facing AI only works on that candidate's own records
- admin-facing AI is limited to administrator access
- assistant output is advisory and read-only
- hiring decisions remain human-controlled
- assistant interactions are logged in the database

## Tech Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Mail
- **Frontend:** Jinja2 templates, Bootstrap 5, custom CSS
- **Database:** PostgreSQL (Neon) via `DATABASE_URL`
- **AI/NLP:** Groq API, spaCy, NLTK, scikit-learn, sentence-transformers
- **Document parsing:** pdfminer.six, python-docx, PyPDF2

## Project Highlights

- role-based authentication for candidates and admins
- resume upload and parsing
- AI-powered resume scoring and job matching
- cover-letter and interview support
- application pipeline with interview scheduling
- admin dashboard with recruitment analytics
- event publishing and public event browsing
- email notification support

## Getting Started

### 1. Clone the repository

```bash
# Clone the repository
git clone https://github.com/eckintosh-4ai360/PROJECT-E-RECRUITMENT-SYSTEM.git

# Navigate into the project directory
cd PROJECT-E-RECRUITMENT-SYSTEM
```

### 2. Create and activate a virtual environment

# Create and activate a virtual environment

```bash
python -m venv .venv
# On Windows:
```

On Windows:

```bash
.venv\Scripts\activate
# On macOS/Linux:
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

# Install required dependencies

```bash
pip install -r requirements.txt
```

# Create an environment file for secrets

# Add your GROQ_API_KEY to this file

echo "GROQ_API_KEY=your_api_key_here" > .env

### 4. Create a `.env` file

At minimum, add your Groq API key:

# Run the application (this will auto-create the database and tables)

```env
SECRET_KEY=change-this-in-production
DATABASE_URL=postgresql://username:password@your-neon-pooler-host/neondb?sslmode=require&channel_binding=require
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Optional mail settings:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=noreply@umat.edu.gh
```

## Running the App

Start the development server with:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

On first run, the app will:

- connect to the configured database from `DATABASE_URL` and create required tables if they do not already exist
- create required tables
- create a default admin account if one does not already exist
- create a sample open job if missing

## Migrating Existing SQLite Data To Neon

If you already have local data in `app.db` and want to move it into Neon, run:

```bash
python migrate_sqlite_to_neon.py
```

The script will:

- create the PostgreSQL tables in Neon if they do not already exist
- copy data from the local SQLite database into Neon
- preserve primary keys and reset PostgreSQL sequences
- ensure the default admin account exists after the migration

## Default Admin Account

For local development, `run.py` creates this default admin user:

- **Email:** `admin@umat.edu.gh`
- **Password:** `adminpassword`

Change this immediately before using the system beyond local testing.

## File Storage

Uploaded files are stored locally:

- resumes and cover letters in `uploads/`
- profile images in `app/static/profile_images/`
- event media in `app/static/event_images/` and related static directories

## Main Application Areas

- `app/routes.py` - core candidate and admin-facing application routes
- `app/admin_routes.py` - additional admin utilities
- `app/assistant_routes.py` - AI assistant endpoints
- `app/assistant_service.py` - shared assistant orchestration and logging
- `app/resume_analyzer.py` - Groq-powered resume analysis
- `app/semantic_job_matcher.py` - semantic matching logic
- `app/templates/` - Jinja templates for public, candidate, and admin views

## Notes For Development

- the app is now configured to use Neon/PostgreSQL when `DATABASE_URL` is present
- for Render or any production host, use the Neon pooled connection string as `DATABASE_URL`
- keep the unpooled Neon connection string only for direct SQL clients or one-off maintenance tasks
- if Groq is unavailable, some assistant and analysis flows fall back to simpler responses
- assistant interactions are saved in the database for traceability
- the AI layer works best when resumes are parsed cleanly and jobs have clear skill requirements

## Future Improvements

- **Real-time Notifications:** Email and in-app alerts for application status updates.
- **Advanced Admin Reporting:** Deeper analytics, custom report generation, and data export capabilities.
- **Mobile App Integration:** Companion mobile application for candidates to apply on the go.
- **Cloud Storage Integration:** Move resume file storage to AWS S3 or Cloudinary for better scalability.

- richer audit and reporting exports
- stronger applicant scoring explainability in the admin interface
- more structured interview scorecards
- cloud file storage integration
- background jobs for heavier AI processing
- stronger production deployment and monitoring setup
