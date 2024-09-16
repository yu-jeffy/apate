import click
from trading_bot.data_acquisition import (
    get_current_price,
    load_market_data,
    get_historical_data,
    save_market_data
)
from trading_bot.portfolio_manager import (
    execute_trade,
    get_portfolio_summary,
    get_transaction_history,
    initialize_portfolio
)
from trading_bot.decision_maker import prepare_input_data, decide_trade_action
from indicators.indicators import (
    calculate_sma,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_bollinger_bands
)
import pandas as pd
from datetime import datetime, timedelta
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

@click.group()
def cli():
    pass

@cli.command()
@click.option('--starting-balance', default=None, type=float, help='Set the starting USD balance.')
def start(starting_balance):
    """
    Start the trading bot.
    """
    # Initialize portfolio with starting balance if provided
    if starting_balance is not None:
        initialize_portfolio(starting_balance)

    while True:
        # Fetch historical data for indicators
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        market_data = get_historical_data(start_date, end_date)
        if market_data is not None:
            save_market_data(market_data)
        else:
            market_data = load_market_data()

        # Calculate indicators
        indicators = pd.DataFrame()
        indicators['sma_20'] = calculate_sma(market_data, 20)
        indicators['ema_20'] = calculate_ema(market_data, 20)
        macd, macd_signal = calculate_macd(market_data)
        indicators['macd'] = macd
        indicators['macd_signal'] = macd_signal
        indicators['rsi'] = calculate_rsi(market_data)
        upper_band, lower_band = calculate_bollinger_bands(market_data)
        indicators['upper_band'] = upper_band
        indicators['lower_band'] = lower_band

        # Prepare data for decision maker
        prepared_data = prepare_input_data(market_data, indicators)

        # Decide trade action
        action, amount_btc, sent_messages, response_message, function_called = decide_trade_action(prepared_data)

        # Display the message sent to GPT
        user_message = sent_messages[-1]['content']
        console.print(Panel(f"[bold]Message Sent to GPT:[/bold]\n{user_message}", title="GPT Input", border_style="blue"))

        # Display the response from GPT
        assistant_content = response_message.content or ""
        function_call_info = ""
        if function_called:
            function_call_info = f"\n[bold]Function Called:[/bold] {response_message.function_call.name}"
            function_call_info += f"\n[bold]Arguments:[/bold] {response_message.function_call.arguments}"
        console.print(Panel(f"[bold]Response from GPT:[/bold]\n{assistant_content}{function_call_info}", title="GPT Response", border_style="green"))

        # Display the action decided
        if action in ['buy', 'sell']:
            console.print(f"[bold]Action Decided:[/bold] {action} {amount_btc} BTC")
            current_price = get_current_price()
            execute_trade(action, amount_btc, current_price)
        else:
            console.print("[bold]Action Decided:[/bold] Hold")

        # Print the portfolio summary
        summary = get_portfolio_summary()
        current_price = get_current_price()
        total_value_usd = summary['balance_usd'] + summary['holdings_btc'] * current_price

        portfolio_table = Table(title="Portfolio Summary", box=box.SIMPLE)
        portfolio_table.add_column("Asset", style="cyan", no_wrap=True)
        portfolio_table.add_column("Amount", style="magenta")
        portfolio_table.add_row("Cash Balance USD", f"{summary['balance_usd']:.2f}")
        portfolio_table.add_row("Holdings BTC", f"{summary['holdings_btc']:.6f}")
        portfolio_table.add_row("Current BTC Price USD", f"{current_price:.2f}")
        portfolio_table.add_row("Total Portfolio Value USD", f"{total_value_usd:.2f}")

        console.print(portfolio_table)

        # Wait for 10 seconds before next iteration
        time.sleep(10)

@cli.command()
def portfolio():
    """
    Show portfolio summary.
    """
    summary = get_portfolio_summary()
    current_price = get_current_price()
    total_value_usd = summary['balance_usd'] + summary['holdings_btc'] * current_price

    print("Portfolio Summary:")
    print(f"Cash Balance USD: {summary['balance_usd']:.2f}")
    print(f"Holdings BTC: {summary['holdings_btc']:.6f}")
    print(f"Current BTC Price USD: {current_price:.2f}")
    print(f"Total Portfolio Value USD: {total_value_usd:.2f}")

@cli.command()
def history():
    """
    Show transaction history.
    """
    transactions = get_transaction_history()
    if transactions:
        print("Transaction History:")
        for tx in transactions:
            print(f"{tx['timestamp']} - {tx['action']} {tx['amount_btc']} BTC at {tx['price_usd']} USD/BTC")
    else:
        print("No transactions found.")

if __name__ == "__main__":
    cli()
