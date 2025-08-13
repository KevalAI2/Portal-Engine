from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from app.logic.user_profile import get_user_profile, get_profile_insights
from app.model.user_profile import UserProfile as UserProfileModel


@dataclass
class LocationContext:
    """Context information about a user's current location"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    timezone: str = ""
    weather: str = ""
    temperature: Optional[float] = None
    time_of_day: str = ""
    day_of_week: str = ""
    is_weekend: bool = False
    is_holiday: bool = False
    local_time: Optional[datetime] = None


@dataclass
class UserContext:
    """Current user context for LIS prompts"""
    mood: str = ""
    energy_level: str = ""
    stress_level: str = ""
    group_size: int = 1
    budget_preference: str = ""
    available_time: str = ""
    transportation_mode: str = ""
    device_type: str = ""


@dataclass
class LISPrompt:
    """A location-based interest prompt"""
    prompt_id: str
    prompt_type: str
    title: str
    description: str
    urgency: str
    relevance_score: float
    reasoning: List[str]
    context_factors: Dict[str, Any]
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = None


class LISEngine:
    """Location-based Interest System Engine"""
    
    def __init__(self):
        # Location-based data (in production, this would come from external APIs)
        self.location_data = {
            "Denver, CO": {
                "restaurants": [
                    {"name": "Sakura Sushi", "cuisine": "Japanese", "price": "$$", "atmosphere": "quiet", "outdoor": True},
                    {"name": "La Trattoria", "cuisine": "Italian", "price": "$$", "atmosphere": "romantic", "outdoor": False},
                    {"name": "Spice Garden", "cuisine": "Thai", "price": "$", "atmosphere": "trendy", "outdoor": True},
                    {"name": "Urban Brew", "cuisine": "American", "price": "$", "atmosphere": "chill", "outdoor": True},
                    {"name": "Taco Fiesta", "cuisine": "Mexican", "price": "$", "atmosphere": "high-energy", "outdoor": False},
                ],
                "activities": [
                    {"name": "Red Rocks Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "2 hours"},
                    {"name": "Denver Art Museum", "type": "indoor", "category": "cultural", "price": "$$", "duration": "3 hours"},
                    {"name": "Cherry Creek Trail", "type": "outdoor", "category": "fitness", "price": "$", "duration": "1 hour"},
                    {"name": "Union Station", "type": "indoor", "category": "social", "price": "$", "duration": "2 hours"},
                ]
            }
        }
        
        # Default location data for other cities
        self.default_location_data = {
            "restaurants": [
                {"name": "Local Cafe", "cuisine": "American", "price": "$", "atmosphere": "casual", "outdoor": True},
                {"name": "Pizza Place", "cuisine": "Italian", "price": "$$", "atmosphere": "family", "outdoor": False},
            ],
            "activities": [
                {"name": "Local Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "1 hour"},
                {"name": "Shopping Center", "type": "indoor", "category": "shopping", "price": "$", "duration": "2 hours"},
            ]
        }

    def generate_location_context(self, location_str: str) -> LocationContext:
        """Generate location context from location string"""
        if "," in location_str and not location_str.replace(",", "").replace(".", "").replace("-", "").isdigit():
            parts = location_str.split(",")
            city = parts[0].strip()
            state = parts[1].strip() if len(parts) > 1 else ""
            
            now = datetime.now()
            time_of_day = self._get_time_of_day(now.hour)
            day_of_week = now.strftime("%A").lower()
            
            return LocationContext(
                location_name=location_str,
                city=city,
                state=state,
                time_of_day=time_of_day,
                day_of_week=day_of_week,
                is_weekend=day_of_week in ["saturday", "sunday"],
                local_time=now,
                weather="sunny",
                temperature=72.0
            )
        else:
            return LocationContext(location_name=location_str)

    def generate_user_context(self, user_profile: UserProfileModel) -> UserContext:
        """Generate current user context from profile"""
        return UserContext(
            mood=user_profile.user_mood or "neutral",
            energy_level=user_profile.user_energy or "medium",
            stress_level=user_profile.user_stress or "low",
            group_size=int(user_profile.typical_group_size) if user_profile.typical_group_size else 1,
            budget_preference=user_profile.preferred_budget or "$$",
            available_time="quick",
            transportation_mode="walking",
            device_type="mobile"
        )

    def generate_lis_prompts(self, db: Session, user_id: int, location_str: str) -> List[LISPrompt]:
        """Generate location-based interest prompts for a user"""
        user_profile = get_user_profile(db, user_id)
        if not user_profile:
            return []
        
        profile_insights = get_profile_insights(db, user_id)
        location_context = self.generate_location_context(location_str)
        user_context = self.generate_user_context(user_profile)
        
        prompts = []
        
        # Generate restaurant prompts
        restaurant_prompts = self._generate_restaurant_prompts(
            user_profile, profile_insights, location_context, user_context
        )
        prompts.extend(restaurant_prompts)
        
        # Generate activity prompts
        activity_prompts = self._generate_activity_prompts(
            user_profile, profile_insights, location_context, user_context
        )
        prompts.extend(activity_prompts)
        
        # Sort by relevance and urgency
        prompts.sort(key=lambda p: (self._get_urgency_score(p.urgency), p.relevance_score), reverse=True)
        
        return prompts[:10]

    def _generate_restaurant_prompts(self, profile: UserProfileModel, insights: Dict, 
                                   location_context: LocationContext, user_context: UserContext) -> List[LISPrompt]:
        """Generate restaurant-related prompts"""
        prompts = []
        
        location_data = self.location_data.get(location_context.location_name, self.default_location_data)
        restaurants = location_data.get("restaurants", [])
        
        cuisine_preferences = [p.get('value', '').lower() for p in (profile.dining_preferences_cuisine or [])]
        atmosphere_preferences = [p.get('value', '').lower() for p in (profile.dining_preferences_other or [])]
        
        for restaurant in restaurants:
            score = 0.0
            reasoning = []
            
            if restaurant['cuisine'].lower() in cuisine_preferences:
                score += 0.4
                reasoning.append(f"Matches your {restaurant['cuisine']} cuisine preference")
            
            if restaurant['atmosphere'].lower() in atmosphere_preferences:
                score += 0.3
                reasoning.append(f"Matches your preferred {restaurant['atmosphere']} atmosphere")
            
            if restaurant['price'] == user_context.budget_preference:
                score += 0.2
                reasoning.append("Matches your budget preference")
            
            if score > 0.3:
                prompt = LISPrompt(
                    prompt_id=f"restaurant_{restaurant['name'].replace(' ', '_').lower()}",
                    prompt_type="restaurant",
                    title=f"Try {restaurant['name']}",
                    description=f"Check out {restaurant['name']} - great {restaurant['cuisine']} cuisine!",
                    urgency=self._determine_urgency(location_context.time_of_day, "restaurant"),
                    relevance_score=score,
                    reasoning=reasoning,
                    context_factors={
                        "cuisine": restaurant['cuisine'],
                        "atmosphere": restaurant['atmosphere'],
                        "price": restaurant['price'],
                        "weather": location_context.weather,
                        "time_of_day": location_context.time_of_day
                    },
                    created_at=datetime.now()
                )
                prompts.append(prompt)
        
        return prompts

    def _generate_activity_prompts(self, profile: UserProfileModel, insights: Dict,
                                 location_context: LocationContext, user_context: UserContext) -> List[LISPrompt]:
        """Generate activity-related prompts"""
        prompts = []
        
        location_data = self.location_data.get(location_context.location_name, self.default_location_data)
        activities = location_data.get("activities", [])
        
        outdoor_preferences = [p.get('value', '').lower() for p in (profile.outdoor_activity_preferences or [])]
        indoor_preferences = [p.get('value', '').lower() for p in (profile.indoor_activity_preferences or [])]
        archetype = insights.get('primary_archetype', '').lower()
        
        for activity in activities:
            score = 0.0
            reasoning = []
            
            if activity['type'] == 'outdoor' and any(pref in activity['name'].lower() for pref in outdoor_preferences):
                score += 0.4
                reasoning.append("Matches your outdoor activity preferences")
            elif activity['type'] == 'indoor' and any(pref in activity['name'].lower() for pref in indoor_preferences):
                score += 0.4
                reasoning.append("Matches your indoor activity preferences")
            
            if 'adventurer' in archetype and activity['category'] in ['adventure', 'nature']:
                score += 0.3
                reasoning.append("Perfect for your adventurous spirit")
            elif 'cultural' in archetype and activity['category'] == 'cultural':
                score += 0.3
                reasoning.append("Matches your cultural interests")
            
            if score > 0.3:
                prompt = LISPrompt(
                    prompt_id=f"activity_{activity['name'].replace(' ', '_').lower()}",
                    prompt_type="activity",
                    title=f"Explore {activity['name']}",
                    description=f"Explore {activity['name']} - a great {activity['category']} activity!",
                    urgency=self._determine_urgency(location_context.time_of_day, "activity"),
                    relevance_score=score,
                    reasoning=reasoning,
                    context_factors={
                        "type": activity['type'],
                        "category": activity['category'],
                        "price": activity['price'],
                        "duration": activity['duration'],
                        "weather": location_context.weather,
                        "time_of_day": location_context.time_of_day
                    },
                    created_at=datetime.now()
                )
                prompts.append(prompt)
        
        return prompts

    def _get_time_of_day(self, hour: int) -> str:
        """Convert hour to time of day category"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    def _determine_urgency(self, time_of_day: str, prompt_type: str) -> str:
        """Determine urgency level for a prompt"""
        if prompt_type == "restaurant" and time_of_day in ["morning", "afternoon", "evening"]:
            return "high"
        elif prompt_type == "activity" and time_of_day in ["morning", "afternoon"]:
            return "medium"
        else:
            return "low"

    def _get_urgency_score(self, urgency: str) -> int:
        """Convert urgency string to numeric score"""
        urgency_scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return urgency_scores.get(urgency, 1)


