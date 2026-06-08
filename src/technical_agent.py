import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trading_bot.db')

class TechnicalAnalystAgent:
    def __init__(self):
        self.name = "Technical Analyst Agent"
        self.role = "Analyzes mathematical market indicators to identify price trends and momentum."

    def _calculate_rsi(self, series, periods=14):
        """Calculates the standard Relative Strength Index (RSI)."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def analyze_market(self):
        """Reads historical data, calculates indicators, and outputs a technical signal report."""
        # 1. Pull data from our local database
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM btc_hourly_prices ORDER BY timestamp ASC", conn)
        conn.close()

        if len(df) < 50:
            return "Insufficient data to calculate moving averages. Need at least 50 historical data points."

        # 2. Calculate Indicators
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['RSI'] = self._calculate_rsi(df['close'], periods=14)

        # Grab the absolute latest closing price row
        latest_row = df.iloc[-1]
        
        current_price = latest_row['close']
        sma_20 = latest_row['SMA_20']
        sma_50 = latest_row['SMA_50']
        rsi = latest_row['RSI']
        timestamp = latest_row['timestamp']

        # 3. Determine the Technical Signal
        # Trend Evaluation
        if sma_20 > sma_50:
            trend = "BULLISH (Short-term trend is above long-term trend)"
            trend_signal = "BUY"
        else:
            trend = "BEARISH (Short-term momentum is dragging below long-term trend)"
            trend_signal = "SELL"

        # Momentum Evaluation (RSI)
        if rsi >= 70:
            momentum = f"OVERBOUGHT (RSI is {rsi:.2f}). Market might be due for a downward correction."
            momentum_signal = "SELL"
        elif rsi <= 30:
            momentum = f"OVERSOLD (RSI is {rsi:.2f}). Market might be primed for a bounce up."
            momentum_signal = "BUY"
        else:
            momentum = f"NEUTRAL (RSI is {rsi:.2f}). Price momentum is stable."
            momentum_signal = "HOLD"

        # Formulate the structured report
        report = f"""
=== TECHNICAL ANALYST AGENT REPORT ===
Timestamp: {timestamp}
Asset: BTC/USDT
Current Closing Price: ${current_price:,.2f}

[INDICATORS]
- SMA(20): ${sma_20:,.2f}
- SMA(50): ${sma_50:,.2f}
- RSI(14): {rsi:.2f}

[ANALYSIS SUMMARY]
Trend Analysis: {trend}
Momentum Analysis: {momentum}

[RECOMMENDED ACTION MATRIX]
Trend Signal: {trend_signal}
Momentum Signal: {momentum_signal}
======================================
"""
        return report

if __name__ == "__main__":
    agent = TechnicalAnalystAgent()
    print(agent.analyze_market())
