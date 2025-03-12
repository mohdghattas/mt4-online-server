from flask import Flask, request, jsonify
import psycopg2
import logging
import os
import json

app = Flask(__name__)

# ✅ Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Database connection function
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# ✅ Ensure all necessary columns exist
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        columns = [
            "margin_used FLOAT",
            "open_charts INT",
            "open_trades INT",
            "realized_pl_daily FLOAT",
            "realized_pl_weekly FLOAT",
            "realized_pl_monthly FLOAT",
            "realized_pl_yearly FLOAT"
        ]
        for col in columns:
            cur.execute(f"ALTER TABLE accounts ADD COLUMN IF NOT EXISTS {col};")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("✅ Database schema updated: Added missing columns if they did not exist.")
    except Exception as e:
        logger.error(f"❌ Database schema update error: {str(e)}")

# ✅ API Endpoint: Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        # 🔍 Log incoming request
        raw_data = request.data.decode("utf-8").strip()
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # ✅ Ensure Content-Type is JSON
        if "application/json" not in request.content_type:
            return jsonify({"error": "Invalid Content-Type"}), 415

        # ✅ Decode JSON safely
        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Decoding Error: {str(e)}")
            return jsonify({"error": "Invalid JSON format"}), 400

        # ✅ Extract Data with Default Values
        broker = json_data.get("broker", "Unknown")
        account_number = json_data.get("account_number")
        balance = json_data.get("balance", 0.0)
        equity = json_data.get("equity", 0.0)
        margin_used = json_data.get("margin_used", 0.0)
        free_margin = json_data.get("free_margin", 0.0)
        margin_percent = json_data.get("margin_percent", 0.0)
        profit_loss = json_data.get("profit_loss", 0.0)
        realized_pl_daily = json_data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = json_data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = json_data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = json_data.get("realized_pl_yearly", 0.0)
        open_charts = json_data.get("open_charts", 0)
        open_trades = json_data.get("open_trades", 0)

        # ✅ Log extracted values before inserting
        logger.debug(f"Extracted Data: {json_data}")

        # ✅ Connect to Database
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or Update Data
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin, 
                margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly, 
                realized_pl_monthly, realized_pl_yearly, open_charts, open_trades
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                open_trades = EXCLUDED.open_trades;
        """, (broker, account_number, balance, equity, margin_used, free_margin,
              margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly,
              realized_pl_monthly, realized_pl_yearly, open_charts, open_trades))

        conn.commit()
        cur.close()
        conn.close()

        logger.info(f"✅ Data stored successfully: {json_data}")
        return jsonify({"message": "Data stored successfully"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ API Endpoint: Retrieve Accounts Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT broker, account_number, balance, equity, margin_used, free_margin, 
                   margin_percent, profit_loss, realized_pl_daily, realized_pl_weekly, 
                   realized_pl_monthly, realized_pl_yearly, open_charts, open_trades
            FROM accounts 
            ORDER BY profit_loss ASC;
        """)
        accounts = cur.fetchall()
        cur.close()
        conn.close()

        accounts_data = [{
            "broker": row[0],
            "account_number": row[1],
            "balance": row[2],
            "equity": row[3],
            "margin_used": row[4],
            "free_margin": row[5],
            "margin_percent": row[6],
            "profit_loss": row[7],
            "realized_pl_daily": row[8],
            "realized_pl_weekly": row[9],
            "realized_pl_monthly": row[10],
            "realized_pl_yearly": row[11],
            "open_charts": row[12],
            "open_trades": row[13]
        } for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Initialize Database on Startup
if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
