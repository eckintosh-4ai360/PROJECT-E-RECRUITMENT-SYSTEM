from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy import Enum
import enum
from datetime import datetime

class UserRole(enum.Enum):
    admin = "admin"
    candidate = "candidate"

    def __str__(self):
        return self.value

class ApplicationStatus(enum.Enum):
    submitted = "Submitted"
    under_review = "Under Review"
    interview_scheduled = "Interview Scheduled"
    accepted = "Accepted"
    rejected = "Rejected"

    def __str__(self):
        return self.value

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_image = db.Column(db.String(255))  # Store the image path
    role = db.Column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.candidate)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    @property
    def profile_image_url(self):
        """Returns the URL for the user's profile image"""
        if self.profile_image:
            return f"/static/img/{self.profile_image}"
        return None

    # Relationships
    candidate_profile = db.relationship("Candidate", backref="user", uselist=False, lazy=True, cascade="all, delete-orphan")
    posted_jobs = db.relationship("Job", backref="poster", lazy=True)
    applications = db.relationship("Application", backref="applicant", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.admin

    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"

class Candidate(db.Model):
    __tablename__ = "candidates"
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    phone_number = db.Column(db.String(50))
    address = db.Column(db.Text)
    profile_summary = db.Column(db.Text)
    portfolio_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))

    # Relationships
    resumes = db.relationship("Resume", backref="candidate", lazy=True, cascade="all, delete-orphan")

class Resume(db.Model):
    __tablename__ = "resumes"
    resume_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidates.candidate_id"), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    parsed_text = db.Column(db.Text)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_primary = db.Column(db.Boolean, default=False)

    # Relationships
    applications = db.relationship("Application", backref="resume", lazy=True)
    matches = db.relationship("JobMatch", backref="resume", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume {self.original_filename} for Candidate ID {self.candidate_id}>"

class Job(db.Model):
    __tablename__ = "jobs"
    job_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text)
    department = db.Column(db.String(100), default="Computer Science")
    location = db.Column(db.String(100))
    salary_range = db.Column(db.String(100))
    posted_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    posted_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default="open")

    # Relationships
    applications = db.relationship("Application", backref="job", lazy=True)
    matches = db.relationship("JobMatch", backref="job", lazy=True)

    def __repr__(self):
        return f"<Job {self.job_id}: {self.title}>"

class Application(db.Model):
    __tablename__ = "applications"
    application_id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.job_id"), nullable=False)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.resume_id"))
    cover_letter = db.Column(db.Text)
    status = db.Column(Enum(ApplicationStatus, native_enum=False), nullable=False, default=ApplicationStatus.submitted)
    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to interviews
    interview = db.relationship("Interview", backref="application", uselist=False)

    def __repr__(self):
        return f"<Application {self.application_id} - {self.job.title} by {self.applicant.username}>"

    @property
    def status_display(self):
        return str(self.status) if self.status else "Unknown"

class JobMatch(db.Model):
    __tablename__ = "job_matches"
    match_id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(db.Integer, db.ForeignKey("resumes.resume_id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.job_id"), nullable=False)
    match_score = db.Column(db.Float, nullable=False)
    match_details = db.Column(db.Text)  # Store detailed match information as JSON
    calculated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<Match Resume:{self.resume_id} Job:{self.job_id} Score:{self.match_score:.4f}>"

class Interview(db.Model):
    __tablename__ = "interviews"
    interview_id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.application_id"), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    interview_type = db.Column(db.String(50), nullable=False)  # e.g., "online", "in-person"
    location_or_link = db.Column(db.String(512), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default="scheduled")  # scheduled, completed, cancelled

    def __repr__(self):
        return f"<Interview {self.interview_id} for Application {self.application_id}>"

