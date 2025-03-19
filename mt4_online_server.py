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

# ✅ Splitting concatenated JSON objects safely
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

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # ✅ Log raw request data
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_chunks = split_json_objects(raw_data)

        for chunk in json_chunks:
            try:
                json_data = json.loads(chunk)

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
                        continue

                # ✅ Extract Data
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
                open_charts = json_data["open_charts"]
                open_trades = json_data["open_trades"]
                empty_charts = json_data["empty_charts"]
                autotrading = json_data["autotrading"]
                deposits_alltime = json_data["deposits_alltime"]
                withdrawals_alltime = json_data["withdrawals_alltime"]

                # ✅ Insert Data into Database
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
