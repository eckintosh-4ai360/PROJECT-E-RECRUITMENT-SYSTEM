from app import create_app, db
from migrations.add_interview_levels import upgrade

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # Create all tables first
        db.create_all()
        # Run the migration
        upgrade()
        print("Migration completed successfully!") 