"""
Script to check and fix the database directly.
"""

import sys
import os
import sqlite3
import hashlib
import base64

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def check_password_hash(stored_hash, password):
    """Check a password against a SHA-256 hash."""
    try:
        print(f"\n===DEBUG=== Starting password verification")
        print(f"===DEBUG=== Checking password hash: {stored_hash}")
        print(f"===DEBUG=== Input password length: {len(password)}")
        
        # Parse the stored hash
        parts = stored_hash.split(':')
        if len(parts) != 3:
            print(f"===DEBUG=== Invalid hash format, got {len(parts)} parts instead of 3")
            print(f"===DEBUG=== Hash parts: {parts}")
            return False
            
        algorithm, salt_b64, hash_value = parts
        
        print(f"===DEBUG=== Hash algorithm: {algorithm}")
        print(f"===DEBUG=== Salt (b64): {salt_b64}")
        print(f"===DEBUG=== Expected hash: {hash_value}")
        
        # Check if this is a new-style hash
        if algorithm == 'sha256':
            try:
                salt = base64.b64decode(salt_b64)
                print(f"===DEBUG=== Decoded salt: {salt!r}")
                password_bytes = password.encode('utf-8')
                print(f"===DEBUG=== Password bytes: {password_bytes!r}")
                
                # Create the combined bytes
                combined = salt + password_bytes
                print(f"===DEBUG=== Combined bytes to hash: {combined!r}")
                
                calculated_hash = hashlib.sha256(combined).hexdigest()
                print(f"===DEBUG=== Calculated hash: {calculated_hash}")
                print(f"===DEBUG=== Expected hash:  {hash_value}")
                result = calculated_hash == hash_value
                print(f"===DEBUG=== Hash match: {result}")
                return result
            except Exception as e:
                print(f"===DEBUG=== Error in SHA-256 hash calculation: {e}")
                return False
        else:
            print(f"===DEBUG=== Unsupported hash algorithm: {algorithm}")
            return False
    except Exception as e:
        print(f"===DEBUG=== Error checking password hash: {e}")
        return False

def check_database():
    print("Checking database structure and data...")
    
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    
    # Check users table
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nUsers table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check users data
        cursor.execute("SELECT id, username, email, role, password_hash FROM users")
        users = cursor.fetchall()
        
        print(f"\nFound {len(users)} users in database:")
        for user in users:
            user_id, username, email, role, password_hash = user
            print(f"\nUser ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Role: {role}")
            print(f"  Password hash: {password_hash}")
            
            # Test password verification
            test_password = "UMaT2024!"
            print(f"\nTesting password '{test_password}' for user {username}")
            is_valid = check_password_hash(password_hash, test_password)
            print(f"Password verification result: {is_valid}")
            
        conn.commit()
        
    except Exception as e:
        print(f"Error checking users table: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
    
    # Check candidate table
    try:
        cursor.execute("PRAGMA table_info(candidate)")
        columns = cursor.fetchall()
        print("\nCandidate table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check candidate data
        cursor.execute("""
            SELECT c.candidate_id, u.username, c.phone_number
            FROM candidate c
            JOIN users u ON c.candidate_id = u.id
        """)
        candidates = cursor.fetchall()
        
        print(f"\nFound {len(candidates)} candidates in database:")
        for candidate in candidates:
            candidate_id, username, phone_number = candidate
            print(f"Candidate ID: {candidate_id}")
            print(f"  Username: {username}")
            print(f"  Phone: {phone_number}")
            print("  " + "-" * 50)
            
    except Exception as e:
        print(f"Error checking candidate table: {e}")
    
    print("\nDatabase check completed")

if __name__ == "__main__":
    check_database() 