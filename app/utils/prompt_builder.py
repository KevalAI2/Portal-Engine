"""
Prompt Builder utility for constructing dynamic LLM prompts
"""
from typing import Dict, Any, List
from app.core.logging import get_logger
from app.models.schemas import UserProfile, LocationData, InteractionData
from app.core.constants import RecommendationType


class PromptBuilder:
    """Dynamic prompt builder for LLM recommendations"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def build_recommendation_prompt(
        self,
        user_profile: UserProfile,
        location_data: LocationData,
        interaction_data: InteractionData,
        recommendation_type: RecommendationType,
        max_results: int = 10
    ) -> str:
        """Build a dynamic prompt for recommendation generation"""
        
        # Base prompt template
        base_prompt = self._get_base_prompt(recommendation_type)
        
        # Build user context
        user_context = self._build_user_context(user_profile, location_data, interaction_data)
        
        # Build specific context based on recommendation type
        type_context = self._build_type_context(recommendation_type, user_profile, location_data)
        
        # Combine all parts
        prompt = f"""
{base_prompt}

USER CONTEXT:
{user_context}

SPECIFIC CONTEXT:
{type_context}

INSTRUCTIONS:
- Generate exactly {max_results} personalized recommendations
- Each recommendation should be relevant to the user's profile and context
- Provide a confidence score between 0.0 and 1.0 for each recommendation
- Include relevant metadata for each recommendation
- Format the response as a structured list

Please provide {max_results} {recommendation_type} recommendations for this user.
"""
        
        self.logger.info(
            "Built recommendation prompt",
            recommendation_type=recommendation_type,
            user_id=user_profile.user_id,
            prompt_length=len(prompt)
        )
        
        return prompt.strip()
    
    def _get_base_prompt(self, recommendation_type: RecommendationType) -> str:
        """Get base prompt template for recommendation type"""
        
        base_prompts = {
            RecommendationType.MUSIC: """
You are an expert music recommendation system. Based on the user's profile, location, and interaction history, 
provide personalized music recommendations that match their taste and current context.
""",
            RecommendationType.MOVIE: """
You are an expert movie recommendation system. Based on the user's profile, location, and interaction history, 
provide personalized movie recommendations that match their preferences and current mood.
""",
            RecommendationType.PLACE: """
You are an expert location-based recommendation system. Based on the user's profile, current location, and preferences, 
provide personalized place recommendations (restaurants, attractions, services) that are relevant and accessible.
""",
            RecommendationType.EVENT: """
You are an expert event recommendation system. Based on the user's profile, location, and interests, 
provide personalized event recommendations that match their schedule and preferences.
"""
        }
        
        return base_prompts.get(recommendation_type, "Provide personalized recommendations based on the user context.")
    
    def _build_user_context(
        self, 
        user_profile: UserProfile, 
        location_data: LocationData, 
        interaction_data: InteractionData
    ) -> str:
        """Build comprehensive user context for the prompt"""
        
        context_parts = []
        
        # Basic profile information
        if user_profile.name:
            context_parts.append(f"Name: {user_profile.name}")
        if user_profile.age:
            context_parts.append(f"Age: {user_profile.age}")
        if user_profile.location:
            context_parts.append(f"General Location: {user_profile.location}")
        
        # Interests and preferences
        if user_profile.interests:
            context_parts.append(f"Interests: {', '.join(user_profile.interests)}")
        if user_profile.preferences:
            context_parts.append(f"Preferences: {self._format_preferences(user_profile.preferences)}")
        
        # Location context
        if location_data.current_location:
            context_parts.append(f"Current Location: {location_data.current_location}")
        if location_data.home_location:
            context_parts.append(f"Home Location: {location_data.home_location}")
        if location_data.work_location:
            context_parts.append(f"Work Location: {location_data.work_location}")
        if location_data.travel_history:
            context_parts.append(f"Recent Travel: {', '.join(location_data.travel_history[-5:])}")
        
        # Interaction context
        if interaction_data.engagement_score:
            context_parts.append(f"Engagement Level: {interaction_data.engagement_score:.2f}")
        if interaction_data.recent_interactions:
            context_parts.append(f"Recent Activity: {self._format_interactions(interaction_data.recent_interactions)}")
        
        return "\n".join(context_parts) if context_parts else "Limited user context available."
    
    def _build_type_context(
        self, 
        recommendation_type: RecommendationType, 
        user_profile: UserProfile, 
        location_data: LocationData
    ) -> str:
        """Build type-specific context for the recommendation"""
        
        if recommendation_type == RecommendationType.MUSIC:
            return self._build_music_context(user_profile, location_data)
        elif recommendation_type == RecommendationType.MOVIE:
            return self._build_movie_context(user_profile, location_data)
        elif recommendation_type == RecommendationType.PLACE:
            return self._build_place_context(user_profile, location_data)
        elif recommendation_type == RecommendationType.EVENT:
            return self._build_event_context(user_profile, location_data)
        else:
            return "General recommendation context."
    
    def _build_music_context(self, user_profile: UserProfile, location_data: LocationData) -> str:
        """Build music-specific context"""
        context = "Music preferences and listening context:"
        
        if user_profile.preferences.get("music"):
            context += f"\n- Music preferences: {self._format_preferences(user_profile.preferences['music'])}"
        
        if location_data.current_location:
            context += f"\n- Current location for music context: {location_data.current_location}"
        
        return context
    
    def _build_movie_context(self, user_profile: UserProfile, location_data: LocationData) -> str:
        """Build movie-specific context"""
        context = "Movie preferences and viewing context:"
        
        if user_profile.preferences.get("movies"):
            context += f"\n- Movie preferences: {self._format_preferences(user_profile.preferences['movies'])}"
        
        if location_data.current_location:
            context += f"\n- Current location for movie availability: {location_data.current_location}"
        
        return context
    
    def _build_place_context(self, user_profile: UserProfile, location_data: LocationData) -> str:
        """Build place-specific context"""
        context = "Location-based recommendations context:"
        
        if location_data.current_location:
            context += f"\n- Current location: {location_data.current_location}"
        if location_data.location_preferences:
            context += f"\n- Location preferences: {self._format_preferences(location_data.location_preferences)}"
        
        return context
    
    def _build_event_context(self, user_profile: UserProfile, location_data: LocationData) -> str:
        """Build event-specific context"""
        context = "Event recommendations context:"
        
        if location_data.current_location:
            context += f"\n- Current location for event proximity: {location_data.current_location}"
        if user_profile.interests:
            context += f"\n- Event interests: {', '.join(user_profile.interests)}"
        
        return context
    
    def _format_preferences(self, preferences: Dict[str, Any]) -> str:
        """Format preferences dictionary for prompt"""
        if isinstance(preferences, dict):
            return ", ".join([f"{k}: {v}" for k, v in preferences.items()])
        return str(preferences)
    
    def _format_interactions(self, interactions: List[Dict[str, Any]]) -> str:
        """Format recent interactions for prompt"""
        if not interactions:
            return "No recent interactions"
        
        # Take last 3 interactions and format them
        recent = interactions[-3:]
        formatted = []
        
        for interaction in recent:
            if isinstance(interaction, dict):
                action = interaction.get("action", "unknown")
                timestamp = interaction.get("timestamp", "")
                formatted.append(f"{action} ({timestamp})")
            else:
                formatted.append(str(interaction))
        
        return "; ".join(formatted)
