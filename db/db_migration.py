# db_migration.py
# Simple migration script to add new columns to jobs table if missing
from sqlalchemy import create_engine, inspect, Column, String, Integer, text
from db.db_models import Base, Job
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../data/scheduler.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
inspector = inspect(engine)

with engine.connect() as conn:
    columns = [col['name'] for col in inspector.get_columns('jobs')]
    if 'partition' not in columns:
        conn.execute(text('ALTER TABLE jobs ADD COLUMN partition VARCHAR'))
    if 'est_run_time' not in columns:
        conn.execute(text('ALTER TABLE jobs ADD COLUMN est_run_time INTEGER'))
print("Migration complete.")
