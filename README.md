# UMaT Job Portal

A web-based career platform and e-recruitment system for the University of Mines and Technology (UMaT), featuring an AI-powered resume analysis module to intelligently match candidates with suitable job opportunities.

## Features
- **Role-based Authentication:** Secure access for Candidates and Administrators.
- **AI-Powered Resume Analysis:** Utilizes Groq AI (Llama 3) for fast and accurate resume parsing, skill extraction, and completeness feedback.
- **Semantic Job Matching:** Intelligent scoring system that aligns candidate skills and experiences with open job requirements.
- **Application Tracking:** Comprehensive pipeline to manage applications from submission through review, interview scheduling, and final outcome.
- **Admin Dashboard:** Recruitment analytics and metrics for streamlined hiring operations.
- **Candidate Profiles:** Personalized portals for users to manage their resumes, view matched jobs, and track applications.

## Built With
- **Backend:** Python, Flask
- **Database:** SQLite (via Flask-SQLAlchemy)
- **Frontend:** HTML5, CSS3, Bootstrap 5, Jinja2
- **AI/NLP:** Groq API (Llama-3.3-70b-versatile), spaCy, NLTK
- **Document Parsing:** pdfminer.six, python-docx

## Screenshots

![Homepage Overview](screenshots/homepage.png)
*(Placeholder: Add your homepage screenshot here)*

![Admin Dashboard](screenshots/dashboard.png)
*(Placeholder: Add your admin dashboard screenshot here)*

![Resume Analysis](screenshots/analysis.png)
*(Placeholder: Add your resume analysis screenshot here)*

## Installation

```bash
# Clone the repository
git clone https://github.com/eckintosh-4ai360/PROJECT-E-RECRUITMENT-SYSTEM.git

# Navigate into the project directory
cd PROJECT-E-RECRUITMENT-SYSTEM

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Create an environment file for secrets
# Add your GROQ_API_KEY to this file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Run the application (this will auto-create the database and tables)
python run.py
```

## Future Improvements
- **Real-time Notifications:** Email and in-app alerts for application status updates.
- **Advanced Admin Reporting:** Deeper analytics, custom report generation, and data export capabilities.
- **Mobile App Integration:** Companion mobile application for candidates to apply on the go.
- **Cloud Storage Integration:** Move resume file storage to AWS S3 or Cloudinary for better scalability.
