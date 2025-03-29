from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

DB_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

def create_tables():
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot create tables: No database connection")
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
                autotrading BOOLEAN DEFAULT FALSE,
                swap_daily DOUBLE PRECISION DEFAULT 0,
                swap_weekly DOUBLE PRECISION DEFAULT 0,
                swap_monthly DOUBLE PRECISION DEFAULT 0,
                swap_yearly DOUBLE PRECISION DEFAULT 0,
                swap_alltime DOUBLE PRECISION DEFAULT 0,
                deposits_daily DOUBLE PRECISION DEFAULT 0,
                deposits_weekly DOUBLE PRECISION DEFAULT 0,
                deposits_monthly DOUBLE PRECISION DEFAULT 0,
                deposits_yearly DOUBLE PRECISION DEFAULT 0,
                withdrawals_daily DOUBLE PRECISION DEFAULT 0,
                withdrawals_weekly DOUBLE PRECISION DEFAULT 0,
                withdrawals_monthly DOUBLE PRECISION DEFAULT 0,
                withdrawals_yearly DOUBLE PRECISION DEFAULT 0,
                prev_day_pl DOUBLE PRECISION DEFAULT 0,
                prev_day_holding_fee DOUBLE PRECISION DEFAULT 0
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                user_id TEXT PRIMARY KEY,
                sort_state JSON,
                is_numbers_masked BOOLEAN DEFAULT FALSE,
                gmt_offset INTEGER DEFAULT 3,
                period_resets JSON,
                main_refresh_rate INTEGER DEFAULT 5,
                critical_margin INTEGER DEFAULT 0,
                warning_margin INTEGER DEFAULT 500,
                is_dark_mode BOOLEAN DEFAULT FALSE,
                mask_timer TEXT DEFAULT '300',
                font_size TEXT DEFAULT '14',
                notes JSON,
                broker_offsets JSON DEFAULT '{"Raw Trading Ltd": -5, "Swissquote": -1, "XTB International": -6}'
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                account_number BIGINT,
                balance DOUBLE PRECISION,
                equity DOUBLE PRECISION,
                margin_used DOUBLE PRECISION,
                free_margin DOUBLE PRECISION,
                margin_level DOUBLE PRECISION,
                open_trade INTEGER,
                profit_loss DOUBLE PRECISION,
                open_charts INTEGER,
                deposit_withdrawal DOUBLE PRECISION,
                margin_percent DOUBLE PRECISION,
                realized_pl_daily DOUBLE PRECISION,
                realized_pl_weekly DOUBLE PRECISION,
                realized_pl_monthly DOUBLE PRECISION,
                realized_pl_yearly DOUBLE PRECISION,
                autotrading BOOLEAN,
                empty_charts INTEGER,
                deposits_alltime DOUBLE PRECISION,
                withdrawals_alltime DOUBLE PRECISION,
                realized_pl_alltime DOUBLE PRECISION,
                holding_fee_daily DOUBLE PRECISION,
                broker TEXT,
                traded_pairs TEXT,
                open_pairs_charts TEXT,
                ea_names TEXT,
                snapshot_time TIMESTAMP WITH TIME ZONE,
                last_update TIMESTAMP WITH TIME ZONE
            );
        """)
        conn.commit()
        logger.info("Tables created or already exist: accounts, settings, history")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
    finally:
        cur.close()
        conn.close()

def clean_json_string(raw_data):
    decoded = raw_data.decode("utf-8", errors="replace")
    cleaned = re.sub(r'[^\x20-\x7E]', '', decoded)
    return cleaned.strip()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = clean_json_string(request.data)
        logger.debug(f"Raw Request Data: {raw_data}")
        json_data = json.loads(raw_data)
        required_fields = [
            "broker", "account_number", "balance", "equity", "margin_used",
            "free_margin", "margin_percent", "profit_loss", "realized_pl_daily",
            "realized_pl_weekly", "realized_pl_monthly", "realized_pl_yearly",
            "realized_pl_alltime", "deposits_alltime", "withdrawals_alltime",
            "holding_fee_daily", "holding_fee_weekly", "holding_fee_monthly",
            "holding_fee_yearly", "holding_fee_alltime", "open_charts",
            "empty_charts", "open_trades", "autotrading", "swap_daily",
            "swap_weekly", "swap_monthly", "swap_yearly", "swap_alltime",
            "deposits_daily", "deposits_weekly", "deposits_monthly",
            "deposits_yearly", "withdrawals_daily", "withdrawals_weekly",
            "withdrawals_monthly", "withdrawals_yearly", "prev_day_pl",
            "prev_day_holding_fee"
        ]
        for field in required_fields:
            if field not in json_data:
                logger.error(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Explicitly convert autotrading to Python boolean
        json_data["autotrading"] = json_data["autotrading"] == "true" or json_data["autotrading"] == True
        
        conn = get_db_connection()
        if not conn:
            logger.error("❌ No database connection")
            return jsonify({"error": "Database connection failed"}), 500
        
        logger.debug("Database connection established")
        cur = conn.cursor()
        
        logger.debug("Executing INSERT/UPDATE query")
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                deposits_alltime, withdrawals_alltime, holding_fee_daily,
                holding_fee_weekly, holding_fee_monthly, holding_fee_yearly,
                holding_fee_alltime, open_charts, empty_charts, open_trades,
                autotrading, swap_daily, swap_weekly, swap_monthly, swap_yearly,
                swap_alltime, deposits_daily, deposits_weekly, deposits_monthly,
                deposits_yearly, withdrawals_daily, withdrawals_weekly,
                withdrawals_monthly, withdrawals_yearly, prev_day_pl,
                prev_day_holding_fee
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker, balance = EXCLUDED.balance,
                equity = EXCLUDED.equity, margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                margin_percent = EXCLUDED.margin_percent,
                profit_loss = EXCLUDED.profit_loss,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl
