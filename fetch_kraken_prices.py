import requests

def get_latest_price(pair="XBTUSDT"):
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        # Extracting the latest price
        price = data["result"][list(data["result"].keys())[0]]["c"][0]
        return float(price)
    else:
        print(f"Error: {data['error']}")
        return None

def get_historical_prices(pair="XBTUSDT", interval=60):
    """
    Get historical prices for the past 24 hours.
    Interval options: 1 (minute), 5, 15, 30, 60 (hour), 240, 1440 (day), 10080 (week).
    """
    url = f"https://api.kraken.com/0/public/OHLC?pair={pair}&interval={interval}"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        # Extract historical prices (timestamp, open, high, low, close)
        historical_prices = [
            {"time": entry[0], "open": float(entry[1]), "high": float(entry[2]), 
             "low": float(entry[3]), "close": float(entry[4])}
            for entry in data["result"][list(data["result"].keys())[0]]
        ]
        return historical_prices
    else:
        print(f"Error: {data['error']}")
        return None

if __name__ == "__main__":
    # Test functions
    print("Latest Price:", get_latest_price())
    print("Historical Prices (past 24h):", get_historical_prices())
