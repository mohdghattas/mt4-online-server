import os
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

db_file = os.path.join(os.path.dirname(__file__), "mt4_data.db")
print("[DEBUG] Database file location:", db_file)

if not os.path.exists(db_file):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number INTEGER,
            balance REAL,
            equity REAL,
            margin_used REAL,
            free_margin REAL,
            margin_level REAL,
            open_trades INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        data = request.json
        print("[DEBUG] Received raw data:", request.data.decode("utf-8"))  # Print raw JSON
        print("[DEBUG] Parsed JSON:", data)  # Print parsed JSON

        account_number = data.get("account_number")
        balance = data.get("balance")
        equity = data.get("equity")
        margin_used = data.get("margin_used")
        free_margin = data.get("free_margin")
        margin_level = data.get("margin_level")
        open_trades = data.get("open_trades")

        if not account_number:
            return jsonify({"error": "Missing account_number"}), 400

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM accounts WHERE account_number = ?", (account_number,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE accounts
                SET balance = ?, equity = ?, margin_used = ?, free_margin = ?, margin_level = ?, open_trades = ?, timestamp = CURRENT_TIMESTAMP
                WHERE account_number = ?
            ''', (balance, equity, margin_used, free_margin, margin_level, open_trades, account_number))
        else:
            cursor.execute('''
                INSERT INTO accounts (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (account_number, balance, equity, margin_used, free_margin, margin_level, open_trades))

        conn.commit()
        conn.close()

        return jsonify({"message": "Data stored successfully"}), 200
    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))
        return jsonify({"error": str(e)}), 500



@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        accounts = [
            {
                "id": row[0],
                "account_number": row[1],
                "balance": row[2],
                "equity": row[3],
                "margin_used": row[4],
                "free_margin": row[5],
                "margin_level": row[6],
                "open_trades": row[7],
                "timestamp": row[8]
            }
            for row in rows
        ]

        return jsonify({"accounts": accounts}), 200
    except Exception as e:
        print("[ERROR] Exception occurred:", str(e))  # Print error logs
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Read PORT from environment
    print("[DEBUG] Starting Flask on port:", port)
    app.run(host="0.0.0.0", port=port)
