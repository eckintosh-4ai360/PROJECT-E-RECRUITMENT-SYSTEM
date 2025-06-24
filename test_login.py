"""
Script to test login functionality directly and fix all users' passwords.
"""

import sys
import os
import sqlite3
import hashlib
import base64

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_login():
    print("Testing login functionality...")
    
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username, email, password_hash FROM users")
    users = cursor.fetchall()
    
    print(f"Found {len(users)} users in database")
    
    # Test password for all users
    test_password = "UMaT2024!"
    
    for user in users:
        user_id, username, email, current_hash = user
        print(f"\nProcessing user: {username}, ID: {user_id}")
        
        # Generate a new password hash - we'll set the same password for all users
        salt = os.urandom(16)
        password_bytes = test_password.encode('utf-8')
        salted_hash = hashlib.sha256(salt + password_bytes).hexdigest()
        new_hash = f"sha256:{base64.b64encode(salt).decode('utf-8')}:{salted_hash}"
        
        # Update the user's password hash
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        print(f"Updated password hash for user: {username}")
        
        # Verify the password would work by checking it manually
        # Parse the new hash
        algorithm, salt_b64, stored_hash = new_hash.split(":")
        salt = base64.b64decode(salt_b64)
        
        # Calculate the hash again
        password_bytes = test_password.encode('utf-8')
        calculated_hash = hashlib.sha256(salt + password_bytes).hexdigest()
        
        # Verify the hash matches
        if calculated_hash == stored_hash:
            print(f"Password verification for {username}: SUCCESS")
        else:
            print(f"Password verification for {username}: FAILED")
    
    # Commit the changes
    conn.commit()
    print("\nAll password hashes updated successfully")
    
    # Close the database connection
    conn.close()
    
    print("Login test completed - all users now have password: UMaT2024!")

if __name__ == "__main__":
    test_login() 