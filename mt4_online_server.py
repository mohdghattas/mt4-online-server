from flask import Flask, request, jsonify
import psycopg2
import logging
import os

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Database connection function
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# Ensure all required columns exist
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_number BIGINT PRIMARY KEY,
                broker TEXT DEFAULT 'Unknown',
                balance FLOAT DEFAULT 0.0,
                equity FLOAT DEFAULT 0.0,
                free_margin FLOAT DEFAULT 0.0,
                profit_loss FLOAT DEFAULT 0.0,
                open_charts INT DEFAULT 0,
                ea_names TEXT DEFAULT '',
                traded_pairs TEXT DEFAULT '',
                deposit_withdrawal FLOAT DEFAULT 0.0,
                margin_percent FLOAT DEFAULT 0.0,
                realized_pl_daily FLOAT DEFAULT 0.0,
                realized_pl_weekly FLOAT DEFAULT 0.0,
                realized_pl_monthly FLOAT DEFAULT 0.0,
                realized_pl_yearly FLOAT DEFAULT 0.0
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema ensured successfully.")
    except Exception as e:
        logger.error(f"❌ Database schema error: {str(e)}")

# API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_json()
        if not raw_data:
            return jsonify({"error": "Invalid JSON format"}), 400

        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # Extract Data
        broker = raw_data.get("broker", "Unknown")
        account_number = raw_data["account_number"]
        balance = raw_data["balance"]
        equity = raw_data["equity"]
        free_margin = raw_data["free_margin"]
        profit_loss = raw_data["profit_loss"]
        open_charts = raw_data.get("open_charts", 0)
        ea_names = raw_data.get("ea_names", "")
        traded_pairs = raw_data.get("traded_pairs", "")
        deposit_withdrawal = raw_data.get("deposit_withdrawal", 0.0)
        margin_percent = raw_data.get("margin_percent", 0.0)
        realized_pl_daily = raw_data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = raw_data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = raw_data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = raw_data.get("realized_pl_yearly", 0.0)

        conn = get_db_connection()
        cur = conn.cursor()

        # **Force Full Update**
        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss,
                                  open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
                                  realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE
            SET broker = EXCLUDED.broker,
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
                realized_pl_yearly = EXCLUDED.realized_pl_yearly
            RETURNING *;
        """, (broker, account_number, balance, equity, free_margin, profit_loss,
              open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
              realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly))

        updated_row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully: {updated_row}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API Endpoint: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, free_margin, profit_loss,
                   open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
                   realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly
            FROM accounts ORDER BY profit_loss ASC;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [{
            "broker": row[0], "account_number": row[1], "balance": row[2], "equity": row[3],
            "free_margin": row[4], "profit_loss": row[5], "open_charts": row[6], "ea_names": row[7],
            "traded_pairs": row[8], "deposit_withdrawal": row[9], "margin_percent": row[10],
            "realized_pl_daily": row[11], "realized_pl_weekly": row[12], "realized_pl_monthly": row[13],
            "realized_pl_yearly": row[14]
        } for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
