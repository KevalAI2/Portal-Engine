"""
LIE (Location Intelligence Engine) Service integration
"""
from typing import Optional
from services.base import BaseService
from models.schemas import LocationData
from core.config import settings


class LIEService(BaseService):
    """Integration with LIE (Location Intelligence Engine) Service"""
    
    def __init__(self):
        super().__init__(settings.lie_service_url)
    
    async def get_location_data(self, user_id: str) -> Optional[LocationData]:
        """Fetch location data for a user"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/location"
            )
            
            return LocationData(**response)
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch location data",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_current_location(self, user_id: str) -> Optional[str]:
        """Get user's current location"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/location/current"
            )
            
            return response.get("current_location")
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch current location",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_location_history(self, user_id: str) -> Optional[list]:
        """Get user's location history"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/location/history"
            )
            
            return response.get("history", [])
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch location history",
                user_id=user_id,
                error=str(e)
            )
            return None
