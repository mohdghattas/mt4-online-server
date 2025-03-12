from flask import Flask, request, jsonify
import logging
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Assuming use of an ORM like SQLAlchemy for a table "account_stats"
from models import AccountStats, db  # hypothetical import of the ORM model and db session

@app.route('/updateStats', methods=['POST'])
def update_stats():
    # 1. Content-Type validation
    if request.content_type is None or "application/json" not in request.content_type.lower():
        app.logger.warning(f"Unsupported Content-Type: {request.content_type}")
        return jsonify({"error": "Unsupported Media Type. Please use application/json"}), 415

    # 2. JSON parsing with error handling
    try:
        data = request.get_json(force=True)  # force parse JSON
    except Exception as e:
        app.logger.error(f"JSONDecodeError: {e}. Body: {request.data}")
        return jsonify({"error": "Bad Request - JSON parse error"}), 400
    if data is None:
        # get_json may return None if JSON is empty or invalid even with force
        app.logger.error(f"No JSON payload received. Body: {request.data}")
        return jsonify({"error": "Bad Request - no JSON data"}), 400

    # 3. Extract fields from JSON
    # Using dict.get to safely get values (will return None if key is missing, which you can handle as needed)
    realized_pl_daily   = data.get('realized_pl_daily')
    realized_pl_weekly  = data.get('realized_pl_weekly')
    realized_pl_monthly = data.get('realized_pl_monthly')
    realized_pl_yearly  = data.get('realized_pl_yearly')
    margin_percent      = data.get('margin_percent')
    total_deposits      = data.get('total_deposits')
    total_withdrawals   = data.get('total_withdrawals')
    open_charts         = data.get('open_charts')

    # (Optional) Validate that none of these are None if they are all expected to be present.
    # If any important field is missing, you might log or set default.
    # For example:
    # if realized_pl_daily is None:
    #     app.logger.warning("Missing realized_pl_daily in JSON payload")

    # 4. Store to database
    try:
        # If updating an existing entry (assuming one per account), find it first:
        # stats = AccountStats.query.filter_by(account_id = some_id).first()
        # if not stats:
        #     stats = AccountStats(account_id=some_id)
        # Then update fields...
        stats = AccountStats()  # creating new record for simplicity
        stats.realized_pl_daily   = realized_pl_daily
        stats.realized_pl_weekly  = realized_pl_weekly
        stats.realized_pl_monthly = realized_pl_monthly
        stats.realized_pl_yearly  = realized_pl_yearly
        stats.margin_percent      = margin_percent
        stats.total_deposits      = total_deposits
        stats.total_withdrawals   = total_withdrawals
        stats.open_charts         = open_charts

        db.session.add(stats)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Database error on saving stats: {e}")
        return jsonify({"error": "Internal Server Error - DB failure"}), 500

    app.logger.info("Stats updated successfully in the database.")
    return jsonify({"status": "success"}), 200

@app.route('/getStats', methods=['GET'])
def get_stats():
    # Retrieve the latest stats (adjust query as needed for your schema)
    stats = AccountStats.query.order_by(AccountStats.id.desc()).first()
    if not stats:
        return jsonify({"error": "No stats available"}), 404

    # Return all the stats fields in JSON
    return jsonify({
        "realized_pl_daily":   stats.realized_pl_daily,
        "realized_pl_weekly":  stats.realized_pl_weekly,
        "realized_pl_monthly": stats.realized_pl_monthly,
        "realized_pl_yearly":  stats.realized_pl_yearly,
        "margin_percent":      stats.margin_percent,
        "total_deposits":      stats.total_deposits,
        "total_withdrawals":   stats.total_withdrawals,
        "open_charts":         stats.open_charts
    }), 200

# Run the Flask app (in production use a proper WSGI server)
if __name__ == "__main__":
    app.run(debug=True)
