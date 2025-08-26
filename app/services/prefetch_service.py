"""
Prefetch Service (LLM) integration
"""
from typing import Optional, Dict, Any, List
from services.base import BaseService
from core.config import settings


class PrefetchService(BaseService):
    """Integration with Prefetch Service (LLM)"""
    
    def __init__(self):
        super().__init__(settings.prefetch_service_url)
    
    async def generate_recommendations(
        self, 
        prompt: str, 
        user_context: Dict[str, Any],
        recommendation_type: str,
        max_results: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Generate recommendations using LLM"""
        try:
            payload = {
                "prompt": prompt,
                "user_context": user_context,
                "recommendation_type": recommendation_type,
                "max_results": max_results,
                "parameters": {
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9
                }
            }
            
            response = await self._make_request(
                method="POST",
                endpoint="/generate",
                data=payload
            )
            
            return response.get("recommendations", [])
            
        except Exception as e:
            self.logger.error(
                "Failed to generate recommendations",
                recommendation_type=recommendation_type,
                error=str(e)
            )
            return None
    
    async def validate_prompt(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Validate prompt before sending to LLM"""
        try:
            response = await self._make_request(
                method="POST",
                endpoint="/validate",
                data={"prompt": prompt}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to validate prompt",
                error=str(e)
            )
            return None
    
    async def get_model_info(self) -> Optional[Dict[str, Any]]:
        """Get information about available LLM models"""
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/models"
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Failed to get model info",
                error=str(e)
            )
            return None
