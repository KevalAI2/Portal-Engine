"""
CIS (Content Interaction Service) integration
"""
from typing import Optional
from services.base import BaseService
from models.schemas import InteractionData
from core.config import settings


class CISService(BaseService):
    """Integration with CIS (Content Interaction Service)"""
    
    def __init__(self):
        super().__init__(settings.cis_service_url)
    
    async def get_interaction_data(self, user_id: str) -> Optional[InteractionData]:
        """Fetch interaction data for a user"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/interactions"
            )
            
            return InteractionData(**response)
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch interaction data",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_recent_interactions(self, user_id: str, limit: int = 10) -> Optional[list]:
        """Get user's recent interactions"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/interactions/recent",
                params={"limit": limit}
            )
            
            return response.get("interactions", [])
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch recent interactions",
                user_id=user_id,
                error=str(e)
            )
            return None
    
    async def get_engagement_score(self, user_id: str) -> Optional[float]:
        """Get user's engagement score"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/users/{user_id}/engagement"
            )
            
            return response.get("score")
            
        except Exception as e:
            self.logger.error(
                "Failed to fetch engagement score",
                user_id=user_id,
                error=str(e)
            )
            return None
