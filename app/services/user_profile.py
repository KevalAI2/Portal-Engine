"""
User Profile Service with Schema-Based Mock Data Generation
"""
import random
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.services.base import BaseService
from app.models.schemas import UserProfile
from app.core.config import settings
from app.core.logging import get_logger, log_exception


class UserProfileService(BaseService):
    """User Profile Service with schema-based mock data generation"""
    
    def __init__(self, timeout: int = 30):
        """Initializes the service with a timeout and logger."""
        self.timeout = timeout
        super().__init__(settings.user_profile_service_url)
        self.logger = get_logger("user_profile_service")
        
        # Schema-based mock data templates matching the provided JSON structure
        self.schema_data = {
            "Keywords (legacy)": [
                "cooking", "baking", "wine tasting", "beer brewing", "mixology", "dancing",
                "stamp collecting", "vintage items", "skiing", "hiking", "cycling", "rock climbing",
                "kayaking", "yoga", "running", "swimming", "weightlifting", "playing tennis",
                "golf", "martial arts", "skateboarding", "surfing", "climbing", "boxing",
                "sailing", "bungee jumping", "adventure sports", "attractions and travel",
                "urban", "spa", "museums", "outdoors", "beach", "roadside", "wildlife",
                "camping", "playground", "national parks", "historical sites", "cultural landmarks",
                "scenic routes", "safari parks", "zoos", "resorts", "buildings", "romantic date",
                "date night", "nightlife", "board games", "karaoke", "picnic", "barbecue",
                "movies", "electronic music", "games", "art", "tech", "concerts", "opera",
                "music festivals", "theater", "exhibitions", "robotics", "education", "workshops",
                "designer", "architecture", "photography", "meditation", "yoga retreats"
            ],
            "Archetypes (legacy)": [
                "adventurer", "nature-lover", "urban-culture", "cultural-explorer", "lifestyle",
                "photographer", "minimalist", "ocean-lover", "food-traveler", "fitness",
                "wellness", "animal-lover", "art-aficionado", "science-enthusiast", "family-oriented",
                "bohemian", "sunset-chaser", "work-motivated", "festival-goer", "fashion-enthusiast",
                "landscape-enthusiast", "luxury-lover", "teen", "young", "adult", "senior",
                "daytime", "nighttime", "sociable", "solitary"
            ],
            "Demographics": [
                "34-year-old woman", "Asian-American", "Good health", "28-year-old man", "Hispanic",
                "Excellent health", "42-year-old woman", "Caucasian", "Fair health", "25-year-old man",
                "African-American", "Good health", "38-year-old woman", "Mixed race", "Excellent health"
            ],
            "Home Location": [
                "Brooklyn", "NY", "Silver Lake", "LA", "Logan Square", "Chicago", "The Mission", "SF",
                "Williamsburg", "Echo Park", "Wicker Park", "North Beach", "Astoria", "Venice Beach",
                "Lincoln Park", "Hayes Valley"
            ],
            "Trips taken": [
                "Tuscany", "New Orleans", "Tokyo", "Marseille", "London", "Barcelona", "Paris",
                "Amsterdam", "Berlin", "Prague", "Vienna", "Budapest", "Rome", "Florence",
                "Venice", "Milan", "Madrid", "Seville", "Lisbon", "Porto", "Dublin", "Edinburgh"
            ],
            "Living Situation": [
                "Lives alone with a cat", "Married with 2 kids", "Lives with roommates",
                "Lives alone", "Married with 1 kid", "Lives with partner", "Lives with family",
                "Lives with dog", "Lives alone with plants", "Married with 3 kids"
            ],
            "Profession": [
                "Teacher", "Product Manager", "Bartender", "Graphic Designer", "Software Engineer",
                "Marketing Manager", "Nurse", "Chef", "Architect", "Lawyer", "Doctor", "Artist",
                "Writer", "Photographer", "Musician", "Actor", "Consultant", "Sales Representative",
                "Accountant", "Designer", "Project Manager", "Data Scientist", "UX Designer"
            ],
            "Education": [
                "Postgrad degree", "In postgrad", "Undergrad degree", "in undergrad",
                "High school degree", "in high school", "Some college", "Associate degree"
            ],
            "Dining preferences (cuisine)": [
                "Italian", "Greek", "Brazilian", "Chinese", "Korean", "Thai", "Sushi", "Japanese",
                "French", "Spanish", "Ukrainian", "Mexican", "Indian", "Vietnamese", "Lebanese",
                "Turkish", "Moroccan", "Ethiopian", "Peruvian", "Argentine", "Cuban", "Puerto Rican"
            ],
            "Music Genres": [
                "Hip hop", "Alt rock", "Indie pop", "Electronic", "Jazz", "Country", "Folk",
                "K-pop", "Punk", "Classical", "R&B", "Soul", "Blues", "Reggae", "Latin",
                "Pop", "Metal", "Rock", "EDM", "House", "Techno", "Dubstep", "Trap"
            ],
            "TV/Movie Genres": [
                "Sci-fi", "Psychological thrillers", "Indie comedies", "Action", "Rom-coms",
                "Documentaries", "Anime", "Horror", "Drama", "Comedy", "Fantasy", "Mystery",
                "Crime", "Adventure", "Biography", "Historical", "War", "Western", "Musical"
            ],
            "Fitness Level": [
                "Active gym-goer", "Weekend hiker", "Casual walker", "Sedentary", "Marathon runner",
                "Yoga enthusiast", "CrossFit athlete", "Swimmer", "Cyclist", "Dancer"
            ],
            "Travel Style": [
                "Urban exploration", "Luxury relaxation", "Nature escapes", "Backpacking",
                "Road trips", "Cultural immersion", "Adventure travel", "Solo travel",
                "Group tours", "Business travel", "Family vacations", "Romantic getaways"
            ],
            "Accommodation Preferences": [
                "Boutique hotels", "Airbnb apartments", "Eco-resorts", "Capsule hotels",
                "Luxury resorts", "Hostels", "Bed and breakfast", "Vacation rentals",
                "Glamping", "Traditional hotels", "All-inclusive resorts"
            ],
            "Favorite Neighborhoods": [
                "Williamsburg NY", "Echo Park LA", "The Mission SF", "Wicker Park Chicago",
                "Lower East Side NY", "Silver Lake LA", "North Beach SF", "Lincoln Park Chicago",
                "Astoria NY", "Venice Beach LA", "Hayes Valley SF", "Logan Square Chicago"
            ],
            "Outdoor Activity Preferences": [
                "Hiking trails", "Street festivals", "Farmers markets", "Rooftop bars",
                "Beaches", "City parks", "Rock climbing", "Cycling", "Running", "Swimming",
                "Kayaking", "Sailing", "Surfing", "Skiing", "Snowboarding", "Camping"
            ],
            "Indoor Activity Preferences": [
                "Art galleries", "Escape rooms", "Arcade bars", "Live theater", "Jazz clubs",
                "Bowling alleys", "Museums", "Libraries", "Coffee shops", "Bookstores",
                "Gaming cafes", "Karaoke bars", "Comedy clubs", "Concert venues"
            ],
            "At-home Activity Preferences": [
                "Binge-watching TV", "Cooking new recipes", "Home workouts", "Reading",
                "Playing video games", "Meditation", "Yoga", "Gardening", "DIY projects",
                "Board games", "Puzzles", "Crafting", "Baking", "Painting", "Writing"
            ],
            "Content Discovery Sources": [
                "TikTok", "Spotify", "Reddit", "Instagram", "YouTube", "Twitter", "Facebook",
                "LinkedIn", "Pinterest", "Snapchat", "Twitch", "Discord", "Telegram"
            ],
            "Preferred Budget": [
                "$ (budget)", "$$ (casual)", "$$$ (upscale)", "$$$$ (luxury)"
            ],
            "Preferred Vibe": [
                "Chill (coffee shops)", "Energetic (clubs)", "Trendy (art galleries)",
                "Cozy (bookstores)", "Luxurious (fine dining)", "Casual (food trucks)",
                "Romantic (candlelit dinners)", "Family-friendly (parks)", "Adventurous (outdoor activities)"
            ],
            "Typical Group Size": [
                "Solo outings", "Date night for two", "Group of 4 friends", "Family of 5",
                "Large group of 8+", "Couple activities", "Small group of 3"
            ],
            "Recent Searches": [
                "\"Best speakeasies nearby\"", "\"Outdoor brunch NYC\"", "\"Indie movie theaters LA\"",
                "\"Hidden coffee shops\"", "\"Rooftop bars downtown\"", "\"Local art galleries\"",
                "\"Live music venues\"", "\"Farmers markets near me\"", "\"Hiking trails weekend\""
            ],
            "Recent Content Likes": [
                "Saved \"Best rooftop bars\" guide", "Favorited Spotify playlist", "Saved TikTok about hidden parks",
                "Liked Instagram post about local restaurants", "Bookmarked Pinterest board", "Shared YouTube video"
            ],
            "Recently Visited Venues": [
                "XYZ Coffee", "ABC Music Hall", "MNO Indie Cinema", "Joe's Pizza", "The Local Bar", "Art Gallery Cafe",
                "Downtown Restaurant", "Central Park", "Museum of Modern Art", "Jazz Club", "Comedy Cellar"
            ],
            "Recent Media Consumption": [
                "Watched \"The Bear\" on Hulu", "Listened to Olivia Rodrigo on Spotify", "Binge-read Reddit threads",
                "Watched \"Succession\" on HBO", "Listened to Taylor Swift on Apple Music", "Read Medium articles"
            ],
            "User Mood": [
                "Happy", "Bored", "Anxious", "Curious", "Inspired", "Relaxed", "Energetic",
                "Tired", "Excited", "Stressed", "Peaceful", "Adventurous", "Creative"
            ],
            "User Energy": [
                "Tired after work", "Morning energy boost", "Low energy midweek",
                "Weekend high energy", "Post-workout energy", "Caffeine-fueled",
                "Natural energy", "Restful energy", "Creative energy", "Social energy"
            ],
            "User Stress": [
                "Work stress high", "Social burnout", "Relaxed weekend mood",
                "Low stress vacation", "Moderate daily stress", "High stress deadline",
                "Minimal stress", "Relationship stress", "Financial stress", "Health stress"
            ]
        }
        
        # Confidence metrics matching the schema
        self.confidence_metrics = {
            "Keywords (legacy)": 0.97543,
            "Archetypes (legacy)": 0.95413,
            "Demographics": 0.75819,
            "Home Location": 0.93107,
            "Trips taken": 0.95887,
            "Living Situation": 0.64913,
            "Profession": 0.39493,
            "Education": 0.58732,
            "Dining preferences (cuisine)": 0.96328,
            "Music Genres": 0.60027,
            "TV/Movie Genres": 0.60056,
            "Fitness Level": 0.60015,
            "Travel Style": 0.60077,
            "Accommodation Preferences": 0.60008,
            "Favorite Neighborhoods": 0.60012,
            "Outdoor Activity Preferences": 0.60093,
            "Indoor Activity Preferences": 0.60042,
            "At-home Activity Preferences": 0.60018,
            "Content Discovery Sources": 0.6,
            "Preferred Budget": 0.6,
            "Preferred Vibe": 0.6,
            "Typical Group Size": 0.6,
            "Recent Searches": 0.9,
            "Recent Content Likes": 0.9,
            "Recently Visited Venues": 0.9,
            "Recent Media Consumption": 0.9,
            "User Mood": 0.25497,
            "User Energy": 0.25716,
            "User Stress": 0.25741
        }
    
    def _generate_schema_based_profile(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive mock user profile data based on the exact schema structure"""
        
        profile_data = {
            "user_id": user_id,
            "name": f"User-{user_id}",
            "email": f"user{user_id}@example.com",
            "age": random.randint(18, 65),
            "location": random.choice(self.schema_data["Home Location"]),
            "preferences": {}
        }
        
        # Generate each category following the exact schema structure
        for category, values in self.schema_data.items():
            # Determine number of items to select based on category
            if category in ["Keywords (legacy)", "Archetypes (legacy)", "Dining preferences (cuisine)", "Music Genres", "TV/Movie Genres"]:
                num_items = random.randint(8, min(15, len(values)))
            elif category in ["Trips taken", "Favorite Neighborhoods", "Outdoor Activity Preferences", "Indoor Activity Preferences", "At-home Activity Preferences"]:
                num_items = random.randint(4, min(8, len(values)))
            elif category in ["Recent Searches", "Recent Content Likes", "Recently Visited Venues", "Recent Media Consumption"]:
                num_items = random.randint(2, min(4, len(values)))
            else:
                num_items = random.randint(1, min(3, len(values)))
            
            # Select random items
            selected_values = random.sample(values, num_items)
            
            # Generate example_values with similarity scores
            example_values = []
            for value in selected_values:
                # Generate realistic similarity scores based on category
                if category in ["Keywords (legacy)", "Archetypes (legacy)"]:
                    similarity_score = round(random.uniform(0.6, 0.95), 5)
                elif category in ["Demographics", "Home Location", "Trips taken"]:
                    similarity_score = round(random.uniform(0.7, 0.95), 5)
                elif category in ["Recent Searches", "Recent Content Likes", "Recent Media Consumption"]:
                    similarity_score = round(random.uniform(0.8, 0.95), 5)
                elif category in ["User Mood", "User Energy", "User Stress"]:
                    similarity_score = round(random.uniform(0.6, 0.9), 5)
                else:
                    similarity_score = round(random.uniform(0.6, 0.9), 5)
                
                example_values.append({
                    "value": value,
                    "similarity_score": similarity_score
                })
            
            # Determine category type
            if category in ["Keywords (legacy)", "Archetypes (legacy)", "Demographics", "Home Location", "Trips taken", 
                          "Living Situation", "Profession", "Education", "Dining preferences (cuisine)", "Music Genres", 
                          "TV/Movie Genres", "Fitness Level", "Travel Style", "Accommodation Preferences", 
                          "Favorite Neighborhoods", "Outdoor Activity Preferences", "Indoor Activity Preferences", 
                          "At-home Activity Preferences"]:
                category_type = "Long-term memory"
            elif category in ["Recent Searches", "Recent Content Likes", "Recently Visited Venues", "Recent Media Consumption",
                            "User Mood", "User Energy", "User Stress"]:
                category_type = "Short-term memory"
            else:
                category_type = "Behavioral & preference patterns"
            
            # Build the category data
            profile_data["preferences"][category] = {
                "category": category_type,
                "example_values": example_values,
                "confidence_metric": self.confidence_metrics.get(category, round(random.uniform(0.6, 0.9), 5))
            }
        
        # Add additional profile fields
        profile_data.update({
            "interests": [item["value"] for category in profile_data["preferences"].values() 
                         for item in category["example_values"][:3]],  # Take first 3 from each category
            "generated_at": datetime.now().isoformat(),
            "profile_completeness": round(random.uniform(0.7, 0.95), 2)
        })
        
        return profile_data
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Fetch user profile data - generates schema-based mock data"""
        try:
            self.logger.info("Generating schema-based mock user profile", 
                           user_id=user_id,
                           service="user_profile",
                           operation="generate_profile")
            
            # Generate comprehensive mock profile data
            profile_data = self._generate_schema_based_profile(user_id)
            
            # Create UserProfile object with the generated data
            user_profile = UserProfile(
                user_id=profile_data["user_id"],
                name=profile_data["name"],
                email=profile_data["email"],
                preferences=profile_data["preferences"],
                interests=profile_data["interests"],
                age=profile_data["age"],
                location=profile_data["location"]
            )
            
            self.logger.info("Schema-based mock user profile generated successfully", 
                           user_id=user_id, 
                           profile_completeness=profile_data["profile_completeness"],
                           interests_count=len(profile_data["interests"]),
                           preferences_count=len(profile_data["preferences"]),
                           service="user_profile",
                           operation="generate_profile")
            
            return user_profile
            
        except Exception as e:
            self.logger.error("Failed to generate schema-based mock user profile", 
                            user_id=user_id, 
                            error=str(e),
                            service="user_profile",
                            operation="generate_profile")
            log_exception("user_profile_service", e, {"user_id": user_id, "operation": "generate_profile"})
            return None
    

