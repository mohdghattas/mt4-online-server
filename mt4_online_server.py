from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

# ✅ Enable Debug Logging
logging.basicConfig(level=logging.DEBUG)

@app.route("/api/mt4data", methods=["POST"])
def receive_mt4_data():
    try:
        raw_data = request.get_data(as_text=True)  # ✅ Capture raw JSON input
        app.logger.debug(f"📥 Raw Request Data: {raw_data}")

        data = request.json  # Convert to JSON object
        app.logger.debug(f"✅ Parsed JSON Data: {data}")

        # ✅ Ensure required fields exist
        required_fields = ["broker", "account_number", "balance", "equity", "free_margin", "profit_loss"]
        for field in required_fields:
            if field not in data:
                app.logger.error(f"❌ Missing field: {field}")
                return jsonify({"error": f"Missing field: {field}"}), 400

        # ✅ Process and store data in database (Placeholder Example)
        account_number = data["account_number"]
        balance = data["balance"]
        equity = data["equity"]
        free_margin = data["free_margin"]
        profit_loss = data["profit_loss"]
        broker = data["broker"]

        app.logger.info(f"✅ Stored Data: {broker} | {account_number} | Balance: {balance} | Equity: {equity} | Free Margin: {free_margin} | P/L: {profit_loss}")

        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        app.logger.error(f"❌ API Processing Error: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# ✅ API Endpoint to Get Accounts
@app.route("/api/accounts", methods=["GET"])
def get_accounts():
    try:
        # Replace with actual database fetching logic
        dummy_data = [
            {"broker": "Swissquote Bank SA", "account_number": 1218923860, "balance": 100000.00, "equity": 99954.69, "free_margin": 98660.80, "profit_loss": -45.31},
            {"broker": "XTB S.A.", "account_number": 6027176, "balance": 2844.85, "equity": 2638.60, "free_margin": 2596.68, "profit_loss": -206.25}
        ]

        return jsonify({"accounts": dummy_data}), 200
    except Exception as e:
        app.logger.error(f"❌ Error fetching accounts: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
