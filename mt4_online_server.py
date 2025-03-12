from flask import Flask, request, jsonify
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/updateStats', methods=['POST'])
def update_stats():
    # Ensure request contains JSON
    if "application/json" not in request.content_type.lower():
        return jsonify({"error": "Unsupported Media Type. Use application/json"}), 415

    # Debug log raw request
    raw_data = request.data
    print("Received raw data:", raw_data)

    # Parse JSON
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as e:
        print("JSON parsing failed:", str(e))
        return jsonify({"error": "Invalid JSON format"}), 400

    # Extract fields
    realized_pl_daily = data.get("realized_pl_daily", 0.0)
    realized_pl_weekly = data.get("realized_pl_weekly", 0.0)
    realized_pl_monthly = data.get("realized_pl_monthly", 0.0)
    realized_pl_yearly = data.get("realized_pl_yearly", 0.0)
    margin_percent = data.get("margin_percent", 0.0)
    total_deposits = data.get("total_deposits", 0.0)
    total_withdrawals = data.get("total_withdrawals", 0.0)
    open_charts = data.get("open_charts", 0)

    # Simulated database save
    print(f"Saving stats: {data}")

    return jsonify({"status": "success"}), 200

@app.route('/getStats', methods=['GET'])
def get_stats():
    # Simulated retrieval of stats
    stats = {
        "realized_pl_daily": 123.45,
        "realized_pl_weekly": -50.0,
        "realized_pl_monthly": 300.0,
        "realized_pl_yearly": 5000.0,
        "margin_percent": 95.6,
        "total_deposits": 10000.0,
        "total_withdrawals": 5000.0,
        "open_charts": 3
    }
    return jsonify(stats), 200

if __name__ == "__main__":
    app.run(debug=True)
