import os
import json
from datetime import datetime

PORTFOLIO_DIR = os.path.join(os.path.dirname(__file__), '../portfolio')
if not os.path.exists(PORTFOLIO_DIR):
    os.makedirs(PORTFOLIO_DIR)

HOLDINGS_FILE = os.path.join(PORTFOLIO_DIR, 'holdings.json')
TRANSACTION_HISTORY_FILE = os.path.join(PORTFOLIO_DIR, 'transaction_history.json')

def initialize_portfolio(starting_balance):
    portfolio = {
        "balance_usd": starting_balance,
        "holdings_btc": 0.0
    }
    save_portfolio(portfolio)
    # Also reset the transaction history
    if os.path.exists(TRANSACTION_HISTORY_FILE):
        os.remove(TRANSACTION_HISTORY_FILE)

def load_portfolio():
    if os.path.exists(HOLDINGS_FILE):
        with open(HOLDINGS_FILE, 'r') as f:
            portfolio = json.load(f)
    else:
        # If holdings.json doesn't exist, prompt the user or set a default
        portfolio = {
            "balance_usd": 1000000.0,  # Default starting balance
            "holdings_btc": 0.0
        }
        save_portfolio(portfolio)
    return portfolio


def save_portfolio(portfolio):
    with open(HOLDINGS_FILE, 'w') as f:
        json.dump(portfolio, f, indent=4)

def execute_trade(action, amount_btc, price_usd):
    if price_usd is None:
        print("Cannot execute trade: Failed to retrieve current price.")
        return
    portfolio = load_portfolio()
    total_usd = amount_btc * price_usd

    if action == 'buy':
        if portfolio['balance_usd'] >= total_usd:
            portfolio['balance_usd'] -= total_usd
            portfolio['holdings_btc'] += amount_btc
            save_portfolio(portfolio)
            record_transaction('buy', amount_btc, price_usd, total_usd)
            print(f"Bought {amount_btc} BTC at {price_usd} USD/BTC")
        else:
            print("Insufficient USD balance.")
    elif action == 'sell':
        if portfolio['holdings_btc'] >= amount_btc:
            portfolio['balance_usd'] += total_usd
            portfolio['holdings_btc'] -= amount_btc
            save_portfolio(portfolio)
            record_transaction('sell', amount_btc, price_usd, total_usd)
            print(f"Sold {amount_btc} BTC at {price_usd} USD/BTC")
        else:
            print("Insufficient BTC holdings.")
    else:
        print("Invalid action.")

def record_transaction(action, amount_btc, price_usd, total_usd):
    transaction = {
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "action": action,
        "amount_btc": amount_btc,
        "price_usd": price_usd,
        "total_usd": total_usd
    }
    transactions = []
    if os.path.exists(TRANSACTION_HISTORY_FILE):
        if os.path.getsize(TRANSACTION_HISTORY_FILE) > 0:
            with open(TRANSACTION_HISTORY_FILE, 'r') as f:
                try:
                    transactions = json.load(f)
                except json.JSONDecodeError:
                    print("Warning: Transaction history file is corrupt. Starting fresh.")
                    transactions = []
        else:
            print("Transaction history file is empty. Starting fresh.")
    transactions.append(transaction)
    with open(TRANSACTION_HISTORY_FILE, 'w') as f:
        json.dump(transactions, f, indent=4)


def get_portfolio_summary():
    portfolio = load_portfolio()
    return portfolio

def get_transaction_history():
    transactions = []
    if os.path.exists(TRANSACTION_HISTORY_FILE):
        if os.path.getsize(TRANSACTION_HISTORY_FILE) > 0:
            with open(TRANSACTION_HISTORY_FILE, 'r') as f:
                try:
                    transactions = json.load(f)
                except json.JSONDecodeError:
                    print("Warning: Transaction history file is empty or corrupt. Returning empty list.")
                    transactions = []
        else:
            # File exists but is empty
            transactions = []
    else:
        # File does not exist
        transactions = []
    return transactions
