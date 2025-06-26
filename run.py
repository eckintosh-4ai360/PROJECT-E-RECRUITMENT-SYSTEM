from app import create_app, db
from app.models import User, Candidate, Resume, Job, JobMatch, UserRole # Import all models
import os

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
    sample_job = Job.query.filter_by(title="Sample CS Lecturer Position").first()
    if not sample_job:
        print("Creating sample CS job...")
        if not admin_user.id:
             db.session.flush() # Ensure admin_user has an ID
        sample_job = Job(
            title="Sample CS Lecturer Position",
            description="Seeking a lecturer for the Computer Science department. Responsibilities include teaching undergraduate courses in programming (Python, Java), data structures, and algorithms. Must have a Master's degree in CS or related field. PhD preferred. Strong communication skills required.",
            requirements="- Master's degree in Computer Science or related field (PhD preferred)\n- 2+ years teaching or relevant industry experience\n- Strong programming skills in Python and Java\n- Experience teaching Data Structures and Algorithms\n- Excellent communication and teaching skills",
            department="Computer Science",
            location="UMAT Campus, Tarkwa",
            salary_range="GHS 5,000 - GHS 8,000 per month",
            posted_by=admin_user.id,
            status="open"
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
        # Add initial data
        add_initial_data()

    # Run the app
    print("Starting Flask application...")
    # Use 0.0.0.0 to be accessible externally within the sandbox network
    app.run(host="0.0.0.0", port=5000, debug=True) # Disable debug for testing stability

