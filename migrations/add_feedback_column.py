"""
Migration script to add feedback column to applications table
"""

from app import db
from sqlalchemy import Column, Text

def upgrade():
    """Add feedback column to applications table."""
    try:
        # Check if the column already exists
        columns = [column.name for column in db.engine.execute("PRAGMA table_info(applications)").fetchall()]
        if 'feedback' not in columns:
            db.engine.execute("ALTER TABLE applications ADD COLUMN feedback TEXT")
            print("Successfully added feedback column to applications table")
        else:
            print("Feedback column already exists in applications table")
    except Exception as e:
        print(f"Error adding feedback column: {str(e)}")
        raise

if __name__ == "__main__":
    upgrade() 