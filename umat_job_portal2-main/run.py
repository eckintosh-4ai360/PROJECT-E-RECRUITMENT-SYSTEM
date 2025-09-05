from app import create_app, db
from app.models import User, Candidate, Resume, Job, JobMatch, UserRole # Import all models
import os
from datetime import datetime, timedelta

app = create_app()

# Optional: Create a shell context for easier debugging
@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Candidate": Candidate,
        "Resume": Resume,
        "Job": Job,
        "JobMatch": JobMatch,
        "UserRole": UserRole
    }

def add_initial_data():
    print("Checking for initial data...")
    # Check if admin user exists
    admin_user = User.query.filter_by(role=UserRole.admin).first()
    if not admin_user:
        print("Creating default admin user...")
        admin_user = User(
            username="admin",
            email="admin@umat.edu.gh", 
            first_name="Admin",
            last_name="User",
            role=UserRole.admin
        )
        admin_user.set_password("adminpassword") # Use a strong password in production!
        db.session.add(admin_user)
        print("Admin user created.")
    else:
        print("Admin user already exists.")

    # Check if a sample CS job exists
    try:
        sample_job = Job.query.filter_by(title="CS Lecturer Position").first()
    except Exception as e:
        print(f"Error querying jobs: {e}")
        print("Recreating jobs table...")
        # Drop and recreate the jobs table
        Job.__table__.drop(db.engine, checkfirst=True)
        Job.__table__.create(db.engine)
        sample_job = None

    if not sample_job:
        print("Creating sample CS job...")
        if not admin_user.id:
             db.session.flush() # Ensure admin_user has an ID
        sample_job = Job(
            title="CS Lecturer Position",
            description="Seeking a lecturer for the Computer Science department. Responsibilities include teaching undergraduate courses in programming (Python, Java), data structures, and algorithms. Must have a Master's degree in CS or related field. PhD preferred. Strong communication skills required.",
            required_skills="- Strong programming skills in Python and Java\n- Experience teaching Data Structures and Algorithms\n- Excellent communication and teaching skills\n- Master's degree in Computer Science or related field (PhD preferred)\n- 2+ years teaching or relevant industry experience",
            department="Computer Science",
            location="UMAT Campus, Tarkwa",
            salary_range="GHS 5,000 - GHS 8,000 per month",
            posted_by=admin_user.id,
            status="open",
            closing_date=datetime.utcnow() + timedelta(days=30)  # Set closing date to 30 days from now
        )
        db.session.add(sample_job)
        print("Sample job created.")
    else:
        print("Sample job already exists.")
    
    try:
        db.session.commit()
        print("Initial data commit successful.")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding initial data: {e}")

if __name__ == "__main__":
    with app.app_context():
        print("Creating database tables (if they don't exist)...")
        db.create_all()
        print("Database tables checked/created.")
        # Add initial data only once when the Werkzeug reloader spawns the main process
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
            add_initial_data()

    # Run the app
    print("Starting Flask application...")
    
    # Configure Flask to watch only our app files, excluding virtual environment
    extra_dirs = ['app/']
    extra_files = []
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            if 'venv' in dirs:
                dirs.remove('venv')  # Don't visit venv directories
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')  # Don't visit pycache directories
            for filename in files:
                if not filename.endswith('.pyc'):  # Skip compiled Python files
                    filename = os.path.join(dirname, filename)
                    if os.path.isfile(filename):
                        extra_files.append(filename)
    
    # Use 0.0.0.0 to be accessible externally within the sandbox network
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        extra_files=extra_files,
        use_reloader=True,
        reloader_type='stat'  # Use stat reloader instead of watchdog
    )

