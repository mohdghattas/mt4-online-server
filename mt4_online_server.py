from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
        return conn
    except Exception as e:
        logger.error(f"❌ Database Connection Error: {str(e)}")
        return None

# Defensive JSON cleaner for MT4 issues
def parse_json_chunks(raw_data):
    chunks = []
    decoder = json.JSONDecoder()
    pos = 0
    raw_data = raw_data.replace('\u0000', '').strip()
    while pos < len(raw_data):
        try:
            obj, index = decoder.raw_decode(raw_data[pos:])
            chunks.append(obj)
            pos += index
            while pos < len(raw_data) and raw_data[pos] in (' ', '\n', '\r'):
                pos += 1
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error in chunk: {e}")
            break
    return chunks

# API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = parse_json_chunks(raw_data)
        if not json_chunks:
            return jsonify({"error": "Invalid JSON received"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        cur = conn.cursor()

        for json_data in json_chunks:
            # Validate required fields for each chunk
            required_fields = [
                "broker", "account_number", "balance", "equity", "margin_used",
                "free_margin", "margin_percent", "profit_loss", "realized_pl_daily",
                "realized_pl_weekly", "realized_pl_monthly", "realized_pl_yearly",
                "realized_pl_alltime", "deposits_alltime", "withdrawals_alltime",
                "holding_fee_daily", "holding_fee_weekly", "holding_fee_monthly",
                "holding_fee_yearly", "holding_fee_alltime",
                "open_charts", "empty_charts", "open_trades", "autotrading"
            ]
            for field in required_fields:
                if field not in json_data:
                    logger.error(f"❌ Missing field: {field}")
                    return jsonify({"error": f"Missing field: {field}"}), 400

            # Extract Data
            data = [json_data[field] for field in required_fields]

            # Insert Data into Database
            cur.execute("""
                INSERT INTO accounts (
                    broker, account_number, balance, equity, margin_used, free_margin,
                    margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                    realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                    deposits_alltime, withdrawals_alltime,
                    holding_fee_daily, holding_fee_weekly, holding_fee_monthly,
                    holding_fee_yearly, holding_fee_alltime,
                    open_charts, empty_charts, open_trades, autotrading
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            """, data)

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


# API: Retrieve Accounts Data
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
                   realized_pl_monthly, realized_pl_yearly, realized_pl_alltime,
                   deposits_alltime, withdrawals_alltime,
                   holding_fee_daily, holding_fee_weekly, holding_fee_monthly,
                   holding_fee_yearly, holding_fee_alltime,
                   open_charts, empty_charts, open_trades, autotrading
            FROM accounts
            ORDER BY profit_loss DESC;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [dict(
            broker=row[0], account_number=row[1], balance=row[2], equity=row[3],
            margin_used=row[4], free_margin=row[5], margin_percent=row[6],
            profit_loss=row[7], realized_pl_daily=row[8], realized_pl_weekly=row[9],
            realized_pl_monthly=row[10], realized_pl_yearly=row[11], realized_pl_alltime=row[12],
            deposits_alltime=row[13], withdrawals_alltime=row[14],
            holding_fee_daily=row[15], holding_fee_weekly=row[16], holding_fee_monthly=row[17],
            holding_fee_yearly=row[18], holding_fee_alltime=row[19],
            open_charts=row[20], empty_charts=row[21], open_trades=row[22], autotrading=row[23]
        ) for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    logger.error("❌ 404 Not Found: The requested URL does not exist.")
    return jsonify({"error": "404 Not Found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
