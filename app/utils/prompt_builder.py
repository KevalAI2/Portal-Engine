"""
Enhanced Prompt Builder utility for constructing ranking-based natural language prompts
with complete JSON structure for all categories
"""
from typing import Dict, Any, List, Optional
from core.logging import get_logger
from models.schemas import UserProfile, LocationData, InteractionData
from core.constants import RecommendationType
import time

class PromptBuilder:
    """Ranking-based prompt builder for nuanced recommendations with complete JSON structure"""
    
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
    
    def _get_complete_json_structure(self, current_city: str = "Barcelona") -> str:
        """Return the complete JSON structure template for all categories"""
        return f'''{{
  "movies": [
    {{
      "title": "Movie Title",
      "year": "2024",
      "genre": "Drama/Action/Comedy",
      "description": "Engaging one-line description of the movie",
      "director": "Director Name",
      "rating": "8.2",
      "duration": "120",
      "streaming_platform": "Netflix/Amazon Prime/Disney+",
      "cast": ["Actor 1", "Actor 2", "Actor 3"],
      "imdb_id": "tt1234567",
      "poster_url": "https://image.tmdb.org/t/p/w500/poster.jpg",
      "trailer_url": "https://youtube.com/watch?v=trailer",
      "language": "English",
      "country": "USA",
      "box_office": "$100M",
      "awards": "Academy Award nominations",
      "age_rating": "PG-13",
      "keywords": ["adventure", "family", "drama"],
      "why_would_you_like_this": "Detailed explanation matching user's profile data, location data, and interaction data specifically"
    }}
  ],
  "music": [
    {{
      "title": "Song/Album Title",
      "artist": "Artist Name",
      "genre": "Pop/Rock/Jazz/Electronic",
      "description": "Captivating one-line description of the music",
      "release_year": "2024",
      "album": "Album Name",
      "duration": "3:45",
      "spotify_url": "https://open.spotify.com/track/...",
      "apple_music_url": "https://music.apple.com/album/...",
      "youtube_url": "https://youtube.com/watch?v=...",
      "label": "Record Label",
      "producer": "Producer Name",
      "featured_artists": ["Featured Artist 1"],
      "lyrics_snippet": "Memorable lyric line",
      "chart_position": "Billboard Hot 100 #15",
      "monthly_listeners": "50M",
      "mood": "upbeat/melancholic/energetic",
      "tempo": "120 BPM",
      "key": "C Major",
      "why_would_you_like_this": "Detailed explanation matching user's profile data, location data, and interaction data specifically"
    }}
  ],
  "places": [
    {{
      "name": "Place Name",
      "type": "restaurant/attraction/activity/cafe/bar",
      "hours": ["Monday: 9:00 – 17:00", "Tuesday: 9:00 – 17:00", "Wednesday: 9:00 – 17:00", "Thursday: 9:00 – 17:00", "Friday: 9:00 – 17:00", "Saturday: 10:00 – 16:00", "Sunday: Closed"],
      "query": "Place Name {current_city}",
      "rating": 4.5,
      "reviews": "Excellent food and atmosphere. Highly recommended for families.",
      "website": "https://restaurant-website.com",
      "category": "restaurant/tourist_attraction/entertainment",
      "location": {{"lat": 41.3851, "lng": 2.1734}},
      "place_id": "ChIJ2WrMN9iipBIRfUeonIcnGWs",
      "vicinity": "Carrer de Example, 123, {current_city}",
      "photo_url": "https://places.googleapis.com/v1/places/PLACE_ID/photos/PHOTO_REFERENCE",
      "time_comments": "Best visited during lunch hours",
      "llmDescription": "Detailed description with local context and specific recommendations",
      "preferred_time": "morning/afternoon/evening/night",
      "business_status": "OPERATIONAL",
      "google_maps_url": "https://maps.google.com/?cid=12345678901234567890",
      "distance_from_user": 150,
      "user_ratings_total": 200,
      "phone_international": "+34 XXX XXX XXX",
      "phone_local": "XXX XXX XXX",
      "price_level": 2,
      "cuisine_type": "Mediterranean/Italian/Asian",
      "delivery_available": true,
      "reservation_required": false,
      "parking_available": true,
      "wifi_available": true,
      "wheelchair_accessible": true,
      "outdoor_seating": true,
      "why_would_you_like_this": "Detailed explanation matching user's profile data, location data, and interaction data specifically"
    }}
  ],
  "events": [
    {{
      "name": "Event Name",
      "date": "2024-09-15T20:00:00Z",
      "end_date": "2024-09-15T23:00:00Z",
      "description": "Engaging one-line description of the event",
      "venue": "Venue Name",
      "address": "Complete address in {current_city}",
      "price": "€25-€50",
      "price_min": 25,
      "price_max": 50,
      "currency": "EUR",
      "category": "music/art/sports/cultural/food/tech",
      "duration": "3 hours",
      "organizer": "Event Organizer Name",
      "website": "https://event-website.com",
      "booking_url": "https://tickets.com/event/12345",
      "age_restriction": "18+",
      "capacity": 500,
      "tickets_available": true,
      "event_type": "concert/festival/workshop/exhibition",
      "languages": ["English", "Spanish", "Catalan"],
      "dress_code": "casual/formal/themed",
      "parking_info": "Street parking available",
      "public_transport": "Metro: L3 Fontana station",
      "contact_phone": "+34 XXX XXX XXX",
      "contact_email": "info@event.com",
      "social_media": {{"facebook": "https://facebook.com/event", "instagram": "@event_handle"}},
      "weather_dependency": false,
      "refund_policy": "Full refund up to 24 hours before",
      "accessibility": "Wheelchair accessible",
      "why_would_you_like_this": "Detailed explanation matching user's profile data, location data, and interaction data specifically"
    }}
  ]
}}'''

    def build_recommendation_prompt(
        self,
        user_profile: UserProfile,
        location_data: LocationData,
        interaction_data: InteractionData,
        recommendation_type: RecommendationType,
        max_results: int = 10
    ) -> str:
        """Build ranking-based recommendation prompt for multiple categories with complete JSON structure"""
        
        # Extract profile data
        profile_data = user_profile.dict() if hasattr(user_profile, 'dict') else user_profile
        location_dict = location_data.dict() if hasattr(location_data, 'dict') else location_data
        interaction_dict = interaction_data.dict() if hasattr(interaction_data, 'dict') else interaction_data
        
        # Get ranking-based interests
        top_interests = self._extract_top_interests(profile_data)
        location_prefs = self._extract_location_preferences(location_dict)
        interaction_prefs = self._extract_interaction_preferences(interaction_dict)
        
        # Safely extract location information
        current_city = "Barcelona"
        current_state = "Catalonia"
        if "current_location" in location_dict:
            current_loc = location_dict["current_location"]
            if isinstance(current_loc, dict):
                current_city = current_loc.get('city', 'Barcelona')
                current_state = current_loc.get('state', 'Catalonia')
            elif isinstance(current_loc, str):
                current_city = current_loc
        
        # Safely extract engagement score
        engagement_score = 0.5
        if "engagement_score" in interaction_dict:
            engagement_score = interaction_dict["engagement_score"]
        elif hasattr(interaction_data, 'engagement_score'):
            engagement_score = interaction_data.engagement_score
        
        # Build comprehensive multi-category recommendation prompt with complete JSON structure
        prompt = f"""You are an expert recommendation system. Based on the following user profile with ranking preferences, provide multiple personalized recommendations across 4 different categories in JSON format with complete structured data.

USER PROFILE:
Name: {profile_data.get('name', 'Unknown User')}
Age: {profile_data.get('age', 'Unknown')}
Currently in: {current_city}, {current_state}
Home: {profile_data.get('home_location', 'Unknown')}

RANKING-BASED INTERESTS:
{chr(10).join(f"• {interest}" for interest in top_interests) if top_interests else "• General entertainment preferences"}

LOCATION PREFERENCES:
{chr(10).join(f"• {pref}" for pref in location_prefs) if location_prefs else "• Standard local venues"}

INTERACTION PREFERENCES:
{chr(10).join(f"• {pref}" for pref in interaction_prefs) if interaction_prefs else "• Balanced content engagement"}

RECOMMENDATION CONTEXT:
Location: {current_city}, {current_state}
Engagement level: {engagement_score:.2f} (High if >0.7, Medium if 0.4-0.7, Low if <0.4)
Current date: {time.strftime('%Y-%m-%d', time.gmtime())}

INSTRUCTIONS:
1. Provide {max_results} recommendations per category
2. Focus on items matching "very likely" and "likely" interests while avoiding "not like" preferences
3. Include complete, realistic data for all fields in the JSON structure
4. For places: Use actual {current_city} coordinates, addresses, and local phone formats
5. For events: Use realistic dates within the next 30 days, local venues, and appropriate pricing
6. For movies: Include current releases and popular films with accurate ratings and platforms
7. For music: Include trending and classic tracks with real streaming URLs format
8. All "why_would_you_like_this" fields must reference specific user profile, location, and interaction data

Respond with a JSON object in this exact format:
{self._get_complete_json_structure(current_city)}

CRITICAL REQUIREMENTS:
- ALL fields must be filled with realistic, relevant data
- NO placeholder text like "PLACE_ID" or "..." 
- Phone numbers must use local format for {current_city}
- Coordinates must be realistic for {current_city} area
- URLs must be properly formatted (even if example URLs)
- Dates must be realistic and future-dated for events
- All explanations must specifically reference user's profile elements"""
        
        return prompt

    def build_fallback_prompt(
        self,
        user_profile: Optional[Any] = None,
        location_data: Optional[Any] = None,
        interaction_data: Optional[Any] = None,
        recommendation_type: RecommendationType = RecommendationType.PLACE,
        max_results: int = 10,
    ) -> str:
        """Build a dynamic fallback prompt with complete JSON structure when some or all inputs are missing"""
        
        # Validate inputs
        if not isinstance(max_results, int) or max_results < 1 or max_results > 20:
            self.logger.warning(f"Invalid max_results {max_results}, defaulting to 10")
            max_results = 10
        if not isinstance(recommendation_type, RecommendationType):
            self.logger.warning(f"Invalid recommendation_type {recommendation_type}, defaulting to PLACE")
            recommendation_type = RecommendationType.PLACE

        # Initialize defaults
        name = "Friend"
        age = "Unknown"
        home = "Unknown"
        current_city = "Barcelona"  # Default to Barcelona as in original
        current_state = "Catalonia"
        country = "Spain"
        engagement_score = 0.5
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        
        # Track what data is available
        available_data = []
        profile_info = []
        location_info = []
        interaction_info = []

        # Extract user profile data
        try:
            if user_profile is not None:
                available_data.append("user profile")
                if hasattr(user_profile, 'dict'):
                    p = user_profile.dict()
                elif hasattr(user_profile, 'model_dump'):
                    p = user_profile.model_dump()
                else:
                    p = user_profile if isinstance(user_profile, dict) else {}
                
                if p.get('name'):
                    name = p['name']
                    profile_info.append(f"Name: {name}")
                if p.get('age'):
                    age = str(p['age'])
                    profile_info.append(f"Age: {age}")
                if p.get('home_location'):
                    home = p['home_location']
                    profile_info.append(f"Home: {home}")
                
                # Extract interests if available
                interests = self._extract_top_interests(p, limit=5)
                if interests:
                    profile_info.append(f"Interests: {', '.join(interests[:3])}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting user profile: {str(e)}")

        # Extract location data
        try:
            if location_data is not None:
                available_data.append("location data")
                if hasattr(location_data, 'dict'):
                    loc = location_data.dict()
                elif hasattr(location_data, 'model_dump'):
                    loc = location_data.model_dump()
                else:
                    loc = location_data if isinstance(location_data, dict) else {}
                
                if loc and 'current_location' in loc:
                    cur = loc['current_location']
                    if isinstance(cur, dict):
                        if cur.get('city'):
                            current_city = cur['city']
                            location_info.append(f"Current city: {current_city}")
                        if cur.get('state'):
                            current_state = cur['state']
                            location_info.append(f"State/Region: {current_state}")
                        if cur.get('country'):
                            country = cur['country']
                    elif isinstance(cur, str) and cur.strip():
                        current_city = cur.strip()
                        location_info.append(f"Current location: {current_city}")
                
                # Extract location preferences
                loc_prefs = self._extract_location_preferences(loc)
                if loc_prefs:
                    location_info.append(f"Venue preferences: {', '.join(loc_prefs[:2])}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting location data: {str(e)}")

        # Extract interaction data
        try:
            if interaction_data is not None:
                available_data.append("interaction data")
                if hasattr(interaction_data, 'dict'):
                    inter = interaction_data.dict()
                elif hasattr(interaction_data, 'model_dump'):
                    inter = interaction_data.model_dump()
                else:
                    inter = interaction_data if isinstance(interaction_data, dict) else {}
                
                if inter and 'engagement_score' in inter:
                    score = inter.get('engagement_score', engagement_score)
                    if isinstance(score, (int, float)) and 0 <= score <= 1:
                        engagement_score = score
                        interaction_info.append(f"Engagement level: {engagement_score:.2f}")
                
                # Extract interaction preferences
                interaction_prefs = self._extract_interaction_preferences(inter)
                if interaction_prefs:
                    interaction_info.append(f"Content preferences: {', '.join(interaction_prefs[:2])}")
                    
        except Exception as e:
            self.logger.error(f"Error extracting interaction data: {str(e)}")

        # Build dynamic user context section
        user_context = f"Name: {name}"
        if age != "Unknown":
            user_context += f"\nAge: {age}"
        if home != "Unknown":
            user_context += f"\nHome: {home}"
        
        # Add available profile info
        if profile_info:
            user_context += f"\nProfile details: {'; '.join(profile_info)}"
        
        # Build location context
        location_context = f"Current location: {current_city}"
        if current_state and current_state != current_city:
            location_context += f", {current_state}"
        if country and country not in location_context:
            location_context += f", {country}"
            
        if location_info:
            location_context += f"\nLocation insights: {'; '.join(location_info)}"

        # Build interaction context
        interaction_context = f"Engagement level: {engagement_score:.2f}"
        if interaction_info:
            interaction_context += f"\nInteraction insights: {'; '.join(interaction_info)}"

        # Data availability status
        data_status = f"Available data: {', '.join(available_data) if available_data else 'limited - using local trends and general preferences'}"

        # Category emphasis based on recommendation type
        category_emphasis = {
            RecommendationType.MOVIE: f"Prioritize movie recommendations with complete metadata",
            RecommendationType.MUSIC: f"Prioritize music recommendations with streaming links",
            RecommendationType.PLACE: f"Prioritize local {current_city} venues with accurate location data",
            RecommendationType.EVENT: f"Prioritize upcoming {current_city} events with complete details",
        }.get(recommendation_type, f"Balance all categories with local {current_city} focus")

        # Build the dynamic fallback prompt
        prompt = f"""You are an expert recommendation system generating personalized suggestions as of {timestamp}.

USER CONTEXT ({data_status}):
{user_context}

LOCATION CONTEXT:
{location_context}

INTERACTION CONTEXT:
{interaction_context}

RECOMMENDATION STRATEGY:
- {category_emphasis}
- Generate {max_results} diverse, high-quality recommendations per category
- Use local {current_city} trends and popular venues for places/events
- Include globally popular movies and music with broad appeal
- Focus on highly-rated, accessible options suitable for available user context
- Ensure variety in genres, styles, price points, and types

RECOMMENDATION STRATEGY:
- {category_emphasis}
- Generate {max_results} diverse, high-quality recommendations per category
- Use local {current_city} trends and popular venues for places/events
- Include globally popular movies and music with broad appeal
- Focus on highly-rated, accessible options suitable for available user context
- Ensure variety in genres, styles, price points, and types

{self._get_json_structure_requirements()}

CONTENT CREATION RULES:
- Create REAL content: actual movie titles, restaurant names, artist names, event titles
- NO placeholder text: Don't use "Movie Title", "Place Name", "Event Name", etc.
- Generate realistic data: proper coordinates for {current_city}, authentic phone numbers, real-sounding addresses
- Vary everything: different genres, release years, price ranges, venue types
- Mix popular and niche options for broader appeal
- Use current date context for events (within 30 days)

PERSONALIZATION GUIDELINES:
- Reference available user data in "why_would_you_like_this" explanations
- When limited data available, focus on broad appeal factors
- Be specific: "Perfect for your Barcelona location and interest in cultural experiences"
- Avoid generic phrases: "You might enjoy this" → "Given your [specific trait]..."

Output exactly {max_results} unique, complete items per category."""
        
        return prompt