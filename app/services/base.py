"""
Base service class for external service integrations
"""
import httpx
from typing import Optional, Dict, Any
from app.core.logging import get_logger
from app.core.config import settings


class BaseService:
    """Base class for external service integrations"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to external service"""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        default_headers = {
            "Content-Type": "application/json",
            "User-Agent": f"PortalEngine/{settings.app_version}"
        }
        
        if headers:
            default_headers.update(headers)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=default_headers
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "HTTP error occurred",
                url=url,
                status_code=e.response.status_code,
                response_text=e.response.text
            )
            raise
        except httpx.RequestError as e:
            self.logger.error(
                "Request error occurred",
                url=url,
                error=str(e)
            )
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error occurred",
                url=url,
                error=str(e)
            )
            raise
    
    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            await self._make_request("GET", "/health/")
            return True
        except Exception:
            return False
