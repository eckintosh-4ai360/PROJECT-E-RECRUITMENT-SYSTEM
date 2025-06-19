import os
import shutil
from flask import Flask, current_app
from app import db, create_app
from app.models import User

def run_migration():
    """
    Migrate profile images from uploads folder to static/profile_images folder
    """
    app = create_app()
    with app.app_context():
        print("Starting profile image migration...")
        
        # Create profile_images directory if it doesn't exist
        profile_images_path = os.path.join(app.static_folder, 'profile_images')
        os.makedirs(profile_images_path, exist_ok=True)
        
        # Get all users with profile images
        users = User.query.filter(User.profile_image.isnot(None)).all()
        print(f"Found {len(users)} users with profile images to migrate")
        
        # Also check for any image files in the uploads directory
        uploads_dir = app.config["UPLOAD_FOLDER"]
        print(f"Checking for image files in: {uploads_dir}")
        
        # Supported image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        
        migrated = 0
        for user in users:
            try:
                # Check if the file exists in uploads folder
                upload_path = os.path.join(uploads_dir, user.profile_image)
                new_path = os.path.join(profile_images_path, user.profile_image)
                
                # Skip if the image is already in the right place
                if os.path.exists(new_path):
                    print(f"Image already migrated for user {user.id}: {user.profile_image}")
                    continue
                
                if os.path.exists(upload_path):
                    # Copy the file to the new location
                    shutil.copy2(upload_path, new_path)
                    print(f"Migrated image for user {user.id}: {user.profile_image}")
                    migrated += 1
                else:
                    print(f"Image not found for user {user.id}: {user.profile_image}")
            except Exception as e:
                print(f"Error migrating profile image for user {user.id}: {e}")
        
        # Check for image files in uploads directory that may not be linked to users
        # but could be profile images
        for filename in os.listdir(uploads_dir):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in image_extensions:
                try:
                    upload_path = os.path.join(uploads_dir, filename)
                    new_path = os.path.join(profile_images_path, filename)
                    
                    if not os.path.exists(new_path):
                        shutil.copy2(upload_path, new_path)
                        print(f"Migrated potential profile image: {filename}")
                        migrated += 1
                except Exception as e:
                    print(f"Error migrating potential profile image {filename}: {e}")
        
        print(f"Profile image migration completed. Migrated {migrated} images.")

if __name__ == "__main__":
    run_migration() 