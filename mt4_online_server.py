import json
import logging
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configure logging to file and console for debugging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Database initialization: connect and ensure required table/columns exist
DB_FILE = "accounts.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()
# Ensure table exists with required columns
cur.execute("""
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    balance REAL DEFAULT 0,
    profit_loss REAL DEFAULT 0
)""")
conn.commit()
# Ensure `profit_loss` column exists (if the table was created earlier without it)
# (In SQLite, the above CREATE won't add new columns to an existing table, so do an ALTER if needed)
columns = [col[1] for col in cur.execute("PRAGMA table_info(accounts)")]
if "profit_loss" not in columns:
    try:
        cur.execute("ALTER TABLE accounts ADD COLUMN profit_loss REAL DEFAULT 0")
        logging.info("Added missing `profit_loss` column to accounts table.")
    except Exception as e:
        logging.error(f"Error adding `profit_loss` column: {e}")
        # If using another DB (e.g., MySQL), ensure the column exists via an appropriate query or migration
conn.commit()

@app.route("/api/write", methods=["POST"])
def write_data():
    """Endpoint for MT4 EA to send account data via WebRequest."""
    raw_body = request.data  # raw bytes
    # Log the raw request data for debugging
    logging.info(f"Received raw data: {raw_body}")
    # Check content type header
    content_type = request.headers.get("Content-Type", "")
    if "application/json" not in content_type.lower():
        logging.warning("Missing or incorrect Content-Type. Expected application/json.")
    # Decode JSON payload
    try:
        body_str = raw_body.decode('utf-8').strip()  # decode bytes to string and trim whitespace/newlines
        data = json.loads(body_str)  # parse JSON
    except json.JSONDecodeError as e:
        # JSON format error (e.g., malformed JSON or extra data)
        error_msg = f"Invalid JSON payload: {e.msg} (at position {e.pos})"
        logging.error(f"JSON decoding failed. Error: {error_msg}. Payload: {raw_body}")
        return jsonify({"error": error_msg}), 400

    # Validate required fields in JSON
    required_fields = ["account_id", "balance", "profit_loss"]
    for field in required_fields:
        if field not in data:
            error_msg = f"Missing field: {field}"
            logging.error(f"JSON validation error – {error_msg}. Received JSON: {data}")
            return jsonify({"error": error_msg}), 400

    account_id = str(data["account_id"])
    balance = float(data.get("balance", 0))
    profit_loss = float(data.get("profit_loss", 0))
    logging.info(f"Parsed JSON -> account_id: {account_id}, balance: {balance}, profit_loss: {profit_loss}")

    # Insert or update the record in database
    try:
        # Use INSERT OR REPLACE to upsert the account record (works in SQLite; adjust for other DBs accordingly)
        cur.execute(
            "INSERT OR REPLACE INTO accounts (account_id, balance, profit_loss) VALUES (?, ?, ?)",
            (account_id, balance, profit_loss)
        )
        conn.commit()
        logging.info(f"Database updated for account {account_id}.")
    except Exception as e:
        logging.error(f"Database error while inserting/updating account {account_id}: {e}")
        return jsonify({"error": "Database update failed", "details": str(e)}), 500

    # Respond with success message
    return jsonify({"status": "success", "account_id": account_id}), 200

@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    """Endpoint for dashboard to retrieve all accounts data."""
    try:
        cur.execute("SELECT account_id, balance, profit_loss FROM accounts")
        rows = cur.fetchall()
    except Exception as e:
        logging.error(f"Database query failed: {e}")
        return jsonify({"error": "Database query failed", "details": str(e)}), 500

    # Build result list of accounts
    accounts = []
    for account_id, balance, profit_loss in rows:
        accounts.append({
            "account_id": account_id,
            "balance": balance,
            "profit_loss": profit_loss
        })
    # (Sorting can also be done here if needed, e.g., sorted by profit_loss descending)
    # accounts.sort(key=lambda x: x["profit_loss"], reverse=True)

    return jsonify({"accounts": accounts}), 200

# (Optional) Serve the dashboard page if needed, e.g., if dashboard code is saved as 'dashboard.html':
# @app.route("/")
# def dashboard_page():
#     return app.send_static_file("dashboard.html")

if __name__ == "__main__":
    # Run the Flask app. Disable debug mode in production as needed.
    app.run(host="0.0.0.0", port=5000, debug=True)
