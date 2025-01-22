from flask import Flask, render_template, jsonify
from flask_cors import CORS
import http.client
import json
import uuid
import datetime
import requests
import base64

def get_access_token():
    # Endpoint URL
    url = "https://api.onegov.nsw.gov.au/oauth/client_credential/accesstoken"
    
    # Your credentials
    client_id = "lzhm90WFGxn0kaEu33g4qTl2t39tOIWz"  # API Key
    client_secret = "nrGdAfVX8ut7T5oG"  # API Secret

    # Base64-encode the client_id and client_secret
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    # Headers
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "accept": "application/json"
    }

    # Query Parameters
    params = {
        "grant_type": "client_credentials"
    }

    try:
        # Make the request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an error for bad HTTP responses

        # Parse the response
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"Access Token: {access_token}")
        return access_token
    except requests.exceptions.RequestException as e:
        print(f"Error fetching access token: {e}")
        return None

# Get and print the access token
access_token = get_access_token()
print(f"Access Token: {access_token}")

app = Flask(__name__)
CORS(app)
# API Configuration
api_key = "lzhm90WFGxn0kaEu33g4qTl2t39tOIWz"  # Replace with your API key  # Replace with your access token
base_url = "api.onegov.nsw.gov.au"

# Station codes
STATION_CODES = ["1842", "1925", "1926", "1372", "945", "243", "1413", "233", "162"]

def fetch_fuel_prices():
    """Fetch fuel prices for all stations."""
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
            print(station_data)

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
