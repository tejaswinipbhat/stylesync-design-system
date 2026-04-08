import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://stylesync:stylesync@localhost:5432/stylesync")


def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Initialize database tables from schema.sql"""
    schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
    if not os.path.exists(schema_path):
        schema_path = "/app/database/schema.sql"

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if os.path.exists(schema_path):
                    with open(schema_path, "r") as f:
                        sql = f.read()
                    cur.execute(sql)
                conn.commit()
    except Exception as e:
        print(f"DB init warning: {e}")
