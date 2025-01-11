import time
from api_kraken import KrakenAPI
from indicators import (
    calculate_moving_average,
    calculate_rsi,
    calculate_macd,
    calculate_potential_profit_loss,
    is_profitable_trade,
    calculate_sentiment,
    fetch_latest_news,
)
from portfolio import portfolio
from config import MIN_TRADE_VOLUME, API_KEY, API_SECRET, API_DOMAIN
from logger_config import logger
from typing import List, Optional
from termcolor import colored

# Initialize Kraken API client
kraken_api = KrakenAPI(API_KEY, API_SECRET, API_DOMAIN)

class TradingStrategy:
    def __init__(self, prices: Optional[List[float]] = None):
        self.prices = prices if prices else []
        self.last_buy_price = None
        self.last_sell_price = None
        self.last_trade_type = None
        self.cooldown_end_time = 0  # Track cooldown period
        self.stop_loss_percent = 0.03  # 3% stop loss
        self.take_profit_percent = 0.15  # 15% take profit
        self.sentiment_score = 0.0

    def update_sentiment(self):
        articles = fetch_latest_news()
        self.sentiment_score = calculate_sentiment(articles)
        logger.info(f"Updated sentiment score: {self.sentiment_score}")

    def execute_strategy(self):
        self.update_sentiment()

        current_price = kraken_api.get_btc_price()
        if current_price is None:
            logger.error("Failed to retrieve BTC price.")
            return

        self.prices.append(current_price)
        if len(self.prices) > 1000:
            self.prices.pop(0)  # keep only the latest 1000

        logger.debug(f"[execute_strategy] Current price history length: {len(self.prices)}")  # NEW LOG

        # Calculate indicators
        moving_avg = calculate_moving_average(self.prices)
        rsi = calculate_rsi(self.prices)
        macd, signal = calculate_macd(self.prices)

        logger.info(f"Current BTC Price: {current_price}, Moving Average: {moving_avg}, "
                    f"RSI: {rsi}, MACD: {macd}, Signal: {signal}, Sentiment Score: {self.sentiment_score}")

        # NEW LOG: Log if any of them are None
        if moving_avg is None:
            logger.debug("[execute_strategy] moving_avg is None - not enough data yet?")
        if rsi is None:
            logger.debug("[execute_strategy] rsi is None - not enough data yet?")
        if macd is None or signal is None:
            logger.debug("[execute_strategy] macd or signal is None - not enough data yet?")

        if moving_avg and rsi and macd and signal:
            self._determine_trade_action(current_price, macd, signal, rsi)
            self

    def _determine_trade_action(self, current_price: float, macd: float, signal: float, rsi: float):
        logger.debug(f"[_determine_trade_action] macd={macd}, signal={signal}, rsi={rsi}, sentiment={self.sentiment_score}")  # NEW LOG

        # Integrate sentiment
        if self.sentiment_score > 0.5:
            logger.info("Strong positive sentiment detected. Considering more aggressive buying opportunity...")
            adjusted_rsi_threshold = 65
            if macd > signal * 0.9 and rsi < adjusted_rsi_threshold:
                logger.info(f"MACD ({macd}) > 0.9 * Signal ({signal}) and RSI ({rsi}) < {adjusted_rsi_threshold}. Executing buy.")
                self._execute_buy(current_price)
            else:
                logger.info(colored(f"Conditions not met for buying despite strong positive sentiment: MACD {macd}, Signal {signal}, RSI {rsi}.", 'yellow'))

        elif 0.1 < self.sentiment_score <= 0.5:
            logger.info("Moderate positive sentiment detected. Considering buying opportunity...")
            if macd > signal and rsi < 60:
                logger.info(f"MACD ({macd}) > Signal ({signal}) and RSI ({rsi}) < 60 with moderate positive sentiment. Executing buy.")
                self._execute_buy(current_price)
            else:
                logger.info(colored(f"Conditions not met for buying despite moderate positive sentiment: MACD {macd}, Signal {signal}, RSI {rsi}.", 'yellow'))

        elif self.sentiment_score < -0.5:
            logger.info("Strong negative sentiment detected. Considering more aggressive selling opportunity...")
            adjusted_rsi_threshold = 50
            if macd < signal * 1.1 and rsi > adjusted_rsi_threshold:
                logger.info(f"MACD ({macd}) < 1.1 * Signal ({signal}) and RSI ({rsi}) > {adjusted_rsi_threshold}. Executing sell.")
                self._execute_sell(current_price)
            else:
                logger.info(colored(f"Conditions not met for selling despite strong negative sentiment: MACD {macd}, Signal {signal}, RSI {rsi}.", 'yellow'))

        elif -0.5 <= self.sentiment_score < -0.1:
            logger.info("Moderate negative sentiment detected. Considering selling opportunity...")
            if macd < signal and rsi > 45:
                logger.info(f"MACD ({macd}) < Signal ({signal}) and RSI ({rsi}) > 45 with moderate negative sentiment. Executing sell.")
                self._execute_sell(current_price)
            else:
                logger.info(colored(f"Conditions not met for selling despite moderate negative sentiment: MACD {macd}, Signal {signal}, RSI {rsi}.", 'yellow'))

        else:
            logger.info("Neutral sentiment detected. Proceeding with regular MACD and RSI checks.")
            if macd > signal and rsi < 40:
                logger.info(f"MACD ({macd}) > Signal ({signal}) and RSI ({rsi}) < 40. Executing buy.")
                self._execute_buy(current_price)
            elif macd < signal and rsi > 60:
                logger.info(f"MACD ({macd}) < Signal ({signal}) and RSI ({rsi}) > 60. Executing partial sell.")
                self._execute_partial_sell(current_price)
            else:
                logger.info(colored(f"No trade signal detected: MACD {macd}, Signal {signal}, RSI {rsi}. "
                                    f"Conditions for buying: MACD > Signal and RSI < 40. "
                                    f"Conditions for selling: MACD < Signal and RSI > 60.", 'yellow'))

    def _execute_buy(self, current_price: float):
        # NEW LOG
        logger.debug(f"[_execute_buy] last_sell_price={self.last_sell_price}, last_trade_type={self.last_trade_type}, current_price={current_price}")

        potential_profit_loss = None
        if self.last_sell_price:
            potential_profit_loss = calculate_potential_profit_loss(current_price, self.last_sell_price)
        logger.debug(f"[_execute_buy] potential_profit_loss={potential_profit_loss}")  # NEW LOG

        # Check market volume to ensure buying during upward momentum
        market_volume = kraken_api.get_market_volume()
        logger.debug(f"[_execute_buy] market_volume={market_volume}")  # NEW LOG

        if market_volume and market_volume < 100:
            logger.info(f"Market volume ({market_volume}) is too low for a confident buy. Skipping buy action.")
            return

        # Check if last trade was also 'buy', or if the trade is profitable
        if (potential_profit_loss is None or is_profitable_trade(potential_profit_loss)):
            logger.info(colored(f"Buying BTC... Potential Profit: {potential_profit_loss if potential_profit_loss else 0:.2f}%, Market Volume: {market_volume}", 'green'))
            kraken_api.execute_trade(portfolio.portfolio['TRADING'], 'buy')
            self.last_buy_price = current_price
            self.last_trade_type = 'buy'
        else:
            # NEW LOG: Let us know exactly why we skipped
            reason_msg = "Already in buy mode" if self.last_trade_type == 'buy' else f"Not profitable yet (profit={potential_profit_loss}%)"
            logger.info(colored(f"Skipping buy action. Reason: {reason_msg}", 'yellow'))

    def _execute_sell(self, current_price: float):
        logger.debug(f"[_execute_sell] last_buy_price={self.last_buy_price}, last_trade_type={self.last_trade_type}, current_price={current_price}")
        potential_profit_loss = None
        if self.last_buy_price:
            potential_profit_loss = calculate_potential_profit_loss(current_price, self.last_buy_price)
        logger.debug(f"[_execute_sell] potential_profit_loss={potential_profit_loss}")  # NEW LOG

        if self.last_trade_type != 'sell' and (potential_profit_loss is None or is_profitable_trade(potential_profit_loss)):
            logger.info(colored(f"Selling BTC... Potential Profit: {potential_profit_loss if potential_profit_loss else 0:.2f}%", 'red'))
            kraken_api.execute_trade(portfolio.portfolio['TRADING'], 'sell')
            self.last_sell_price = current_price
            self.last_trade_type = 'sell'
        else:
            reason_msg = "Already in sell mode" if self.last_trade_type == 'sell' else f"Not profitable yet (profit={potential_profit_loss}%)"
            logger.info(colored(f"Skipping sell action. Reason: {reason_msg}", 'yellow'))

    def _execute_partial_sell(self, current_price: float):
        logger.debug(f"[_execute_partial_sell] last_buy_price={self.last_buy_price}, last_trade_type={self.last_trade_type}, current_price={current_price}")
        potential_profit_loss = None
        if self.last_buy_price:
            potential_profit_loss = calculate_potential_profit_loss(current_price, self.last_buy_price)
        logger.debug(f"[_execute_partial_sell] potential_profit_loss={potential_profit_loss}")  # NEW LOG

        if self.last_trade_type != 'sell' and (potential_profit_loss is None or is_profitable_trade(potential_profit_loss)):
            logger.info(colored(f"Partially selling BTC... Potential Profit: {potential_profit_loss if potential_profit_loss else 0:.2f}%", 'yellow'))
            kraken_api.execute_trade(portfolio.portfolio['TRADING'] / 2, 'sell')
            self.last_sell_price = current_price
            self.last_trade_type = 'sell'
        else:
            reason_msg = "Already in sell mode" if self.last_trade_type == 'sell' else f"Not profitable yet (profit={potential_profit_loss}%)"
            logger.info(colored(f"Skipping partial sell. Reason: {reason_msg}", 'yellow'))


# Initialize TradingStrategy
trading_strategy_instance = TradingStrategy()

def trading_strategy(prices: List[float]):
    trading_strategy_instance.prices = prices
    trading_strategy_instance.execute_strategy()
