from flask import Flask, request, jsonify
import psycopg2
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Database Connection
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# Ensure Table Schema is Correct
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        columns = [
            "open_charts INT", "ea_names TEXT", "traded_pairs TEXT", "deposit_withdrawal FLOAT",
            "margin_percent FLOAT", "realized_pl_daily FLOAT", "realized_pl_weekly FLOAT",
            "realized_pl_monthly FLOAT", "realized_pl_yearly FLOAT"
        ]
        for col in columns:
            cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated: Added missing columns.")
    except Exception as e:
        logger.error(f"❌ Database schema update error: {str(e)}")

# Receive Data from MT4
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # ✅ Force JSON Parsing Regardless of Content-Type
        raw_data = request.get_json(force=True)
        
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
        realized_pl_daily = raw_data["realized_pl_daily"]
        realized_pl_weekly = raw_data["realized_pl_weekly"]
        realized_pl_monthly = raw_data["realized_pl_monthly"]
        realized_pl_yearly = raw_data["realized_pl_yearly"]

        # ✅ Insert/Update Database
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(""" UPDATE accounts SET
                        balance = %s, equity = %s, free_margin = %s, profit_loss = %s,
                        realized_pl_daily = %s, realized_pl_weekly = %s,
                        realized_pl_monthly = %s, realized_pl_yearly = %s
                        WHERE account_number = %s""",
                    (balance, equity, free_margin, profit_loss, realized_pl_daily,
                     realized_pl_weekly, realized_pl_monthly, realized_pl_yearly, account_number))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Retrieve Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT broker, account_number, balance, equity, free_margin, profit_loss, open_charts, 
                   ea_names, traded_pairs, deposit_withdrawal, margin_percent, realized_pl_daily, 
                   realized_pl_weekly, realized_pl_monthly, realized_pl_yearly FROM accounts
            ORDER BY profit_loss ASC;
        """)
        
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({"accounts": [dict(zip([col.name for col in cur.description], row)) for row in accounts]})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
