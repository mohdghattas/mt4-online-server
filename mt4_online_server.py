from flask import Flask, request, jsonify
import psycopg2
import logging
import os
import json
import traceback

app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Database connection function
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# Ensure necessary columns exist in the database
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        columns = [
            "open_charts INT", "ea_names TEXT", "traded_pairs TEXT", 
            "deposit_withdrawal FLOAT", "margin_percent FLOAT", 
            "realized_pl_daily FLOAT", "realized_pl_weekly FLOAT", 
            "realized_pl_monthly FLOAT", "realized_pl_yearly FLOAT", 
            "last_update TIMESTAMP DEFAULT NOW()"
        ]
        for col in columns:
            cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated: Added missing columns if needed.")
    except Exception as e:
        logger.error(f"❌ Database schema update error: {str(e)}")

# API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        if request.content_type != "application/json":
            return jsonify({"error": "Unsupported Media Type"}), 415

        raw_data = request.get_json()
        if not raw_data:
            return jsonify({"error": "Invalid JSON format"}), 400

        logger.debug(f"📥 Raw Request Data: {json.dumps(raw_data, indent=2)}")

        # Extract data
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

        # Insert or update data
        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, 
                                  open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent, 
                                  realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly, last_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (account_number) DO UPDATE SET 
                broker = EXCLUDED.broker, balance = EXCLUDED.balance, equity = EXCLUDED.equity, 
                free_margin = EXCLUDED.free_margin, profit_loss = EXCLUDED.profit_loss, 
                open_charts = EXCLUDED.open_charts, ea_names = EXCLUDED.ea_names, 
                traded_pairs = EXCLUDED.traded_pairs, deposit_withdrawal = EXCLUDED.deposit_withdrawal, 
                margin_percent = EXCLUDED.margin_percent, realized_pl_daily = EXCLUDED.realized_pl_daily, 
                realized_pl_weekly = EXCLUDED.realized_pl_weekly, realized_pl_monthly = EXCLUDED.realized_pl_monthly, 
                realized_pl_yearly = EXCLUDED.realized_pl_yearly, last_update = NOW();
        """, (broker, account_number, balance, equity, free_margin, profit_loss, open_charts, ea_names,
              traded_pairs, deposit_withdrawal, margin_percent, realized_pl_daily, realized_pl_weekly,
              realized_pl_monthly, realized_pl_yearly))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully: {json.dumps(raw_data, indent=2)}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# API Endpoint: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, free_margin, profit_loss, open_charts, 
                   ea_names, traded_pairs, deposit_withdrawal, margin_percent, realized_pl_daily, 
                   realized_pl_weekly, realized_pl_monthly, realized_pl_yearly, last_update
            FROM accounts
            ORDER BY profit_loss ASC;
        """)

        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [{
            "broker": row[0], "account_number": row[1], "balance": row[2], "equity": row[3], 
            "free_margin": row[4], "profit_loss": row[5], "open_charts": row[6], 
            "ea_names": row[7], "traded_pairs": row[8], "deposit_withdrawal": row[9], 
            "margin_percent": row[10], "realized_pl_daily": row[11], "realized_pl_weekly": row[12], 
            "realized_pl_monthly": row[13], "realized_pl_yearly": row[14], "last_update": row[15]
        } for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
