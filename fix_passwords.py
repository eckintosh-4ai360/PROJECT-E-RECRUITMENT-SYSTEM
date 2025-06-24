import sqlite3
import os
import hashlib
import base64

def generate_password_hash(password):
    """Generate a SHA-256 password hash compatible with Python 3.13."""
    salt = os.urandom(16)  # 16 bytes of random salt
    password_bytes = password.encode('utf-8')
    salted_hash = hashlib.sha256(salt + password_bytes).hexdigest()
    # Store as algorithm:salt:hash
    return f"sha256:{base64.b64encode(salt).decode('utf-8')}:{salted_hash}"

def fix_passwords():
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Set a temporary known password for all users
    temp_password = "UMaT2024!"
    new_hash = generate_password_hash(temp_password)
    
    try:
        # Get all users first
        cursor.execute("SELECT id, username, email FROM users")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database.")
            return
            
        print(f"Found {len(users)} users. Resetting passwords...")
        
        # Update each user with a unique salt
        for user_id, username, email in users:
            # Generate a new hash with a unique salt for each user
            user_hash = generate_password_hash(temp_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (user_hash, user_id))
            print(f"Reset password for user: {username} ({email})")
        
        conn.commit()
        print("\nAll passwords have been reset to: UMaT2024!")
        print("Please inform users to change their passwords upon next login.")
        
    except Exception as e:
        print(f"Error updating passwords: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_passwords() 