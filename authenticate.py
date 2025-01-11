import os
import logging
import openai
from dotenv import load_dotenv

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from the .env file
logger.info("Loading environment variables from .env file...")
load_dotenv()

# Get Twitter API credentials from environment variables with error handling
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError(
        "OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable."
    )


def open_ai_auth():
    """
    Authenticate with OpenAI API using the provided API key.
    """
    logger.info("Authenticating with OpenAI API...")

    ai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    logger.info("Successfully authenticated with OpenAI API.")
    return ai_client
