"""
User Profile Service with Mock Data Generation
"""
import random
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from services.base import BaseService
from models.schemas import UserProfile
from core.config import settings
from core.logging import get_logger


class UserProfileService(BaseService):
    """User Profile Service with comprehensive mock data generation"""
    
    def __init__(self):
        super().__init__(settings.user_profile_service_url)
        self.logger = get_logger("user_profile_service")
        
        # Mock data templates based on the provided schema
        self.mock_data = {
            "keywords": [
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
            "archetypes": [
                "adventurer", "nature-lover", "urban-culture", "cultural-explorer", "lifestyle",
                "photographer", "minimalist", "ocean-lover", "food-traveler", "fitness",
                "wellness", "animal-lover", "art-aficionado", "science-enthusiast", "family-oriented",
                "bohemian", "sunset-chaser", "work-motivated", "festival-goer", "fashion-enthusiast",
                "landscape-enthusiast", "luxury-lover", "teen", "young", "adult", "senior",
                "daytime", "nighttime", "sociable", "solitary"
            ],
            "demographics": [
                "34-year-old woman", "Asian-American", "Good health", "28-year-old man", "Hispanic",
                "Excellent health", "42-year-old woman", "Caucasian", "Fair health", "25-year-old man",
                "African-American", "Good health", "38-year-old woman", "Mixed race", "Excellent health"
            ],
            "home_locations": [
                "Brooklyn, NY", "Silver Lake, LA", "Logan Square, Chicago", "The Mission, SF",
                "Williamsburg, NY", "Echo Park, LA", "Wicker Park, Chicago", "North Beach, SF",
                "Astoria, NY", "Venice Beach, LA", "Lincoln Park, Chicago", "Hayes Valley, SF"
            ],
            "trips_taken": [
                "Tuscany", "New Orleans", "Tokyo", "Marseille", "London", "Barcelona", "Paris",
                "Amsterdam", "Berlin", "Prague", "Vienna", "Budapest", "Rome", "Florence",
                "Venice", "Milan", "Madrid", "Seville", "Lisbon", "Porto", "Dublin", "Edinburgh"
            ],
            "living_situations": [
                "Lives alone with a cat", "Married with 2 kids", "Lives with roommates",
                "Lives alone", "Married with 1 kid", "Lives with partner", "Lives with family",
                "Lives with dog", "Lives alone with plants", "Married with 3 kids"
            ],
            "professions": [
                "Teacher", "Product Manager", "Bartender", "Graphic Designer", "Software Engineer",
                "Marketing Manager", "Nurse", "Chef", "Architect", "Lawyer", "Doctor", "Artist",
                "Writer", "Photographer", "Musician", "Actor", "Consultant", "Sales Representative",
                "Accountant", "Designer", "Project Manager", "Data Scientist", "UX Designer"
            ],
            "education_levels": [
                "Postgrad degree", "In postgrad", "Undergrad degree", "in undergrad",
                "High school degree", "in high school", "Some college", "Associate degree"
            ],
            "cuisines": [
                "Italian", "Greek", "Brazilian", "Chinese", "Korean", "Thai", "Sushi", "Japanese",
                "French", "Spanish", "Ukrainian", "Mexican", "Indian", "Vietnamese", "Lebanese",
                "Turkish", "Moroccan", "Ethiopian", "Peruvian", "Argentine", "Cuban", "Puerto Rican"
            ],
            "music_genres": [
                "Hip hop", "Alt rock", "Indie pop", "Electronic", "Jazz", "Country", "Folk",
                "K-pop", "Punk", "Classical", "R&B", "Soul", "Blues", "Reggae", "Latin",
                "Pop", "Metal", "Rock", "EDM", "House", "Techno", "Dubstep", "Trap"
            ],
            "tv_movie_genres": [
                "Sci-fi", "Psychological thrillers", "Indie comedies", "Action", "Rom-coms",
                "Documentaries", "Anime", "Horror", "Drama", "Comedy", "Fantasy", "Mystery",
                "Crime", "Adventure", "Biography", "Historical", "War", "Western", "Musical"
            ],
            "fitness_levels": [
                "Active gym-goer", "Weekend hiker", "Casual walker", "Sedentary", "Marathon runner",
                "Yoga enthusiast", "CrossFit athlete", "Swimmer", "Cyclist", "Dancer"
            ],
            "travel_styles": [
                "Urban exploration", "Luxury relaxation", "Nature escapes", "Backpacking",
                "Road trips", "Cultural immersion", "Adventure travel", "Solo travel",
                "Group tours", "Business travel", "Family vacations", "Romantic getaways"
            ],
            "accommodation_preferences": [
                "Boutique hotels", "Airbnb apartments", "Eco-resorts", "Capsule hotels",
                "Luxury resorts", "Hostels", "Bed and breakfast", "Vacation rentals",
                "Glamping", "Traditional hotels", "All-inclusive resorts"
            ],
            "neighborhoods": [
                "Williamsburg NY", "Echo Park LA", "The Mission SF", "Wicker Park Chicago",
                "Lower East Side NY", "Silver Lake LA", "North Beach SF", "Lincoln Park Chicago",
                "Astoria NY", "Venice Beach LA", "Hayes Valley SF", "Logan Square Chicago"
            ],
            "outdoor_activities": [
                "Hiking trails", "Street festivals", "Farmers markets", "Rooftop bars",
                "Beaches", "City parks", "Rock climbing", "Cycling", "Running", "Swimming",
                "Kayaking", "Sailing", "Surfing", "Skiing", "Snowboarding", "Camping"
            ],
            "indoor_activities": [
                "Art galleries", "Escape rooms", "Arcade bars", "Live theater", "Jazz clubs",
                "Bowling alleys", "Museums", "Libraries", "Coffee shops", "Bookstores",
                "Gaming cafes", "Karaoke bars", "Comedy clubs", "Concert venues"
            ],
            "at_home_activities": [
                "Binge-watching TV", "Cooking new recipes", "Home workouts", "Reading",
                "Playing video games", "Meditation", "Yoga", "Gardening", "DIY projects",
                "Board games", "Puzzles", "Crafting", "Baking", "Painting", "Writing"
            ],
            "content_sources": [
                "TikTok", "Spotify", "Reddit", "Instagram", "YouTube", "Twitter", "Facebook",
                "LinkedIn", "Pinterest", "Snapchat", "Twitch", "Discord", "Telegram"
            ],
            "budget_preferences": [
                "$ (budget)", "$$ (casual)", "$$$ (upscale)", "$$$$ (luxury)"
            ],
            "vibe_preferences": [
                "Chill (coffee shops)", "Energetic (clubs)", "Trendy (art galleries)",
                "Cozy (bookstores)", "Luxurious (fine dining)", "Casual (food trucks)",
                "Romantic (candlelit dinners)", "Family-friendly (parks)", "Adventurous (outdoor activities)"
            ],
            "group_sizes": [
                "Solo outings", "Date night for two", "Group of 4 friends", "Family of 5",
                "Large group of 8+", "Couple activities", "Small group of 3"
            ],
            "moods": [
                "Happy", "Bored", "Anxious", "Curious", "Inspired", "Relaxed", "Energetic",
                "Tired", "Excited", "Stressed", "Peaceful", "Adventurous", "Creative"
            ],
            "energy_levels": [
                "Tired after work", "Morning energy boost", "Low energy midweek",
                "Weekend high energy", "Post-workout energy", "Caffeine-fueled",
                "Natural energy", "Restful energy", "Creative energy", "Social energy"
            ],
            "stress_levels": [
                "Work stress high", "Social burnout", "Relaxed weekend mood",
                "Low stress vacation", "Moderate daily stress", "High stress deadline",
                "Minimal stress", "Relationship stress", "Financial stress", "Health stress"
            ]
        }
    
    def _generate_mock_profile_data(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive mock user profile data based on the schema"""
        
        # Generate random selections from each category with safe sampling
        max_keywords = min(15, len(self.mock_data["keywords"]))
        max_archetypes = min(8, len(self.mock_data["archetypes"]))
        max_trips = min(8, len(self.mock_data["trips_taken"]))
        max_cuisines = min(8, len(self.mock_data["cuisines"]))
        max_music = min(10, len(self.mock_data["music_genres"]))
        max_tv = min(7, len(self.mock_data["tv_movie_genres"]))
        max_neighborhoods = min(5, len(self.mock_data["neighborhoods"]))
        max_outdoor = min(8, len(self.mock_data["outdoor_activities"]))
        max_indoor = min(7, len(self.mock_data["indoor_activities"]))
        max_athome = min(6, len(self.mock_data["at_home_activities"]))
        max_sources = min(6, len(self.mock_data["content_sources"]))
        
        keywords = random.sample(self.mock_data["keywords"], random.randint(5, max_keywords))
        archetypes = random.sample(self.mock_data["archetypes"], random.randint(3, max_archetypes))
        demographics = random.choice(self.mock_data["demographics"])
        home_location = random.choice(self.mock_data["home_locations"])
        trips = random.sample(self.mock_data["trips_taken"], random.randint(2, max_trips))
        living_situation = random.choice(self.mock_data["living_situations"])
        profession = random.choice(self.mock_data["professions"])
        education = random.choice(self.mock_data["education_levels"])
        cuisines = random.sample(self.mock_data["cuisines"], random.randint(3, max_cuisines))
        music_genres = random.sample(self.mock_data["music_genres"], random.randint(4, max_music))
        tv_genres = random.sample(self.mock_data["tv_movie_genres"], random.randint(3, max_tv))
        fitness_level = random.choice(self.mock_data["fitness_levels"])
        travel_style = random.choice(self.mock_data["travel_styles"])
        accommodation = random.choice(self.mock_data["accommodation_preferences"])
        neighborhoods = random.sample(self.mock_data["neighborhoods"], random.randint(2, max_neighborhoods))
        outdoor_activities = random.sample(self.mock_data["outdoor_activities"], random.randint(3, max_outdoor))
        indoor_activities = random.sample(self.mock_data["indoor_activities"], random.randint(3, max_indoor))
        at_home_activities = random.sample(self.mock_data["at_home_activities"], random.randint(3, max_athome))
        content_sources = random.sample(self.mock_data["content_sources"], random.randint(3, max_sources))
        budget = random.choice(self.mock_data["budget_preferences"])
        vibe = random.choice(self.mock_data["vibe_preferences"])
        group_size = random.choice(self.mock_data["group_sizes"])
        mood = random.choice(self.mock_data["moods"])
        energy = random.choice(self.mock_data["energy_levels"])
        stress = random.choice(self.mock_data["stress_levels"])
        
        # Generate confidence metrics (0.3 to 0.98)
        confidence_metrics = {
            "Keywords": round(random.uniform(0.6, 0.98), 5),
            "Archetypes": round(random.uniform(0.6, 0.96), 5),
            "Demographics": round(random.uniform(0.7, 0.9), 5),
            "Home Location": round(random.uniform(0.8, 0.95), 5),
            "Trips taken": round(random.uniform(0.8, 0.98), 5),
            "Living Situation": round(random.uniform(0.6, 0.8), 5),
            "Profession": round(random.uniform(0.4, 0.9), 5),
            "Education": round(random.uniform(0.5, 0.8), 5),
            "Dining preferences": round(random.uniform(0.8, 0.98), 5),
            "Music Genres": round(random.uniform(0.6, 0.8), 5),
            "TV/Movie Genres": round(random.uniform(0.6, 0.8), 5),
            "Fitness Level": round(random.uniform(0.6, 0.8), 5),
            "Travel Style": round(random.uniform(0.6, 0.8), 5),
            "Accommodation": round(random.uniform(0.6, 0.8), 5),
            "Neighborhoods": round(random.uniform(0.6, 0.8), 5),
            "Outdoor Activities": round(random.uniform(0.6, 0.8), 5),
            "Indoor Activities": round(random.uniform(0.6, 0.8), 5),
            "At-home Activities": round(random.uniform(0.6, 0.8), 5),
            "Content Sources": round(random.uniform(0.6, 0.8), 5),
            "Budget": round(random.uniform(0.6, 0.8), 5),
            "Vibe": round(random.uniform(0.6, 0.8), 5),
            "Group Size": round(random.uniform(0.6, 0.8), 5),
            "Mood": round(random.uniform(0.2, 0.9), 5),
            "Energy": round(random.uniform(0.2, 0.9), 5),
            "Stress": round(random.uniform(0.2, 0.9), 5)
        }
        
        # Generate recent searches and activities
        recent_searches = [
            f"Best {random.choice(['speakeasies', 'rooftop bars', 'coffee shops', 'restaurants'])} nearby",
            f"Outdoor {random.choice(['brunch', 'dinner', 'activities', 'events'])} {random.choice(['NYC', 'LA', 'Chicago', 'SF'])}",
            f"Indie {random.choice(['movie theaters', 'bookstores', 'art galleries', 'music venues'])} {random.choice(['NYC', 'LA', 'Chicago', 'SF'])}"
        ]
        
        recent_likes = [
            f"Saved \"Best {random.choice(['rooftop bars', 'hidden parks', 'local cafes', 'street art'])}\" guide",
            f"Favorited {random.choice(['Spotify playlist', 'Instagram post', 'TikTok video', 'YouTube channel'])}",
            f"Saved {random.choice(['TikTok', 'Instagram post', 'Pinterest board'])} about {random.choice(['hidden parks', 'local restaurants', 'travel tips', 'fitness routines'])}"
        ]
        
        recent_venues = [
            random.choice(['XYZ Coffee', 'ABC Music Hall', 'MNO Indie Cinema', "Joe's Pizza", 'The Local Bar', 'Art Gallery Cafe']),
            random.choice(['Downtown Restaurant', 'Central Park', 'Museum of Modern Art', 'Jazz Club', 'Comedy Cellar', 'Bowling Alley']),
            random.choice(['Rooftop Lounge', 'Beach Club', 'Mountain View Cafe', 'Urban Garden', 'Tech Hub', 'Creative Space'])
        ]
        
        recent_media = [
            f"Watched \"{random.choice(['The Bear', 'Succession', 'Ted Lasso', 'The Crown', 'Stranger Things'])}\" on {random.choice(['Hulu', 'Netflix', 'HBO Max', 'Disney+'])}",
            f"Listened to {random.choice(['Olivia Rodrigo', 'Taylor Swift', 'Drake', 'Beyoncé', 'The Weeknd'])} on Spotify",
            f"Binge-read {random.choice(['Reddit threads', 'Medium articles', 'Twitter threads', 'Blog posts'])}"
        ]
        
        # Build comprehensive profile
        profile_data = {
            "user_id": user_id,
            "name": f"User-{user_id}",
            "email": f"user{user_id}@example.com",
            "age": random.randint(18, 65),
            "location": home_location,
            "preferences": {
                "Keywords (legacy)": {
                    "category": "Long-term memory",
                    "example_values": [{"value": kw, "similarity_score": round(random.uniform(0.6, 0.95), 5)} for kw in keywords],
                    "confidence_metric": confidence_metrics["Keywords"]
                },
                "Archetypes (legacy)": {
                    "category": "Long-term memory",
                    "example_values": [{"value": arch, "similarity_score": round(random.uniform(0.6, 0.95), 5)} for arch in archetypes],
                    "confidence_metric": confidence_metrics["Archetypes"]
                },
                "Demographics": {
                    "category": "Long-term memory",
                    "example_values": [{"value": demographics, "similarity_score": round(random.uniform(0.7, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Demographics"]
                },
                "Home Location": {
                    "category": "Long-term memory",
                    "example_values": [{"value": home_location, "similarity_score": round(random.uniform(0.8, 0.95), 5)}],
                    "confidence_metric": confidence_metrics["Home Location"]
                },
                "Trips taken": {
                    "category": "Long-term memory",
                    "example_values": [{"value": trip, "similarity_score": round(random.uniform(0.8, 0.95), 5)} for trip in trips],
                    "confidence_metric": confidence_metrics["Trips taken"]
                },
                "Living Situation": {
                    "category": "Long-term memory",
                    "example_values": [{"value": living_situation, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Living Situation"]
                },
                "Profession": {
                    "category": "Long-term memory",
                    "example_values": [{"value": profession, "similarity_score": round(random.uniform(0.4, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Profession"]
                },
                "Education": {
                    "category": "Long-term memory",
                    "example_values": [{"value": education, "similarity_score": round(random.uniform(0.5, 0.8), 5)}],
                    "confidence_metric": confidence_metrics["Education"]
                },
                "Dining preferences (cuisine)": {
                    "category": "Long-term memory",
                    "example_values": [{"value": cuisine, "similarity_score": round(random.uniform(0.7, 0.95), 5)} for cuisine in cuisines],
                    "confidence_metric": confidence_metrics["Dining preferences"]
                },
                "Music Genres": {
                    "category": "Long-term memory",
                    "example_values": [{"value": genre, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for genre in music_genres],
                    "confidence_metric": confidence_metrics["Music Genres"]
                },
                "TV/Movie Genres": {
                    "category": "Long-term memory",
                    "example_values": [{"value": genre, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for genre in tv_genres],
                    "confidence_metric": confidence_metrics["TV/Movie Genres"]
                },
                "Fitness Level": {
                    "category": "Long-term memory",
                    "example_values": [{"value": fitness_level, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Fitness Level"]
                },
                "Travel Style": {
                    "category": "Long-term memory",
                    "example_values": [{"value": travel_style, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Travel Style"]
                },
                "Accommodation Preferences": {
                    "category": "Long-term memory",
                    "example_values": [{"value": accommodation, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Accommodation"]
                },
                "Favorite Neighborhoods": {
                    "category": "Long-term memory",
                    "example_values": [{"value": hood, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for hood in neighborhoods],
                    "confidence_metric": confidence_metrics["Neighborhoods"]
                },
                "Outdoor Activity Preferences": {
                    "category": "Long-term memory",
                    "example_values": [{"value": activity, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for activity in outdoor_activities],
                    "confidence_metric": confidence_metrics["Outdoor Activities"]
                },
                "Indoor Activity Preferences": {
                    "category": "Long-term memory",
                    "example_values": [{"value": activity, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for activity in indoor_activities],
                    "confidence_metric": confidence_metrics["Indoor Activities"]
                },
                "At-home Activity Preferences": {
                    "category": "Long-term memory",
                    "example_values": [{"value": activity, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for activity in at_home_activities],
                    "confidence_metric": confidence_metrics["At-home Activities"]
                },
                "Content Discovery Sources": {
                    "category": "Behavioral & preference patterns",
                    "example_values": [{"value": source, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for source in content_sources],
                    "confidence_metric": confidence_metrics["Content Sources"]
                },
                "Preferred Budget": {
                    "category": "Behavioral & preference patterns",
                    "example_values": [{"value": budget, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Budget"]
                },
                "Preferred Vibe": {
                    "category": "Behavioral & preference patterns",
                    "example_values": [{"value": vibe, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Vibe"]
                },
                "Typical Group Size": {
                    "category": "Behavioral & preference patterns",
                    "example_values": [{"value": group_size, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Group Size"]
                },
                "Recent Searches": {
                    "category": "Short-term memory",
                    "example_values": [{"value": search, "similarity_score": round(random.uniform(0.8, 0.95), 5)} for search in recent_searches],
                    "confidence_metric": 0.9
                },
                "Recent Content Likes": {
                    "category": "Short-term memory",
                    "example_values": [{"value": like, "similarity_score": round(random.uniform(0.8, 0.95), 5)} for like in recent_likes],
                    "confidence_metric": 0.9
                },
                "Recently Visited Venues": {
                    "category": "Short-term memory",
                    "example_values": [{"value": venue, "similarity_score": round(random.uniform(0.6, 0.9), 5)} for venue in recent_venues],
                    "confidence_metric": 0.9
                },
                "Recent Media Consumption": {
                    "category": "Short-term memory",
                    "example_values": [{"value": media, "similarity_score": round(random.uniform(0.8, 0.95), 5)} for media in recent_media],
                    "confidence_metric": 0.9
                },
                "User Mood": {
                    "category": "Short-term memory",
                    "example_values": [{"value": mood, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Mood"]
                },
                "User Energy": {
                    "category": "Short-term memory",
                    "example_values": [{"value": energy, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Energy"]
                },
                "User Stress": {
                    "category": "Short-term memory",
                    "example_values": [{"value": stress, "similarity_score": round(random.uniform(0.6, 0.9), 5)}],
                    "confidence_metric": confidence_metrics["Stress"]
                }
            },
            "interests": keywords + archetypes,
            "generated_at": datetime.now().isoformat(),
            "profile_completeness": round(random.uniform(0.7, 0.95), 2)
        }
        
        return profile_data
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Fetch user profile data - now generates comprehensive mock data"""
        try:
            self.logger.info("Generating mock user profile", user_id=user_id)
            
            # Generate comprehensive mock profile data
            profile_data = self._generate_mock_profile_data(user_id)
            
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
            
            self.logger.info("Mock user profile generated successfully", 
                           user_id=user_id, 
                           profile_completeness=profile_data["profile_completeness"])
            
            return user_profile
            
        except Exception as e:
            self.logger.error("Failed to generate mock user profile", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_user_preferences(self, user_id: str) -> Optional[dict]:
        """Fetch user preferences - returns comprehensive mock preferences"""
        try:
            self.logger.info("Generating mock user preferences", user_id=user_id)
            
            # Generate mock profile data and extract preferences
            profile_data = self._generate_mock_profile_data(user_id)
            
            self.logger.info("Mock user preferences generated successfully", user_id=user_id)
            
            return profile_data.get("preferences", {})
            
        except Exception as e:
            self.logger.error("Failed to generate mock user preferences", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_user_interests(self, user_id: str) -> Optional[List[str]]:
        """Fetch user interests - returns mock interests"""
        try:
            self.logger.info("Generating mock user interests", user_id=user_id)
            
            # Generate mock profile data and extract interests
            profile_data = self._generate_mock_profile_data(user_id)
            
            self.logger.info("Mock user interests generated successfully", 
                           user_id=user_id, 
                           interest_count=len(profile_data.get("interests", [])))
            
            return profile_data.get("interests", [])
            
        except Exception as e:
            self.logger.error("Failed to generate mock user interests", 
                            user_id=user_id, error=str(e))
            return None
