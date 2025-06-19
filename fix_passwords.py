from app import create_app, db
from app.models import User, UserRole
from app.utils import generate_password_hash
import traceback

def fix_passwords():
    """Reset passwords to use SHA-256 hashing"""
    try:
        print("Starting password rehashing process...")
        app = create_app()
        with app.app_context():
            print("Acquired app context")
            users = User.query.all()
            print(f"Found {len(users)} users in the database")
            
            if not users:
                print("No users found in the database.")
                return
            
            # Create a temporary admin account with known credentials
            admin_exists = User.query.filter_by(role=UserRole.admin).first()
            if not admin_exists:
                print("Creating a default admin account...")
                admin = User(
                    username="admin",
                    email="admin@example.com",
                    role=UserRole.admin,
                    first_name="Admin",
                    last_name="User"
                )
                admin.password_hash = generate_password_hash("admin123")
                db.session.add(admin)
                db.session.commit()
                print("Default admin account created:")
                print("Email: admin@example.com")
                print("Password: admin123")
                print("IMPORTANT: Change this password immediately after logging in!")
            else:
                print(f"Admin user found: {admin_exists.username} ({admin_exists.email})")
                admin_exists.password_hash = generate_password_hash("admin123")
                print("Reset admin password to: admin123")
            
            print("Setting temporary passwords for all users...")
            
            # Reset all user passwords to a known temporary value
            temp_password = "TempPass123!"
            
            for user in users:
                if user.role == UserRole.admin:
                    continue  # Skip admin user, already handled above
                
                print(f"Rehashing password for user: {user.username} ({user.email})")
                user.password_hash = generate_password_hash(temp_password)
            
            db.session.commit()
            print("\nPassword rehashing completed.")
            print("Admin password: admin123")
            print(f"All other users now have the temporary password: {temp_password}")
            print("Please advise users to change their passwords immediately after logging in.")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    fix_passwords() 