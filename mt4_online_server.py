from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_data = json.loads(raw_data)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin, 
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly, 
                realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                open_charts, open_trades, empty_charts, autotrading, 
                deposits_daily, withdrawals_daily, deposits_weekly, withdrawals_weekly, 
                deposits_monthly, withdrawals_monthly, deposits_yearly, withdrawals_yearly,
                deposits_alltime, withdrawals_alltime,
                holding_fee_daily, holding_fee_weekly, holding_fee_monthly, holding_fee_yearly, holding_fee_alltime,
                open_pairs_charts
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                open_charts = EXCLUDED.open_charts,
                open_trades = EXCLUDED.open_trades,
                empty_charts = EXCLUDED.empty_charts,
                autotrading = EXCLUDED.autotrading,
                deposits_daily = EXCLUDED.deposits_daily,
                withdrawals_daily = EXCLUDED.withdrawals_daily,
                deposits_weekly = EXCLUDED.deposits_weekly,
                withdrawals_weekly = EXCLUDED.withdrawals_weekly,
                deposits_monthly = EXCLUDED.deposits_monthly,
                withdrawals_monthly = EXCLUDED.withdrawals_monthly,
                deposits_yearly = EXCLUDED.deposits_yearly,
                withdrawals_yearly = EXCLUDED.withdrawals_yearly,
                deposits_alltime = EXCLUDED.deposits_alltime,
                withdrawals_alltime = EXCLUDED.withdrawals_alltime,
                holding_fee_daily = EXCLUDED.holding_fee_daily,
                holding_fee_weekly = EXCLUDED.holding_fee_weekly,
                holding_fee_monthly = EXCLUDED.holding_fee_monthly,
                holding_fee_yearly = EXCLUDED.holding_fee_yearly,
                holding_fee_alltime = EXCLUDED.holding_fee_alltime,
                open_pairs_charts = EXCLUDED.open_pairs_charts;
        """, (
            json_data["broker"],
            json_data["account_number"],
            json_data["balance"],
            json_data["equity"],
            json_data["margin_used"],
            json_data["free_margin"],
            json_data["margin_percent"],
            json_data["profit_loss"],
            json_data["realized_pl_daily"],
            json_data["realized_pl_weekly"],
            json_data["realized_pl_monthly"],
            json_data["realized_pl_yearly"],
            json_data["realized_pl_alltime"],
            json_data["open_charts"],
            json_data["open_trades"],
            json_data["empty_charts"],
            json_data["autotrading"],
            json_data["deposits_daily"],
            json_data["withdrawals_daily"],
            json_data["deposits_weekly"],
            json_data["withdrawals_weekly"],
            json_data["deposits_monthly"],
            json_data["withdrawals_monthly"],
            json_data["deposits_yearly"],
            json_data["withdrawals_yearly"],
            json_data["deposits_alltime"],
            json_data["withdrawals_alltime"],
            json_data["holding_fee_daily"],
            json_data["holding_fee_weekly"],
            json_data["holding_fee_monthly"],
            json_data["holding_fee_yearly"],
            json_data["holding_fee_alltime"],
            json_data["open_pairs_charts"]
        ))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully for account {json_data['account_number']}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()
        cur.execute("SELECT * FROM accounts ORDER BY profit_loss DESC;")
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        accounts = [dict(zip(colnames, row)) for row in rows]
        return jsonify({"accounts": accounts})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
