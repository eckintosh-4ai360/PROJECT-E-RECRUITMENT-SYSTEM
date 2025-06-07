from app import db
from flask import current_app
from sqlalchemy import text

def upgrade():
    with current_app.app_context():
        # Create a new table with all columns including feedback
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS applications_new (
                application_id INTEGER PRIMARY KEY,
                job_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                resume_id INTEGER NOT NULL,
                application_date DATETIME NOT NULL,
                status VARCHAR NOT NULL,
                cover_letter TEXT,
                feedback TEXT,
                last_updated DATETIME,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id),
                FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id),
                FOREIGN KEY(resume_id) REFERENCES resumes(resume_id)
            )
        '''))
        
        # Copy data from the old table to the new one (only existing columns)
        db.session.execute(text('''
            INSERT INTO applications_new (
                application_id, job_id, candidate_id, resume_id,
                application_date, status, cover_letter
            )
            SELECT 
                application_id, job_id, candidate_id, resume_id,
                application_date, status, cover_letter
            FROM applications
        '''))
        
        # Drop the old table
        db.session.execute(text('DROP TABLE IF EXISTS applications'))
        
        # Rename the new table to the original name
        db.session.execute(text('ALTER TABLE applications_new RENAME TO applications'))
        
        db.session.commit()

def downgrade():
    with current_app.app_context():
        # Create a new table without the feedback column
        db.session.execute(text('''
            CREATE TABLE IF NOT EXISTS applications_old (
                application_id INTEGER PRIMARY KEY,
                job_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                resume_id INTEGER NOT NULL,
                application_date DATETIME NOT NULL,
                status VARCHAR NOT NULL,
                cover_letter TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id),
                FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id),
                FOREIGN KEY(resume_id) REFERENCES resumes(resume_id)
            )
        '''))
        
        # Copy data from the current table to the old structure
        db.session.execute(text('''
            INSERT INTO applications_old (
                application_id, job_id, candidate_id, resume_id,
                application_date, status, cover_letter
            )
            SELECT 
                application_id, job_id, candidate_id, resume_id,
                application_date, status, cover_letter
            FROM applications
        '''))
        
        # Drop the current table
        db.session.execute(text('DROP TABLE IF EXISTS applications'))
        
        # Rename the old structure table to the original name
        db.session.execute(text('ALTER TABLE applications_old RENAME TO applications'))
        
        db.session.commit() 