# Global LIS engine instance
lis_engine = LISEngine()


def generate_lis_prompts_for_user(db: Session, user_id: int, location: str) -> List[LISPrompt]:
    """Main function to generate LIS prompts for a user"""
    return lis_engine.generate_lis_prompts(db, user_id, location)


def get_location_based_recommendations(db: Session, user_id: int, location: str) -> Dict[str, Any]:
    """Get comprehensive location-based recommendations including prompts"""
    prompts = generate_lis_prompts_for_user(db, user_id, location)
    
    grouped_prompts = {}
    for prompt in prompts:
        if prompt.prompt_type not in grouped_prompts:
            grouped_prompts[prompt.prompt_type] = []
        grouped_prompts[prompt.prompt_type].append({
            "id": prompt.prompt_id,
            "title": prompt.title,
            "description": prompt.description,
            "urgency": prompt.urgency,
            "relevance_score": prompt.relevance_score,
            "reasoning": prompt.reasoning,
            "context_factors": prompt.context_factors,
            "created_at": prompt.created_at.isoformat() if prompt.created_at else None
        })
    
    return {
        "location": location,
        "total_prompts": len(prompts),
        "prompts_by_type": grouped_prompts,
        "top_prompts": [
            {
                "id": p.prompt_id,
                "type": p.prompt_type,
                "title": p.title,
                "description": p.description,
                "urgency": p.urgency,
                "relevance_score": p.relevance_score
            }
            for p in prompts[:5]
        ],
        "generated_at": datetime.now().isoformat()
    } 