import os
import sqlite3
import re
from datetime import datetime
from risk_manager_agent import RiskManagerAgent

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trading_bot.db')

class PaperLedger:
    def __init__(self):
        self.init_ledger_tables()

    def init_ledger_tables(self):
        """Creates the tracking tables for our virtual wallet and trade logs."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Create Portfolio Table (Holds current balances)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paper_portfolio (
                asset TEXT PRIMARY KEY,
                balance REAL
            )
        ''')
        
        # 2. Create Transaction Ledger (Logs history of executions including the full agent reports)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transaction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                signal TEXT,
                price REAL,
                amount REAL,
                total_value REAL,
                cash_remaining REAL,
                btc_remaining REAL,
                full_report TEXT
            )
        ''')
        
        # Seed the wallet with $10,000 virtual cash if empty
        cursor.execute("SELECT COUNT(*) FROM paper_portfolio")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO paper_portfolio (asset, balance) VALUES ('USD', 10000.0)")
            cursor.execute("INSERT INTO paper_portfolio (asset, balance) VALUES ('BTC', 0.0)")
            
        conn.commit()
        conn.close()

    def get_balances(self):
        """Retrieves current USD and BTC balances."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        usd = cursor.execute("SELECT balance FROM paper_portfolio WHERE asset='USD'").fetchone()[0]
        btc = cursor.execute("SELECT balance FROM paper_portfolio WHERE asset='BTC'").fetchone()[0]
        conn.close()
        return usd, btc

    def execute_order(self, signal, current_price, report):
        """Simulates executing a buy/sell trade based on the agent's signal and saves logs."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        usd_balance, btc_balance = self.get_balances()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Trade execution parameters (We trade 10% of our available balance per signal to manage risk)
        allocation_percentage = 0.10 
        
        if signal == "BUY" and usd_balance > 10:
            # Spend 10% of our cash to buy BTC
            cash_to_spend = usd_balance * allocation_percentage
            btc_to_buy = cash_to_spend / current_price
            
            new_usd = usd_balance - cash_to_spend
            new_btc = btc_balance + btc_to_buy
            
            cursor.execute("UPDATE paper_portfolio SET balance = ? WHERE asset='USD'", (new_usd,))
            cursor.execute("UPDATE paper_portfolio SET balance = ? WHERE asset='BTC'", (new_btc,))
            cursor.execute('''
                INSERT INTO transaction_history (timestamp, signal, price, amount, total_value, cash_remaining, btc_remaining, full_report)
                VALUES (?, 'BUY', ?, ?, ?, ?, ?, ?)
            ''', (timestamp, current_price, btc_to_buy, cash_to_spend, new_usd, new_btc, report))
            
            print(f"🛒 [EXECUTION] Bought {btc_to_buy:.6f} BTC at ${current_price:,.2f} using ${cash_to_spend:.2f} USD.")
            
        elif signal == "SELL" and btc_balance > 0.0001:
            # Sell 10% of our BTC holding back into cash
            btc_to_sell = btc_balance * allocation_percentage
            cash_to_receive = btc_to_sell * current_price
            
            new_usd = usd_balance + cash_to_receive
            new_btc = btc_balance - btc_to_sell
            
            cursor.execute("UPDATE paper_portfolio SET balance = ? WHERE asset='USD'", (new_usd,))
            cursor.execute("UPDATE paper_portfolio SET balance = ? WHERE asset='BTC'", (new_btc,))
            cursor.execute('''
                INSERT INTO transaction_history (timestamp, signal, price, amount, total_value, cash_remaining, btc_remaining, full_report)
                VALUES (?, 'SELL', ?, ?, ?, ?, ?, ?)
            ''', (timestamp, current_price, btc_to_sell, cash_to_receive, new_usd, new_btc, report))
            
            print(f"💰 [EXECUTION] Sold {btc_to_sell:.6f} BTC at ${current_price:,.2f} for ${cash_to_receive:.2f} USD.")
            
        else:
            # HOLD signal or insufficient funds to execute the action safely
            cursor.execute('''
                INSERT INTO transaction_history (timestamp, signal, price, amount, total_value, cash_remaining, btc_remaining, full_report)
                VALUES (?, 'HOLD', ?, 0, 0, ?, ?, ?)
            ''', (timestamp, current_price, usd_balance, btc_balance, report))
            print("💤 [EXECUTION] Position held. No changes made to portfolio.")

        conn.commit()
        conn.close()

def parse_signal_from_report(report_text):
    """Uses regex to look inside the agent's markdown report text and extract the exact SIGNAL string."""
    match = re.search(r"SIGNAL:\s*(BUY|SELL|HOLD)", report_text)
    if match:
        return match.group(1)
    return "HOLD"

def run_live_simulation_tick():
    """Triggers the full multi-agent pipeline and updates the simulated ledger balances."""
    ledger = PaperLedger()
    manager = RiskManagerAgent()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    latest_price = cursor.execute("SELECT close FROM btc_hourly_prices ORDER BY timestamp DESC LIMIT 1").fetchone()[0]
    conn.close()
    
    print("\n--- Starting Agentic Trading Sequence ---")
    usd, btc = ledger.get_balances()
    portfolio_value = usd + (btc * latest_price)
    print(f"Current Portfolio Net Worth: ${portfolio_value:,.2f} (Cash: ${usd:,.2f}, Holdings: {btc:.6f} BTC)")
    
    # 1. Receive the dictionary containing ALL agent results
    reports_dict = manager.evaluate_and_route_trade()
    
    # 2. Extract the signal from the risk manager's specific text block
    final_signal = parse_signal_from_report(reports_dict["risk"])
    print(f"Extracted Strategy Signal: {final_signal}")
    
    # 3. Stitch them together cleanly with unique headers so our frontend parser reads them flawlessly
    combined_report_string = f"""
--- TECHNICAL DESK SUB-REPORT ---
{reports_dict['technical']}

--- GLOBAL SENTIMENT DESK SUB-REPORT ---
{reports_dict['sentiment']}

{reports_dict['risk']}
"""
    
    # 4. Record execution to database with the perfectly formatted combined string
    ledger.execute_order(final_signal, latest_price, combined_report_string)
    
    new_usd, new_btc = ledger.get_balances()
    new_value = new_usd + (new_btc * latest_price)
    print(f"Updated Portfolio Net Worth: ${new_value:,.2f} (Cash: ${new_usd:,.2f}, Holdings: {new_btc:.6f} BTC)")
    print("-------------------------------------------\n")

if __name__ == "__main__":
    run_live_simulation_tick()
