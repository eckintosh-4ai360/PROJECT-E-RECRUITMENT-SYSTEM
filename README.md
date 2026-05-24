# UMaT E-Recruitment System

A Flask-based recruitment platform for the University of Mines and Technology (UMaT) that supports candidate applications, resume analysis, interview tracking, recruitment analytics, and role-based AI assistance for candidates, administrators, and portal visitors.

## Overview

This project brings the main recruitment workflow into one web application:

- candidates can create profiles, upload resumes, discover jobs, apply, and track progress
- administrators can manage jobs, review applications, schedule interviews, and monitor hiring activity
- AI features help explain resume quality, job fit, cover letters, interview preparation, candidate comparisons, and portal FAQs

## What The System Can Do

### Candidate experience

- register and sign in as a candidate
- upload one or more resumes
- run AI-assisted resume analysis
- view job-match scores against open roles
- generate cover-letter drafts from resume and job context
- apply for jobs and track application status
- view scheduled interviews and interview progress
- use a Candidate Resume Coach for resume feedback, fit explanations, and interview prep

### Admin experience

- create, edit, close, and delete job postings
- manage university events
- review all submitted applications
- schedule interviews and notify candidates
- update candidate status with feedback
- view dashboard analytics for users, jobs, resumes, applications, and pipeline flow
- use an Admin Recruitment Copilot for applicant summaries, candidate comparison, feedback drafting, shortlist reasoning, and interview prep notes

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
- **Database:** SQLite
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
git clone https://github.com/eckintosh-4ai360/PROJECT-E-RECRUITMENT-SYSTEM.git
cd PROJECT-E-RECRUITMENT-SYSTEM
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

At minimum, add your Groq API key:

```env
SECRET_KEY=change-this-in-production
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

- create the SQLite database if needed
- create required tables
- create a default admin account if one does not already exist
- create a sample open job if missing

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

- the app uses SQLite by default
- if Groq is unavailable, some assistant and analysis flows fall back to simpler responses
- assistant interactions are saved in the database for traceability
- the AI layer works best when resumes are parsed cleanly and jobs have clear skill requirements

## Future Improvements

- richer audit and reporting exports
- stronger applicant scoring explainability in the admin interface
- more structured interview scorecards
- cloud file storage integration
- background jobs for heavier AI processing
- stronger production deployment and monitoring setup
