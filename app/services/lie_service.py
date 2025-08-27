"""
LIE (Location Intelligence Engine) Service with Mock Data Generation
"""
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from services.base import BaseService
from models.schemas import LocationData
from core.config import settings
from core.logging import get_logger


class LIEService(BaseService):
    """LIE (Location Intelligence Engine) Service with comprehensive mock location data"""
    
    def __init__(self):
        super().__init__(settings.lie_service_url)
        self.logger = get_logger("lie_service")
        
        # Mock location data templates
        self.mock_data = {
            "cities": [
                "New York, NY", "Los Angeles, CA", "Chicago, IL", "San Francisco, CA",
                "Miami, FL", "Austin, TX", "Seattle, WA", "Denver, CO", "Boston, MA",
                "Portland, OR", "Nashville, TN", "Las Vegas, NV", "Phoenix, AZ",
                "Atlanta, GA", "Dallas, TX", "Houston, TX", "Philadelphia, PA",
                "Washington, DC", "San Diego, CA", "Orlando, FL", "Minneapolis, MN",
                "Detroit, MI", "Cleveland, OH", "Pittsburgh, PA", "Cincinnati, OH"
            ],
            "neighborhoods": {
                "New York, NY": [
                    "Williamsburg", "Lower East Side", "Astoria", "Brooklyn Heights",
                    "Chelsea", "Greenwich Village", "Upper West Side", "Harlem",
                    "Bushwick", "Long Island City", "DUMBO", "Park Slope"
                ],
                "Los Angeles, CA": [
                    "Silver Lake", "Echo Park", "Venice Beach", "Santa Monica",
                    "West Hollywood", "Downtown LA", "Hollywood", "Beverly Hills",
                    "Culver City", "Pasadena", "Glendale", "Burbank"
                ],
                "Chicago, IL": [
                    "Logan Square", "Wicker Park", "Lincoln Park", "The Loop",
                    "River North", "West Loop", "Bucktown", "Lakeview",
                    "Andersonville", "Pilsen", "Hyde Park", "Wrigleyville"
                ],
                "San Francisco, CA": [
                    "The Mission", "North Beach", "Hayes Valley", "Marina District",
                    "Pacific Heights", "Castro District", "Haight-Ashbury", "SOMA",
                    "Fisherman's Wharf", "Chinatown", "Japantown", "Nob Hill"
                ]
            },
            "venue_types": [
                "restaurant", "coffee shop", "bar", "gym", "park", "museum",
                "theater", "shopping mall", "grocery store", "pharmacy",
                "bank", "post office", "library", "school", "hospital",
                "gas station", "hotel", "airport", "train station", "bus stop"
            ],
            "venue_names": [
                "Central Park", "Times Square", "Empire State Building", "Statue of Liberty",
                "Golden Gate Bridge", "Alcatraz", "Fisherman's Wharf", "Pier 39",
                "Millennium Park", "Navy Pier", "Willis Tower", "Magnificent Mile",
                "Griffith Observatory", "Hollywood Walk of Fame", "Universal Studios",
                "Disneyland", "Venice Beach Boardwalk", "Santa Monica Pier",
                "Brooklyn Bridge", "High Line", "Chelsea Market", "Union Square"
            ],
            "travel_destinations": [
                "Tokyo, Japan", "Paris, France", "London, UK", "Barcelona, Spain",
                "Rome, Italy", "Amsterdam, Netherlands", "Berlin, Germany",
                "Prague, Czech Republic", "Vienna, Austria", "Budapest, Hungary",
                "Bangkok, Thailand", "Singapore", "Sydney, Australia", "Toronto, Canada",
                "Mexico City, Mexico", "Rio de Janeiro, Brazil", "Buenos Aires, Argentina",
                "Cape Town, South Africa", "Cairo, Egypt", "Dubai, UAE"
            ],
            "location_preferences": [
                "walkable neighborhoods", "public transportation access", "bike-friendly areas",
                "quiet residential areas", "vibrant nightlife districts", "family-friendly zones",
                "cultural districts", "shopping areas", "outdoor recreation spots",
                "foodie neighborhoods", "arts districts", "tech hubs", "university areas",
                "business districts", "tourist areas", "historic districts", "waterfront areas",
                "mountain views", "beach access", "park proximity"
            ],
            "activity_types": [
                "dining", "entertainment", "shopping", "fitness", "cultural",
                "outdoor recreation", "nightlife", "business", "education",
                "healthcare", "transportation", "residential", "tourist"
            ],
            "time_periods": [
                "morning", "afternoon", "evening", "night", "weekend", "weekday"
            ]
        }
    
    def _generate_mock_location_data(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive mock location data"""
        
        # Generate random location data
        home_city = random.choice(self.mock_data["cities"])
        work_city = random.choice(self.mock_data["cities"])
        current_city = random.choice([home_city, work_city] + random.sample(self.mock_data["cities"], 2))
        
        # Get neighborhoods for the cities
        home_neighborhood = random.choice(self.mock_data["neighborhoods"].get(home_city, ["Downtown"]))
        work_neighborhood = random.choice(self.mock_data["neighborhoods"].get(work_city, ["Business District"]))
        current_neighborhood = random.choice(self.mock_data["neighborhoods"].get(current_city, ["Downtown"]))
        
        # Generate travel history
        max_travel = min(8, len(self.mock_data["travel_destinations"]))
        travel_history = random.sample(self.mock_data["travel_destinations"], random.randint(3, max_travel))
        
        # Generate recent locations
        recent_locations = []
        for _ in range(random.randint(5, 15)):
            venue_type = random.choice(self.mock_data["venue_types"])
            venue_name = random.choice(self.mock_data["venue_names"])
            location = f"{venue_name}, {random.choice(self.mock_data['cities'])}"
            recent_locations.append({
                "venue_name": venue_name,
                "venue_type": venue_type,
                "location": location,
                "visited_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                "duration_minutes": random.randint(15, 240),
                "rating": round(random.uniform(3.0, 5.0), 1)
            })
        
        # Generate location preferences
        max_preferences = min(8, len(self.mock_data["location_preferences"]))
        max_cities = min(3, len(self.mock_data["cities"]))
        max_venues = min(6, len(self.mock_data["venue_types"]))
        max_activities = min(8, len(self.mock_data["activity_types"]))
        max_times = min(4, len(self.mock_data["time_periods"]))
        
        location_preferences = {
            "preferred_neighborhoods": random.sample(self.mock_data["location_preferences"], random.randint(3, max_preferences)),
            "avoided_areas": random.sample(self.mock_data["cities"], random.randint(1, max_cities)),
            "favorite_venue_types": random.sample(self.mock_data["venue_types"], random.randint(3, max_venues)),
            "preferred_activities": random.sample(self.mock_data["activity_types"], random.randint(4, max_activities)),
            "travel_frequency": random.choice(["frequent", "moderate", "occasional", "rare"]),
            "commute_preference": random.choice(["walking", "cycling", "public_transit", "driving", "rideshare"]),
            "radius_preference_km": random.randint(1, 50),
            "time_preferences": random.sample(self.mock_data["time_periods"], random.randint(2, max_times))
        }
        
        # Generate location patterns
        location_patterns = {
            "home_work_commute": {
                "from": f"{home_neighborhood}, {home_city}",
                "to": f"{work_neighborhood}, {work_city}",
                "average_duration_minutes": random.randint(15, 90),
                "preferred_route": random.choice(["fastest", "scenic", "public_transit", "bike_friendly"]),
                "frequency": "weekdays"
            },
            "weekend_routine": {
                "morning": random.choice(self.mock_data["venue_types"]),
                "afternoon": random.choice(self.mock_data["venue_types"]),
                "evening": random.choice(self.mock_data["venue_types"]),
                "preferred_neighborhoods": random.sample(self.mock_data["neighborhoods"].get(home_city, ["Downtown"]), min(2, len(self.mock_data["neighborhoods"].get(home_city, ["Downtown"]))))
            },
            "travel_patterns": {
                "domestic_trips_per_year": random.randint(2, 8),
                "international_trips_per_year": random.randint(1, 4),
                "preferred_destinations": random.sample(self.mock_data["travel_destinations"], min(3, len(self.mock_data["travel_destinations"]))),
                "average_trip_duration_days": random.randint(3, 14)
            }
        }
        
        # Build comprehensive location data
        location_data = {
            "user_id": user_id,
            "current_location": {
                "city": current_city,
                "neighborhood": current_neighborhood,
                "coordinates": {
                    "latitude": round(random.uniform(25.0, 49.0), 6),
                    "longitude": round(random.uniform(-125.0, -66.0), 6)
                },
                "accuracy_meters": random.randint(10, 1000),
                "last_updated": datetime.now().isoformat(),
                "venue_type": random.choice(self.mock_data["venue_types"]),
                "venue_name": random.choice(self.mock_data["venue_names"])
            },
            "home_location": {
                "city": home_city,
                "neighborhood": home_neighborhood,
                "coordinates": {
                    "latitude": round(random.uniform(25.0, 49.0), 6),
                    "longitude": round(random.uniform(-125.0, -66.0), 6)
                },
                "address": f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St'])}, {home_neighborhood}, {home_city}",
                "residence_type": random.choice(["apartment", "house", "condo", "townhouse"]),
                "years_lived": random.randint(1, 15)
            },
            "work_location": {
                "city": work_city,
                "neighborhood": work_neighborhood,
                "coordinates": {
                    "latitude": round(random.uniform(25.0, 49.0), 6),
                    "longitude": round(random.uniform(-125.0, -66.0), 6)
                },
                "company_name": f"{random.choice(['Tech', 'Global', 'Innovation', 'Digital', 'Creative'])} {random.choice(['Corp', 'Inc', 'Labs', 'Solutions', 'Group'])}",
                "office_type": random.choice(["headquarters", "branch", "co-working", "remote"]),
                "commute_days": random.randint(1, 5)
            },
            "travel_history": travel_history,
            "recent_locations": recent_locations,
            "location_preferences": location_preferences,
            "location_patterns": location_patterns,
            "location_insights": {
                "favorite_cities": random.sample(self.mock_data["cities"], min(3, len(self.mock_data["cities"]))),
                "most_visited_venue_type": random.choice(self.mock_data["venue_types"]),
                "average_daily_distance_km": round(random.uniform(5.0, 50.0), 1),
                "location_consistency_score": round(random.uniform(0.6, 0.95), 2),
                "exploration_tendency": random.choice(["high", "medium", "low"]),
                "routine_following_score": round(random.uniform(0.3, 0.9), 2)
            },
            "generated_at": datetime.now().isoformat(),
            "data_confidence": round(random.uniform(0.7, 0.95), 2)
        }
        
        return location_data
    
    async def get_location_data(self, user_id: str) -> Optional[LocationData]:
        """Fetch location data for a user - now generates comprehensive mock data"""
        try:
            self.logger.info("Generating mock location data", user_id=user_id)
            
            # Generate comprehensive mock location data
            location_data = self._generate_mock_location_data(user_id)
            
            # Create LocationData object
            location_obj = LocationData(
                user_id=location_data["user_id"],
                current_location=location_data["current_location"]["city"],
                home_location=location_data["home_location"]["city"],
                work_location=location_data["work_location"]["city"],
                travel_history=location_data["travel_history"],
                location_preferences=location_data["location_preferences"]
            )
            
            self.logger.info("Mock location data generated successfully", 
                           user_id=user_id, 
                           data_confidence=location_data["data_confidence"])
            
            return location_obj
            
        except Exception as e:
            self.logger.error("Failed to generate mock location data", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_current_location(self, user_id: str) -> Optional[str]:
        """Get user's current location - returns mock current location"""
        try:
            self.logger.info("Generating mock current location", user_id=user_id)
            
            location_data = self._generate_mock_location_data(user_id)
            current_location = location_data["current_location"]["city"]
            
            self.logger.info("Mock current location generated", user_id=user_id, location=current_location)
            
            return current_location
            
        except Exception as e:
            self.logger.error("Failed to generate mock current location", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_location_history(self, user_id: str) -> Optional[list]:
        """Get user's location history - returns mock location history"""
        try:
            self.logger.info("Generating mock location history", user_id=user_id)
            
            location_data = self._generate_mock_location_data(user_id)
            history = location_data["recent_locations"]
            
            self.logger.info("Mock location history generated", 
                           user_id=user_id, 
                           history_count=len(history))
            
            return history
            
        except Exception as e:
            self.logger.error("Failed to generate mock location history", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_location_insights(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get location insights and patterns"""
        try:
            self.logger.info("Generating mock location insights", user_id=user_id)
            
            location_data = self._generate_mock_location_data(user_id)
            insights = location_data["location_insights"]
            
            self.logger.info("Mock location insights generated", user_id=user_id)
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate mock location insights", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_location_patterns(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get location patterns and routines"""
        try:
            self.logger.info("Generating mock location patterns", user_id=user_id)
            
            location_data = self._generate_mock_location_data(user_id)
            patterns = location_data["location_patterns"]
            
            self.logger.info("Mock location patterns generated", user_id=user_id)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Failed to generate mock location patterns", 
                            user_id=user_id, error=str(e))
            return None
