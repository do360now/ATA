from gpt_trading_decision import gpt_trading_decision
from indicators import fetch_latest_news, calculate_sentiment, calculate_moving_average, calculate_rsi, calculate_macd
from trading_strategy import trading_strategy
from portfolio import rebalance_portfolio
from api_kraken import KrakenAPI
from logger_config import logger
from config import API_KEY, API_SECRET, API_DOMAIN, SLEEP_DURATION
from version import __version__

# Initialize Kraken API client
kraken_api = KrakenAPI(API_KEY, API_SECRET, API_DOMAIN)


def portfolio_manager():
    
    # Mock data for testing
    latest_price = kraken_api.get_btc_price()
    # Load initial historical data
    logger.info("Fetching historical BTC data...")
    historical_prices = kraken_api.get_historical_prices()
    prices = historical_prices if historical_prices else []
    if not prices:
        logger.warning("No historical prices fetched, starting with an empty dataset.")
    else:
        logger.info(f"Loaded {len(prices)} historical prices.")


    # articles = fetch_latest_news()
    # sentiment = calculate_sentiment(articles)
    sentiment = 0.3 # Mock sentiment score
    logger.info(f"Updated sentiment score: {sentiment}")

    # Calculate technical indicators
    logger.info("Calculating technical indicators...")
    moving_average = calculate_moving_average(prices)
    rsi = calculate_rsi(prices)
    macd, signal_line = calculate_macd(prices)
    logger.info(f"Moving Average: {moving_average}")
    logger.info(f"RSI: {rsi}")
    logger.info(f"MACD: {macd}")
    logger.info(f"Signal Line: {signal_line}")

     # Rebalance the portfolio
    logger.info("Rebalancing portfolio...")
    portfolio = rebalance_portfolio()


    decision = gpt_trading_decision(latest_price, historical_prices, sentiment, moving_average, rsi, macd, signal_line, portfolio)
            # Display the current script version
    logger.info("Portfolio Manager %s", __version__)
    
        
   # Rebalance the portfolio
    logger.info("Rebalancing portfolio...")
    rebalance_portfolio()

    # Execute the trading strategy
    logger.info("Executing trading strategy...")
    logger.info(f"Trading Decision: {decision}")
  
    # trading_strategy(prices)


if __name__ == "__main__":
    portfolio_manager()
