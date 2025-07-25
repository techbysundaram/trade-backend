import google.generativeai as genai
from typing import Dict, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            logger.warning("Gemini API key not configured")
            self.model = None
    
    async def analyze_sector_data(self, sector: str, market_data: Dict[str, Any]) -> str:
        """
        Analyze sector data using Gemini AI and generate insights.
        
        Args:
            sector: The sector name to analyze
            market_data: Dictionary containing market information
            
        Returns:
            Structured markdown analysis report
        """
        if not self.model:
            return self._generate_fallback_analysis(sector, market_data)
        
        try:
            # Prepare the prompt for Gemini
            prompt = self._create_analysis_prompt(sector, market_data)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text
            else:
                logger.error("Empty response from Gemini API")
                return self._generate_fallback_analysis(sector, market_data)
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {str(e)}")
            return self._generate_fallback_analysis(sector, market_data)
    
    def _create_analysis_prompt(self, sector: str, market_data: Dict[str, Any]) -> str:
        """Create a structured prompt for Gemini analysis."""
        
        news_summary = "\n".join([
            f"- {item.get('title', 'No title')}: {item.get('snippet', 'No summary')}"
            for item in market_data.get('news', [])[:5]
        ])
        
        prompt = f"""
        As a market analyst specializing in Indian markets, analyze the {sector} sector and provide trade opportunities.
        
        Current Market Information:
        {news_summary}
        
        Please provide a comprehensive markdown analysis report with the following structure:
        
        # {sector.title()} Sector Analysis Report
        
        ## Executive Summary
        Provide a 2-3 sentence overview of the current state and opportunities.
        
        ## Market Overview
        - Current market size and growth trends
        - Key players and market dynamics
        - Recent developments affecting the sector
        
        ## Trade Opportunities
        ### Short-term Opportunities (1-3 months)
        - List 3-5 specific opportunities with brief explanations
        
        ### Medium-term Opportunities (3-12 months)  
        - List 3-5 opportunities with market drivers
        
        ### Long-term Opportunities (1-3 years)
        - List 2-3 strategic opportunities
        
        ## Risk Analysis
        - Key risks and challenges
        - Mitigation strategies
        
        ## Investment Recommendations
        - Recommended investment strategies
        - Entry and exit points to consider
        
        ## Key Metrics to Monitor
        - Important indicators to track
        - Regulatory changes to watch
        
        ## Conclusion
        Summary of key takeaways and next steps.
        
        Focus on Indian market context, current economic conditions, and provide actionable insights.
        Make sure all recommendations are based on the provided market data and current trends.
        """
        
        return prompt
    
    def _generate_fallback_analysis(self, sector: str, market_data: Dict[str, Any]) -> str:
        """Generate a basic analysis when Gemini API is not available."""
        
        news_items = market_data.get('news', [])
        
        report = f"""# {sector.title()} Sector Analysis Report

## Executive Summary
Based on current market data, the {sector} sector in India shows mixed signals with both opportunities and challenges present in the current economic environment.

## Market Overview
The {sector} sector is experiencing dynamic changes driven by various economic and regulatory factors. Recent developments suggest:

"""
        
        if news_items:
            report += "### Recent Market News:\n"
            for item in news_items[:3]:
                title = item.get('title', 'Market Update')
                snippet = item.get('snippet', 'No details available')
                report += f"- **{title}**: {snippet}\n"
        
        report += f"""
## Trade Opportunities

### Short-term Opportunities (1-3 months)
- Monitor daily price movements and volatility patterns
- Look for sector-specific news that could drive short-term price action
- Consider technical analysis for entry and exit points

### Medium-term Opportunities (3-12 months)
- Evaluate fundamental changes in sector regulation
- Assess impact of government policies on {sector} companies
- Monitor quarterly earnings trends

### Long-term Opportunities (1-3 years)
- Consider structural changes in the Indian economy
- Evaluate demographic trends affecting {sector} demand
- Assess technological disruption potential

## Risk Analysis
- **Market Risk**: General market volatility could affect sector performance
- **Regulatory Risk**: Changes in government policies
- **Economic Risk**: Broader economic slowdown impact
- **Competition Risk**: Increased competition from domestic and international players

## Investment Recommendations
- Diversify across multiple companies within the sector
- Consider both large-cap stability and mid-cap growth potential
- Monitor key economic indicators that affect the {sector} sector
- Maintain appropriate position sizing based on risk tolerance

## Key Metrics to Monitor
- Sector-specific growth rates
- Government policy announcements
- Export/import data (if applicable)
- Raw material costs and availability
- Consumer demand trends

## Conclusion
The {sector} sector presents various opportunities for traders and investors. Success will depend on careful analysis of market conditions, proper risk management, and staying informed about sector-specific developments.

*Note: This analysis is based on available market data and should not be considered as financial advice. Please consult with financial advisors before making investment decisions.*
"""
        
        return report