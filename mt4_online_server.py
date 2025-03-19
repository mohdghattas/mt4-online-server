from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

DB_URL = os.getenv("DATABASE_URL")

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

# Create the accounts table if it doesn't exist
def create_table():
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot create table: No database connection")
        return
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                broker TEXT NOT NULL,
                account_number BIGINT PRIMARY KEY,
                balance DOUBLE PRECISION DEFAULT 0,
                equity DOUBLE PRECISION DEFAULT 0,
                margin_used DOUBLE PRECISION DEFAULT 0,
                free_margin DOUBLE PRECISION DEFAULT 0,
                margin_percent DOUBLE PRECISION DEFAULT 0,
                profit_loss DOUBLE PRECISION DEFAULT 0,
                realized_pl_daily DOUBLE PRECISION DEFAULT 0,
                realized_pl_weekly DOUBLE PRECISION DEFAULT 0,
                realized_pl_monthly DOUBLE PRECISION DEFAULT 0,
                realized_pl_yearly DOUBLE PRECISION DEFAULT 0,
                realized_pl_alltime DOUBLE PRECISION DEFAULT 0,
                deposits_alltime DOUBLE PRECISION DEFAULT 0,
                withdrawals_alltime DOUBLE PRECISION DEFAULT 0,
                holding_fee_daily DOUBLE PRECISION DEFAULT 0,
                holding_fee_weekly DOUBLE PRECISION DEFAULT 0,
                holding_fee_monthly DOUBLE PRECISION DEFAULT 0,
                holding_fee_yearly DOUBLE PRECISION DEFAULT 0,
                holding_fee_alltime DOUBLE PRECISION DEFAULT 0,
                open_charts INTEGER DEFAULT 0,
                empty_charts INTEGER DEFAULT 0,
                open_trades INTEGER DEFAULT 0,
                autotrading BOOLEAN DEFAULT FALSE
            );
        """)
        conn.commit()
        logger.info("Accounts table created or already exists")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
    finally:
        cur.close()
        conn.close()

# Ensure all columns exist
def ensure_columns():
    expected_columns = {
        "realized_pl_alltime": "DOUBLE PRECISION DEFAULT 0",
        "deposits_alltime": "DOUBLE PRECISION DEFAULT 0",
        "withdrawals_alltime": "DOUBLE PRECISION DEFAULT 0",
        "holding_fee_daily": "DOUBLE PRECISION DEFAULT 0",
        "holding_fee_weekly": "DOUBLE PRECISION DEFAULT 0",
        "holding_fee_monthly": "DOUBLE PRECISION DEFAULT 0",
        "holding_fee_yearly": "DOUBLE PRECISION DEFAULT 0",
        "holding_fee_alltime": "DOUBLE PRECISION DEFAULT 0"
    }
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot ensure columns: No database connection")
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'accounts';")
        existing_columns = {row[0] for row in cur.fetchall()}
        for column, col_type in expected_columns.items():
            if column not in existing_columns:
                logger.info(f"Adding missing column: {column}")
                cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {column} {col_type};")
        conn.commit()
        logger.info("All expected columns ensured")
    except Exception as e:
        logger.error(f"Column check/creation failed: {e}")
    finally:
        cur.close()
        conn.close()

# API Endpoint
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace").strip()  # Fix: Trim extra characters
        logger.debug(f"Raw Request Data: {raw_data}")
        json_data = json.loads(raw_data)

        required_fields = [
            "broker", "account_number", "balance", "equity", "margin_used",
            "free_margin", "margin_percent", "profit_loss", "realized_pl_daily",
            "realized_pl_weekly", "realized_pl_monthly", "realized_pl_yearly",
            "realized_pl_alltime", "deposits_alltime", "withdrawals_alltime",
            "holding_fee_daily", "holding_fee_weekly", "holding_fee_monthly",
            "holding_fee_yearly", "holding_fee_alltime", "open_charts",
            "empty_charts", "open_trades", "autotrading"
        ]
        for field in required_fields:
            if field not in json_data:
                logger.error(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                deposits_alltime, withdrawals_alltime,
                holding_fee_daily, holding_fee_weekly, holding_fee_monthly,
                holding_fee_yearly, holding_fee_alltime, open_charts,
                empty_charts, open_trades, autotrading
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_percent = EXCLUDED.margin_percent,
                profit_loss = EXCLUDED.profit_loss,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                realized_pl_yearly = EXCLUDED.realized_pl_yearly,
                realized_pl_alltime = EXCLUDED.realized_pl_alltime,
                deposits_alltime = EXCLUDED.deposits_alltime,
                withdrawals_alltime = EXCLUDED.withdrawals_alltime,
                holding_fee_daily = EXCLUDED.holding_fee_daily,
                holding_fee_weekly = EXCLUDED.holding_fee_weekly,
                holding_fee_monthly = EXCLUDED.holding_fee_monthly,
                holding_fee_yearly = EXCLUDED.holding_fee_yearly,
                holding_fee_alltime = EXCLUDED.holding_fee_alltime,
                open_charts = EXCLUDED.open_charts,
                empty_charts = EXCLUDED.empty_charts,
                open_trades = EXCLUDED.open_trades,
                autotrading = EXCLUDED.autotrading;
        """, tuple(json_data[field] for field in required_fields))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Data stored successfully for account {json_data['account_number']}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin,
                   margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                   realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                   deposits_alltime, withdrawals_alltime, holding_fee_daily, 
                   holding_fee_weekly, holding_fee_monthly, holding_fee_yearly,
                   holding_fee_alltime, open_charts, empty_charts, open_trades, autotrading
            FROM accounts;
        """)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return jsonify({"accounts": [dict(zip(columns, row)) for row in rows]})
    except Exception as e:
        logger.error(f"API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

# Run table creation and column checks on startup
create_table()
ensure_columns()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
