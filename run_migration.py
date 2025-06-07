from app import create_app
from migrations.add_feedback_column import upgrade

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        upgrade()
        print("Migration completed successfully!") 