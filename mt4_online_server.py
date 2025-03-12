from flask import Flask, request, jsonify
import psycopg2
import logging
import os

app = Flask(__name__)

# ✅ Configure Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mt4_online_server")

# ✅ Ensure Database Connection URL Exists
DATABASE_URL = os.getenv("DATABASE_URL", "your_database_url_here")

if DATABASE_URL == "your_database_url_here":
    logger.error("❌ ERROR: Database URL is not set!")
    exit(1)

# ✅ Ensure Database Table Has Required Columns
def ensure_database_schema():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id SERIAL PRIMARY KEY,
                    broker TEXT,
                    account_number BIGINT UNIQUE,
                    balance NUMERIC(20,2),
                    equity NUMERIC(20,2),
                    free_margin NUMERIC(20,2),
                    profit_loss NUMERIC(20,2),
                    open_charts INT DEFAULT 0,
                    ea_names TEXT DEFAULT '',
                    traded_pairs TEXT DEFAULT '',
                    deposit_withdrawal NUMERIC(20,2) DEFAULT 0,
                    margin_percent NUMERIC(10,2) DEFAULT 0,
                    realized_pl_daily NUMERIC(20,2) DEFAULT 0,
                    realized_pl_weekly NUMERIC(20,2) DEFAULT 0,
                    realized_pl_monthly NUMERIC(20,2) DEFAULT 0,
                    realized_pl_yearly NUMERIC(20,2) DEFAULT 0
                );
            """)
            conn.commit()
            logger.info("✅ Database schema ensured.")

ensure_database_schema()

# ✅ API: GET Account Data
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT broker, account_number, balance, equity, free_margin, profit_loss, 
                           open_charts, ea_names, traded_pairs, deposit_withdrawal, 
                           margin_percent, realized_pl_daily, realized_pl_weekly, 
                           realized_pl_monthly, realized_pl_yearly 
                    FROM accounts
                """)
                accounts = cur.fetchall()

        accounts_list = [
            {
                "broker": acc[0],
                "account_number": acc[1],
                "balance": float(acc[2]),
                "equity": float(acc[3]),
                "free_margin": float(acc[4]),
                "profit_loss": float(acc[5]),
                "open_charts": acc[6],
                "ea_names": acc[7],
                "traded_pairs": acc[8],
                "deposit_withdrawal": float(acc[9]),
                "margin_percent": float(acc[10]),
                "realized_pl_daily": float(acc[11]),
                "realized_pl_weekly": float(acc[12]),
                "realized_pl_monthly": float(acc[13]),
                "realized_pl_yearly": float(acc[14])
            }
            for acc in accounts
        ]

        return jsonify({"accounts": accounts_list})

    except Exception as e:
        logger.error(f"❌ API Fetch Error: {e}")
        return jsonify({"error": str(e)}), 500

# ✅ API: Receive Data from MT4
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)
        logger.debug(f"📥 Raw Request Data: {raw_data}")

        data = request.get_json()

        # ✅ Ensure Required Fields Exist
        required_fields = [
            "broker", "account_number", "balance", "equity", "free_margin", "profit_loss",
            "open_charts", "ea_names", "traded_pairs", "deposit_withdrawal",
            "margin_percent", "realized_pl_daily", "realized_pl_weekly",
            "realized_pl_monthly", "realized_pl_yearly"
        ]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing field: {field}")

        # ✅ Insert or Update Data
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO accounts (
                        broker, account_number, balance, equity, free_margin, profit_loss,
                        open_charts, ea_names, traded_pairs, deposit_withdrawal,
                        margin_percent, realized_pl_daily, realized_pl_weekly,
                        realized_pl_monthly, realized_pl_yearly
                    ) VALUES (
                        %(broker)s, %(account_number)s, %(balance)s, %(equity)s, %(free_margin)s, %(profit_loss)s,
                        %(open_charts)s, %(ea_names)s, %(traded_pairs)s, %(deposit_withdrawal)s,
                        %(margin_percent)s, %(realized_pl_daily)s, %(realized_pl_weekly)s,
                        %(realized_pl_monthly)s, %(realized_pl_yearly)s
                    )
                    ON CONFLICT (account_number) DO UPDATE SET
                        broker = EXCLUDED.broker,
                        balance = EXCLUDED.balance,
                        equity = EXCLUDED.equity,
                        free_margin = EXCLUDED.free_margin,
                        profit_loss = EXCLUDED.profit_loss,
                        open_charts = EXCLUDED.open_charts,
                        ea_names = EXCLUDED.ea_names,
                        traded_pairs = EXCLUDED.traded_pairs,
                        deposit_withdrawal = EXCLUDED.deposit_withdrawal,
                        margin_percent = EXCLUDED.margin_percent,
                        realized_pl_daily = EXCLUDED.realized_pl_daily,
                        realized_pl_weekly = EXCLUDED.realized_pl_weekly,
                        realized_pl_monthly = EXCLUDED.realized_pl_monthly,
                        realized_pl_yearly = EXCLUDED.realized_pl_yearly;
                """, data)
                conn.commit()

        logger.info("✅ Data stored successfully")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"❌ API Processing Error: {e}")
        return jsonify({"error": str(e)}), 400

# ✅ Run Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
