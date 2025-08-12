from sqlalchemy.orm import Session
from app.logic.user_profile import get_user_profile, get_profile_insights
from app.schema.user_profile import ProfileRecommendationRequest, ProfileRecommendationResponse
from typing import List, Dict, Any, Optional
import random
from datetime import datetime


class ProfileRecommendationEngine:
    """Engine for generating personalized recommendations based on user profiles"""
    
    def __init__(self):
        # Sample recommendation data - in production, this would come from external APIs
        self.restaurants = [
            {"name": "Sakura Sushi", "cuisine": "Japanese", "price_range": "$$", "vibe": "quiet", "location": "Downtown"},
            {"name": "La Trattoria", "cuisine": "Italian", "price_range": "$$", "vibe": "romantic", "location": "Midtown"},
            {"name": "Spice Garden", "cuisine": "Thai", "price_range": "$", "vibe": "trendy", "location": "East Side"},
            {"name": "Ocean View Grill", "cuisine": "Seafood", "price_range": "$$$", "vibe": "luxury", "location": "Waterfront"},
            {"name": "Urban Brew", "cuisine": "American", "price_range": "$", "vibe": "chill", "location": "Downtown"},
            {"name": "Zen Garden", "cuisine": "Japanese", "price_range": "$$$", "vibe": "quiet", "location": "Uptown"},
            {"name": "Taco Fiesta", "cuisine": "Mexican", "price_range": "$", "vibe": "high-energy", "location": "West Side"},
            {"name": "Le Petit Bistro", "cuisine": "French", "price_range": "$$$", "vibe": "romantic", "location": "Historic District"},
        ]
        
        self.activities = [
            {"name": "Yoga in the Park", "type": "outdoor", "category": "wellness", "price": "$", "duration": "1 hour"},
            {"name": "Art Gallery Tour", "type": "indoor", "category": "cultural", "price": "$$", "duration": "2 hours"},
            {"name": "Hiking Trail", "type": "outdoor", "category": "adventure", "price": "$", "duration": "3 hours"},
            {"name": "Jazz Club Night", "type": "indoor", "category": "entertainment", "price": "$$", "duration": "2 hours"},
            {"name": "Cooking Class", "type": "indoor", "category": "educational", "price": "$$$", "duration": "3 hours"},
            {"name": "Beach Day", "type": "outdoor", "category": "relaxation", "price": "$", "duration": "4 hours"},
            {"name": "Museum Visit", "type": "indoor", "category": "cultural", "price": "$$", "duration": "2 hours"},
            {"name": "Rock Climbing", "type": "outdoor", "category": "adventure", "price": "$$", "duration": "2 hours"},
        ]
        
        self.accommodations = [
            {"name": "Boutique Hotel Downtown", "type": "boutique", "price_range": "$$$", "amenities": ["spa", "restaurant"]},
            {"name": "Eco Resort", "type": "eco-resort", "price_range": "$$$", "amenities": ["nature", "sustainability"]},
            {"name": "Urban Airbnb", "type": "apartment", "price_range": "$$", "amenities": ["kitchen", "local"]},
            {"name": "Luxury Hotel", "type": "luxury", "price_range": "$$$$", "amenities": ["concierge", "pool", "spa"]},
            {"name": "Capsule Hotel", "type": "capsule", "price_range": "$", "amenities": ["minimal", "efficient"]},
        ]

    def generate_recommendations(self, db: Session, request: ProfileRecommendationRequest) -> ProfileRecommendationResponse:
        """Generate personalized recommendations based on user profile"""
        profile = get_user_profile(db, request.user_id)
        if not profile:
            return ProfileRecommendationResponse(
                recommendations=[],
                reasoning="No user profile found",
                confidence_score=0.0,
                profile_insights={}
            )
        
        insights = get_profile_insights(db, request.user_id)
        
        # Generate different types of recommendations
        restaurant_recs = self._recommend_restaurants(profile, insights)
        activity_recs = self._recommend_activities(profile, insights)
        accommodation_recs = self._recommend_accommodations(profile, insights)
        
        # Combine and rank recommendations
        all_recommendations = restaurant_recs + activity_recs + accommodation_recs
        ranked_recommendations = self._rank_recommendations(all_recommendations, profile, insights)
        
        # Limit results
        final_recommendations = ranked_recommendations[:request.limit]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(profile, insights, final_recommendations)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(profile, insights)
        
        return ProfileRecommendationResponse(
            recommendations=final_recommendations,
            reasoning=reasoning,
            confidence_score=confidence_score,
            profile_insights=insights
        )

    def _recommend_restaurants(self, profile, insights) -> List[Dict[str, Any]]:
        """Recommend restaurants based on dining preferences"""
        recommendations = []
        
        # Get user's cuisine preferences
        cuisine_preferences = []
        if profile.dining_preferences_cuisine:
            cuisine_preferences = [p.get('value', '').lower() for p in profile.dining_preferences_cuisine]
        
        # Get user's vibe preferences
        vibe_preferences = []
        if profile.dining_preferences_other:
            vibe_preferences = [p.get('value', '').lower() for p in profile.dining_preferences_other]
        
        # Get user's budget
        user_budget = profile.preferred_budget or "$$"
        
        for restaurant in self.restaurants:
            score = 0.0
            reasoning = []
            
            # Score based on cuisine preference
            if restaurant['cuisine'].lower() in cuisine_preferences:
                score += 0.4
                reasoning.append(f"Matches your preference for {restaurant['cuisine']} cuisine")
            
            # Score based on vibe preference
            if restaurant['vibe'].lower() in vibe_preferences:
                score += 0.3
                reasoning.append(f"Matches your preferred {restaurant['vibe']} atmosphere")
            
            # Score based on budget
            if restaurant['price_range'] == user_budget:
                score += 0.2
                reasoning.append("Matches your budget preference")
            elif restaurant['price_range'] in ["$", "$$"] and user_budget in ["$", "$$"]:
                score += 0.1
                reasoning.append("Within your budget range")
            
            # Add some randomness for variety
            score += random.uniform(0, 0.1)
            
            if score > 0.2:  # Only include if there's some relevance
                recommendations.append({
                    "type": "restaurant",
                    "name": restaurant['name'],
                    "details": restaurant,
                    "score": score,
                    "reasoning": reasoning
                })
        
        return recommendations

    def _recommend_activities(self, profile, insights) -> List[Dict[str, Any]]:
        """Recommend activities based on activity preferences"""
        recommendations = []
        
        # Get user's activity preferences
        outdoor_preferences = []
        indoor_preferences = []
        
        if profile.outdoor_activity_preferences:
            outdoor_preferences = [p.get('value', '').lower() for p in profile.outdoor_activity_preferences]
        if profile.indoor_activity_preferences:
            indoor_preferences = [p.get('value', '').lower() for p in profile.indoor_activity_preferences]
        
        # Get user's archetype for additional context
        archetype = insights.get('primary_archetype', '').lower()
        
        for activity in self.activities:
            score = 0.0
            reasoning = []
            
            # Score based on indoor/outdoor preference
            if activity['type'] == 'outdoor' and any(pref in activity['name'].lower() for pref in outdoor_preferences):
                score += 0.4
                reasoning.append("Matches your outdoor activity preferences")
            elif activity['type'] == 'indoor' and any(pref in activity['name'].lower() for pref in indoor_preferences):
                score += 0.4
                reasoning.append("Matches your indoor activity preferences")
            
            # Score based on archetype
            if 'wellness' in archetype and activity['category'] == 'wellness':
                score += 0.3
                reasoning.append("Aligns with your wellness-focused lifestyle")
            elif 'adventure' in archetype and activity['category'] == 'adventure':
                score += 0.3
                reasoning.append("Perfect for your adventurous spirit")
            elif 'cultural' in archetype and activity['category'] == 'cultural':
                score += 0.3
                reasoning.append("Matches your cultural interests")
            
            # Add some randomness for variety
            score += random.uniform(0, 0.1)
            
            if score > 0.2:
                recommendations.append({
                    "type": "activity",
                    "name": activity['name'],
                    "details": activity,
                    "score": score,
                    "reasoning": reasoning
                })
        
        return recommendations

    def _recommend_accommodations(self, profile, insights) -> List[Dict[str, Any]]:
        """Recommend accommodations based on travel style and preferences"""
        recommendations = []
        
        # Get user's accommodation preferences
        accommodation_preferences = []
        if profile.accommodation_preferences:
            accommodation_preferences = [p.get('value', '').lower() for p in profile.accommodation_preferences]
        
        # Get user's travel style
        travel_style = insights.get('travel_style', '').lower()
        
        # Get user's budget
        user_budget = profile.preferred_budget or "$$"
        
        for accommodation in self.accommodations:
            score = 0.0
            reasoning = []
            
            # Score based on accommodation type preference
            if accommodation['type'].lower() in accommodation_preferences:
                score += 0.4
                reasoning.append(f"Matches your preference for {accommodation['type']} accommodations")
            
            # Score based on travel style
            if 'luxury' in travel_style and accommodation['type'] == 'luxury':
                score += 0.3
                reasoning.append("Perfect for your luxury travel style")
            elif 'backpacking' in travel_style and accommodation['type'] == 'capsule':
                score += 0.3
                reasoning.append("Ideal for your backpacking style")
            elif 'eco' in travel_style and accommodation['type'] == 'eco-resort':
                score += 0.3
                reasoning.append("Aligns with your eco-conscious travel preferences")
            
            # Score based on budget
            if accommodation['price_range'] == user_budget:
                score += 0.2
                reasoning.append("Matches your budget preference")
            
            # Add some randomness for variety
            score += random.uniform(0, 0.1)
            
            if score > 0.2:
                recommendations.append({
                    "type": "accommodation",
                    "name": accommodation['name'],
                    "details": accommodation,
                    "score": score,
                    "reasoning": reasoning
                })
        
        return recommendations

    def _rank_recommendations(self, recommendations: List[Dict[str, Any]], profile, insights) -> List[Dict[str, Any]]:
        """Rank recommendations by relevance score"""
        # Sort by score in descending order
        ranked = sorted(recommendations, key=lambda x: x['score'], reverse=True)
        
        # Add ranking metadata
        for i, rec in enumerate(ranked):
            rec['rank'] = i + 1
            rec['confidence'] = min(rec['score'] * 2, 1.0)  # Convert score to confidence
        
        return ranked

    def _generate_reasoning(self, profile, insights, recommendations) -> str:
        """Generate human-readable reasoning for recommendations"""
        if not recommendations:
            return "No recommendations available based on current profile data."
        
        reasoning_parts = []
        
        # Add archetype-based reasoning
        archetype = insights.get('primary_archetype')
        if archetype:
            reasoning_parts.append(f"Based on your {archetype} profile")
        
        # Add travel style reasoning
        travel_style = insights.get('travel_style')
        if travel_style:
            reasoning_parts.append(f"and {travel_style} travel preferences")
        
        # Add budget reasoning
        budget = insights.get('budget_preference')
        if budget:
            reasoning_parts.append(f"within your {budget} budget range")
        
        # Add activity preferences
        activities = insights.get('top_activity_preferences', [])
        if activities:
            reasoning_parts.append(f"considering your interest in {', '.join(activities[:2])}")
        
        # Add dining preferences
        dining = insights.get('top_dining_preferences', [])
        if dining:
            reasoning_parts.append(f"and your taste for {', '.join(dining[:2])} cuisine")
        
        reasoning = " ".join(reasoning_parts) + "."
        
        # Add confidence note
        confidence = insights.get('confidence_scores', {})
        if confidence:
            avg_confidence = sum(confidence.values()) / len(confidence.values())
            if avg_confidence < 0.3:
                reasoning += " (Note: Limited profile data available - consider adding more preferences for better recommendations)"
        
        return reasoning

    def _calculate_confidence(self, profile, insights) -> float:
        """Calculate overall confidence score for recommendations"""
        confidence_scores = insights.get('confidence_scores', {})
        
        if not confidence_scores:
            return 0.1
        
        # Calculate weighted average
        weights = {
            'archetypes': 0.3,
            'activities': 0.25,
            'dining': 0.25,
            'travel_history': 0.2
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for category, score in confidence_scores.items():
            weight = weights.get(category, 0.1)
            total_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.1
        
        return min(total_score / total_weight, 1.0)


# Global instance
recommendation_engine = ProfileRecommendationEngine()


def get_personalized_recommendations(db: Session, request: ProfileRecommendationRequest) -> ProfileRecommendationResponse:
    """Main function to get personalized recommendations"""
    return recommendation_engine.generate_recommendations(db, request) 