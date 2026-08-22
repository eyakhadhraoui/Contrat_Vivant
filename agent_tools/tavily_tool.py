import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()
_tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query: str) -> str:
    """Recherche des informations récentes sur le web (ex: réglementation assurance)."""
    results = _tavily.search(query, max_results=3)
    return str(results)