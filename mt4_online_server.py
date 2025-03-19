from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json

# ✅ Initialize Flask App
app = Flask(__name__)
CORS(app)  # ✅ Allow external API access

# ✅ Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.json
        logger.debug(f"📥 Incoming Data: {data}")

        required_fields = [
            "broker", "account_number", "balance", "equity", "margin_used", "free_margin",
            "margin_percent", "profit_loss", "realized_pl_daily", "realized_pl_weekly",
            "realized_pl_monthly", "realized_pl_yearly", "open_charts", "open_trades",
            "autotrading_status", "ea_status", "terminal_errors", "empty_charts_count",
            "empty_charts_symbols", "open_pairs_charts", "deposits_today", "withdrawals_today",
            "deposits_weekly", "withdrawals_weekly", "deposits_monthly", "withdrawals_monthly",
            "deposits_yearly", "withdrawals_yearly", "deposits_all_time", "withdrawals_all_time"
        ]

        for field in required_fields:
            if field not in data:
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
                realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                autotrading_status, ea_status, terminal_errors, empty_charts_count,
                empty_charts_symbols, open_pairs_charts, deposits_today, withdrawals_today,
                deposits_weekly, withdrawals_weekly, deposits_monthly, withdrawals_monthly,
                deposits_yearly, withdrawals_yearly, deposits_all_time, withdrawals_all_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE 
            SET broker = EXCLUDED.broker,
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
                open_charts = EXCLUDED.open_charts,
                open_trades = EXCLUDED.open_trades,
                autotrading_status = EXCLUDED.autotrading_status,
                ea_status = EXCLUDED.ea_status,
                terminal_errors = EXCLUDED.terminal_errors,
                empty_charts_count = EXCLUDED.empty_charts_count,
                empty_charts_symbols = EXCLUDED.empty_charts_symbols,
                open_pairs_charts = EXCLUDED.open_pairs_charts,
                deposits_today = EXCLUDED.deposits_today,
                withdrawals_today = EXCLUDED.withdrawals_today,
                deposits_weekly = EXCLUDED.deposits_weekly,
                withdrawals_weekly = EXCLUDED.withdrawals_weekly,
                deposits_monthly = EXCLUDED.deposits_monthly,
                withdrawals_monthly = EXCLUDED.withdrawals_monthly,
                deposits_yearly = EXCLUDED.deposits_yearly,
                withdrawals_yearly = EXCLUDED.withdrawals_yearly,
                deposits_all_time = EXCLUDED.deposits_all_time,
                withdrawals_all_time = EXCLUDED.withdrawals_all_time;
        """, tuple(data[field] for field in required_fields))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully for account {data['account_number']}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ✅ API: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts ORDER BY profit_loss DESC;")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [dict(zip(columns, row)) for row in rows]
        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
