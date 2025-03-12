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
        if request.content_type != "application/json":
            return jsonify({"error": "Unsupported Media Type: Content-Type must be application/json"}), 415

        raw_data = request.get_json()
        if not raw_data:
            return jsonify({"error": "Invalid JSON format"}), 400

        logger.debug(f"📥 Raw Request Data: {raw_data}")

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, 
                                 open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent, 
                                 realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE 
            SET broker = EXCLUDED.broker, balance = EXCLUDED.balance, equity = EXCLUDED.equity, 
                free_margin = EXCLUDED.free_margin, profit_loss = EXCLUDED.profit_loss, 
                open_charts = EXCLUDED.open_charts, ea_names = EXCLUDED.ea_names, 
                traded_pairs = EXCLUDED.traded_pairs, deposit_withdrawal = EXCLUDED.deposit_withdrawal, 
                margin_percent = EXCLUDED.margin_percent, realized_pl_daily = EXCLUDED.realized_pl_daily, 
                realized_pl_weekly = EXCLUDED.realized_pl_weekly, realized_pl_monthly = EXCLUDED.realized_pl_monthly, 
                realized_pl_yearly = EXCLUDED.realized_pl_yearly;
        """, tuple(raw_data.values()))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully: {raw_data}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
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
