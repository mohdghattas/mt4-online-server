from flask import Flask, request, jsonify
import psycopg2
import logging
import os

app = Flask(__name__)

# ✅ Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Database connection function
def get_db_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# ✅ Ensure necessary columns exist in the database
def ensure_column_exists():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        columns = [
            "open_charts INT",
            "open_trades INT",
            "ea_names TEXT",
            "traded_pairs TEXT",
            "deposit_withdrawal FLOAT",
            "margin_percent FLOAT",
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
        # 🔍 Log the incoming request for debugging
        raw_data = request.data.decode("utf-8")
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        # ✅ Ensure Content-Type is application/json
        if "application/json" not in request.content_type:
            return jsonify({"error": "Invalid Content-Type"}), 415

        # ✅ Parse JSON safely
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "Invalid JSON format"}), 400

        # ✅ Extract Data
        broker = json_data.get("broker", "Unknown")
        account_number = json_data["account_number"]
        balance = json_data["balance"]
        equity = json_data["equity"]
        margin_used = json_data.get("margin_used", 0.0)
        free_margin = json_data["free_margin"]
        profit_loss = json_data["profit_loss"]
        margin_percent = json_data["margin_percent"]
        open_charts = json_data.get("open_charts", 0)
        open_trades = json_data.get("open_trades", 0)
        realized_pl_daily = json_data.get("realized_pl_daily", 0.0)
        realized_pl_weekly = json_data.get("realized_pl_weekly", 0.0)
        realized_pl_monthly = json_data.get("realized_pl_monthly", 0.0)
        realized_pl_yearly = json_data.get("realized_pl_yearly", 0.0)

        # ✅ Connect to Database
        conn = get_db_connection()
        cur = conn.cursor()

        # ✅ Insert or Update Data
        cur.execute("""
            INSERT INTO accounts (
                broker, account_number, balance, equity, margin_used, free_margin, 
                profit_loss, margin_percent, open_charts, open_trades, 
                realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_number) DO UPDATE 
            SET broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                margin_used = EXCLUDED.margin_used,
                free_margin = EXCLUDED.free_margin,
                profit_loss = EXCLUDED.profit_loss,
                margin_percent = EXCLUDED.margin_percent,
                open_charts = EXCLUDED.open_charts,
                open_trades = EXCLUDED.open_trades,
                realized_pl_daily = EXCLUDED.realized_pl_daily,
                realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                realized_pl_yearly = EXCLUDED.realized_pl_yearly;
        """, (broker, account_number, balance, equity, margin_used, free_margin,
              profit_loss, margin_percent, open_charts, open_trades, 
              realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly))

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
                   profit_loss, margin_percent, open_charts, open_trades, 
                   realized_pl_daily, realized_pl_weekly, realized_pl_monthly, realized_pl_yearly
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
            "profit_loss": row[6],
            "margin_percent": row[7],
            "open_charts": row[8],
            "open_trades": row[9],
            "realized_pl_daily": row[10],
            "realized_pl_weekly": row[11],
            "realized_pl_monthly": row[12],
            "realized_pl_yearly": row[13]
        } for row in accounts]

        return jsonify({"accounts": accounts_data})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Initialize Database on Startup
if __name__ == "__main__":
    ensure_column_exists()
    app.run(host="0.0.0.0", port=5000)
