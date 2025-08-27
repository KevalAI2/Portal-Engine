"""
CIS (Content Interaction Service) with Enhanced Mock Data Generation
"""
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from services.base import BaseService
from models.schemas import InteractionData
from core.config import settings
from core.logging import get_logger


class CISService(BaseService):
    """CIS (Content Interaction Service) with comprehensive mock interaction data"""
    
    def __init__(self):
        super().__init__(settings.cis_service_url)
        self.logger = get_logger("cis_service")
        
        # Enhanced mock interaction data templates
        self.mock_data = {
            "content_types": [
                "restaurant", "movie", "music", "book", "article", "video", "podcast",
                "event", "place", "product", "service", "game", "app", "website",
                "social_media_post", "news", "review", "recommendation", "advertisement",
                "live_stream", "webinar", "course", "tutorial", "guide", "story", "blog"
            ],
            "interaction_types": [
                "view", "like", "share", "comment", "save", "bookmark", "click",
                "purchase", "download", "install", "subscribe", "follow", "rate",
                "review", "recommend", "search", "browse", "watch", "listen", "read",
                "react", "report", "block", "mute", "pin", "highlight", "annotate"
            ],
            "content_categories": [
                "food_dining", "entertainment", "travel", "fashion", "technology",
                "health_fitness", "education", "business", "lifestyle", "sports",
                "arts_culture", "news_politics", "science", "automotive", "real_estate",
                "finance", "parenting", "pets", "home_garden", "outdoor_adventure",
                "gaming", "music", "film", "literature", "photography", "cooking"
            ],
            "platforms": [
                "Instagram", "TikTok", "YouTube", "Twitter", "Facebook", "LinkedIn",
                "Pinterest", "Reddit", "Spotify", "Netflix", "Amazon", "Google",
                "Apple", "Uber", "Airbnb", "Yelp", "TripAdvisor", "OpenTable",
                "Eventbrite", "Meetup", "Discord", "Twitch", "Snapchat", "Tumblr",
                "Medium", "Quora", "Stack Overflow", "GitHub", "Behance", "Dribbble"
            ],
            "content_titles": [
                "Best Coffee Shops in NYC", "Hidden Gems in LA", "Top 10 Travel Destinations",
                "Amazing Restaurant Recommendations", "Must-Watch Movies This Year",
                "Trending Music Playlist", "Fitness Tips for Beginners", "Tech Gadgets Review",
                "Fashion Trends 2024", "Healthy Recipe Ideas", "Travel Photography Tips",
                "Local Event Guide", "Book Recommendations", "Podcast Episodes Worth Listening",
                "Art Gallery Exhibitions", "Concert Venues Guide", "Outdoor Adventure Spots",
                "Cultural Festivals", "Food Truck Locations", "Nightlife Hotspots",
                "Programming Tutorial for Beginners", "Design Principles Every Developer Should Know",
                "Startup Success Stories", "Investment Strategies for 2024", "Mental Health Tips",
                "Sustainable Living Guide", "Digital Marketing Trends", "AI and Machine Learning Basics"
            ],
            "user_actions": [
                "liked a post about", "shared content from", "commented on", "saved article about",
                "bookmarked page for", "clicked on ad for", "purchased item from", "downloaded app for",
                "subscribed to channel about", "followed account for", "rated service for",
                "reviewed place for", "recommended to friends", "searched for", "browsed category",
                "watched video about", "listened to podcast about", "read article about",
                "reacted to story about", "reported inappropriate content", "blocked user for",
                "muted notifications from", "pinned important post", "highlighted key information"
            ],
            "engagement_levels": [
                "high", "medium", "low", "passive", "active", "very_active", "inactive",
                "super_active", "minimal", "moderate", "engaged", "disengaged"
            ],
            "sentiment_types": [
                "positive", "negative", "neutral", "excited", "disappointed", "surprised",
                "interested", "bored", "confused", "satisfied", "frustrated", "curious",
                "amazed", "angry", "happy", "sad", "anxious", "relaxed", "motivated", "inspired"
            ],
            "time_periods": [
                "morning", "afternoon", "evening", "night", "weekend", "weekday", "lunch_break",
                "commute", "work_hours", "leisure_time", "bedtime", "early_morning",
                "late_night", "rush_hour", "quiet_hours", "peak_time", "off_peak"
            ],
            "device_types": [
                "mobile", "desktop", "tablet", "smart_tv", "smartwatch", "laptop",
                "gaming_console", "smart_speaker", "vr_headset", "ar_glasses"
            ],
            "interaction_contexts": [
                "social_recommendation", "advertisement", "search_result", "trending_content",
                "personalized_suggestion", "friend_activity", "brand_content", "influencer_post",
                "news_article", "entertainment_content", "educational_content", "promotional_offer",
                "algorithmic_feed", "curated_collection", "user_generated", "professional_content",
                "community_discussion", "expert_opinion", "user_review", "official_announcement"
            ],
            "content_qualities": [
                "high_quality", "medium_quality", "low_quality", "premium", "basic",
                "professional", "amateur", "expert", "beginner", "advanced"
            ],
            "interaction_intensities": [
                "light", "moderate", "heavy", "intense", "casual", "focused", "distracted"
            ]
        }
    
    def _generate_mock_interaction_data(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive mock interaction data"""
        
        # Generate recent interactions with more variety
        recent_interactions = []
        for i in range(random.randint(15, 35)):
            content_type = random.choice(self.mock_data["content_types"])
            interaction_type = random.choice(self.mock_data["interaction_types"])
            platform = random.choice(self.mock_data["platforms"])
            content_title = random.choice(self.mock_data["content_titles"])
            
            # Generate more realistic timestamps
            hours_ago = random.randint(1, 168)
            timestamp = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
            
            # Generate realistic engagement scores based on interaction type
            base_engagement = {
                "like": 0.8, "share": 0.9, "comment": 0.7, "save": 0.85,
                "purchase": 0.95, "subscribe": 0.9, "follow": 0.8,
                "view": 0.5, "click": 0.6, "browse": 0.4
            }.get(interaction_type, 0.6)
            
            engagement_score = round(base_engagement * random.uniform(0.8, 1.2), 2)
            engagement_score = min(1.0, max(0.1, engagement_score))
            
            interaction = {
                "id": f"interaction_{user_id}_{i}",
                "content_type": content_type,
                "interaction_type": interaction_type,
                "platform": platform,
                "content_title": content_title,
                "content_id": f"content_{random.randint(1000, 9999)}",
                "timestamp": timestamp,
                "duration_seconds": random.randint(5, 1800) if interaction_type in ["watch", "listen", "read"] else None,
                "engagement_score": engagement_score,
                "sentiment": random.choice(self.mock_data["sentiment_types"]),
                "device_type": random.choice(self.mock_data["device_types"]),
                "context": random.choice(self.mock_data["interaction_contexts"]),
                "content_quality": random.choice(self.mock_data["content_qualities"]),
                "interaction_intensity": random.choice(self.mock_data["interaction_intensities"]),
                "metadata": {
                    "category": random.choice(self.mock_data["content_categories"]),
                    "time_period": random.choice(self.mock_data["time_periods"]),
                    "location": random.choice(["home", "work", "commute", "outdoor", "restaurant", "gym", "cafe", "library"]),
                    "social_context": random.choice(["alone", "with_friends", "with_family", "with_colleagues", "in_group"]),
                    "network_quality": random.choice(["excellent", "good", "fair", "poor"]),
                    "battery_level": random.randint(10, 100),
                    "screen_time": random.randint(1, 120)
                }
            }
            recent_interactions.append(interaction)
        
        # Generate interaction history (longer term) with more realistic patterns
        interaction_history = []
        for i in range(random.randint(80, 200)):
            content_type = random.choice(self.mock_data["content_types"])
            interaction_type = random.choice(self.mock_data["interaction_types"])
            platform = random.choice(self.mock_data["platforms"])
            
            # Generate realistic historical timestamps
            days_ago = random.randint(1, 365)
            timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            history_item = {
                "id": f"history_{user_id}_{i}",
                "content_type": content_type,
                "interaction_type": interaction_type,
                "platform": platform,
                "content_title": random.choice(self.mock_data["content_titles"]),
                "content_id": f"content_{random.randint(1000, 9999)}",
                "timestamp": timestamp,
                "engagement_score": round(random.uniform(0.1, 1.0), 2),
                "sentiment": random.choice(self.mock_data["sentiment_types"]),
                "category": random.choice(self.mock_data["content_categories"]),
                "month": random.randint(1, 12),
                "year": random.randint(2020, 2024),
                "season": random.choice(["spring", "summer", "fall", "winter"]),
                "weekday": random.choice(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
            }
            interaction_history.append(history_item)
        
        # Generate enhanced interaction preferences
        max_content_types = min(10, len(self.mock_data["content_types"]))
        max_platforms = min(8, len(self.mock_data["platforms"]))
        max_categories = min(12, len(self.mock_data["content_categories"]))
        max_interaction_types = min(8, len(self.mock_data["interaction_types"]))
        max_time_periods = min(6, len(self.mock_data["time_periods"]))
        max_device_types = min(4, len(self.mock_data["device_types"]))
        max_avoided_content = min(4, len(self.mock_data["content_types"]))
        max_avoided_platforms = min(3, len(self.mock_data["platforms"]))
        
        interaction_preferences = {
            "preferred_content_types": random.sample(self.mock_data["content_types"], random.randint(4, max_content_types)),
            "preferred_platforms": random.sample(self.mock_data["platforms"], random.randint(4, max_platforms)),
            "preferred_categories": random.sample(self.mock_data["content_categories"], random.randint(5, max_categories)),
            "preferred_interaction_types": random.sample(self.mock_data["interaction_types"], random.randint(4, max_interaction_types)),
            "preferred_time_periods": random.sample(self.mock_data["time_periods"], random.randint(3, max_time_periods)),
            "preferred_device_types": random.sample(self.mock_data["device_types"], random.randint(2, max_device_types)),
            "avoided_content_types": random.sample(self.mock_data["content_types"], random.randint(1, max_avoided_content)),
            "avoided_platforms": random.sample(self.mock_data["platforms"], random.randint(1, max_avoided_platforms)),
            "interaction_frequency": random.choice(["high", "medium", "low", "very_high", "very_low"]),
            "engagement_style": random.choice(["passive_consumer", "active_creator", "social_sharer", "reviewer", "influencer", "curator", "critic"]),
            "content_discovery_methods": random.sample(["search", "recommendations", "social_feed", "trending", "following", "advertisements", "curated_lists", "algorithmic_suggestions"], random.randint(3, 5)),
            "content_quality_preference": random.choice(["high_quality", "mixed", "quantity_over_quality"]),
            "interaction_depth": random.choice(["surface", "moderate", "deep", "very_deep"])
        }
        
        # Generate enhanced engagement metrics
        engagement_metrics = {
            "daily_active_minutes": random.randint(45, 360),
            "weekly_interactions": random.randint(70, 250),
            "monthly_content_consumed": random.randint(150, 600),
            "engagement_rate": round(random.uniform(0.06, 0.30), 3),
            "retention_rate": round(random.uniform(0.35, 0.85), 2),
            "interaction_depth": random.choice(["surface", "moderate", "deep", "very_deep"]),
            "social_interaction_ratio": round(random.uniform(0.15, 0.70), 2),
            "content_creation_ratio": round(random.uniform(0.02, 0.25), 2),
            "platform_diversity": random.randint(4, 10),
            "session_duration_minutes": round(random.uniform(8, 60), 1),
            "bounce_rate": round(random.uniform(0.1, 0.5), 2),
            "return_visitor_rate": round(random.uniform(0.2, 0.8), 2),
            "content_completion_rate": round(random.uniform(0.3, 0.9), 2),
            "interaction_velocity": round(random.uniform(0.5, 3.0), 1)
        }
        
        # Generate enhanced interaction patterns
        interaction_patterns = {
            "daily_patterns": {
                "morning": random.choice(self.mock_data["content_types"]),
                "afternoon": random.choice(self.mock_data["content_types"]),
                "evening": random.choice(self.mock_data["content_types"]),
                "night": random.choice(self.mock_data["content_types"])
            },
            "weekly_patterns": {
                "weekdays": {
                    "primary_platform": random.choice(self.mock_data["platforms"]),
                    "primary_content_type": random.choice(self.mock_data["content_types"]),
                    "peak_hours": random.sample(["9-11", "12-14", "17-19", "20-22"], min(2, 4)),
                    "average_daily_interactions": random.randint(20, 50)
                },
                "weekends": {
                    "primary_platform": random.choice(self.mock_data["platforms"]),
                    "primary_content_type": random.choice(self.mock_data["content_types"]),
                    "peak_hours": random.sample(["10-12", "14-16", "18-20", "21-23"], min(2, 4)),
                    "average_daily_interactions": random.randint(30, 70)
                }
            },
            "seasonal_patterns": {
                "spring": random.choice(self.mock_data["content_categories"]),
                "summer": random.choice(self.mock_data["content_categories"]),
                "fall": random.choice(self.mock_data["content_categories"]),
                "winter": random.choice(self.mock_data["content_categories"])
            },
            "behavioral_patterns": {
                "session_frequency": random.choice(["multiple_daily", "daily", "every_few_days", "weekly"]),
                "session_length": random.choice(["short", "medium", "long", "very_long"]),
                "interaction_style": random.choice(["burst", "steady", "sporadic", "intensive"]),
                "platform_switching": random.choice(["frequent", "moderate", "rare", "never"])
            }
        }
        
        # Calculate enhanced engagement score
        recent_engagement_scores = [interaction["engagement_score"] for interaction in recent_interactions]
        avg_engagement = sum(recent_engagement_scores) / len(recent_engagement_scores) if recent_engagement_scores else 0.5
        
        # Add some variability based on user patterns
        engagement_multiplier = random.uniform(0.7, 1.3)
        engagement_score = round(avg_engagement * engagement_multiplier, 2)
        engagement_score = min(1.0, max(0.0, engagement_score))
        
        # Build comprehensive interaction data
        interaction_data = {
            "user_id": user_id,
            "recent_interactions": recent_interactions,
            "interaction_history": interaction_history,
            "interaction_preferences": interaction_preferences,
            "engagement_metrics": engagement_metrics,
            "interaction_patterns": interaction_patterns,
            "engagement_score": engagement_score,
            "interaction_insights": {
                "most_engaged_platform": random.choice(self.mock_data["platforms"]),
                "favorite_content_type": random.choice(self.mock_data["content_types"]),
                "peak_activity_hours": random.sample(["9-11", "12-14", "17-19", "20-22"], min(2, 4)),
                "interaction_trend": random.choice(["increasing", "stable", "decreasing", "fluctuating"]),
                "content_discovery_preference": random.choice(["algorithmic", "social", "search", "manual", "curated"]),
                "social_interaction_level": random.choice(["high", "medium", "low", "very_high", "very_low"]),
                "content_creation_frequency": random.choice(["daily", "weekly", "monthly", "rarely", "never"]),
                "platform_loyalty_score": round(random.uniform(0.3, 0.95), 2),
                "content_quality_preference": random.choice(["high", "medium", "low", "mixed"]),
                "interaction_velocity": round(random.uniform(0.5, 3.0), 1),
                "engagement_consistency": random.choice(["consistent", "variable", "sporadic", "intensive"]),
                "social_influence_score": round(random.uniform(0.1, 0.9), 2)
            },
            "generated_at": datetime.now().isoformat(),
            "data_confidence": round(random.uniform(0.75, 0.98), 2)
        }
        
        return interaction_data
    
    async def get_interaction_data(self, user_id: str) -> Optional[InteractionData]:
        """Fetch interaction data for a user - now generates comprehensive mock data"""
        try:
            self.logger.info("Generating mock interaction data", user_id=user_id)
            
            # Generate comprehensive mock interaction data
            interaction_data = self._generate_mock_interaction_data(user_id)
            
            # Create InteractionData object
            interaction_obj = InteractionData(
                user_id=interaction_data["user_id"],
                recent_interactions=interaction_data["recent_interactions"],
                interaction_history=interaction_data["interaction_history"],
                preferences=interaction_data["interaction_preferences"],
                engagement_score=interaction_data["engagement_score"]
            )
            
            self.logger.info("Mock interaction data generated successfully", 
                           user_id=user_id, 
                           engagement_score=interaction_data["engagement_score"],
                           data_confidence=interaction_data["data_confidence"])
            
            return interaction_obj
            
        except Exception as e:
            self.logger.error("Failed to generate mock interaction data", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_recent_interactions(self, user_id: str, limit: int = 10) -> Optional[list]:
        """Get user's recent interactions - returns mock recent interactions"""
        try:
            self.logger.info("Generating mock recent interactions", user_id=user_id, limit=limit)
            
            interaction_data = self._generate_mock_interaction_data(user_id)
            recent_interactions = interaction_data["recent_interactions"][:limit]
            
            self.logger.info("Mock recent interactions generated", 
                           user_id=user_id, 
                           interaction_count=len(recent_interactions))
            
            return recent_interactions
            
        except Exception as e:
            self.logger.error("Failed to generate mock recent interactions", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_engagement_score(self, user_id: str) -> Optional[float]:
        """Get user's engagement score - returns mock engagement score"""
        try:
            self.logger.info("Generating mock engagement score", user_id=user_id)
            
            interaction_data = self._generate_mock_interaction_data(user_id)
            engagement_score = interaction_data["engagement_score"]
            
            self.logger.info("Mock engagement score generated", 
                           user_id=user_id, 
                           engagement_score=engagement_score)
            
            return engagement_score
            
        except Exception as e:
            self.logger.error("Failed to generate mock engagement score", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_interaction_insights(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get interaction insights and patterns"""
        try:
            self.logger.info("Generating mock interaction insights", user_id=user_id)
            
            interaction_data = self._generate_mock_interaction_data(user_id)
            insights = interaction_data["interaction_insights"]
            
            self.logger.info("Mock interaction insights generated", user_id=user_id)
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate mock interaction insights", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_interaction_patterns(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get interaction patterns and behaviors"""
        try:
            self.logger.info("Generating mock interaction patterns", user_id=user_id)
            
            interaction_data = self._generate_mock_interaction_data(user_id)
            patterns = interaction_data["interaction_patterns"]
            
            self.logger.info("Mock interaction patterns generated", user_id=user_id)
            
            return patterns
            
        except Exception as e:
            self.logger.error("Failed to generate mock interaction patterns", 
                            user_id=user_id, error=str(e))
            return None
    
    async def get_engagement_metrics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed engagement metrics"""
        try:
            self.logger.info("Generating mock engagement metrics", user_id=user_id)
            
            interaction_data = self._generate_mock_interaction_data(user_id)
            metrics = interaction_data["engagement_metrics"]
            
            self.logger.info("Mock engagement metrics generated", user_id=user_id)
            
            return metrics
            
        except Exception as e:
            self.logger.error("Failed to generate mock engagement metrics", 
                            user_id=user_id, error=str(e))
            return None
