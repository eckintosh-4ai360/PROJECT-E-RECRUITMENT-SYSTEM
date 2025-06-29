"""Add cover letter file column

Revision ID: add_cover_letter_file
Create Date: 2024-03-21
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('applications', sa.Column('cover_letter_file', sa.String(512), nullable=True))

def downgrade():
    op.drop_column('applications', 'cover_letter_file') 