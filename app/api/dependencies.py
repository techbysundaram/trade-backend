from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time
from typing import Dict, Any, Optional
import uuid
from app.utils.auth import verify_token, get_user
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Security scheme
security = HTTPBearer(auto_error=False)

# In-memory session store
session_store: Dict[str, Dict[str, Any]] = {}

def get_rate_limiter():
    """Get rate limiter instance."""
    return limiter

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """
    Get current authenticated user or allow guest access.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        User information or None for guest access
    """
    if credentials is None:
        # Allow guest access
        return {"username": "guest", "is_guest": True}
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Get user details
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.get("disabled"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return {
            "username": user["username"],
            "is_guest": False,
            "authenticated": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_user_session(request: Request, current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Get or create user session identifier.
    
    Args:
        request: FastAPI request object
        current_user: Current user information
        
    Returns:
        Session identifier string
    """
    # Create session key based on user and IP
    client_ip = get_remote_address(request)
    username = current_user.get("username", "guest")
    
    session_key = f"{username}_{client_ip}_{int(time.time() // 3600)}"  # Hour-based session
    
    # Initialize session if not exists
    if session_key not in session_store:
        session_store[session_key] = {
            "username": username,
            "ip": client_ip,
            "created_at": time.time(),
            "request_count": 0,
            "is_guest": current_user.get("is_guest", True)
        }
    
    # Update request count
    session_store[session_key]["request_count"] += 1
    session_store[session_key]["last_seen"] = time.time()
    
    return session_key

def validate_sector_name(sector: str) -> str:
    """
    Validate and sanitize sector name input.
    
    Args:
        sector: Raw sector name from user input
        
    Returns:
        Cleaned sector name
        
    Raises:
        HTTPException: If sector name is invalid
    """
    if not sector:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name cannot be empty"
        )
    
    # Clean the sector name
    cleaned_sector = sector.strip().lower()
    
    # Check length
    if len(cleaned_sector) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name must be at least 2 characters long"
        )
    
    if len(cleaned_sector) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name must be less than 50 characters"
        )
    
    # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9\s\-_]+$', cleaned_sector):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sector name contains invalid characters. Use only letters, numbers, spaces, hyphens, and underscores."
        )
    
    # List of valid sectors (you can expand this)
    valid_sectors = [
        "pharmaceuticals", "technology", "agriculture", "automotive", "banking", 
        "healthcare", "energy", "telecommunications", "retail", "manufacturing",
        "textiles", "chemicals", "steel", "cement", "real estate", "education",
        "hospitality", "logistics", "aviation", "railways", "defense", "space",
        "renewable energy", "fintech", "biotech", "mining", "oil gas", "food processing"
    ]
    
    # Allow any sector but log unknown ones
    if cleaned_sector not in valid_sectors:
        logger.info(f"Unknown sector requested: {cleaned_sector}")
    
    return cleaned_sector

def cleanup_old_sessions():
    """Clean up old session data (call periodically)."""
    current_time = time.time()
    expired_sessions = []
    
    for session_key, session_data in session_store.items():
        # Remove sessions older than 24 hours
        if current_time - session_data.get("created_at", 0) > 86400:
            expired_sessions.append(session_key)
    
    for session_key in expired_sessions:
        del session_store[session_key]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

def get_session_stats() -> Dict[str, Any]:
    """Get session statistics."""
    cleanup_old_sessions()  # Clean up before getting stats
    
    total_sessions = len(session_store)
    guest_sessions = sum(1 for s in session_store.values() if s.get("is_guest", True))
    authenticated_sessions = total_sessions - guest_sessions
    
    return {
        "total_sessions": total_sessions,
        "guest_sessions": guest_sessions,
        "authenticated_sessions": authenticated_sessions,
        "session_keys": list(session_store.keys())
    }