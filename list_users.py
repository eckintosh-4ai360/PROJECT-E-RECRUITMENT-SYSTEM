import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Query to get all users with their profile images and password hashes
cursor.execute("SELECT id, username, email, password_hash, profile_image FROM users")
users = cursor.fetchall()

print(f"Found {len(users)} users:")
for user in users:
    user_id, username, email, password_hash, profile_image = user
    print(f"\nUser ID: {user_id}")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password Hash: {password_hash}")
    print(f"Profile Image: {profile_image}")
    print("-" * 80)

# Close the connection
conn.close() 