import sqlite3
import os

# Connect to the SQLite database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Get all users with profile images
cursor.execute("SELECT id, username, profile_image FROM users WHERE profile_image IS NOT NULL")
users = cursor.fetchall()

print(f"Found {len(users)} users with profile images:")
for user in users:
    user_id, username, profile_image = user
    print(f"User ID: {user_id}, Username: {username}, Profile Image: {profile_image}")
    
    # Check if the profile_image path ends with .jpg.jpg or similar duplicated extension
    if '.jpg.jpg' in profile_image:
        # Remove the duplicated extension
        fixed_path = profile_image.replace('.jpg.jpg', '.jpg')
        print(f"  - Fixing path: {profile_image} -> {fixed_path}")
        
        # Update the database
        cursor.execute("UPDATE users SET profile_image = ? WHERE id = ?", (fixed_path, user_id))
        conn.commit()
        print(f"  - Updated profile image path for user {user_id}")

# Close the connection
conn.commit()
conn.close()

print("Profile image path fixing completed.") 