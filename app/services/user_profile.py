"""
User Profile Service integration
"""
from typing import Optional
from services.base import BaseService
from models.schemas import UserProfile
from core.config import settings


class UserProfileService(BaseService):
    """Integration with User Profile Service"""
    
    def __init__(self):
        super().__init__(settings.user_profile_service_url)
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Fetch user profile data"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/profile"
            )
            
            return UserProfile(**response)
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch user profile",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_user_preferences(self, user_id: str) -> Optional[dict]:
        """Fetch user preferences"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/preferences"
            )
            
            return response.get("preferences", {})
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch user preferences",
                user_id=user_id,
                error=str(e)
            )
            return None
