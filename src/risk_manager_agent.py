import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import our individual worker agents
from technical_agent import TechnicalAnalystAgent
from sentiment_agent import SentimentAnalystAgent

# Automatically load environmental keys from the root .env file
load_dotenv()

class RiskManagerAgent:
    def __init__(self):
        self.name = "Risk Manager Agent"
        self.role = "Synthesizes multi-agent insights against system rules to issue clean trade commands."
        
        # Verify the key is populated before initializing client
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("✕ Critical Error: GEMINI_API_KEY is missing from your .env file.")
            
        self.client = genai.Client()
        
        # Instantiate internal worker analytics bureaus
        self.tech_analyst = TechnicalAnalystAgent()
        self.sent_analyst = SentimentAnalystAgent()

    def _generate_with_retry(self, user_prompt, system_instruction, max_retries=3, backoff_factor=2):
        """Queries the LLM engine with automatic model-failover to handle free-tier server load spikes."""
        current_model = 'gemini-2.5-flash'
        
        for attempt in range(max_retries):
            try:
                # Execution attempt using the currently selected model
                response = self.client.models.generate_content(
                    model=current_model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,  # Low temperature preserves analytical reasoning consistency
                    )
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                
                # Intercept temporary service capacity limits (503) or request rate boundaries (429)
                if "503" in error_msg or "429" in error_msg:
                    sleep_time = backoff_factor ** attempt
                    
                    # If primary tier model fails, drop down to flash-lite instantly
                    if current_model == 'gemini-2.5-flash':
                        print(f"  ⚠️ 'gemini-2.5-flash' busy (503). Hot-swapping to failover model 'gemini-2.5-flash-lite'...")
                        current_model = 'gemini-2.5-flash-lite'
                    else:
                        print(f"  ⚠️ Failover model also throttled. Sleeping for {sleep_time}s... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(sleep_time)
                else:
                    # Reraise permanent configuration exceptions immediately (e.g., bad API key schemas)
                    raise e
        
        # Default safety fallback text block if all remote connections are congested
        return """
=== CAPITAL RISK MANAGEMENT REPORT ===
Risk Evaluation Assessment: CRITICAL TIMEOUT. Both primary and secondary models are completely unavailable.
Consensus Vector Summary: Upstream network disconnect. Activating defensive risk posture.

[FINAL COMPLIANCE EXECUTION COMMAND]
SIGNAL: HOLD
======================================
"""

    def evaluate_and_route_trade(self):
        """Gathers insights from Technical and Sentiment desks, then passes them to the risk model."""
        print("Gathering technical indicators...")
        tech_report = self.tech_analyst.analyze_market()
        
        print("Gathering global news sentiment data...")
        sent_report = self.sent_analyst.analyze_sentiment()

        system_instruction = """
        You are the Chief Risk Officer (CRO) and Risk Manager of a systematic digital asset trading firm. 
        Your absolute priority is Capital Preservation. You analyze conflicting inputs from your analysis divisions 
        and render an objective, final trading command.
        
        Strict Operational Risk Rules:
        1. If Technical & Sentiment indicators directly conflict (e.g., Tech is BUY but Sentiment is BEARISH), you must default to HOLD. Protect liquidity over speculation.
        2. If Technical indicators show extreme conditions (OVERSOLD or OVERBOUGHT), give heavy weight to those levels to protect against buying tops or selling bottoms.
        3. Your response MUST end with a *[FINAL COMPLIANCE EXECUTION COMMAND]* block that explicitly sets the SIGNAL.
        """

        user_prompt = f"""
        Review the reports from our trading desk analytics divisions:

        --- TECHNICAL DESK SUB-REPORT ---
        {tech_report}

        --- GLOBAL SENTIMENT DESK SUB-REPORT ---
        {sent_report}

        ---
        Based on the data sets above, compile our risk evaluation profile and finalize the allocation decision.
        You must structure your output exactly like this:
        
        === CAPITAL RISK MANAGEMENT REPORT ===
        Risk Evaluation Assessment: [Provide a brief, analytical overview of the underlying risk climate]
        Consensus Vector Summary: [State if analytics are aligned or conflicting]
        
        [FINAL COMPLIANCE EXECUTION COMMAND]
        SIGNAL: [MUST be exactly either BUY, SELL, or HOLD]
        ======================================
        """

        print("Synthesizing metrics across risk desk models...")
        risk_report = self._generate_with_retry(user_prompt, system_instruction)
        
        # --- THE FIX: Return a structured dictionary containing all 3 reports ---
        return {
            "technical": tech_report,
            "sentiment": sent_report,
            "risk": risk_report
        }

if __name__ == "__main__":
    try:
        manager = RiskManagerAgent()
        print(manager.evaluate_and_route_trade())
    except Exception as err:
        print(err)
