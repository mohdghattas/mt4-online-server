from flask import Flask, request, jsonify
import psycopg2
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Ensure you use the correct database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://your_username:your_password@your_host:your_port/your_database")

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

# ✅ Check and create missing columns automatically
def ensure_columns_exist():
    conn = get_db_connection()
    if conn is None:
        return

    cur = conn.cursor()
    try:
        cur.execute("""
        ALTER TABLE accounts 
        ADD COLUMN IF NOT EXISTS broker TEXT DEFAULT 'Unknown Broker',
        ADD COLUMN IF NOT EXISTS open_charts INT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS ea_names TEXT DEFAULT '',
        ADD COLUMN IF NOT EXISTS traded_pairs TEXT DEFAULT '',
        ADD COLUMN IF NOT EXISTS deposit_withdrawal FLOAT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS margin_percent FLOAT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS realized_pl_daily FLOAT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS realized_pl_weekly FLOAT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS realized_pl_monthly FLOAT DEFAULT 0,
        ADD COLUMN IF NOT EXISTS realized_pl_yearly FLOAT DEFAULT 0;
        """)
        conn.commit()
    except Exception as e:
        logger.error(f"❌ Database Column Update Error: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    """Receives and processes data from the MT4 EA."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    ensure_columns_exist()

    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        try:
            data = request.get_json()
        except Exception as e:
            logger.error(f"❌ JSON Decoding Error: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        if not data:
            return jsonify({"error": "Received empty JSON data"}), 400

        # ✅ Debugging: Print parsed data
        logger.debug(f"✅ Parsed JSON Data: {data}")

        # Extract fields safely
        broker = data.get("broker", "Unknown Broker")
        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        free_margin = data.get("free_margin")
        profit_loss = data.get("profit_loss")
        open_charts = data.get("open_charts", 0)
        ea_names = data.get("ea_names", "")
        traded_pairs = data.get("traded_pairs", "")
        deposit_withdrawal = data.get("deposit_withdrawal", 0)
        margin_percent = data.get("margin_percent", 0.0)
        realized_pl_daily = data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = data.get("realized_pl_yearly", 0.0)

        # ✅ Debugging: Check Data Types
        logger.debug(f"📊 Data Types: {type(account_number)}, {type(balance)}, {type(equity)}, {type(profit_loss)}")

        # ✅ Check if required fields are missing
        required_fields = ["account_number", "balance", "equity", "profit_loss"]
        for field in required_fields:
            if data.get(field) is None:
                logger.error(f"❌ Missing required field: {field}")
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # ✅ Ensure all numeric values are properly formatted
        try:
            account_number = int(account_number)
            balance = float(balance)
            equity = float(equity)
            free_margin = float(free_margin)
            profit_loss = float(profit_loss)
            deposit_withdrawal = float(deposit_withdrawal)
            margin_percent = float(margin_percent)
            realized_pl_daily = float(realized_pl_daily)
            realized_pl_weekly = float(realized_pl_weekly)
            realized_pl_monthly = float(realized_pl_monthly)
            realized_pl_yearly = float(realized_pl_yearly)
        except ValueError as e:
            logger.error(f"❌ Data Conversion Error: {str(e)}")
            return jsonify({"error": "Data type conversion error"}), 400

        # ✅ Insert data into database
        cur = conn.cursor()
        query = """
        INSERT INTO accounts (
            broker, account_number, balance, equity, free_margin, profit_loss,
            open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
            realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (account_number) 
        DO UPDATE SET
            broker = EXCLUDED.broker,
            balance = EXCLUDED.balance,
            equity = EXCLUDED.equity,
            free_margin = EXCLUDED.free_margin,
            profit_loss = EXCLUDED.profit_loss,
            open_charts = EXCLUDED.open_charts,
            ea_names = EXCLUDED.ea_names,
            traded_pairs = EXCLUDED.traded_pairs,
            deposit_withdrawal = EXCLUDED.deposit_withdrawal,
            margin_percent = EXCLUDED.margin_percent,
            realized_pl_daily = EXCLUDED.realized_pl_daily,
            realized_pl_weekly = EXCLUDED.realized_pl_weekly,
            realized_pl_monthly = EXCLUDED.realized_pl_monthly,
            realized_pl_yearly = EXCLUDED.realized_pl_yearly;
        """

        cur.execute(query, (broker, account_number, balance, equity, free_margin, profit_loss,
                            open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
                            realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly))
        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ Data stored successfully")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    """Fetches all account data."""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    ensure_columns_exist()

    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts;")
        rows = cur.fetchall()

        accounts = []
        for row in rows:
            accounts.append({
                "broker": row[0], "account_number": row[1], "balance": row[2], "equity": row[3],
                "free_margin": row[4], "profit_loss": row[5], "open_charts": row[6], "ea_names": row[7],
                "traded_pairs": row[8], "deposit_withdrawal": row[9], "margin_percent": row[10],
                "realized_pl_daily": row[11], "realized_pl_weekly": row[12], "realized_pl_monthly": row[13],
                "realized_pl_yearly": row[14]
            })

        return jsonify({"accounts": accounts}), 200

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
