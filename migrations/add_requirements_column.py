from app import db
from app.models import Job
import sqlite3

def upgrade():
    # Create a new jobs table with the requirements column
    with db.engine.connect() as conn:
        # First, rename the existing table
        conn.execute('ALTER TABLE jobs RENAME TO jobs_old')
        
        # Create new table with all columns including requirements
        conn.execute('''
            CREATE TABLE jobs (
                job_id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT,
                department VARCHAR(100),
                location VARCHAR(100),
                salary_range VARCHAR(100),
                posted_by INTEGER NOT NULL,
                posted_date DATETIME NOT NULL,
                status VARCHAR(50) NOT NULL,
                FOREIGN KEY(posted_by) REFERENCES users(id)
            )
        ''')
        
        # Copy data from old table to new table
        conn.execute('''
            INSERT INTO jobs (
                job_id, title, description, department, location, 
                salary_range, posted_by, posted_date, status
            )
            SELECT 
                job_id, title, description, department, location, 
                salary_range, posted_by, posted_date, status
            FROM jobs_old
        ''')
        
        # Drop the old table
        conn.execute('DROP TABLE jobs_old')
        
        conn.commit()

def downgrade():
    # Remove requirements column (by recreating table without it)
    with db.engine.connect() as conn:
        # First, rename the existing table
        conn.execute('ALTER TABLE jobs RENAME TO jobs_temp')
        
        # Create new table without requirements column
        conn.execute('''
            CREATE TABLE jobs (
                job_id INTEGER PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                department VARCHAR(100),
                location VARCHAR(100),
                salary_range VARCHAR(100),
                posted_by INTEGER NOT NULL,
                posted_date DATETIME NOT NULL,
                status VARCHAR(50) NOT NULL,
                FOREIGN KEY(posted_by) REFERENCES users(id)
            )
        ''')
        
        # Copy data from temp table to new table
        conn.execute('''
            INSERT INTO jobs (
                job_id, title, description, department, location, 
                salary_range, posted_by, posted_date, status
            )
            SELECT 
                job_id, title, description, department, location, 
                salary_range, posted_by, posted_date, status
            FROM jobs_temp
        ''')
        
        # Drop the temp table
        conn.execute('DROP TABLE jobs_temp')
        
        conn.commit() 