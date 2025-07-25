from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any
import logging
from app.services.analysis import MarketAnalysisService
from app.api.dependencies import (
    get_current_user, 
    get_user_session, 
    validate_sector_name,
    get_rate_limiter
)
from app.config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analyze", tags=["analysis"])

# Initialize services
analysis_service = MarketAnalysisService()
limiter = get_rate_limiter()

@router.get("/{sector}")
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/{settings.RATE_LIMIT_WINDOW}seconds")
async def analyze_sector(
    request: Request,
    sector: str,
    response: Response,
    format: str = "json",
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_session: str = Depends(get_user_session)
) -> Dict[str, Any]:
    """
    Analyze a specific sector and return trade opportunities.
    
    Args:
        request: FastAPI request object
        sector: Name of the sector to analyze (e.g., "pharmaceuticals", "technology")
        response: FastAPI response object
        format: Response format ("json" or "markdown")
        current_user: Current authenticated user
        user_session: User session identifier
        
    Returns:
        Structured market analysis report
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        # Validate and clean sector name
        clean_sector = validate_sector_name(sector)
        
        logger.info(f"Analyzing sector '{clean_sector}' for user '{current_user.get('username', 'unknown')}' (session: {user_session[:10]}...)")
        
        # Perform analysis
        analysis_result = await analysis_service.analyze_sector(clean_sector, user_session)
        
        # Add user context to response
        analysis_result["user_context"] = {
            "username": current_user.get("username"),
            "is_guest": current_user.get("is_guest", True),
            "session_id": user_session[:10] + "..."  # Partial session ID for privacy
        }
        
        # Set response headers
        response.headers["X-Analysis-Status"] = analysis_result.get("status", "unknown")
        response.headers["X-User-Type"] = "guest" if current_user.get("is_guest") else "authenticated"
        
        # Return markdown format if requested
        if format.lower() == "markdown":
            return PlainTextResponse(
                content=analysis_result.get("analysis", "No analysis available"),
                media_type="text/markdown"
            )
        
        # Return JSON format by default
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error analyzing sector '{sector}': {str(