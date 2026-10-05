"""
backend/scripts/init_postgres_schema.py
Initializes all PostgreSQL tables in the live container and verifies table creation.
"""

import sys
import os
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

os.environ["DATABASE_URL"] = "postgresql+psycopg2://kalyan:kalyan_secure_pass_2026@localhost:5432/kalyan_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from backend.app.core.config import settings
settings.DATABASE_URL = "postgresql+psycopg2://kalyan:kalyan_secure_pass_2026@localhost:5432/kalyan_db"
settings.REDIS_URL = "redis://localhost:6379/0"

from backend.app.core.database import init_db
init_db()

import psycopg2
conn = psycopg2.connect(
    dbname="kalyan_db",
    user="kalyan",
    password="kalyan_secure_pass_2026",
    host="localhost",
    port=5432
)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
tables = [t[0] for t in cur.fetchall()]
print(f"SUCCESS: {len(tables)} tables created in PostgreSQL 'kalyan_db':")
for t in tables:
    print(f"  - {t}")
conn.close()
