from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

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

        # Handling potential multiple concatenated JSON objects
        parts = re.split(r'}\s*{', raw_data)
        parts = [p if p.startswith('{') else '{' + p for p in parts]
        parts = [p if p.endswith('}') else p + '}' for p in parts]

        for chunk in parts:
            try:
                json_data = json.loads(chunk)
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON Decoding Error in chunk: {e}")
                continue

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

            # Extract all fields from json_data
            broker = json_data["broker"]
            account_number = json_data["account_number"]
            balance = json_data["balance"]
            equity = json_data["equity"]
            margin_used = json_data["margin_used"]
            free_margin = json_data["free_margin"]
            margin_percent = json_data["margin_percent"]
            profit_loss = json_data["profit_loss"]
            realized_pl_daily = json_data["realized_pl_daily"]
            realized_pl_weekly = json_data["realized_pl_weekly"]
            realized_pl_monthly = json_data["realized_pl_monthly"]
            realized_pl_yearly = json_data["realized_pl_yearly"]
            realized_pl_alltime = json_data["realized_pl_alltime"]
            deposits_alltime = json_data["deposits_alltime"]
            withdrawals_alltime = json_data["withdrawals_alltime"]
            holding_fee_daily = json_data["holding_fee_daily"]
            holding_fee_weekly = json_data["holding_fee_weekly"]
            holding_fee_monthly = json_data["holding_fee_monthly"]
            holding_fee_yearly = json_data["holding_fee_yearly"]
            holding_fee_alltime = json_data["holding_fee_alltime"]
            open_charts = json_data["open_charts"]
            empty_charts = json_data["empty_charts"]
            open_trades = json_data["open_trades"]
            autotrading = json_data["autotrading"]

            conn = get_db_connection()
            if not conn:
                return jsonify({"error": "Database connection failed"}), 500

            cur = conn.cursor()
            cur.execute("""
                INSERT INTO accounts (
                    broker, account_number, balance, equity, margin_used, free_margin,
                    margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                    realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                    deposits_alltime, withdrawals_alltime, holding_fee_daily,
                    holding_fee_weekly, holding_fee_monthly, holding_fee_yearly,
                    holding_fee_alltime, open_charts, empty_charts, open_trades, autotrading
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            """, (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                deposits_alltime, withdrawals_alltime, holding_fee_daily,
                holding_fee_weekly, holding_fee_monthly, holding_fee_yearly,
                holding_fee_alltime, open_charts, empty_charts, open_trades, autotrading
            ))
            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"✅ Data stored successfully for account {account_number}")

        return jsonify({"message": "All valid JSON parts processed successfully"}), 200

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
        cur.execute("""
            SELECT * FROM accounts ORDER BY profit_loss DESC;
        """)
        columns = [desc[0] for desc in cur.description]
        accounts = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()

        return jsonify({"accounts": accounts})
    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    logger.error("❌ 404 Not Found: The requested URL does not exist.")
    return jsonify({"error": "404 Not Found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
