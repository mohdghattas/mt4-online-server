from flask import Flask, request, jsonify
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Database Connection
DB_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/mt4db")

# Logger Configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Connect to Database
def get_db_connection():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# 🔵 Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400

        # Extract Fields
        broker = data.get("broker", "Unknown Broker")
        account_number = data["account_number"]
        balance = data["balance"]
        equity = data["equity"]
        free_margin = data["free_margin"]
        profit_loss = data["profit_loss"]
        open_charts = data.get("open_charts", 0)
        ea_names = data.get("ea_names", "")
        traded_pairs = data.get("traded_pairs", "")
        deposit_withdrawal = data.get("deposit_withdrawal", 0)
        margin_percent = data.get("margin_percent", 0.0)
        realized_pl_daily = data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = data.get("realized_pl_yearly", 0.0)

        # Store Data in Database
        conn = get_db_connection()
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

# 🔵 Fetch Account Data for Dashboard
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = """
        SELECT broker, account_number, balance, equity, free_margin, profit_loss,
               open_charts, ea_names, traded_pairs, deposit_withdrawal, margin_percent,
               realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly
        FROM accounts ORDER BY profit_loss ASC;
        """
        cur.execute(query)
        accounts = cur.fetchall()
        
        cur.close()
        conn.close()

        return jsonify({"accounts": accounts}), 200

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
