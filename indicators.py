import numpy as np
import pandas as pd
from typing import Optional, List
import os
import logging
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
import requests
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk


# Load environment variables from the .env file
load_dotenv()

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get News API credentials from environment variables with error handling
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Ensure NLTK data is available
nltk.download('vader_lexicon')

# Set up Sentiment Intensity Analyzer
sid = SentimentIntensityAnalyzer()

# Cache for latest news
news_cache = {
    "timestamp": None,
    "articles": None
}

def fetch_latest_news(top_n: int = 10) -> Optional[list]:
    """
    Fetch the latest news articles about Bitcoin in English.
    Returns a list of up to 'top_n' articles.
    """
    current_time = datetime.now()
    if news_cache["timestamp"] and (current_time - news_cache["timestamp"]) < timedelta(minutes=25):
        logger.info("Using cached news articles.")
        return news_cache["articles"][:top_n]  # Return only the top_n cached articles

    logger.info("Fetching latest Bitcoin news...")
    url = f"https://newsapi.org/v2/everything?q=bitcoin&sortBy=publishedAt&language=en&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        articles = response.json().get('articles', [])
        news_cache["timestamp"] = current_time
        news_cache["articles"] = articles
        logger.info(f"Successfully fetched {len(articles)} news articles.")

        # Log the titles and URLs of the articles
        for article in articles[:top_n]:  # Log only the top_n articles
            title = article.get('title', 'No Title Available')
            article_url = article.get('url', 'No URL Available')
            logger.info(f"Article Title: {title}")
            logger.info(f"Article URL: {article_url}")

        return articles[:top_n]  # Return only the top_n articles
    else:
        logger.error(f"Failed to fetch news. Status code: {response.status_code}")
        return None


# Function to analyze the sentiment of news articles
def calculate_sentiment(articles: Optional[list]) -> float:
    """
    Analyze the sentiment of news articles.
    """
    total_sentiment = 0
    if not articles:
        logger.warning("No articles found for sentiment analysis.")
        return 0  # Neutral sentiment

    for article in articles:
        headline = article.get('title', '') or ''
        description = article.get('description', '') or ''
        content = headline + ". " + description

        sentiment_score = sid.polarity_scores(content)['compound']
        total_sentiment += sentiment_score

    average_sentiment = total_sentiment / len(articles)
    logger.info(f"Calculated average sentiment score: {average_sentiment}")
    return average_sentiment


# Function to calculate Moving Average
def calculate_moving_average(prices: List[float], window: int = 7) -> Optional[float]:
    if len(prices) < window:
        return None  # Not enough data points yet
    return float(np.mean(prices[-window:]))

# Function to calculate Relative Strength Index (RSI)
def calculate_rsi(prices: List[float], window: int = 14) -> Optional[float]:
    if len(prices) < window + 1:
        return None  # Not enough data points yet
    delta = np.diff(prices)
    gains = np.where(delta > 0, delta, 0)
    losses = np.where(delta < 0, -delta, 0)
    avg_gain = np.mean(gains[-window:])
    avg_loss = np.mean(losses[-window:])
    if avg_loss == 0:
        return 100.0  # Prevent division by zero, indicates strong upward trend
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))

# Function to calculate Moving Average Convergence Divergence (MACD)
def calculate_macd(prices: List[float], short_window: int = 12, long_window: int = 26, signal_window: int = 7) -> Optional[tuple]:
    if len(prices) < long_window:
        return None, None  # Not enough data points yet
    prices_series = pd.Series(prices)
    short_ema = prices_series.ewm(span=short_window, adjust=False).mean()
    long_ema = prices_series.ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    return float(macd.iloc[-1]), float(signal.iloc[-1])

# Function to calculate potential profit or loss percentage
def calculate_potential_profit_loss(current_price: float, previous_price: float) -> float:
    return ((current_price - previous_price) / previous_price) * 100.0

# Function to determine if the potential gain/loss is greater than the transaction fee
def is_profitable_trade(potential_profit_loss: float, transaction_fee_percentage: float = 0.26) -> bool:
    return potential_profit_loss > transaction_fee_percentage
