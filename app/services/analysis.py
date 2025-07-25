import asyncio
import httpx
from typing import Dict, List, Any, Optional
from duckduckgo_search import DDGS
import logging
from bs4 import BeautifulSoup
from app.services.gemini import GeminiService
from app.config import settings

logger = logging.getLogger(__name__)

class MarketAnalysisService:
    def __init__(self):
        self.gemini_service = GeminiService()
        self.session_cache = {}  # In-memory cache for session data
    
    async def analyze_sector(self, sector: str, user_session: str) -> Dict[str, Any]:
        """
        Main method to analyze a sector and generate trade opportunities report.
        
        Args:
            sector: The sector name to analyze
            user_session: User session identifier for caching
            
        Returns:
            Dictionary containing the analysis report
        """
        try:
            # Check cache first
            cache_key = f"{user_session}_{sector}"
            if cache_key in self.session_cache:
                logger.info(f"Returning cached analysis for {sector}")
                return self.session_cache[cache_key]
            
            # Collect market data
            market_data = await self._collect_market_data(sector)
            
            # Generate AI analysis
            analysis_report = await self.gemini_service.analyze_sector_data(sector, market_data)
            
            # Prepare response
            result = {
                "sector": sector,
                "analysis": analysis_report,
                "data_sources": market_data.get("sources", []),
                "generated_at": self._get_current_timestamp(),
                "status": "success"
            }
            
            # Cache the result (simple in-memory cache)
            self.session_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sector {sector}: {str(e)}")
            return {
                "sector": sector,
                "analysis": f"# Error Analyzing {sector.title()} Sector\n\nWe encountered an error while analyzing this sector. Please try again later.",
                "error": str(e),
                "status": "error",
                "generated_at": self._get_current_timestamp()
            }
    
    async def _collect_market_data(self, sector: str) -> Dict[str, Any]:
        """
        Collect market data from various sources.
        
        Args:
            sector: The sector to collect data for
            
        Returns:
            Dictionary containing collected market data
        """
        data = {
            "news": [],
            "sources": [],
            "sector": sector
        }
        
        try:
            # Search for recent news about the sector
            news_data = await self._search_sector_news(sector)
            data["news"] = news_data
            data["sources"].append("DuckDuckGo Search")
            
            # You can add more data sources here:
            # - Financial APIs
            # - Government data sources
            # - Stock market APIs
            # - Economic indicators
            
        except Exception as e:
            logger.error(f"Error collecting market data: {str(e)}")
            data["error"] = str(e)
        
        return data
    
    async def _search_sector_news(self, sector: str) -> List[Dict[str, Any]]:
        """
        Search for recent news about the sector using DuckDuckGo.
        
        Args:
            sector: The sector to search news for
            
        Returns:
            List of news items
        """
        try:
            # Create search queries
            queries = [
                f"{sector} sector India market news 2024",
                f"{sector} industry India opportunities",
                f"Indian {sector} market trends investment"
            ]
            
            news_items = []
            
            for query in queries:
                try:
                    # Use DuckDuckGo search
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=3))
                        
                        for result in results:
                            news_item = {
                                "title": result.get("title", ""),
                                "snippet": result.get("body", ""),
                                "url": result.get("href", ""),
                                "source": "DuckDuckGo"
                            }
                            news_items.append(news_item)
                            
                except Exception as e:
                    logger.error(f"Error searching with query '{query}': {str(e)}")
                    continue
            
            # Remove duplicates based on title
            seen_titles = set()
            unique_news = []
            for item in news_items:
                if item["title"] not in seen_titles:
                    seen_titles.add(item["title"])
                    unique_news.append(item)
            
            return unique_news[:10]  # Return top 10 unique results
            
        except Exception as e:
            logger.error(f"Error in news search: {str(e)}")
            return []
    
    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL (for additional data collection).
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Text content of the page or None if failed
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract text content (basic extraction)
                text = soup.get_text()
                
                # Clean up the text
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:2000]  # Limit content length
                
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def clear_user_cache(self, user_session: str):
        """Clear cache for a specific user session."""
        keys_to_remove = [key for key in self.session_cache.keys() if key.startswith(user_session)]
        for key in keys_to_remove:
            del self.session_cache[key]
        logger.info(f"Cleared cache for user session: {user_session}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_items": len(self.session_cache),
            "cache_keys": list(self.session_cache.keys())
        }