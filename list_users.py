import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# Query to get all users with their profile images
cursor.execute("SELECT id, username, email, profile_image FROM users")
users = cursor.fetchall()

print(f"Found {len(users)} users:")
for user in users:
    user_id, username, email, profile_image = user
    print(f"User ID: {user_id}, Username: {username}, Email: {email}, Profile Image: {profile_image}")

# Close the connection
conn.close() 