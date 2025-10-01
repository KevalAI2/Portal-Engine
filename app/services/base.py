"""
Base service class for external service integrations
"""
import httpx
from typing import Optional, Dict, Any
from app.core.logging import get_logger
from app.core.config import settings
import time


class _SimpleCircuitBreaker:
    """Very lightweight in-process circuit breaker to protect external calls."""
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.open_until = 0.0

    def allow(self) -> bool:
        return time.time() >= self.open_until

    def record_success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.open_until = time.time() + self.recovery_time


class BaseService:
    """Base class for external service integrations"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)
        self._circuit = _SimpleCircuitBreaker()
    
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
        
        # Circuit breaker check
        if not self._circuit.allow():
            self.logger.warning("Circuit open, skipping external request", url=url)
            return {"success": False, "error": "circuit_open"}

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
                self._circuit.record_success()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "HTTP error occurred",
                url=url,
                status_code=e.response.status_code,
                response_text=e.response.text
            )
            self._circuit.record_failure()
            raise
        except httpx.RequestError as e:
            self.logger.error(
                "Request error occurred",
                url=url,
                error=str(e)
            )
            self._circuit.record_failure()
            raise
        except Exception as e:
            self.logger.error(
                "Unexpected error occurred",
                url=url,
                error=str(e)
            )
            self._circuit.record_failure()
            raise
    
    async def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            await self._make_request("GET", "/health/")
            return True
        except Exception:
            return False
