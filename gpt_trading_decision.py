import logging
import openai

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Configure OpenAI API
openai.api_key = "your_openai_api_key"

def gpt_trading_decision(latest_price, historical_prices, sentiment):
    """
    Uses OpenAI's GPT model to decide whether to Buy, Hold, or Sell Bitcoin.
    Parameters:
        - latest_price: The most recent Bitcoin price.
        - historical_prices: A list of historical price data (e.g., [{time, open, high, low, close}]).
        - sentiment: A tuple containing sentiment ("Positive", "Neutral", "Negative") and a confidence score.
    Returns:
        - decision: A string ("buy", "hold", or "sell").
    """
    logger.info(f"Generating trading decision using ChatGPT API...")
    
    # Prepare historical trend data
    trend = historical_prices[-1]["close"] - historical_prices[0]["close"]
    trend_direction = "upward" if trend > 0 else "downward" if trend < 0 else "flat"
    sentiment_label, sentiment_score = sentiment

    # Generate prompt
    prompt = (
        f"You are a trading expert. Based on the following data, decide whether to Buy, Hold, or Sell Bitcoin:\n\n"
        f"- Latest price: ${latest_price:.2f}\n"
        f"- Historical price trend: {trend_direction} trend over the past period with a change of ${trend:.2f}.\n"
        f"- Sentiment: {sentiment_label} (confidence: {sentiment_score:.2f}).\n\n"
        f"Provide your decision (Buy, Hold, or Sell) and explain the reasoning in under 100 words."
    )

    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful and knowledgeable trading assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        # Parse the response
        decision = response.choices[0].message.content.strip().lower()
        logger.info(f"Generated Decision: {decision}")

        # Return decision
        return decision

    except Exception as e:
        logger.error(f"Failed to generate trading decision: {str(e)}")
        return "hold"

# Example usage
if __name__ == "__main__":
    # Mock data for testing
    latest_price = 40000.0
    historical_prices = [
        {"time": 1, "open": 39500, "high": 40500, "low": 39000, "close": 39800},
        {"time": 2, "open": 39800, "high": 41000, "low": 39500, "close": 40000},
    ]
    sentiment = ("Positive", 0.85)  # Mock sentiment data

    decision = gpt_trading_decision(latest_price, historical_prices, sentiment)
    print(f"Trading Decision: {decision}")
