import argparse
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime, Float, Integer


TABLE_ORDER = [
    "users",
    "candidates",
    "jobs",
    "resumes",
    "applications",
    "job_matches",
    "interviews",
    "events",
    "assistant_interactions",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create the Neon schema and migrate data from SQLite into PostgreSQL."
    )
    parser.add_argument(
        "--source",
        default="app.db",
        help="Path to the SQLite database file. Defaults to app.db.",
    )
    parser.add_argument(
        "--target-url",
        default=os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL"),
        help="Target PostgreSQL URL. Defaults to DATABASE_URL_UNPOOLED, then DATABASE_URL.",
    )
    parser.add_argument(
        "--replace-target",
        action="store_true",
        help="Truncate the target app tables before importing. Use only when you want to overwrite Neon data.",
    )
    return parser.parse_args()


def load_sqlite_rows(sqlite_path, table_name):
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        cursor = connection.cursor()
        cursor.execute(f'SELECT * FROM "{table_name}"')
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def normalize_value(value, column_type):
    if value is None:
        return None

    if isinstance(column_type, Boolean):
        return bool(value)

    if isinstance(column_type, Integer):
        return int(value)

    if isinstance(column_type, Float):
        return float(value)

    if isinstance(column_type, DateTime):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)

    if isinstance(column_type, Date):
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)

    return value


def get_target_app(target_url):
    os.environ["DATABASE_URL"] = target_url

    from app import create_app, db
    import app.models  # noqa: F401 - ensure all models are registered before create_all

    app = create_app()
    return app, db


def get_row_count(connection, table_name):
    return connection.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar() or 0


def truncate_target_tables(connection):
    joined_tables = ", ".join(f'"{table}"' for table in reversed(TABLE_ORDER))
    connection.execute(text(f"TRUNCATE TABLE {joined_tables} RESTART IDENTITY CASCADE"))


def insert_rows(connection, inspector, table_name, rows):
    if not rows:
        return 0

    columns = inspector.get_columns(table_name)
    column_names = [column["name"] for column in columns if column["name"] in rows[0]]
    column_types = {column["name"]: column["type"] for column in columns}

    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {column: normalize_value(row[column], column_types[column]) for column in column_names}
        )

    column_sql = ", ".join(f'"{column}"' for column in column_names)
    value_sql = ", ".join(f":{column}" for column in column_names)
    statement = text(f'INSERT INTO "{table_name}" ({column_sql}) VALUES ({value_sql})')
    connection.execute(statement, normalized_rows)
    return len(normalized_rows)


def reset_sequences(connection, inspector):
    for table_name in TABLE_ORDER:
        pk = inspector.get_pk_constraint(table_name).get("constrained_columns") or []
        if len(pk) != 1:
            continue

        pk_name = pk[0]
        sequence_name = connection.execute(
            text("SELECT pg_get_serial_sequence(:table_name, :column_name)"),
            {"table_name": f"public.{table_name}", "column_name": pk_name},
        ).scalar()

        if not sequence_name:
            continue

        max_value = connection.execute(
            text(f'SELECT COALESCE(MAX("{pk_name}"), 0) FROM "{table_name}"')
        ).scalar() or 0

        if max_value > 0:
            connection.execute(text(f"SELECT setval('{sequence_name}', {max_value}, true)"))


def ensure_default_admin(app, db):
    from app.models import User, UserRole

    with app.app_context():
        admin_user = User.query.filter_by(role=UserRole.admin).first()
        if admin_user:
            print(f"Default admin present: {admin_user.email}")
            return

        print("Default admin missing. Creating admin@umat.edu.gh ...")
        admin_user = User(
            username="admin",
            email="admin@umat.edu.gh",
            first_name="Admin",
            last_name="User",
            role=UserRole.admin,
        )
        admin_user.set_password("adminpassword")
        db.session.add(admin_user)
        db.session.commit()


def main():
    load_dotenv()
    args = parse_args()

    sqlite_path = Path(args.source).resolve()
    if not sqlite_path.exists():
        raise SystemExit(f"SQLite database not found: {sqlite_path}")

    if not args.target_url:
        raise SystemExit("Target PostgreSQL URL not found. Set DATABASE_URL or DATABASE_URL_UNPOOLED.")

    print(f"Source SQLite DB: {sqlite_path}")
    print("Target PostgreSQL DB: configured from environment")

    app, db = get_target_app(args.target_url)

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names(schema="public")
        print("Target tables after schema init:", ", ".join(existing_tables) if existing_tables else "(none)")

        with db.engine.begin() as connection:
            target_counts = {table: get_row_count(connection, table) for table in TABLE_ORDER}
            has_existing_data = any(count > 0 for count in target_counts.values())

            if has_existing_data:
                if not args.replace_target:
                    existing_summary = ", ".join(
                        f"{table}={count}" for table, count in target_counts.items() if count > 0
                    )
                    raise SystemExit(
                        "Target database already has app data. "
                        f"Existing rows: {existing_summary}. Re-run with --replace-target to overwrite."
                    )

                print("Target database has existing rows. Truncating target tables before import...")
                truncate_target_tables(connection)

            inspector = inspect(db.engine)
            for table_name in TABLE_ORDER:
                rows = load_sqlite_rows(str(sqlite_path), table_name)
                inserted = insert_rows(connection, inspector, table_name, rows)
                print(f"Migrated {inserted} row(s) into {table_name}")

            reset_sequences(connection, inspector)

        ensure_default_admin(app, db)

        with db.engine.connect() as connection:
            print("Verification counts from PostgreSQL:")
            for table_name in TABLE_ORDER:
                print(f"  {table_name}: {get_row_count(connection, table_name)}")


if __name__ == "__main__":
    main()
