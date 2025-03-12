from flask import Flask, request, jsonify
import json
import psycopg2
import os
import logging

# Initialize Flask app
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
            "open_charts INT",
            "ea_names TEXT",
            "traded_pairs TEXT",
            "deposit_withdrawal FLOAT",
            "margin_percent FLOAT",
            "realized_pl_daily FLOAT",
            "realized_pl_weekly FLOAT",
            "realized_pl_monthly FLOAT",
            "realized_pl_yearly FLOAT"
        ]
        for col in columns:
            cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated: Added missing columns if they did not exist.")
    except Exception as e:
        logger.error(f"❌ Database schema update error: {str(e)}")

# API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # Ensure request has the correct content type
        if "application/json" not in request.content_type.lower():
            return jsonify({"error": "Unsupported Media Type. Use application/json"}), 415
        
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
        margin_percent = raw_data.get("margin_percent", 0.0)
        realized_pl_daily = raw_data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = raw_data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = raw_data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = raw_data.get("realized_pl_yearly", 0.0)
        open_charts = raw_data.get("open_charts", 0)

        conn = get_db_connection()
        cur = conn.cursor()

        # Insert or Update Data
        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, margin_percent, realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly, open_charts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss,
                margin_percent = EXCLUDED.margin_percent,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                realized_pl_yearly = EXCLUDED.realized_pl_yearly,
                open_charts = EXCLUDED.open_charts;
        """, (broker, account_number, balance, equity, free_margin, profit_loss, margin_percent, realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly, open_charts))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Data stored successfully: {raw_data}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Start the server
if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
