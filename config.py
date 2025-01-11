import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get API credentials from environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Ensure critical environment variables are set
if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY or API_SECRET is missing. Please check your environment variables.")

# API-related constants
API_DOMAIN = os.getenv("API_DOMAIN", "https://api.kraken.com")

# Allocation strategy for portfolio management
ALLOCATIONS = {
    'HODL': float(os.getenv("ALLOC_HODL")),
    'YIELD': float(os.getenv("ALLOC_YIELD")),
    'TRADING': float(os.getenv("ALLOC_TRADING")),
}

# Initial BTC balance
TOTAL_BTC = float(os.getenv("TOTAL_BTC"))


# Minimum trading volume to avoid very small trades
MIN_TRADE_VOLUME = float(os.getenv("MIN_TRADE_VOLUME"))

# Cooldown period in seconds between trades
GLOBAL_TRADE_COOLDOWN = int(os.getenv("GLOBAL_TRADE_COOLDOWN"))  # 5 minutes
