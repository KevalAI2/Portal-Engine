"""
Prompt Builder utility for constructing ranking-based natural language prompts
"""
from typing import Dict, Any, List
from core.logging import get_logger
from models.schemas import UserProfile, LocationData, InteractionData
from core.constants import RecommendationType


class PromptBuilder:
    """Ranking-based prompt builder for nuanced recommendations"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def _get_ranking_language(self, score: float) -> str:
        """Convert similarity score to ranking language"""
        if score >= 0.9:
            return "very likely"
        elif score >= 0.8:
            return "likely"
        elif score >= 0.7:
            return "may be like"
        elif score >= 0.6:
            return "somewhat interested in"
        elif score >= 0.5:
            return "not very interested in"
        else:
            return "not like"
    
    def _extract_top_interests(self, profile_data: Dict[str, Any], limit: int = 8) -> List[str]:
        """Extract top interests based on similarity scores"""
        interests = []
        
        # Check if preferences exist in the profile data
        preferences = profile_data.get("preferences", {})
        
        # Extract from keywords (legacy)
        if "Keywords (legacy)" in preferences:
            keywords_data = preferences["Keywords (legacy)"]
            if "example_values" in keywords_data:
                keywords = keywords_data["example_values"]
                for item in keywords[:limit//2]:
                    if "similarity_score" in item and "value" in item:
                        ranking = self._get_ranking_language(item["similarity_score"])
                        interests.append(f"{ranking} {item['value']}")
        
        # Extract from archetypes (legacy)
        if "Archetypes (legacy)" in preferences:
            archetypes_data = preferences["Archetypes (legacy)"]
            if "example_values" in archetypes_data:
                archetypes = archetypes_data["example_values"]
                for item in archetypes[:limit//4]:
                    if "similarity_score" in item and "value" in item:
                        ranking = self._get_ranking_language(item["similarity_score"])
                        interests.append(f"{ranking} {item['value']}")
        
        # Extract from music genres
        if "Music Genres" in preferences:
            music_data = preferences["Music Genres"]
            if "example_values" in music_data:
                music_genres = music_data["example_values"]
                for item in music_genres[:limit//4]:
                    if "similarity_score" in item and "value" in item:
                        ranking = self._get_ranking_language(item["similarity_score"])
                        interests.append(f"{ranking} {item['value']}")
        
        # Extract from dining preferences
        if "Dining preferences (cuisine)" in preferences:
            dining_data = preferences["Dining preferences (cuisine)"]
            if "example_values" in dining_data:
                cuisines = dining_data["example_values"]
                for item in cuisines[:limit//4]:
                    if "similarity_score" in item and "value" in item:
                        ranking = self._get_ranking_language(item["similarity_score"])
                        interests.append(f"{ranking} {item['value']}")
        
        return interests[:limit]
    
    def _extract_location_preferences(self, location_data: Dict[str, Any]) -> List[str]:
        """Extract location preferences based on ranking"""
        preferences = []
        
        # Extract from location patterns
        if "location_patterns" in location_data:
            patterns = location_data["location_patterns"]
            for pattern in patterns[:3]:
                if "similarity" in pattern and "venue_type" in pattern:
                    ranking = self._get_ranking_language(pattern["similarity"])
                    preferences.append(f"{ranking} {pattern['venue_type']}")
        
        return preferences
    
    def _extract_interaction_preferences(self, interaction_data: Dict[str, Any]) -> List[str]:
        """Extract interaction preferences based on ranking"""
        preferences = []
        
        # Extract from interaction patterns
        if "interaction_patterns" in interaction_data:
            patterns = interaction_data["interaction_patterns"]
            for pattern in patterns[:3]:
                if "similarity" in pattern and "content_type" in pattern:
                    ranking = self._get_ranking_language(pattern["similarity"])
                    preferences.append(f"{ranking} {pattern['content_type']}")
        
        return preferences
    
    def build_recommendation_prompt(
        self,
        user_profile: UserProfile,
        location_data: LocationData,
        interaction_data: InteractionData,
        recommendation_type: RecommendationType,
        max_results: int = 10
    ) -> str:
        """Build ranking-based recommendation prompt for multiple categories"""
        
        # Extract profile data
        profile_data = user_profile.dict() if hasattr(user_profile, 'dict') else user_profile
        location_dict = location_data.dict() if hasattr(location_data, 'dict') else location_data
        interaction_dict = interaction_data.dict() if hasattr(interaction_data, 'dict') else interaction_data
        
        # Get ranking-based interests
        top_interests = self._extract_top_interests(profile_data)
        location_prefs = self._extract_location_preferences(location_dict)
        interaction_prefs = self._extract_interaction_preferences(interaction_dict)
        
        # Safely extract location information
        current_city = "Unknown"
        current_state = ""
        if "current_location" in location_dict:
            current_loc = location_dict["current_location"]
            if isinstance(current_loc, dict):
                current_city = current_loc.get('city', 'Unknown')
                current_state = current_loc.get('state', '')
            elif isinstance(current_loc, str):
                current_city = current_loc
        
        # Safely extract engagement score
        engagement_score = 0.5
        if "engagement_score" in interaction_dict:
            engagement_score = interaction_dict["engagement_score"]
        elif hasattr(interaction_data, 'engagement_score'):
            engagement_score = interaction_data.engagement_score
        
        # Build comprehensive multi-category recommendation prompt
        prompt = f"""You are an expert recommendation system. Based on the following user profile with ranking preferences, provide multiple personalized recommendations across 4 different categories in JSON format.

USER PROFILE:
Name: {profile_data.get('name', 'Unknown User')}
Age: {profile_data.get('age', 'Unknown')}
Currently in: {current_city}, {current_state}
Home: {profile_data.get('home_location', 'Unknown')}

RANKING-BASED INTERESTS:
{chr(10).join(f"• {interest}" for interest in top_interests)}

LOCATION PREFERENCES:
{chr(10).join(f"• {pref}" for pref in location_prefs)}

INTERACTION PREFERENCES:
{chr(10).join(f"• {pref}" for pref in interaction_prefs)}

RECOMMENDATION CONTEXT:
Location: {current_city}, {current_state}
Engagement level: {engagement_score:.2f} (High if >0.7, Medium if 0.4-0.7, Low if <0.4)

Please provide 3-5 recommendations for each of the following 4 categories in JSON format. Focus on items that match their "very likely" and "likely" interests while avoiding what they "not like".

Respond with a JSON object in this exact format:
{{
  "movies": [
    {{
      "title": "Movie Title",
      "year": "Year",
      "genre": "Movie Genre",
      "description": "Short one-line description",
      "reason": "Brief explanation of why it matches their ranking preferences"
    }}
  ],
  "music": [
    {{
      "title": "Album/Artist Name",
      "genre": "Music Genre",
      "description": "Short one-line description",
      "reason": "Brief explanation of why it matches their ranking preferences"
    }}
  ],
  "places": [
    {{
      "name": "Place Name",
      "type": "Restaurant/Attraction/Activity",
      "description": "Short one-line description",
      "reason": "Brief explanation of why it matches their ranking preferences"
    }}
  ],
  "events": [
    {{
      "name": "Event Name",
      "date": "Event Date/Time",
      "description": "Short one-line description",
      "reason": "Brief explanation of why it matches their ranking preferences"
    }}
  ]
}}"""
        
        return prompt