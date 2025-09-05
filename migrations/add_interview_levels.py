"""Add interview levels migration"""

from app import db
from alembic import op
import sqlalchemy as sa
from datetime import datetime

def upgrade():
    # Add interview_level column
    op.add_column('interviews', sa.Column('interview_level', sa.String(50), nullable=False, server_default='department'))
    
    # Add level_status column to track status at each level
    op.add_column('interviews', sa.Column('level_status', sa.String(50), nullable=False, server_default='pending'))
    
    # Add next_level_date column to track when the next level interview is scheduled
    op.add_column('interviews', sa.Column('next_level_date', sa.DateTime, nullable=True))
    
    # Add interviewer_notes column for each level's feedback
    op.add_column('interviews', sa.Column('interviewer_notes', sa.Text, nullable=True))
    
    # Add interviewer_id column to track who conducted the interview
    op.add_column('interviews', sa.Column('interviewer_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True))

def downgrade():
    # Remove the added columns in reverse order
    op.drop_column('interviews', 'interviewer_id')
    op.drop_column('interviews', 'interviewer_notes')
    op.drop_column('interviews', 'next_level_date')
    op.drop_column('interviews', 'level_status')
    op.drop_column('interviews', 'interview_level') 