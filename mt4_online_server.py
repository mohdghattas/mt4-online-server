from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re
from datetime import datetime
import pytz  # Add pytz for timezone handling

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

# Create tables if they don’t exist (assuming history table already exists)
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
                autotrading BOOLEAN DEFAULT FALSE
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
                logs JSON
            );
        """)
        # Assuming history table exists; if not, uncomment and adjust schema as needed
        # cur.execute("""
        #     CREATE TABLE IF NOT EXISTS history (
        #         id SERIAL PRIMARY KEY,
        #         account_number BIGINT NOT NULL,
        #         timestamp TIMESTAMP NOT NULL,
        #         balance DOUBLE PRECISION,
        #         equity DOUBLE PRECISION,
        #         profit_loss DOUBLE PRECISION,
        #         realized_pl_daily DOUBLE PRECISION,
        #         FOREIGN KEY (account_number) REFERENCES accounts(account_number)
        #     );
        # """)
        conn.commit()
        logger.info("Tables created or already exist: accounts, settings")
    except Exception as e:
        logger.error(f"Table creation failed: {e}")
    finally:
        cur.close()
        conn.close()

# Ensure all columns exist in accounts table
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
                logger.info(f"Adding missing column to accounts: {column}")
                cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {column} {col_type};")
        conn.commit()
        logger.info("All expected columns ensured in accounts table")
    except Exception as e:
        logger.error(f"Column check/creation failed: {e}")
    finally:
        cur.close()
        conn.close()

# Clean raw data
def clean_json_string(raw_data):
    decoded = raw_data.decode("utf-8", errors="replace")
    cleaned = re.sub(r'[^\x20-\x7E]', '', decoded)
    return cleaned.strip()

# API Endpoint to receive MT4 data
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

# API Endpoint to retrieve accounts data
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

# API Endpoint to retrieve settings
@app.route("/api/settings", methods=["GET"])
def get_settings():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            SELECT sort_state, is_numbers_masked, gmt_offset, period_resets,
                   main_refresh_rate, critical_margin, warning_margin, is_dark_mode,
                   mask_timer, font_size, notes, logs
            FROM settings WHERE user_id = 'default';
        """)
        settings = cur.fetchone()
        cur.close()
        conn.close()
        if settings:
            columns = [desc[0] for desc in cur.description]
            return jsonify(dict(zip(columns, settings)))
        return jsonify({})
    except Exception as e:
        logger.error(f"Settings Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API Endpoint to save settings
@app.route("/api/settings", methods=["POST"])
def save_settings():
    try:
        settings = request.get_json()
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO settings (
                user_id, sort_state, is_numbers_masked, gmt_offset, period_resets,
                main_refresh_rate, critical_margin, warning_margin, is_dark_mode,
                mask_timer, font_size, notes, logs
            ) VALUES ('default', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                sort_state = EXCLUDED.sort_state,
                is_numbers_masked = EXCLUDED.is_numbers_masked,
                gmt_offset = EXCLUDED.gmt_offset,
                period_resets = EXCLUDED.period_resets,
                main_refresh_rate = EXCLUDED.main_refresh_rate,
                critical_margin = EXCLUDED.critical_margin,
                warning_margin = EXCLUDED.warning_margin,
                is_dark_mode = EXCLUDED.is_dark_mode,
                mask_timer = EXCLUDED.mask_timer,
                font_size = EXCLUDED.font_size,
                notes = EXCLUDED.notes,
                logs = EXCLUDED.logs;
        """, (
            json.dumps(settings.get('sortState', {})),
            settings.get('isNumbersMasked', False),
            settings.get('gmtOffset', 3),
            json.dumps(settings.get('periodResets', {})),
            settings.get('mainRefreshRate', 5),
            settings.get('criticalMargin', 0),
            settings.get('warningMargin', 500),
            settings.get('isDarkMode', False),
            settings.get('maskTimer', '300'),
            settings.get('fontSize', '14'),
            json.dumps(settings.get('notes', {})),
            json.dumps(settings.get('logs', []))
        ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Settings saved successfully")
        return jsonify({"message": "Settings saved"}), 200
    except Exception as e:
        logger.error(f"Settings Save Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API Endpoint to save historical data (assuming existing history table)
@app.route("/api/history", methods=["POST"])
def save_history():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            data = [data]  # Handle single or multiple records
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()

        # Assuming history table has these columns; adjust if different
        for entry in data:
            # Convert timestamp to UTC
            local_tz = pytz.timezone('Asia/Beirut')
            local_time = datetime.strptime(entry['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC)
            utc_time = local_time.astimezone(pytz.UTC)
            cur.execute("""
                INSERT INTO history (account_number, timestamp, balance, equity, profit_loss, realized_pl_daily)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                entry['account_number'],
                utc_time,
                entry.get('balance'),
                entry.get('equity'),
                entry.get('profit_loss'),
                entry.get('realized_pl_daily')
            ))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"History saved for {len(data)} accounts")
        return jsonify({"message": "History saved"}), 200
    except Exception as e:
        logger.error(f"History Save Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API Endpoint to retrieve historical data
@app.route("/api/history", methods=["GET"])
def get_history():
    try:
        account = request.args.get('account')
        start = request.args.get('start')
        end = request.args.get('end')
        broker = request.args.get('broker')
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()
        query = "SELECT h.account_number, h.timestamp, h.balance, h.equity, h.profit_loss, h.realized_pl_daily, a.broker " \
                "FROM history h JOIN accounts a ON h.account_number = a.account_number WHERE 1=1"
        params = []
        if account:
            query += " AND h.account_number = %s"
            params.append(account)
        if start:
            query += " AND h.timestamp >= %s"
            params.append(start)
        if end:
            query += " AND h.timestamp <= %s"
            params.append(end)
        if broker:
            query += " AND a.broker = %s"
            params.append(broker)
        cur.execute(query, params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return jsonify({"history": [dict(zip(columns, row)) for row in rows]})
    except Exception as e:
        logger.error(f"History Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

# Run table creation and column checks on startup
create_tables()
ensure_columns()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
