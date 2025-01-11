import requests
from config import API_KEY

# Load environment variables from the .env file
load_dotenv()


def get_bitcoin_sentiment():
    """
    Fetch sentiment about Bitcoin from a sentiment analysis service.
    Replace `API_URL` and `API_KEY` with the actual service you use.
    """
    API_URL = "https://sentiment-api.example.com/bitcoin"
        
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(API_URL, headers=headers)
    data = response.json()
    
    if response.status_code == 200:
        # Example: Positive, Neutral, Negative sentiment with score
        sentiment = data.get("sentiment", "Neutral")
        score = data.get("score", 0)  # Confidence level
        return sentiment, score
    else:
        print(f"Error: {data.get('error', 'Unable to fetch sentiment')}")
        return None, 0

if __name__ == "__main__":
    # Test function
    sentiment, score = get_bitcoin_sentiment()
    print(f"Sentiment: {sentiment}, Score: {score}")
