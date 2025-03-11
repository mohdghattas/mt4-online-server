from flask import Flask, request, jsonify
import psycopg2
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "dbname=mt4monitor user=postgres password=yourpassword host=localhost")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# Ensure database has required fields
cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        broker TEXT,
        account_number BIGINT UNIQUE,
        balance NUMERIC,
        equity NUMERIC,
        free_margin NUMERIC,
        margin_used NUMERIC,
        margin_level NUMERIC,
        open_trades INT,
        ea_names TEXT,
        traded_pairs TEXT,
        deposit_balance NUMERIC,
        withdrawal_balance NUMERIC,
        daily_pl NUMERIC,
        weekly_pl NUMERIC,
        monthly_pl NUMERIC,
        yearly_pl NUMERIC,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.json
        broker = data.get("broker", "Unknown Broker")
        account_number = data["account_number"]
        balance = data["balance"]
        equity = data["equity"]
        free_margin = data["free_margin"]
        margin_used = data.get("margin_used", 0)
        margin_level = data.get("margin_level", 0)
        open_trades = data.get("open_trades", 0)
        ea_names = data.get("ea_names", "None")
        traded_pairs = data.get("traded_pairs", "None")
        deposit_balance = data.get("deposit_balance", 0)
        withdrawal_balance = data.get("withdrawal_balance", 0)
        daily_pl = data.get("daily_pl", 0)
        weekly_pl = data.get("weekly_pl", 0)
        monthly_pl = data.get("monthly_pl", 0)
        yearly_pl = data.get("yearly_pl", 0)

        cursor.execute(
            """
            INSERT INTO accounts (broker, account_number, balance, equity, free_margin, margin_used, margin_level, 
                                  open_trades, ea_names, traded_pairs, deposit_balance, withdrawal_balance, 
                                  daily_pl, weekly_pl, monthly_pl, yearly_pl, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (account_number) DO UPDATE SET
                broker = EXCLUDED.broker,
                balance = EXCLUDED.balance,
                equity = EXCLUDED.equity,
                free_margin = EXCLUDED.free_margin,
                margin_used = EXCLUDED.margin_used,
                margin_level = EXCLUDED.margin_level,
                open_trades = EXCLUDED.open_trades,
                ea_names = EXCLUDED.ea_names,
                traded_pairs = EXCLUDED.traded_pairs,
                deposit_balance = EXCLUDED.deposit_balance,
                withdrawal_balance = EXCLUDED.withdrawal_balance,
                daily_pl = EXCLUDED.daily_pl,
                weekly_pl = EXCLUDED.weekly_pl,
                monthly_pl = EXCLUDED.monthly_pl,
                yearly_pl = EXCLUDED.yearly_pl,
                last_updated = NOW()
            """,
            (broker, account_number, balance, equity, free_margin, margin_used, margin_level,
             open_trades, ea_names, traded_pairs, deposit_balance, withdrawal_balance,
             daily_pl, weekly_pl, monthly_pl, yearly_pl)
        )
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"❌ API Processing Error: {e}")
        return jsonify({"error": str(e)}), 400

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    cursor.execute("""
        SELECT broker, account_number, balance, equity, free_margin, margin_used, margin_level, open_trades, 
               ea_names, traded_pairs, deposit_balance, withdrawal_balance, daily_pl, weekly_pl, 
               monthly_pl, yearly_pl FROM accounts ORDER BY daily_pl ASC
    """)
    accounts = cursor.fetchall()
    accounts_list = []
    for row in accounts:
        accounts_list.append({
            "broker": row[0],
            "account_number": row[1],
            "balance": float(row[2]),
            "equity": float(row[3]),
            "free_margin": float(row[4]),
            "margin_used": float(row[5]),
            "margin_level": float(row[6]),
            "open_trades": row[7],
            "ea_names": row[8],
            "traded_pairs": row[9],
            "deposit_balance": float(row[10]),
            "withdrawal_balance": float(row[11]),
            "daily_pl": float(row[12]),
            "weekly_pl": float(row[13]),
            "monthly_pl": float(row[14]),
            "yearly_pl": float(row[15])
        })
    return jsonify({"accounts": accounts_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
