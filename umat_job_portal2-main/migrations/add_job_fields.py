"""Add required_skills and closing_date fields to jobs table

Revision ID: add_job_fields
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add required_skills column
    op.add_column('jobs', sa.Column('required_skills', sa.Text(), nullable=True))
    # Add closing_date column
    op.add_column('jobs', sa.Column('closing_date', sa.DateTime(), nullable=True))

def downgrade():
    # Remove the columns in reverse order
    op.drop_column('jobs', 'closing_date')
    op.drop_column('jobs', 'required_skills') 