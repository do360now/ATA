import requests
import time
import base64
import hashlib
import hmac
import json
from typing import Optional, List, Dict
from config import API_KEY, API_SECRET, API_DOMAIN
from logger_config import logger
from tenacity import retry, wait_exponential, stop_after_attempt


class KrakenAPI:
    def __init__(self, api_key: str, api_secret: str, api_domain: str):
        self.api_key = api_key
        # Decode the base64-encoded secret
        self.api_secret = base64.b64decode(api_secret)
        self.api_domain = api_domain

    def _sign_request(self, api_path: str, api_nonce: str, api_postdata: str) -> str:
        """
        Creates a cryptographic signature required by the Kraken API for private endpoints.
        """
        # Step 1: SHA-256 of (nonce + POST data)
        api_sha256 = hashlib.sha256(api_nonce.encode('utf-8') + api_postdata.encode('utf-8')).digest()
        # Step 2: HMAC-SHA512 of (API path + previous hash), keyed by the API secret
        api_hmacsha512 = hmac.new(self.api_secret, api_path.encode('utf-8') + api_sha256, hashlib.sha512)
        # Step 3: Base64-encode the final HMAC
        return base64.b64encode(api_hmacsha512.digest()).decode()

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
    def _make_request(self, method: str, path: str, data: Optional[Dict] = None, is_private: bool = False) -> Optional[Dict]:
        """
        Handles GET (public) and POST (private) requests to the Kraken API.
        Retries on failure, up to 5 attempts with exponential backoff.
        """
        url = f"{self.api_domain}{path}{method}"
        headers = {"User-Agent": "Kraken REST API"}

        if is_private:
            # For private endpoints, add the necessary authentication headers
            nonce = str(int(time.time() * 1000))
            if not data:
                data = {}
            data['nonce'] = nonce
            # Construct POST data as key=value pairs joined by '&'
            post_data_string = "&".join([f"{key}={value}" for key, value in data.items()])
            headers["API-Key"] = self.api_key
            headers["API-Sign"] = self._sign_request(path + method, nonce, post_data_string)

        try:
            logger.info(f"Making {method} request to {url} with data: {data}")
            if is_private:
                # Private endpoints typically use POST
                response = requests.post(url, headers=headers, data=data)
            else:
                # Public endpoints typically use GET
                response = requests.get(url, headers=headers, params=data)

            # Raise if we get an HTTP error
            response.raise_for_status()

            api_reply = response.json()

            # Kraken usually returns an 'error' array; check if it has any entries
            if 'error' in api_reply and len(api_reply['error']) > 0:
                logger.error(f"API error: {api_reply['error']}")
                return None

            return api_reply.get('result', None)

        except requests.RequestException as error:
            logger.error(f"API call failed with error: {error}")
            return None

    def get_btc_order_book(self) -> Optional[Dict]:
        """
        Gets the current order book for BTC/USDT.
        """
        result = self._make_request(method="Depth", path="/0/public/", data={"pair": "XBTUSDT"})
        if result:
            return result.get('XBTUSDT')
        return None

    def get_optimal_price(self, order_book: Dict, side: str, buffer: float = 0.05) -> Optional[float]:
        """
        Calculates an optimal price for buying or selling based on the order book.
        A buffer amount is added or subtracted from the best bid/ask to get a slightly better fill.
        """
        if side == "buy":
            best_ask = float(order_book['asks'][0][0])
            optimal_price = best_ask - buffer
        elif side == "sell":
            best_bid = float(order_book['bids'][0][0])
            optimal_price = best_bid + buffer
        else:
            return None

        # Round the optimal price to 1 decimal place (Kraken often accepts prices up to 1 decimal)
        return round(optimal_price, 1)

    def get_historical_prices(self, pair: str = "XBTUSDT", interval: int = 60, since: Optional[int] = None) -> List[float]:
        """
        Fetches historical OHLC (Open/High/Low/Close) data for the given pair.
        Returns a list of closing prices.
        """
        data = {"pair": pair, "interval": interval}
        if since:
            data["since"] = since

        result = self._make_request(method="OHLC", path="/0/public/", data=data)
        if result:
            # Each entry in the OHLC array is [time, open, high, low, close, vwap, volume, count]
            return [float(entry[4]) for entry in result.get(pair, [])]
        return []

    def get_btc_price(self) -> Optional[float]:
        """
        Fetches the current BTC price in USDT.
        """
        result = self._make_request(method="Ticker", path="/0/public/", data={"pair": "XBTUSDT"})
        if result:
            # 'c' typically represents the current "last trade closed" price
            return float(result['XBTUSDT']['c'][0])
        return None

    def execute_trade(self, volume: float, side: str) -> None:
        """
        Executes a limit order to buy or sell a specified volume of BTC at an optimal price.
        """
        order_book = self.get_btc_order_book()
        if order_book:
            optimal_price = self.get_optimal_price(order_book, side)
            if optimal_price:
                data = {
                    "pair": "XBTUSDT",
                    "type": side,
                    "ordertype": "limit",
                    "price": optimal_price,
                    "volume": volume,
                }
                result = self._make_request(method="AddOrder", path="/0/private/", data=data, is_private=True)
                if result:
                    logger.info(
                        f"\033[92mExecuted {side} order for {volume} BTC at {optimal_price}.\033[0m "
                        f"Order response: {result}"
                    )

    def get_market_volume(self, pair: str = "XBTUSDT") -> Optional[float]:
        """
        Fetches the 24-hour trading volume for a given pair.
        """
        result = self._make_request(method="Ticker", path="/0/public/", data={"pair": pair})
        if result:
            try:
                volume_data = result[pair].get('v', [])
                # v[1] is the 24-hour volume
                if len(volume_data) > 1:
                    return float(volume_data[1])
                else:
                    logger.error("Volume data is incomplete.")
            except (KeyError, ValueError, IndexError) as e:
                logger.error(f"Error retrieving market volume: {e}")
        return None

    def get_total_btc_balance(self) -> Optional[float]:
        """
        Returns the total BTC balance in your Kraken account.
        Requires private access/keys with 'Balance' permission.
        """
        result = self._make_request(method="Balance", path="/0/private/", is_private=True)
        # The returned JSON should include an 'XBT.F' field for BTC
        if result and 'XBT.F' in result:
            return float(result['XBT.F'])
        else:
            logger.warning("BTC balance not found in the API response.")
            return None


if __name__ == "__main__":
    # Example usage:
    kraken_api = KrakenAPI(API_KEY, API_SECRET, API_DOMAIN)
    
    btc_balance = kraken_api.get_total_btc_balance()
    if btc_balance is not None:
        logger.info(f"Your total BTC balance is: {btc_balance}")
    else:
        logger.info("Could not retrieve BTC balance.")
