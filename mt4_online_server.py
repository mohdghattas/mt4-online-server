from flask import Flask, request, jsonify
import logging
import json
import sqlite3  # Use PostgreSQL if needed

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# ✅ Database Connection Function
def get_db_connection():
    conn = sqlite3.connect("mt4_data.db")  # Replace with PostgreSQL connection if needed
    conn.row_factory = sqlite3.Row
    return conn

# ✅ Create Table If Not Exists
def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        broker TEXT,
        account_number INTEGER UNIQUE,
        balance REAL,
        equity REAL,
        free_margin REAL,
        profit_loss REAL,
        margin_percent REAL,
        open_trades INTEGER
    )
    """)
    conn.commit()
    conn.close()

create_table()  # Ensure table exists on startup

# ✅ Receive Data from MT4 EA
@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.data.decode("utf-8").strip()
        logging.debug(f"📥 Raw Request Data: {raw_data}")

        # ✅ Parse JSON
        json_data = json.loads(raw_data)

        # ✅ Ensure required fields exist
        required_keys = ["broker", "account_number", "balance", "equity", "free_margin", "profit_loss", "margin_percent", "open_trades"]
        for key in required_keys:
            if key not in json_data:
                logging.error(f"❌ Missing key: {key}")
                return jsonify({"error": f"Missing key: {key}"}), 400

        # ✅ Extract Data
        broker = json_data["broker"]
        account_number = json_data["account_number"]
        balance = json_data["balance"]
        equity = json_data["equity"]
        free_margin = json_data["free_margin"]
        profit_loss = json_data["profit_loss"]
        margin_percent = json_data["margin_percent"]
        open_trades = json_data["open_trades"]

        # ✅ Store in Database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO accounts (broker, account_number, balance, equity, free_margin, profit_loss, margin_percent, open_trades)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_number) 
        DO UPDATE SET balance=?, equity=?, free_margin=?, profit_loss=?, margin_percent=?, open_trades=?
        """, (broker, account_number, balance, equity, free_margin, profit_loss, margin_percent, open_trades,
              balance, equity, free_margin, profit_loss, margin_percent, open_trades))

        conn.commit()
        conn.close()

        logging.info(f"✅ Data stored successfully for account {account_number} - Broker: {broker}")
        return jsonify({"message": "Data received successfully"}), 200

    except json.JSONDecodeError as e:
        logging.error(f"❌ JSON Decoding Error: {str(e)}")
        return jsonify({"error": f"JSON Decoding Error: {str(e)}"}), 400

    except Exception as e:
        logging.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": f"API Processing Error: {str(e)}"}), 500

# ✅ Get Data for Dashboard
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT broker, account_number, balance, equity, free_margin, profit_loss, margin_percent, open_trades 
        FROM accounts
        """)
        accounts = cursor.fetchall()
        conn.close()

        account_list = [dict(acc) for acc in accounts]
        return jsonify({"accounts": account_list}), 200

    except Exception as e:
        logging.error(f"❌ API Fetching Error: {str(e)}")
        return jsonify({"error": f"API Fetching Error: {str(e)}"}), 500

# ✅ Start Flask Server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
