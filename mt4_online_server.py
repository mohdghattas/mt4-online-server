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

def split_concatenated_json(raw_data):
    pattern = r'}\s*{'
    split_data = re.split(pattern, raw_data)
    corrected_jsons = []
    for i, part in enumerate(split_data):
        if i > 0:
            part = '{' + part
        if i < len(split_data) - 1:
            part = part + '}'
        corrected_jsons.append(part)
    return corrected_jsons

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    raw_data = request.data.decode("utf-8", errors="replace")
    logger.debug(f"📥 Raw Request Data: {raw_data}")
    
    chunks = split_concatenated_json(raw_data)
    success_count = 0

    for chunk in chunks:
        try:
            json_data = json.loads(chunk)
            process_json_data(json_data)
            success_count += 1
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error in chunk: {e}")

    if success_count > 0:
        logger.info("✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "Data processed"}), 200
    else:
        return jsonify({"error": "No valid JSON processed"}), 400

def process_json_data(json_data):
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
            raise KeyError(f"Missing field: {field}")

    conn = get_db_connection()
    if not conn:
        raise Exception("Database connection failed")
    
    cur = conn.cursor()
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
        json_data["realized_pl_monthly"], json_data["realized_pl_yearly"], json_data["open_charts"],
        json_data["open_trades"], json_data["empty_charts"], json_data["autotrading"],
        json_data["deposits_alltime"], json_data["withdrawals_alltime"]
    ))

    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"✅ Data stored successfully for account {json_data['account_number']}")

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
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
        ORDER BY profit_loss DESC;
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

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
