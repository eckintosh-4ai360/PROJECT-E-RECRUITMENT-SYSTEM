from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    users_with_images = User.query.filter(User.profile_image.isnot(None)).all()
    print(f"Found {len(users_with_images)} users with profile images:")
    for user in users_with_images:
        print(f"User {user.id}: {user.username} - Profile image: {user.profile_image}") 