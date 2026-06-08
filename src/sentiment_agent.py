import os
import feedparser
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Automatically searches for a .env file up the folder tree and injects it into os.environ
load_dotenv()

class SentimentAnalystAgent:
    def __init__(self):
        self.name = "Sentiment Analyst Agent"
        self.role = "Analyzes real-time news narratives to evaluate market psychology."
        
        # Verify the key is populated before initializing client
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("✕ Critical Error: GEMINI_API_KEY is missing from .env configuration file.")
            
        # Initializes standard client using variables injected by dotenv
        self.client = genai.Client()
        self.news_feed_url = "https://cryptoslate.com/feed/"

    def _fetch_latest_headlines(self, limit=10):
        """Fetches latest crypto headlines for free using RSS."""
        print("Scraping live news headlines...")
        feed = feedparser.parse(self.news_feed_url)
        if not feed.entries:
            return ""
        
        headlines = []
        for entry in feed.entries[:limit]:
            headlines.append(f"- {entry.title}: {entry.get('summary', '')[:150]}...")
            
        return "\n".join(headlines)

    def analyze_sentiment(self):
        """Processes live news text and extracts structural sentiment using Gemini 2.5 Flash."""
        raw_news = self._fetch_latest_headlines()
        
        if not raw_news:
            return "Could not retrieve news data. Defaulting to NEUTRAL narrative sentiment."

        system_instruction = """
        You are an expert crypto hedge fund sentiment analyst. Your job is to read a list of raw news headlines, 
        strip away speculative hype, identify systemic macroeconomic factors shifting market sentiment, 
        and output a structured evaluation report.
        """

        user_prompt = f"""
        Analyze the following live market news headlines regarding Bitcoin and cryptocurrency:
        
        {raw_news}
        
        Generate a report following this exact format:
        === SENTIMENT ANALYST AGENT REPORT ===
        Live Narrative Score: [BULLISH, BEARISH, or NEUTRAL]
        Psychology Summary: [Provide a brief, 2-sentence summary of the general market mood]
        Primary Driver: [Identify the single biggest news item or factor steering the narrative today]
        ======================================
        """

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
                )
            )
            return response.text
        except Exception as e:
            return f"✕ Error executing LLM inference: {e}"

if __name__ == "__main__":
    try:
        agent = SentimentAnalystAgent()
        print(agent.analyze_sentiment())
    except Exception as error:
        print(error)
