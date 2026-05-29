import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)


SCHEMA_COLUMNS = {
    "resumes": {
        "is_primary": {
            "postgresql": "ALTER TABLE resumes ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE",
            "sqlite": "ALTER TABLE resumes ADD COLUMN is_primary BOOLEAN DEFAULT 0",
        },
    },
    "jobs": {
        "required_skills": {
            "postgresql": "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS required_skills TEXT",
            "sqlite": "ALTER TABLE jobs ADD COLUMN required_skills TEXT",
        },
        "closing_date": {
            "postgresql": "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS closing_date TIMESTAMP",
            "sqlite": "ALTER TABLE jobs ADD COLUMN closing_date DATETIME",
        },
    },
    "applications": {
        "cover_letter_file": {
            "postgresql": "ALTER TABLE applications ADD COLUMN IF NOT EXISTS cover_letter_file VARCHAR(512)",
            "sqlite": "ALTER TABLE applications ADD COLUMN cover_letter_file VARCHAR(512)",
        },
        "feedback": {
            "postgresql": "ALTER TABLE applications ADD COLUMN IF NOT EXISTS feedback TEXT",
            "sqlite": "ALTER TABLE applications ADD COLUMN feedback TEXT",
        },
    },
    "interviews": {
        "interview_level": {
            "postgresql": "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS interview_level VARCHAR(50) DEFAULT 'department' NOT NULL",
            "sqlite": "ALTER TABLE interviews ADD COLUMN interview_level VARCHAR(50) DEFAULT 'department' NOT NULL",
        },
        "level_status": {
            "postgresql": "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS level_status VARCHAR(50) DEFAULT 'pending' NOT NULL",
            "sqlite": "ALTER TABLE interviews ADD COLUMN level_status VARCHAR(50) DEFAULT 'pending' NOT NULL",
        },
        "next_level_date": {
            "postgresql": "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS next_level_date TIMESTAMP",
            "sqlite": "ALTER TABLE interviews ADD COLUMN next_level_date DATETIME",
        },
        "interviewer_notes": {
            "postgresql": "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS interviewer_notes TEXT",
            "sqlite": "ALTER TABLE interviews ADD COLUMN interviewer_notes TEXT",
        },
        "interviewer_id": {
            "postgresql": "ALTER TABLE interviews ADD COLUMN IF NOT EXISTS interviewer_id INTEGER",
            "sqlite": "ALTER TABLE interviews ADD COLUMN interviewer_id INTEGER",
        },
    },
}


def ensure_schema_compatibility(db):
    """Add app columns that older deployed databases may be missing."""
    engine = db.engine
    dialect = engine.dialect.name
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table_name, columns in SCHEMA_COLUMNS.items():
            if table_name not in existing_tables:
                continue

            existing_columns = {
                column["name"]
                for column in inspector.get_columns(table_name)
            }

            for column_name, sql_by_dialect in columns.items():
                if column_name in existing_columns:
                    continue

                statement = sql_by_dialect.get(dialect)
                if not statement:
                    logger.warning("No schema compatibility SQL for %s.%s on %s", table_name, column_name, dialect)
                    continue

                logger.warning("Adding missing database column %s.%s", table_name, column_name)
                connection.execute(text(statement))
