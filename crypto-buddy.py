import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import spacy  # or any other NLP library you prefer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import re
from fuzzywuzzy import process

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load NLP model (e.g., spaCy)
nlp = spacy.load("en_core_web_sm")  # Load the English NLP model

# Define the AI server URL
AI_SERVER_URL = os.getenv('AI_SERVER_URL')  # e.g., "http://localhost:5001"
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')  # Telegram bot API key

# Initialize the Telegram bot
app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Crypto Buddy! Ask me anything about cryptocurrencies.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    user_question = update.message.text
    response = ask_crypto_buddy(user_question)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

def ask_crypto_buddy(user_question):
    # Step 2: NLP to determine intent and extract cryptocurrency name
    intent, crypto_name = determine_intent_and_crypto(user_question)

    # Step 3: Prepare the request to the AI server based on the intent
    if intent and crypto_name:
        response = trigger_ai_server(intent, crypto_name)
        return response
    else:
        return "Could not determine intent or cryptocurrency."

def determine_intent_and_crypto(question):
    # Normalize the question
    question = question.lower().strip()

    # Define intents and their keywords
    intents = {
        "price trends": ["price trend", "current price trend", "price trends"],
        "performance comparison": ["compare", "performance comparison"],
        "forecast": ["forecast", "price prediction"],
        "support and resistance": ["support", "resistance", "support and resistance"],
        "analytical insights": ["insight", "analytical insights"]
    }

    # Initialize variables
    crypto_name = None
    intent = None

    # Check for intent using fuzzy matching
    for key, keywords in intents.items():
        # Use fuzzy matching to find the best match
        match, score = process.extractOne(question, keywords)
        if score >= 80:  # You can adjust the threshold as needed
            intent = key
            break

    # List of known cryptocurrencies
    known_cryptos = ["bitcoin", "ethereum", "litecoin", "cardano", "ripple", "solana", "polkadot"]

    # Extract cryptocurrency name using regex
    for token in known_cryptos:
        if re.search(r'\b' + re.escape(token) + r'\b', question):
            crypto_name = token
            break

    print("Question:", question)  # Debugging output
    print("Intent:", intent)  # Debugging output
    print("Crypto Name:", crypto_name)  # Debugging output

    return intent, crypto_name

def get_coin_id(crypto_name):
    """Fetch the coin_id from the AI server based on the crypto name."""
    response = requests.get(f"{AI_SERVER_URL}/api/get_coin_id", params={"name": crypto_name})
    if response.status_code == 200:
        return response.json().get('coin_id')
    else:
        print(f"Error fetching coin ID: {response.text}")
        return None

def trigger_ai_server(intent, crypto_name):
    """Trigger the AI server based on the intent."""
    if intent == "price trends":
        coin_id = get_coin_id(crypto_name)
        if coin_id:
            # Construct the full URL for the price trends request
            url = f"{AI_SERVER_URL}/api/price_trends?coin_id={coin_id}&timeframe=month"
            print(f"Calling AI server at: {url}")  # Debugging output

            # Make a GET request to fetch price trends
            response = requests.get(url)

            # Debugging output to check the response
            print("Response Status Code:", response.status_code)
            print("Response Text:", response.text)  # Print the raw response text

            try:
                return response.json().get('response', 'No response from server.')
            except ValueError as e:
                print("Error parsing JSON:", e)
                return "Error parsing response from server."
        else:
            return "Could not find the coin ID for the specified cryptocurrency."
    else:
        return "Invalid intent."

# Set up command and message handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Start the Telegram bot
app.run_polling()

# Start the Flask app (if needed for other purposes)
if __name__ == '__main__':
    app.run(debug=True, port=3000)  # Run the AI agent on port 3000
