"""
Database migration to add Events table
"""

import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Event

def add_events_table():
    """Add Events table to the database."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the events table
            db.create_all()
            print("✅ Events table created successfully!")
            
            # Verify the table was created
            tables = db.engine.table_names()
            if 'events' in tables:
                print("✅ Events table confirmed in database")
            else:
                print("❌ Events table not found in database")
                
        except Exception as e:
            print(f"❌ Error creating events table: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("Creating Events table...")
    success = add_events_table()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
