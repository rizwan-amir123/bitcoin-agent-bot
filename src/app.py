import os
import sqlite3
import pandas as pd
import streamlit as st
from backtester import run_live_simulation_tick, PaperLedger

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'trading_bot.db')

st.set_page_config(
    page_title="Bitcoin Agentic Trading Desk",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize database tables on app boot
try:
    ledger_initializer = PaperLedger()
except Exception as e:
    st.error(f"Failed to initialize ledger database: {e}")

def get_portfolio_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        usd = cursor.execute("SELECT balance FROM paper_portfolio WHERE asset='USD'").fetchone()[0]
        btc = cursor.execute("SELECT balance FROM paper_portfolio WHERE asset='BTC'").fetchone()[0]
        latest_price = cursor.execute("SELECT close FROM btc_hourly_prices ORDER BY timestamp DESC LIMIT 1").fetchone()[0]
        return usd, btc, latest_price
    except sqlite3.OperationalError:
        return 10000.0, 0.0, 0.0
    finally:
        conn.close()

def get_transaction_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM transaction_history ORDER BY id DESC", conn)
    conn.close()
    return df

# --- UI Header ---
st.title("🤖 Bitcoin Multi-Agent Portfolio")
st.markdown("An autonomous AI-driven quantitative network executing trades via technical indicators & live sentiment analysis.")
st.write("---")

usd_bal, btc_bal, btc_price = get_portfolio_data()
net_worth = usd_bal + (btc_bal * btc_price)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Net Portfolio Value", value=f"${net_worth:,.2f}")
with col2:
    st.metric(label="Available Cash (USD)", value=f"${usd_bal:,.2f}")
with col3:
    st.metric(label="Bitcoin Price", value=f"${btc_price:,.2f}")

st.subheader("Execute Autonomous Strategy Loop")
if st.button("▶ Run Multi-Agent Tick", type="primary", use_container_width=True):
    with st.spinner("Agents are communicating, analyzing, and auditing... Please wait."):
        try:
            run_live_simulation_tick()
            st.success("✓ Strategy loop processed and ledger updated safely!")
            st.rerun()
        except Exception as e:
            st.error(f"Execution Error: {e}")

st.write("---")

tab1, tab2 = st.tabs(["📊 Portfolio Allocation", "📜 Live Agent Audit Logs"])

with tab1:
    st.subheader("Current Asset Holding")
    portfolio_df = pd.DataFrame([
        {"Asset": "Cash (USD)", "Balance": f"${usd_bal:,.2f}"},
        {"Asset": "Bitcoin (BTC)", "Balance": f"{btc_bal:.6f} BTC"}
    ])
    st.dataframe(portfolio_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Multi-Agent Executive Stream Logs")
    history_df = get_transaction_history()
    
    if history_df.empty:
        st.info("No logs registered yet. Trigger a multi-agent loop run.")
    else:
        for index, row in history_df.iterrows():
            timestamp = row['timestamp']
            signal = row['signal']
            price = row['price']
            report_text = row['full_report'] if row['full_report'] else ""
            
            emoji = "🛒" if signal == "BUY" else "💰" if signal == "SELL" else "💤"
            
            with st.expander(f"{emoji} [{timestamp}] - Operational Signal: **{signal}** at ${price:,.2f}"):
                
                # Dynamic Parsing Loop based on specific database markers
                try:
                    # Isolate Technical Agent Report
                    tech_part = report_text.split("--- TECHNICAL DESK SUB-REPORT ---")[1]
                    tech_report = tech_part.split("--- GLOBAL SENTIMENT DESK SUB-REPORT ---")[0].strip()
                    
                    # Isolate Sentiment Agent Report
                    sent_part = tech_part.split("--- GLOBAL SENTIMENT DESK SUB-REPORT ---")[1]
                    sent_report = sent_part.split("===\n\n===")[0].split("=== CAPITAL RISK MANAGEMENT REPORT ===")[0].strip()
                    
                    # Ensure closing tags are preserved for clean rendering block
                    if not sent_report.endswith("======"):
                        sent_report += "\n======================================"
                    
                    # Isolate Risk Manager Report
                    risk_report = "=== CAPITAL RISK MANAGEMENT REPORT ===" + report_text.split("=== CAPITAL RISK MANAGEMENT REPORT ===")[1]
                except Exception:
                    # Robust failover: if string format variations happen, print the raw master log
                    st.text(report_text)
                    continue

                # --- Render with Beautiful Individual UI Components ---
                st.markdown("### 🛠️ Technical Analyst Agent Report")
                st.text(tech_report)
                st.write("") # Margin spacer
                
                st.markdown("### 📰 Sentiment Analyst Agent Report")
                st.text(sent_report)
                st.write("")
                
                st.markdown("### 🛡️ Risk Manager Execution Decision")
                st.text(risk_report)
