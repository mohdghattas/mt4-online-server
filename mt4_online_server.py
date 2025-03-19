from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re

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

# ✅ Function to clean and split raw JSON chunks if needed
def split_and_clean_json(raw_data):
    parts = re.findall(r'\{.*?\}(?=\{|\Z)', raw_data)
    cleaned = []
    for part in parts:
        try:
            cleaned.append(json.loads(part))
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error in chunk: {e}")
    return cleaned

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = split_and_clean_json(raw_data)
        if not json_chunks:
            return jsonify({"error": "No valid JSON chunks found"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        cur = conn.cursor()

        for json_data in json_chunks:
            # Validate required fields
            required_fields = [
                "broker", "account_number", "balance", "equity", "margin_used",
                "free_margin", "margin_percent", "profit_loss", "realized_pl_daily",
                "realized_pl_weekly", "realized_pl_monthly", "realized_pl_yearly",
                "open_charts", "open_trades", "empty_charts", "autotrading",
                "deposits_alltime", "withdrawals_alltime"
            ]
            for field in required_fields:
                if field not in json_data:
                    logger.error(f"❌ Missing field: {field}")
                    return jsonify({"error": f"Missing field: {field}"}), 400

            # Insert or Update
            cur.execute("""
                INSERT INTO accounts (
                    broker, account_number, balance, equity, margin_used, free_margin,
                    margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                    realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                    empty_charts, autotrading, deposits_alltime, withdrawals_alltime
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    empty_charts = EXCLUDED.empty_charts,
                    autotrading = EXCLUDED.autotrading,
                    deposits_alltime = EXCLUDED.deposits_alltime,
                    withdrawals_alltime = EXCLUDED.withdrawals_alltime;
            """, (
                json_data["broker"], json_data["account_number"], json_data["balance"], json_data["equity"],
                json_data["margin_used"], json_data["free_margin"], json_data["margin_percent"],
                json_data["profit_loss"], json_data["realized_pl_daily"], json_data["realized_pl_weekly"],
                json_data["realized_pl_monthly"], json_data["realized_pl_yearly"],
                json_data["open_charts"], json_data["open_trades"], json_data["empty_charts"],
                json_data["autotrading"], json_data["deposits_alltime"], json_data["withdrawals_alltime"]
            ))
            logger.info(f"✅ Data stored successfully for account {json_data['account_number']}")

        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "All valid JSON processed"}), 200

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
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin,
                   margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                   realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                   empty_charts, autotrading, deposits_alltime, withdrawals_alltime
            FROM accounts 
            ORDER BY profit_loss ASC;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [dict(
            broker=row[0], account_number=row[1], balance=row[2], equity=row[3],
            margin_used=row[4], free_margin=row[5], margin_percent=row[6],
            profit_loss=row[7], realized_pl_daily=row[8], realized_pl_weekly=row[9],
            realized_pl_monthly=row[10], realized_pl_yearly=row[11],
            open_charts=row[12], open_trades=row[13], empty_charts=row[14],
            autotrading=row[15], deposits_alltime=row[16], withdrawals_alltime=row[17]
        ) for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ 404 Handler
@app.errorhandler(404)
def not_found(error):
    logger.error("❌ 404 Not Found: The requested URL does not exist.")
    return jsonify({"error": "404 Not Found"}), 404

# ✅ Main entry
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
