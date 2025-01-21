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

# Load environment variables
AI_SERVER_URL = os.getenv('AI_SERVER_URL')  # e.g., "http://localhost:5001"
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')  # Telegram bot API key

# Initialize the Telegram bot
app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to Crypto Buddy! Ask me anything about cryptocurrencies.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    user_question = update.message.text.lower()
    
    # Determine intent based on keywords in the user question
    if "volatility" in user_question:
        intent = "volatility"
    elif "price" in user_question:
        intent = "price trends"
    else:
        intent = "unknown"

    # Extract the cryptocurrency name from the user question
    crypto_name = "Bitcoin"  # This should be extracted based on user input

    # Call the AI server based on the determined intent
    response = trigger_ai_server(intent, crypto_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

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
                return response.json().get('historical_data', 'No response from server.')
            except ValueError as e:
                print("Error parsing JSON:", e)
                return "Error parsing response from server."
        else:
            return "Could not find the coin ID for the specified cryptocurrency."

    elif intent == "volatility":
        coin_id = get_coin_id(crypto_name)
        if coin_id:
            # Construct the full URL for the volatility request
            url = f"{AI_SERVER_URL}/api/volatility?coin_id={coin_id}&timeframe=month"
            print(f"Calling AI server at: {url}")  # Debugging output

            # Make a GET request to fetch volatility
            response = requests.get(url)

            # Debugging output to check the response
            print("Response Status Code:", response.status_code)
            print("Response Text:", response.text)  # Print the raw response text

            try:
                return response.json().get('volatility', 'No response from server.')
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
