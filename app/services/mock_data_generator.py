"""
Advanced Mock Data Generator Service

This module provides high-quality, realistic mock data generation for testing
and development with comprehensive data validation and consistency.
"""
import random
import uuid
import hashlib
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import faker
from faker import Faker
from app.core.logging import get_logger

logger = get_logger("mock_data_generator")

# Initialize Faker for realistic data generation
fake = faker.Faker()


class DataQuality(str, Enum):
    """Data quality levels"""
    BASIC = "basic"
    REALISTIC = "realistic"
    PREMIUM = "premium"


@dataclass
class MockDataConfig:
    """Configuration for mock data generation"""
    quality: DataQuality = DataQuality.REALISTIC
    locale: str = "en_US"
    seed: Optional[int] = None
    include_optional_fields: bool = True
    realistic_relationships: bool = True
    data_consistency: bool = True


class MockDataGenerator:
    """
    Advanced mock data generator with high-quality, realistic data generation.
    
    This class provides comprehensive mock data generation with:
    - Realistic data using Faker library
    - Data consistency and relationships
    - Configurable quality levels
    - Validation and error handling
    - Performance optimization
    """
    
    def __init__(self, config: Optional[MockDataConfig] = None):
        self.config = config or MockDataConfig()
        self.logger = logger
        
        # Set seed for reproducible data
        if self.config.seed:
            random.seed(self.config.seed)
            Faker.seed(self.config.seed)
        
        # Initialize data consistency tracking
        self._user_consistency: Dict[str, Dict[str, Any]] = {}
        self._location_consistency: Dict[str, Dict[str, Any]] = {}
        self._interaction_consistency: Dict[str, Dict[str, Any]] = {}
        
        # Common data templates
        self.cities = [
            "New York, NY", "Los Angeles, CA", "Chicago, IL", "San Francisco, CA",
            "Miami, FL", "Austin, TX", "Seattle, WA", "Denver, CO", "Boston, MA",
            "Portland, OR", "Nashville, TN", "Las Vegas, NV", "Phoenix, AZ",
            "Atlanta, GA", "Dallas, TX", "Houston, TX", "Philadelphia, PA",
            "Washington, DC", "San Diego, CA", "Orlando, FL", "Minneapolis, MN"
        ]
        
        self.venue_types = [
            "restaurant", "coffee shop", "bar", "gym", "park", "museum",
            "theater", "shopping mall", "grocery store", "pharmacy",
            "bank", "post office", "library", "school", "hospital"
        ]
        
        self.content_types = [
            "restaurant", "movie", "music", "book", "article", "video", "podcast",
            "event", "place", "product", "service", "game", "app", "website"
        ]
        
        self.interaction_types = [
            "view", "like", "share", "comment", "save", "bookmark", "click",
            "purchase", "download", "install", "subscribe", "follow", "rate"
        ]
        
        self.genres = {
            "movies": ["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance", "Thriller"],
            "music": ["Pop", "Rock", "Hip-Hop", "Jazz", "Classical", "Electronic", "Country"],
            "places": ["Restaurant", "Cafe", "Bar", "Museum", "Park", "Theater", "Shopping"],
            "events": ["Concert", "Festival", "Conference", "Workshop", "Exhibition", "Sports"]
        }
    
    def generate_user_profile_data(self, user_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive, realistic user profile data.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Realistic user profile data with consistent relationships
        """
        # Generate realistic personal information
        if self.config.quality == DataQuality.PREMIUM:
            name = fake.name()
            email = fake.email()
            phone = fake.phone_number()
        else:
            name = f"User-{user_id}"
            email = f"user{user_id}@example.com"
            phone = None
        
        # Generate age with realistic distribution
        age = self._generate_realistic_age()
        
        # Generate interests with realistic relationships
        interests = self._generate_realistic_interests(age)
        
        # Generate location with consistency
        location_data = self._generate_consistent_location(user_id)
        
        # Generate preferences based on age and interests
        preferences = self._generate_realistic_preferences(age, interests)
        
        profile_data = {
            "user_id": user_id,
            "name": name,
            "email": email,
            "age": age,
            "location": location_data["current_location"],
            "preferences": preferences,
            "interests": interests,
            "generated_at": datetime.now().isoformat(),
            "profile_completeness": self._calculate_profile_completeness(age, interests),
            "data_quality": self.config.quality.value
        }
        
        # Add optional fields based on quality level
        if self.config.include_optional_fields:
            profile_data.update({
                "phone": phone,
                "gender": random.choice(["male", "female", "non-binary", "prefer_not_to_say"]),
                "occupation": self._generate_occupation(age),
                "education_level": self._generate_education_level(age),
                "income_range": self._generate_income_range(age),
                "marital_status": self._generate_marital_status(age),
                "languages": self._generate_languages(),
                "timezone": fake.timezone(),
                "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat()
            })
        
        # Store for consistency tracking
        if self.config.data_consistency:
            self._user_consistency[user_id] = {
                "age": age,
                "interests": interests,
                "location": location_data,
                "preferences": preferences
            }
        
        return profile_data
    
    def generate_location_data(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive location data"""
        home_city = random.choice(self.cities)
        work_city = random.choice(self.cities)
        current_city = random.choice([home_city, work_city] + random.sample(self.cities, 2))
        
        return {
            "user_id": user_id,
            "current_location": current_city,
            "home_location": home_city,
            "work_location": work_city,
            "travel_history": random.sample(self.cities, random.randint(3, 8)),
            "location_preferences": {
                "preferred_neighborhoods": random.sample([
                    "downtown", "suburbs", "waterfront", "historic", "arts district"
                ], random.randint(2, 4)),
                "avoided_areas": random.sample(self.cities, random.randint(1, 3)),
                "favorite_venue_types": random.sample(self.venue_types, random.randint(3, 6)),
                "travel_frequency": random.choice(["frequent", "moderate", "occasional", "rare"])
            },
            "generated_at": datetime.now().isoformat(),
            "data_confidence": round(random.uniform(0.7, 0.95), 2)
        }
    
    def generate_interaction_data(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive interaction data"""
        recent_interactions = []
        for i in range(random.randint(15, 35)):
            content_type = random.choice(self.content_types)
            interaction_type = random.choice(self.interaction_types)
            hours_ago = random.randint(1, 168)
            timestamp = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
            
            recent_interactions.append({
                "id": f"interaction_{user_id}_{i}",
                "content_type": content_type,
                "interaction_type": interaction_type,
                "content_title": f"Sample {content_type.title()} {i+1}",
                "content_id": f"content_{random.randint(1000, 9999)}",
                "timestamp": timestamp,
                "engagement_score": round(random.uniform(0.1, 1.0), 2),
                "sentiment": random.choice(["positive", "negative", "neutral", "excited", "interested"])
            })
        
        engagement_score = round(random.uniform(0.2, 0.9), 2)
        
        return {
            "user_id": user_id,
            "recent_interactions": recent_interactions,
            "interaction_history": self._generate_interaction_history(user_id),
            "preferences": {
                "preferred_content_types": random.sample(self.content_types, random.randint(4, 8)),
                "preferred_interaction_types": random.sample(self.interaction_types, random.randint(4, 8)),
                "interaction_frequency": random.choice(["high", "medium", "low"]),
                "engagement_style": random.choice(["passive_consumer", "active_creator", "social_sharer"])
            },
            "engagement_score": engagement_score,
            "generated_at": datetime.now().isoformat(),
            "data_confidence": round(random.uniform(0.75, 0.98), 2)
        }
    
    def generate_recommendations_data(self, user_id: str, categories: List[str] = None) -> Dict[str, Any]:
        """Generate mock recommendations data"""
        if categories is None:
            categories = ["movies", "music", "places", "events"]
        
        recommendations = {}
        for category in categories:
            genre_list = self.genres.get(category, ["General"])
            items = []
            for i in range(random.randint(3, 8)):
                items.append({
                    "title": f"Sample {category.title().rstrip('s')} {i+1}",
                    "description": f"Great {category} option for your preferences",
                    "genre": random.choice(genre_list),
                    "rating": round(random.uniform(3.0, 5.0), 1),
                    "ranking_score": round(random.uniform(0.6, 0.95), 2),
                    "why_would_you_like_this": f"Based on your interests, this {category} matches your preferences"
                })
            recommendations[category] = items
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations,
            "metadata": {
                "total_recommendations": sum(len(items) for items in recommendations.values()),
                "categories": categories,
                "generated_at": datetime.now().isoformat(),
                "model": "mock-generator-v1.0"
            }
        }
    
    def _generate_preferences(self) -> Dict[str, Any]:
        """Generate user preferences with realistic structure"""
        return {
            "language": random.choice(["en", "es", "fr", "de"]),
            "theme": random.choice(["light", "dark", "auto"]),
            "notifications": random.choice([True, False]),
            "privacy_level": random.choice(["public", "friends", "private"]),
            "content_filters": random.sample(["explicit", "violence", "adult"], random.randint(0, 3))
        }
    
    def _generate_interaction_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate historical interaction data"""
        history = []
        for i in range(random.randint(50, 150)):
            days_ago = random.randint(1, 365)
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            history.append({
                "id": f"history_{user_id}_{i}",
                "content_type": random.choice(self.content_types),
                "interaction_type": random.choice(self.interaction_types),
                "content_title": f"Historical {random.choice(self.content_types).title()} {i+1}",
                "timestamp": timestamp,
                "engagement_score": round(random.uniform(0.1, 1.0), 2),
                "category": random.choice(["entertainment", "lifestyle", "news", "education"])
            })
        return history
    
    def _generate_realistic_age(self) -> int:
        """Generate age with realistic distribution"""
        # Weighted distribution: more users in 25-45 range
        age_weights = {
            (18, 24): 0.15,
            (25, 34): 0.35,
            (35, 44): 0.30,
            (45, 54): 0.15,
            (55, 65): 0.05
        }
        
        rand = random.random()
        cumulative = 0
        for (min_age, max_age), weight in age_weights.items():
            cumulative += weight
            if rand <= cumulative:
                return random.randint(min_age, max_age)
        
        return random.randint(25, 35)  # Fallback
    
    def _generate_realistic_interests(self, age: int) -> List[str]:
        """Generate interests based on age demographics"""
        all_interests = [
            "technology", "travel", "music", "movies", "sports", "cooking",
            "photography", "art", "fitness", "reading", "gaming", "fashion",
            "gardening", "dancing", "writing", "volunteering", "investing",
            "parenting", "career_development", "health_wellness"
        ]
        
        # Age-based interest preferences
        age_interests = {
            (18, 24): ["gaming", "music", "fashion", "technology", "fitness"],
            (25, 34): ["travel", "cooking", "fitness", "career_development", "investing"],
            (35, 44): ["parenting", "health_wellness", "cooking", "gardening", "volunteering"],
            (45, 54): ["gardening", "reading", "volunteering", "health_wellness", "travel"],
            (55, 65): ["reading", "gardening", "volunteering", "health_wellness", "art"]
        }
        
        # Get age-appropriate interests
        preferred_interests = []
        for age_range, interests in age_interests.items():
            if age_range[0] <= age <= age_range[1]:
                preferred_interests = interests
                break
        
        if not preferred_interests:
            preferred_interests = ["technology", "travel", "music", "fitness"]
        
        # Select 3-8 interests with preference for age-appropriate ones
        num_interests = random.randint(3, 8)
        selected_interests = []
        
        # Add preferred interests first
        for interest in preferred_interests:
            if len(selected_interests) < num_interests and interest not in selected_interests:
                selected_interests.append(interest)
        
        # Fill remaining slots with random interests
        remaining_interests = [i for i in all_interests if i not in selected_interests]
        while len(selected_interests) < num_interests and remaining_interests:
            interest = random.choice(remaining_interests)
            selected_interests.append(interest)
            remaining_interests.remove(interest)
        
        return selected_interests
    
    def _generate_consistent_location(self, user_id: str) -> Dict[str, Any]:
        """Generate location data with consistency"""
        if self.config.data_consistency and user_id in self._location_consistency:
            return self._location_consistency[user_id]
        
        # Generate realistic location data
        if self.config.quality == DataQuality.PREMIUM:
            home_city = fake.city() + ", " + fake.state_abbr()
            work_city = fake.city() + ", " + fake.state_abbr()
            current_city = random.choice([home_city, work_city, fake.city() + ", " + fake.state_abbr()])
        else:
            home_city = random.choice(self.cities)
            work_city = random.choice(self.cities)
            current_city = random.choice([home_city, work_city] + random.sample(self.cities, 2))
        
        location_data = {
            "current_location": current_city,
            "home_location": home_city,
            "work_location": work_city,
            "timezone": fake.timezone(),
            "country": fake.country(),
            "coordinates": {
                "lat": float(fake.latitude()),
                "lng": float(fake.longitude())
            }
        }
        
        if self.config.data_consistency:
            self._location_consistency[user_id] = location_data
        
        return location_data
    
    def _generate_realistic_preferences(self, age: int, interests: List[str]) -> Dict[str, Any]:
        """Generate preferences based on age and interests"""
        preferences = {
            "language": random.choice(["en", "es", "fr", "de", "zh", "ja"]),
            "theme": random.choice(["light", "dark", "auto"]),
            "notifications": random.choice([True, False]),
            "privacy_level": random.choice(["public", "friends", "private"]),
            "content_filters": random.sample(["explicit", "violence", "adult"], random.randint(0, 3)),
            "accessibility": {
                "high_contrast": random.choice([True, False]),
                "large_text": random.choice([True, False]),
                "screen_reader": random.choice([True, False])
            }
        }
        
        # Age-based preferences
        if age < 30:
            preferences.update({
                "social_sharing": True,
                "push_notifications": True,
                "location_tracking": True
            })
        elif age < 50:
            preferences.update({
                "social_sharing": random.choice([True, False]),
                "push_notifications": True,
                "location_tracking": random.choice([True, False])
            })
        else:
            preferences.update({
                "social_sharing": False,
                "push_notifications": False,
                "location_tracking": False
            })
        
        return preferences
    
    def _calculate_profile_completeness(self, age: int, interests: List[str]) -> float:
        """Calculate profile completeness score"""
        base_score = 0.5
        age_bonus = 0.1 if 18 <= age <= 65 else 0.0
        interests_bonus = min(len(interests) * 0.05, 0.3)
        return min(base_score + age_bonus + interests_bonus, 1.0)
    
    def _generate_occupation(self, age: int) -> str:
        """Generate occupation based on age"""
        occupations_by_age = {
            (18, 24): ["Student", "Intern", "Entry-level", "Freelancer"],
            (25, 34): ["Software Engineer", "Marketing Manager", "Consultant", "Designer"],
            (35, 44): ["Senior Manager", "Director", "Entrepreneur", "Specialist"],
            (45, 54): ["Executive", "Senior Director", "Principal", "Advisor"],
            (55, 65): ["Executive", "Consultant", "Advisor", "Retired"]
        }
        
        for age_range, occupations in occupations_by_age.items():
            if age_range[0] <= age <= age_range[1]:
                return random.choice(occupations)
        
        return "Professional"
    
    def _generate_education_level(self, age: int) -> str:
        """Generate education level based on age"""
        if age < 22:
            return random.choice(["High School", "Some College", "Associate's"])
        elif age < 30:
            return random.choice(["Bachelor's", "Master's", "Some Graduate"])
        else:
            return random.choice(["Bachelor's", "Master's", "Doctorate", "Professional"])
    
    def _generate_income_range(self, age: int) -> str:
        """Generate income range based on age"""
        income_ranges = {
            (18, 24): ["$20k-40k", "$40k-60k"],
            (25, 34): ["$40k-60k", "$60k-80k", "$80k-100k"],
            (35, 44): ["$60k-80k", "$80k-100k", "$100k-150k"],
            (45, 54): ["$80k-100k", "$100k-150k", "$150k+"],
            (55, 65): ["$100k-150k", "$150k+", "Retired"]
        }
        
        for age_range, ranges in income_ranges.items():
            if age_range[0] <= age <= age_range[1]:
                return random.choice(ranges)
        
        return "$60k-80k"
    
    def _generate_marital_status(self, age: int) -> str:
        """Generate marital status based on age"""
        if age < 25:
            return random.choice(["Single", "In a relationship"])
        elif age < 35:
            return random.choice(["Single", "In a relationship", "Married"])
        else:
            return random.choice(["Married", "Divorced", "Widowed", "Single"])
    
    def _generate_languages(self) -> List[str]:
        """Generate realistic language list"""
        languages = ["English"]
        additional_languages = ["Spanish", "French", "German", "Chinese", "Japanese", "Portuguese", "Italian"]
        
        if random.random() < 0.3:  # 30% chance of additional languages
            num_additional = random.randint(1, 2)
            languages.extend(random.sample(additional_languages, num_additional))
        
        return languages


# Global instance
mock_data_generator = MockDataGenerator()
