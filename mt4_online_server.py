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

# Database connection function
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")
    return conn

# Custom JSON Splitter
def split_concatenated_json(raw_data):
    parts = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(raw_data):
        raw_data = raw_data.lstrip()
        try:
            obj, end = decoder.raw_decode(raw_data[idx:])
            parts.append(obj)
            idx += end
        except json.JSONDecodeError:
            break
    return parts

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = split_concatenated_json(raw_data)
        if not json_chunks:
            return jsonify({"error": "Invalid or empty JSON"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        for json_data in json_chunks:
            broker = json_data.get("broker")
            account_number = json_data.get("account_number")
            balance = json_data.get("balance")
            equity = json_data.get("equity")
            margin_used = json_data.get("margin_used")
            free_margin = json_data.get("free_margin")
            margin_percent = json_data.get("margin_percent")
            profit_loss = json_data.get("profit_loss")
            realized_pl_daily = json_data.get("realized_pl_daily")
            realized_pl_weekly = json_data.get("realized_pl_weekly")
            realized_pl_monthly = json_data.get("realized_pl_monthly")
            realized_pl_yearly = json_data.get("realized_pl_yearly")
            realized_pl_alltime = json_data.get("realized_pl_alltime")
            holding_fee_daily = json_data.get("holding_fee_daily")
            holding_fee_weekly = json_data.get("holding_fee_weekly")
            holding_fee_monthly = json_data.get("holding_fee_monthly")
            holding_fee_yearly = json_data.get("holding_fee_yearly")
            holding_fee_alltime = json_data.get("holding_fee_alltime")
            deposits_alltime = json_data.get("deposits_alltime")
            withdrawals_alltime = json_data.get("withdrawals_alltime")
            open_charts = json_data.get("open_charts")
            empty_charts = json_data.get("empty_charts")
            open_trades = json_data.get("open_trades")
            autotrading = json_data.get("autotrading")

            cur.execute("""
                INSERT INTO accounts (
                    broker, account_number, balance, equity, margin_used, free_margin, margin_percent, 
                    profit_loss, realized_pl_daily, realized_pl_weekly, realized_pl_monthly, 
                    realized_pl_yearly, realized_pl_alltime, holding_fee_daily, holding_fee_weekly, 
                    holding_fee_monthly, holding_fee_yearly, holding_fee_alltime, deposits_alltime, 
                    withdrawals_alltime, open_charts, empty_charts, open_trades, autotrading
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
                    holding_fee_daily = EXCLUDED.holding_fee_daily,
                    holding_fee_weekly = EXCLUDED.holding_fee_weekly,
                    holding_fee_monthly = EXCLUDED.holding_fee_monthly,
                    holding_fee_yearly = EXCLUDED.holding_fee_yearly,
                    holding_fee_alltime = EXCLUDED.holding_fee_alltime,
                    deposits_alltime = EXCLUDED.deposits_alltime,
                    withdrawals_alltime = EXCLUDED.withdrawals_alltime,
                    open_charts = EXCLUDED.open_charts,
                    empty_charts = EXCLUDED.empty_charts,
                    open_trades = EXCLUDED.open_trades,
                    autotrading = EXCLUDED.autotrading;
            """, (
                broker, account_number, balance, equity, margin_used, free_margin, margin_percent, 
                profit_loss, realized_pl_daily, realized_pl_weekly, realized_pl_monthly, 
                realized_pl_yearly, realized_pl_alltime, holding_fee_daily, holding_fee_weekly, 
                holding_fee_monthly, holding_fee_yearly, holding_fee_alltime, deposits_alltime, 
                withdrawals_alltime, open_charts, empty_charts, open_trades, autotrading
            ))

        conn.commit()
        cur.close()
        conn.close()

        logger.info("✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin, margin_percent,
                   profit_loss, realized_pl_daily, realized_pl_weekly, realized_pl_monthly, 
                   realized_pl_yearly, realized_pl_alltime, holding_fee_daily, holding_fee_weekly,
                   holding_fee_monthly, holding_fee_yearly, holding_fee_alltime, deposits_alltime, 
                   withdrawals_alltime, open_charts, empty_charts, open_trades, autotrading
            FROM accounts;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [dict(
            broker=row[0], account_number=row[1], balance=row[2], equity=row[3],
            margin_used=row[4], free_margin=row[5], margin_percent=row[6],
            profit_loss=row[7], realized_pl_daily=row[8], realized_pl_weekly=row[9],
            realized_pl_monthly=row[10], realized_pl_yearly=row[11], realized_pl_alltime=row[12],
            holding_fee_daily=row[13], holding_fee_weekly=row[14], holding_fee_monthly=row[15],
            holding_fee_yearly=row[16], holding_fee_alltime=row[17], deposits_alltime=row[18],
            withdrawals_alltime=row[19], open_charts=row[20], empty_charts=row[21],
            open_trades=row[22], autotrading=row[23]
        ) for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
