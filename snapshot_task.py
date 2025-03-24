# snapshot_task.py

import psycopg2
import os
import logging
from datetime import datetime
from pytz import timezone

# Configs
DB_URL = os.getenv("DATABASE_URL")
BEIRUT_TZ = timezone("Asia/Beirut")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_snapshot")

def get_db_connection():
    conn = psycopg2.connect(DB_URL, sslmode="require")
    return conn

def sync_history_columns():
    """Ensure history table has same columns as accounts."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Get columns from accounts table
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='accounts';")
    account_columns = {row[0]: row[1] for row in cur.fetchall()}

    # Get columns from history table
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='history';")
    history_columns = {row[0] for row in cur.fetchall()}

    # Add missing columns to history
    for col, dtype in account_columns.items():
        if col not in history_columns:
            logger.info(f"Adding missing column '{col}' to history table")
            sql_dtype = "DOUBLE PRECISION DEFAULT 0"
            if dtype == 'bigint':
                sql_dtype = "BIGINT"
            elif dtype == 'boolean':
                sql_dtype = "BOOLEAN DEFAULT FALSE"
            elif dtype == 'text':
                sql_dtype = "TEXT"
            cur.execute(f"ALTER TABLE history ADD COLUMN {col} {sql_dtype};")

    # Add snapshot_time column if missing
    if 'snapshot_time' not in history_columns:
        logger.info("Adding 'snapshot_time' column to history table")
        cur.execute("ALTER TABLE history ADD COLUMN snapshot_time TIMESTAMP;")

    conn.commit()
    cur.close()
    conn.close()


def insert_daily_snapshots():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get Beirut time
    beirut_now = datetime.now(BEIRUT_TZ)

    # Fetch all accounts
    cur.execute("SELECT * FROM accounts;")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    for row in rows:
        data = dict(zip(columns, row))
        data['snapshot_time'] = beirut_now

        placeholders = ','.join(['%s'] * len(data))
        cols = ','.join(data.keys())
        values = list(data.values())

        cur.execute(f"INSERT INTO history ({cols}) VALUES ({placeholders});", values)

    conn.commit()
    logger.info(f"Inserted {len(rows)} daily snapshots at {beirut_now}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    sync_history_columns()
    insert_daily_snapshots()
