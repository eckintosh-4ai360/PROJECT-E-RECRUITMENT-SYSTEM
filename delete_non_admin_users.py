from app import create_app, db
from app.models import User, UserRole

app = create_app()

def delete_non_admin_users():
    with app.app_context():
        # Get count of users before deletion
        total_users = User.query.count()
        non_admin_users = User.query.filter(User.role != UserRole.admin).all()
        
        # Delete all non-admin users
        for user in non_admin_users:
            db.session.delete(user)
        
        # Commit the changes
        db.session.commit()
        
        # Get count after deletion
        remaining_users = User.query.count()
        
        print(f"Total users before deletion: {total_users}")
        print(f"Users deleted: {len(non_admin_users)}")
        print(f"Remaining users: {remaining_users}")

if __name__ == "__main__":
    delete_non_admin_users() 