from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_caching import Cache
import http.client
import json
import uuid
import datetime

app = Flask(__name__)
CORS(app)

# Cache configuration
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # Cache timeout in seconds (1 hour)
cache = Cache(app)

# API Configuration
api_key = "lzhm90WFGxn0kaEu33g4qTl2t39tOIWz"  # Replace with your API key
access_token = "Am0sdzGAAzm7gyGVdHMjfrjEufBr"  # Replace with your access token
base_url = "api.onegov.nsw.gov.au"

# Station codes
STATION_CODES = ["1842", "1925", "1926", "1372", "945", "243", "1413", "233", "162"]

@cache.cached(timeout=3600, key_prefix="fuel_prices")
def fetch_fuel_prices():
    """Fetch fuel prices for all stations and cache for 1 hour."""
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",
        "apikey": api_key,
        "transactionid": str(uuid.uuid4()),
        "requesttimestamp": datetime.datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S %p"),
    }

    conn = http.client.HTTPSConnection(base_url)
    table_data = []

    try:
        for station_code in STATION_CODES:
            endpoint = f"/FuelPriceCheck/v2/fuel/prices/station/{station_code}"
            conn.request("GET", endpoint, headers=headers)
            response = conn.getresponse()
            data = response.read()

            # Decode and parse JSON response
            response_text = data.decode("utf-8")
            station_data = json.loads(response_text)

            # Extract fuel prices
            station_prices = {"Station Code": station_code}
            for price_data in station_data.get("prices", []):
                fuel_type = price_data["fueltype"]
                price = price_data["price"]
                station_prices[fuel_type] = price

            table_data.append(station_prices)
    except Exception as e:
        print(f"Error fetching fuel prices: {e}")
    finally:
        conn.close()

    return table_data

@app.route("/")
def index():
    """Render the main page with the table."""
    return render_template("Fuleprice.html")

@app.route("/api/fuel-prices")
def fuel_prices():
    """API endpoint to fetch live fuel prices."""
    table_data = fetch_fuel_prices()

    # Format table rows
    formatted_table = []
    for row in table_data:
        formatted_table.append({
            "Station Code": row.get("Station Code", ""),
            "E10": row.get("E10", "N/A"),
            "U91": row.get("U91", "N/A"),
            "P98": row.get("P98", "N/A"),
            "PDL": row.get("PDL", "N/A"),
        })
    return jsonify(formatted_table)

if __name__ == "__main__":
    app.run(debug=True)
