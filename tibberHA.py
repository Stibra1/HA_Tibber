import requests
import json
from datetime import datetime
import numpy as np

# Replace with your actual Tibber access token
access_token = 'access_token_here'

# The GraphQL query
query = {
    "query": """
    {
      viewer {
        homes {
          currentSubscription{
            priceInfo{
              current{
                total
                startsAt
              }
              today {
                total
                startsAt
              }
            }
          }
        }
      }
    }
    """
}

# The Tibber API endpoint for GraphQL queries
url = 'https://api.tibber.com/v1-beta/gql'

# The headers including the Authorization token
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Make a POST request to the Tibber API
response = requests.post(url, json=query, headers=headers)

# Ensure the request was successful
if response.status_code != 200:
    print("Failed to fetch data:", response.status_code, response.text)
    exit()

# Extracting the data
data = response.json()

# Extracting the "today" pricing data
prices_today = data['data']['viewer']['homes'][0]['currentSubscription']['priceInfo']['today']

# Checking and extracting the current price data, if available
current_price_data = data['data']['viewer']['homes'][0]['currentSubscription']['priceInfo'].get('current')


if current_price_data:
    current_price = float(current_price_data['total'])
    current_hour = datetime.fromisoformat(current_price_data['startsAt']).hour
else:
    current_price = None
    current_hour = datetime.now().hour

# Prepare data for today
timestamps_today = [datetime.fromisoformat(entry['startsAt']) for entry in prices_today]
prices_today = [float(entry['total']) for entry in prices_today]

# Calculate average, minimum, and maximum prices for today
average_price_today = round(np.mean(prices_today), 2)
min_price_today = round(min(prices_today), 2)
max_price_today = round(max(prices_today), 2)

# Function to classify the price level
def classify_price(price, min_price, avg_price, max_price):
    if price <= min_price:
        return 0
    elif min_price < price <= avg_price:
        return int((price - min_price) / ((avg_price - min_price) / 5)) + 1
    elif avg_price < price < max_price:
        return int((price - avg_price) / ((max_price - avg_price) / 5)) + 6
    else:
        return 10

# Get the current price
current_price = float(current_price_data['total'])
current_hour = datetime.fromisoformat(current_price_data['startsAt']).hour

# Modify the classification function and the call to it based on the availability of current_price
if current_price is not None:
    price_level = classify_price(current_price, min_price_today, average_price_today, max_price_today)
else:
    price_level = "No current price data available"

# Print the results for debugging
print(f"Average Price Today: {average_price_today}, Min Price Today: {min_price_today}, Max Price Today: {max_price_today}")
print(f"Current Hour: {current_hour}, Current Price: {current_price}, Price Level: {price_level}")

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Define your connection parameters
influxdb_token = 'influxdb token here'
influxdb_org = 'organization'
influxdb_bucket = 'bucket'
influxdb_url = 'http://192.168.86.53:8086'  #host:8086

# Create a client
client = InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)

# Create a write API
write_api = client.write_api(write_options=SYNCHRONOUS)

# Current time for timestamp
current_time = datetime.utcnow()

# Modify the points to reflect today's data
point_max_price = Point("max_price").tag("unit", "currency").field("value", max_price_today).time(current_time, WritePrecision.NS)
point_average_price = Point("average_price").tag("unit", "currency").field("value", average_price_today).time(current_time, WritePrecision.NS)
point_min_price = Point("min_price").tag("unit", "currency").field("value", min_price_today).time(current_time, WritePrecision.NS)
point_price_level = Point("price_level").tag("unit", "currency").field("value", price_level).time(current_time, WritePrecision.NS)

# Write the points to the database
write_api.write(bucket=influxdb_bucket, org=influxdb_org, record=[point_max_price, point_average_price, point_min_price, point_price_level])


# Close the client
client.close()

##############################
# Sensors for Home Assistant #
##############################

# sensor:
#   - platform: time_date
#     display_options:
#       - 'time'
#       - 'date'
#       - 'date_time'
#       - 'date_time_utc'
#       - 'date_time_iso'
#       - 'time_date'
#       - 'time_utc'
#       - 'beat'
#   - platform: influxdb
#     api_version: 2
#     ssl: false
#     host: 192.168.86.53
#     port: 8086
#     token: influxdb token
#     organization: iota
#     bucket: tibber
#     queries_flux:
#       - group_function: last
#         imports:
#           - strings
#         name: "Average Price"
#         query: >
#           filter(fn: (r) => r._field == "value" and r._measurement == "average_price")
#         range_start: "-2h"
#         value_template: "{{ value | float }}"
#   - platform: influxdb
#     api_version: 2
#     ssl: false
#     host: 192.168.86.53
#     port: 8086
#     token: influxdb token
#     organization: iota
#     bucket: tibber
#     queries_flux:
#       - group_function: last
#         imports:
#           - strings
#         name: "Max Price"
#         query: >
#           filter(fn: (r) => r._field == "value" and r._measurement == "max_price")
#         range_start: "-2h"
#         value_template: "{{ value | float }}"
#   - platform: influxdb
#     api_version: 2
#     ssl: false
#     host: 192.168.86.53
#     port: 8086
#     token: influxdb token
#     organization: iota
#     bucket: tibber
#     queries_flux:
#       - group_function: last
#         imports:
#           - strings
#         name: "Min Price"
#         query: >
#           filter(fn: (r) => r._field == "value" and r._measurement == "min_price")
#         range_start: "-2h"
#         value_template: "{{ value | float }}"
#   - platform: influxdb
#     api_version: 2
#     ssl: false
#     host: 192.168.86.53
#     port: 8086
#     token: influxdb token
#     organization: iota
#     bucket: tibber
#     queries_flux:
#       - group_function: last
#         imports:
#           - strings
#         name: "Price Level"
#         query: >
#           filter(fn: (r) => r._field == "value" and r._measurement == "price_level")
#         range_start: "-2h"
#         value_template: "{{ value | float }}"