import os
import openai
import json
from dotenv import load_dotenv

# Import functions to get portfolio and transaction history
from trading_bot.portfolio_manager import get_portfolio_summary, get_transaction_history
from trading_bot.data_acquisition import get_historical_prices

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def prepare_input_data(market_data, indicators):
    """
    Prepare data for GPT-4 function calling.
    """
    latest_data = {
        'price': market_data['price'].iloc[-1],
        'sma_20': indicators['sma_20'].iloc[-1],
        'ema_20': indicators['ema_20'].iloc[-1],
        'macd': indicators['macd'].iloc[-1],
        'macd_signal': indicators['macd_signal'].iloc[-1],
        'rsi': indicators['rsi'].iloc[-1],
        'upper_band': indicators['upper_band'].iloc[-1],
        'lower_band': indicators['lower_band'].iloc[-1]
    }

    # Fetch historical prices at specific intervals
    # 1 min, 2 min, 5 min, etc.
    intervals_minutes = [1, 2, 3, 4, 5, 10, 30, 60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900, 960, 1020, 1080, 1140, 1200, 1260, 1320, 1380, 1440]
    historical_prices = get_historical_prices(intervals_minutes)

    if historical_prices:
        latest_data.update(historical_prices)
    else:
        print("Warning: Could not retrieve historical prices.")

    return latest_data


def decide_trade_action(prepared_data):
    """
    Use OpenAI SDK to decide trade action.
    """
    # Get portfolio and transaction history
    portfolio = get_portfolio_summary()
    transaction_history = get_transaction_history()

    # Include holdings, portfolio, and transaction history in the user message
    user_content = {
        "market_data_and_indicators": prepared_data,
        "portfolio": portfolio,
        "transaction_history": transaction_history
    }

    functions = [
        {
            "name": "execute_trade",
            "description": "Execute a trade action based on the analysis of market data, indicators, and portfolio state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["buy", "sell", "hold"],
                        "description": "The trade action to perform."
                    },
                    "amount_btc": {
                        "type": "number",
                        "description": "Amount of BTC to trade."
                    }
                },
                "required": ["action"],
                "additionalProperties": False
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are an automated algorithmic day-trader that decides whether to buy, sell, or hold BTC "
                "based on market data, technical indicators, current portfolio holdings, and transaction history. "
                "Perform trades to maximize your profit, and trade aggressively to increase your balance."
                "Act autonomously, without asking me for permission, and make decisions based on the latest data."
            )
        },
        {
            "role": "user",
            "content": f"Here is the latest data:\n{json.dumps(user_content)}"
        }
    ]

    # print('Messages:', messages)

    response = openai.chat.completions.create(
        model='gpt-4o',  # Use a model that supports function calling
        messages=messages,
        functions=functions,
        function_call="auto",  # Let the model decide whether to call a function
    )

    message = response.choices[0].message
    # print("Response:", message)

    function_called = False

    # Check if the model decided to call a function
    if message.function_call:
        function_called = True
        function_call = message.function_call
        arguments = json.loads(function_call.arguments)
        action = arguments.get('action')
        amount_btc = arguments.get('amount_btc', 0.0)
        return action, amount_btc, messages, message, function_called
    else:
        print("No trade action decided.")
        return None, None
