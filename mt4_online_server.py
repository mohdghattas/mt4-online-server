import json
import sqlite3
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
DB_PATH = "mt4_data.db"
TABLE_NAME = "trade_stats"  # example table name where data is stored

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Initialize database connection (thread-safe for HTTPServer usage if needed)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Ensure the main table exists (create if not exists with at least an ID and timestamp)
cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT
        /* other initial columns can be defined here if known, e.g. balance, equity, etc. */
    )
""")
conn.commit()

# Function to ensure a column exists in the table (adds if missing)
def ensure_column_exists(column_name, value_example=None):
    """Check if column exists in TABLE_NAME; if not, alter table to add it."""
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [row[1] for row in cursor.fetchall()]  # PRAGMA table_info returns list of columns in position 1
    if column_name not in columns:
        # Determine column type based on example value (if provided)
        # Default to TEXT if type cannot be determined
        col_type = "TEXT"
        if value_example is not None:
            if isinstance(value_example, int):
                col_type = "INTEGER"
            elif isinstance(value_example, float):
                col_type = "REAL"
            elif isinstance(value_example, bool):
                # Store booleans as integers 0/1
                col_type = "INTEGER"
            # (For strings, TEXT is already the default)
        try:
            logging.info(f"Adding missing column '{column_name}' to table {TABLE_NAME} ({col_type})")
            cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {column_name} {col_type}")
            conn.commit()
        except Exception as e:
            # Ignore error if column already exists (in case of race condition) or log other errors
            if "duplicate column name" in str(e).lower():
                logging.warning(f"Column '{column_name}' already exists (caught duplicate error).")
            else:
                logging.error(f"Error adding column '{column_name}': {e}")

# Custom HTTP request handler
class MT4RequestHandler(BaseHTTPRequestHandler):
    # Buffer to accumulate data (class-level, one per connection if keep-alive is used)
    buffer = ""

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            # No data to read
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No JSON payload received")
            return

        # Read the raw POST body data
        raw_data = self.rfile.read(content_length).decode('utf-8', errors='ignore')
        # Append to buffer (in case of partial data or multiple JSON objects concatenated)
        MT4RequestHandler.buffer += raw_data

        # Try to parse as many JSON objects as possible from the buffer
        decoder = json.JSONDecoder()
        data_objects = []
        while MT4RequestHandler.buffer:
            MT4RequestHandler.buffer = MT4RequestHandler.buffer.lstrip()  # strip any leading whitespace/newlines
            try:
                obj, index = decoder.raw_decode(MT4RequestHandler.buffer)
            except json.JSONDecodeError:
                # Incomplete or malformed JSON at the current position
                break  # break out to wait for more data (or end if none)
            # If decoded successfully, append the object and trim the buffer
            data_objects.append(obj)
            MT4RequestHandler.buffer = MT4RequestHandler.buffer[index:]  # remove the parsed JSON from buffer

        # Process each fully parsed JSON object
        for data in data_objects:
            if not isinstance(data, dict):
                # If the JSON root is not an object (dict), skip it
                logging.warning("Received JSON is not an object/dict, skipping.")
                continue

            # Ensure required columns exist for all keys in the JSON data
            for key, value in data.items():
                if key is None:
                    continue
                ensure_column_exists(key, value)

            # Also ensure the specific `realized_pl_alltime` column exists (for safety, even if not in this payload)
            # This is somewhat redundant if the key is present in data, but covers cases where we expect it even if value is 0/missing.
            ensure_column_exists("realized_pl_alltime", data.get("realized_pl_alltime", 0.0))

            # Prepare SQL insertion of the data into the table
            # Using parameterized query for safety
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            values = list(data.values())
            try:
                cursor.execute(f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})", values)
                conn.commit()
                logging.info(f"Inserted data: {data}")
            except Exception as e:
                logging.error(f"Database insertion error: {e}")
                # (Optional) send an error response or handle accordingly

        # Send success response after processing all objects
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # Overriding to reduce console output (optional)
        return

# Start the HTTP server (listening on a port, e.g., 8080)
def run_server(server_class=HTTPServer, handler_class=MT4RequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info(f"Starting MT4 API server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        logging.info("Shutting down server.")
        httpd.server_close()
        conn.close()

if __name__ == "__main__":
    run_server()
