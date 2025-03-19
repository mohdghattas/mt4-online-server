from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json

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

def split_json_objects(data):
    json_objects = []
    buffer = ""
    depth = 0
    in_string = False

    for char in data:
        buffer += char
        if char == '"' and (len(buffer) < 2 or buffer[-2] != '\\'):
            in_string = not in_string
        elif not in_string:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    json_objects.append(buffer.strip())
                    buffer = ""

    if depth != 0:
        raise ValueError("Unbalanced JSON braces detected.")
    return json_objects

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = split_json_objects(raw_data)

        for chunk in json_chunks:
            try:
                json_data = json.loads(chunk)

                # Safe extraction with defaults for optional fields
                broker = json_data.get("broker")
                account_number = json_data.get("account_number")
                balance = json_data.get("balance", 0)
                equity = json_data.get("equity", 0)
                margin_used = json_data.get("margin_used", 0)
                free_margin = json_data.get("free_margin", 0)
                margin_percent = json_data.get("margin_percent", 0)
                profit_loss = json_data.get("profit_loss", 0)
                realized_pl_daily = json_data.get("realized_pl_daily", 0)
                realized_pl_weekly = json_data.get("realized_pl_weekly", 0)
                realized_pl_monthly = json_data.get("realized_pl_monthly", 0)
                realized_pl_yearly = json_data.get("realized_pl_yearly", 0)
                open_charts = json_data.get("open_charts", 0)
                open_trades = json_data.get("open_trades", 0)
                empty_charts = json_data.get("empty_charts", 0)
                autotrading = json_data.get("autotrading", False)
                deposits_alltime = json_data.get("deposits_alltime", 0)
                withdrawals_alltime = json_data.get("withdrawals_alltime", 0)

                conn = get_db_connection()
                if not conn:
                    continue

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
                    broker, account_number, balance, equity, margin_used, free_margin,
                    margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                    realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                    empty_charts, autotrading, deposits_alltime, withdrawals_alltime
                ))

                conn.commit()
                cur.close()
                conn.close()

                logger.info(f"✅ Data stored successfully for account {account_number}")

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON Decoding Error in chunk: {e}")

        logger.info("✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "Data processed successfully"}), 200

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

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
