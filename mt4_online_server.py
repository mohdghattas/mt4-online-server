from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import logging
import os
import json
import re

# ✅ Initialize Flask App
app = Flask(__name__)
CORS(app)

# ✅ Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Database connection function
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# ✅ Ensure required columns exist
def ensure_columns():
    columns = [
        ("autotrading", "BOOLEAN"),
        ("empty_charts", "INTEGER"),
        ("deposits_alltime", "NUMERIC"),
        ("withdrawals_alltime", "NUMERIC"),
        ("open_pairs_charts", "TEXT")
    ]
    conn = get_db_connection()
    cur = conn.cursor()
    for column, col_type in columns:
        cur.execute(f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                               WHERE table_name='accounts' AND column_name='{column}') THEN
                    ALTER TABLE accounts ADD COLUMN {column} {col_type};
                END IF;
            END
            $$;
        """)
    conn.commit()
    cur.close()
    conn.close()

# ✅ Handle multiple JSON objects concatenated in request
def split_json_objects(raw_data):
    json_objects = []
    pattern = re.compile(r'({.*?})(?=\s*{|\s*$)', re.DOTALL)
    matches = pattern.findall(raw_data)
    for match in matches:
        try:
            json_objects.append(json.loads(match))
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error in part: {e}")
    return json_objects

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8", errors="replace")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        json_objects = split_json_objects(raw_data)
        conn = get_db_connection()
        cur = conn.cursor()

        for json_data in json_objects:
            # ✅ Extract Data
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
            open_charts = json_data.get("open_charts")
            open_trades = json_data.get("open_trades")
            autotrading = json_data.get("autotrading")
            empty_charts = json_data.get("empty_charts")
            deposits_alltime = json_data.get("deposits_alltime")
            withdrawals_alltime = json_data.get("withdrawals_alltime")
            open_pairs_charts = json_data.get("open_pairs_charts")

            # ✅ Insert/Update Query
            cur.execute("""
                INSERT INTO accounts (
                    broker, account_number, balance, equity, margin_used, free_margin,
                    margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                    realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                    autotrading, empty_charts, deposits_alltime, withdrawals_alltime, open_pairs_charts
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    autotrading = EXCLUDED.autotrading,
                    empty_charts = EXCLUDED.empty_charts,
                    deposits_alltime = EXCLUDED.deposits_alltime,
                    withdrawals_alltime = EXCLUDED.withdrawals_alltime,
                    open_pairs_charts = EXCLUDED.open_pairs_charts;
            """, (
                broker, account_number, balance, equity, margin_used, free_margin,
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                autotrading, empty_charts, deposits_alltime, withdrawals_alltime, open_pairs_charts
            ))

        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ All valid JSON parts processed successfully.")
        return jsonify({"message": "Data processed successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# ✅ API: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin,
                   margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
                   realized_pl_monthly, realized_pl_yearly, open_charts, open_trades,
                   autotrading, empty_charts, deposits_alltime, withdrawals_alltime, open_pairs_charts
            FROM accounts 
            ORDER BY profit_loss DESC;
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = []
        for row in rows:
            accounts_data.append({
                "broker": row[0], "account_number": row[1], "balance": row[2], "equity": row[3],
                "margin_used": row[4], "free_margin": row[5], "margin_percent": row[6],
                "profit_loss": row[7], "realized_pl_daily": row[8], "realized_pl_weekly": row[9],
                "realized_pl_monthly": row[10], "realized_pl_yearly": row[11],
                "open_charts": row[12], "open_trades": row[13], "autotrading": row[14],
                "empty_charts": row[15], "deposits_alltime": row[16],
                "withdrawals_alltime": row[17], "open_pairs_charts": row[18]
            })

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ 404 Handler
@app.errorhandler(404)
def not_found(error):
    logger.error("❌ 404 Not Found: The requested URL does not exist.")
    return jsonify({"error": "404 Not Found"}), 404

# ✅ Initialize columns on startup
if __name__ == "__main__":
    ensure_columns()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
