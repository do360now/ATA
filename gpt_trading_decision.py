import logging
import openai
from authenticate import open_ai_auth

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Configure OpenAI API
ai_client = open_ai_auth()

def gpt_trading_decision(latest_price, historical_prices, sentiment, moving_average, rsi, macd, signal_line, portfolio):
    """
    Uses OpenAI's GPT model to decide whether to Buy, Hold, or Sell Bitcoin.
    Parameters:
        - latest_price: The most recent Bitcoin price.
        - historical_prices: A list of historical price data (e.g., [float]).
        - sentiment: A tuple containing sentiment ("Positive", "Neutral", "Negative") and a confidence score.
    Returns:
        - decision: A string ("buy", "hold", or "sell").
    """
    logger.info(f"Generating trading decision using ChatGPT API...")
    
    # Prepare historical trend data
    trend = historical_prices[-1] - historical_prices[0]  # Use raw float values for the trend
    trend_direction = "upward" if trend > 0 else "downward" if trend < 0 else "flat"
    sentiment_score = sentiment

    # Generate prompt
    prompt = (
        f"You are a trading expert. Based on the following data, decide whether to Buy, Hold, or Sell Bitcoin:\n\n"
        f"- Latest price: ${latest_price:.2f}\n"
        f"- Historical price trend: {trend_direction} trend over the past period with a change of ${trend:.2f}.\n"
        f"- Sentiment:  (sentiment score: {sentiment_score:.2f}).\n\n"
        f"- Technical Indicators: (moving average: {moving_average}, rsi: {rsi}, macd: {macd}, signal: {signal_line} \n"
        f"- Portfolio: Based on this portfolio, {portfolio}.\n\n"
        f"Provide your decision (Buy, Hold, or Sell). Explain the reasoning in under 100 words\n"
    )

    try:
        # Call OpenAI API
        response = ai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful and knowledgeable trading assistant."},
                {"role": "user", "content": prompt},
            ],
        )

        # Parse the response
        decision = response.choices[0].message.content.strip().lower()
        logger.info(f"Generated Decision: {decision}")
      
        return decision

    except Exception as e:
        logger.error(f"Failed to generate trading decision: {str(e)}")
        return "hold"
