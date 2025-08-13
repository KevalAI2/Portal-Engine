#!/usr/bin/env python3
"""
Simplified LIS (Location-based Interest System) Demo
Demonstrates automatic prompt generation based on user profiles and locations
without requiring database setup
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class UserProfile:
    """Simplified user profile for demo"""
    user_id: int
    archetypes: List[str]
    outdoor_activities: List[str]
    indoor_activities: List[str]
    cuisine_preferences: List[str]
    atmosphere_preferences: List[str]
    budget: str
    mood: str
    energy_level: str
    group_size: int


@dataclass
class LocationData:
    """Location-specific data"""
    restaurants: List[Dict[str, Any]]
    activities: List[Dict[str, Any]]


@dataclass
class LISPrompt:
    """Location-based interest prompt"""
    prompt_id: str
    prompt_type: str
    title: str
    description: str
    urgency: str
    relevance_score: float
    reasoning: List[str]


class LISDemoEngine:
    """Simplified LIS engine for demonstration"""
    
    def __init__(self):
        # Sample location data
        self.location_data = {
            "Denver, CO": LocationData(
                restaurants=[
                    {"name": "Sakura Sushi", "cuisine": "Japanese", "price": "$$", "atmosphere": "quiet", "outdoor": True},
                    {"name": "La Trattoria", "cuisine": "Italian", "price": "$$", "atmosphere": "romantic", "outdoor": False},
                    {"name": "Spice Garden", "cuisine": "Thai", "price": "$", "atmosphere": "trendy", "outdoor": True},
                    {"name": "Urban Brew", "cuisine": "American", "price": "$", "atmosphere": "casual", "outdoor": True},
                    {"name": "Taco Fiesta", "cuisine": "Mexican", "price": "$", "atmosphere": "high-energy", "outdoor": False},
                ],
                activities=[
                    {"name": "Red Rocks Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "2 hours"},
                    {"name": "Denver Art Museum", "type": "indoor", "category": "cultural", "price": "$$", "duration": "3 hours"},
                    {"name": "Cherry Creek Trail", "type": "outdoor", "category": "fitness", "price": "$", "duration": "1 hour"},
                    {"name": "Union Station", "type": "indoor", "category": "social", "price": "$", "duration": "2 hours"},
                ]
            ),
            "New York, NY": LocationData(
                restaurants=[
                    {"name": "Le Bernardin", "cuisine": "French", "price": "$$$$", "atmosphere": "luxury", "outdoor": False},
                    {"name": "Katz's Delicatessen", "cuisine": "American", "price": "$$", "atmosphere": "casual", "outdoor": False},
                    {"name": "Momofuku Noodle Bar", "cuisine": "Asian", "price": "$$", "atmosphere": "trendy", "outdoor": False},
                    {"name": "Gramercy Tavern", "cuisine": "American", "price": "$$$", "atmosphere": "romantic", "outdoor": True},
                ],
                activities=[
                    {"name": "Central Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "2 hours"},
                    {"name": "Metropolitan Museum", "type": "indoor", "category": "cultural", "price": "$$", "duration": "3 hours"},
                    {"name": "Times Square", "type": "indoor", "category": "entertainment", "price": "$", "duration": "1 hour"},
                    {"name": "Brooklyn Bridge", "type": "outdoor", "category": "sightseeing", "price": "$", "duration": "1 hour"},
                ]
            ),
            "Chicago, IL": LocationData(
                restaurants=[
                    {"name": "Alinea", "cuisine": "American", "price": "$$$$", "atmosphere": "luxury", "outdoor": False},
                    {"name": "Giordano's", "cuisine": "Italian", "price": "$$", "atmosphere": "family", "outdoor": False},
                    {"name": "Portillo's", "cuisine": "American", "price": "$", "atmosphere": "casual", "outdoor": False},
                    {"name": "Girl & The Goat", "cuisine": "American", "price": "$$$", "atmosphere": "trendy", "outdoor": True},
                ],
                activities=[
                    {"name": "Millennium Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "2 hours"},
                    {"name": "Art Institute of Chicago", "type": "indoor", "category": "cultural", "price": "$$", "duration": "3 hours"},
                    {"name": "Navy Pier", "type": "outdoor", "category": "entertainment", "price": "$$", "duration": "2 hours"},
                    {"name": "Willis Tower", "type": "indoor", "category": "sightseeing", "price": "$$", "duration": "1 hour"},
                ]
            )
        }
        
        # Default location data for other cities
        self.default_location = LocationData(
            restaurants=[
                {"name": "Local Cafe", "cuisine": "American", "price": "$", "atmosphere": "casual", "outdoor": True},
                {"name": "Pizza Place", "cuisine": "Italian", "price": "$$", "atmosphere": "family", "outdoor": False},
            ],
            activities=[
                {"name": "Local Park", "type": "outdoor", "category": "nature", "price": "$", "duration": "1 hour"},
                {"name": "Shopping Center", "type": "indoor", "category": "shopping", "price": "$", "duration": "2 hours"},
            ]
        )

    def generate_prompts(self, user_profile: UserProfile, location: str) -> List[LISPrompt]:
        """Generate location-based prompts for a user"""
        prompts = []
        
        # Get location data
        location_data = self.location_data.get(location, self.default_location)
        
        # Generate restaurant prompts
        restaurant_prompts = self._generate_restaurant_prompts(user_profile, location_data)
        prompts.extend(restaurant_prompts)
        
        # Generate activity prompts
        activity_prompts = self._generate_activity_prompts(user_profile, location_data)
        prompts.extend(activity_prompts)
        
        # Sort by relevance score
        prompts.sort(key=lambda p: p.relevance_score, reverse=True)
        
        return prompts[:10]  # Return top 10 prompts

    def _generate_restaurant_prompts(self, profile: UserProfile, location_data: LocationData) -> List[LISPrompt]:
        """Generate restaurant-related prompts"""
        prompts = []
        
        for restaurant in location_data.restaurants:
            score = 0.0
            reasoning = []
            
            # Score based on cuisine preference
            if restaurant['cuisine'].lower() in [c.lower() for c in profile.cuisine_preferences]:
                score += 0.4
                reasoning.append(f"Matches your {restaurant['cuisine']} cuisine preference")
            
            # Score based on atmosphere preference
            if restaurant['atmosphere'].lower() in [a.lower() for a in profile.atmosphere_preferences]:
                score += 0.3
                reasoning.append(f"Matches your preferred {restaurant['atmosphere']} atmosphere")
            
            # Score based on budget
            if restaurant['price'] == profile.budget:
                score += 0.2
                reasoning.append("Matches your budget preference")
            elif restaurant['price'] in ["$", "$$"] and profile.budget in ["$", "$$"]:
                score += 0.1
                reasoning.append("Within your budget range")
            
            # Score based on group size and atmosphere
            if profile.group_size > 2 and restaurant['atmosphere'] in ['family', 'casual']:
                score += 0.1
                reasoning.append("Good for your group size")
            
            if score > 0.3:  # Only include relevant restaurants
                prompt = LISPrompt(
                    prompt_id=f"restaurant_{restaurant['name'].replace(' ', '_').lower()}",
                    prompt_type="restaurant",
                    title=f"Try {restaurant['name']}",
                    description=f"Check out {restaurant['name']} - great {restaurant['cuisine']} cuisine with a {restaurant['atmosphere']} atmosphere!",
                    urgency="high" if restaurant['price'] in ["$", "$$"] else "medium",
                    relevance_score=score,
                    reasoning=reasoning
                )
                prompts.append(prompt)
        
        return prompts

    def _generate_activity_prompts(self, profile: UserProfile, location_data: LocationData) -> List[LISPrompt]:
        """Generate activity-related prompts"""
        prompts = []
        
        for activity in location_data.activities:
            score = 0.0
            reasoning = []
            
            # Score based on indoor/outdoor preference
            if activity['type'] == 'outdoor' and any(act.lower() in activity['name'].lower() for act in profile.outdoor_activities):
                score += 0.4
                reasoning.append("Matches your outdoor activity preferences")
            elif activity['type'] == 'indoor' and any(act.lower() in activity['name'].lower() for act in profile.indoor_activities):
                score += 0.4
                reasoning.append("Matches your indoor activity preferences")
            
            # Score based on archetype
            if 'adventurer' in profile.archetypes and activity['category'] in ['nature', 'fitness']:
                score += 0.3
                reasoning.append("Perfect for your adventurous spirit")
            elif 'cultural' in profile.archetypes and activity['category'] == 'cultural':
                score += 0.3
                reasoning.append("Matches your cultural interests")
            elif 'luxury' in profile.archetypes and activity['price'] in ['$$$', '$$$$']:
                score += 0.2
                reasoning.append("Aligns with your luxury preferences")
            
            # Score based on energy level
            if profile.energy_level == 'high' and activity['type'] == 'outdoor':
                score += 0.1
                reasoning.append("Great for your high energy level")
            elif profile.energy_level == 'low' and activity['type'] == 'indoor':
                score += 0.1
                reasoning.append("Perfect for your current energy level")
            
            if score > 0.3:
                prompt = LISPrompt(
                    prompt_id=f"activity_{activity['name'].replace(' ', '_').lower()}",
                    prompt_type="activity",
                    title=f"Explore {activity['name']}",
                    description=f"Explore {activity['name']} - a great {activity['category']} activity! Duration: {activity['duration']}",
                    urgency="medium" if activity['type'] == 'outdoor' else "low",
                    relevance_score=score,
                    reasoning=reasoning
                )
                prompts.append(prompt)
        
        return prompts


def create_sample_profiles():
    """Create sample user profiles for demonstration"""
    profiles = {
        "adventurer": UserProfile(
            user_id=1,
            archetypes=["adventurer", "nature-lover"],
            outdoor_activities=["hiking", "rock climbing", "camping", "trails"],
            indoor_activities=["museums", "art galleries"],
            cuisine_preferences=["Mexican", "Thai", "American"],
            atmosphere_preferences=["casual", "trendy"],
            budget="$",
            mood="excited",
            energy_level="high",
            group_size=2
        ),
        "luxury_traveler": UserProfile(
            user_id=2,
            archetypes=["luxury-lover", "cultural-explorer"],
            outdoor_activities=["golf", "yacht tours"],
            indoor_activities=["fine dining", "spa treatments", "art galleries"],
            cuisine_preferences=["French", "Japanese", "Italian"],
            atmosphere_preferences=["romantic", "luxury"],
            budget="$$$",
            mood="relaxed",
            energy_level="medium",
            group_size=2
        ),
        "family_traveler": UserProfile(
            user_id=3,
            archetypes=["family-oriented", "budget-conscious"],
            outdoor_activities=["parks", "beaches", "zoos"],
            indoor_activities=["museums", "movie theaters", "indoor playgrounds"],
            cuisine_preferences=["American", "Italian", "Mexican"],
            atmosphere_preferences=["family-friendly", "casual"],
            budget="$$",
            mood="happy",
            energy_level="medium",
            group_size=4
        )
    }
    return profiles


def demo_lis_system():
    """Demonstrate the LIS system"""
    print("🚀 LIS (Location-based Interest System) Demo")
    print("=" * 60)
    
    # Create LIS engine
    lis_engine = LISDemoEngine()
    
    # Create sample profiles
    profiles = create_sample_profiles()
    
    # Test locations
    test_locations = ["Denver, CO", "New York, NY", "Chicago, IL", "San Francisco, CA"]
    
    for profile_name, profile in profiles.items():
        print(f"\n👤 {profile_name.upper()} Profile")
        print("-" * 50)
        print(f"   Archetypes: {', '.join(profile.archetypes)}")
        print(f"   Budget: {profile.budget}")
        print(f"   Mood: {profile.mood}, Energy: {profile.energy_level}")
        print(f"   Group Size: {profile.group_size}")
        
        for location in test_locations:
            print(f"\n📍 Location: {location}")
            print("-" * 30)
            
            # Generate prompts
            prompts = lis_engine.generate_prompts(profile, location)
            
            print(f"📊 Generated {len(prompts)} prompts")
            
            # Show top prompts
            for i, prompt in enumerate(prompts[:3], 1):
                print(f"\n  {i}. {prompt.title}")
                print(f"     Type: {prompt.prompt_type}")
                print(f"     Description: {prompt.description}")
                print(f"     Relevance: {prompt.relevance_score:.2f}")
                print(f"     Urgency: {prompt.urgency}")
                print(f"     Reasoning: {', '.join(prompt.reasoning)}")
        
        print("\n" + "="*60)
    
    print("\n🎉 LIS System Demo Complete!")
    print("\n📈 Key Features Demonstrated:")
    print("  • Location-aware prompt generation")
    print("  • User profile-based personalization")
    print("  • Multi-factor scoring algorithm")
    print("  • Context-aware recommendations")
    print("  • Relevance scoring and urgency ranking")
    print("  • Detailed reasoning for each recommendation")


def demo_specific_scenario():
    """Demonstrate a specific scenario in detail"""
    print("\n🔍 Detailed Scenario: Adventurer in Denver")
    print("=" * 50)
    
    # Create adventurer profile
    adventurer = UserProfile(
        user_id=100,
        archetypes=["adventurer", "nature-lover"],
        outdoor_activities=["hiking", "rock climbing", "camping", "trails"],
        indoor_activities=["museums", "art galleries"],
        cuisine_preferences=["Mexican", "Thai", "American"],
        atmosphere_preferences=["casual", "trendy"],
        budget="$",
        mood="excited",
        energy_level="high",
        group_size=2
    )
    
    # Create LIS engine
    lis_engine = LISDemoEngine()
    
    # Generate prompts for Denver
    location = "Denver, CO"
    prompts = lis_engine.generate_prompts(adventurer, location)
    
    print(f"📍 Location: {location}")
    print(f"👤 User: Adventurer (Budget: ${adventurer.budget}, Energy: {adventurer.energy_level})")
    print(f"📊 Generated {len(prompts)} prompts")
    
    # Group prompts by type
    restaurant_prompts = [p for p in prompts if p.prompt_type == "restaurant"]
    activity_prompts = [p for p in prompts if p.prompt_type == "activity"]
    
    print(f"\n🍽️  RESTAURANT PROMPTS ({len(restaurant_prompts)}):")
    for prompt in restaurant_prompts:
        print(f"  🎯 {prompt.title}")
        print(f"     📝 {prompt.description}")
        print(f"     ⭐ Relevance: {prompt.relevance_score:.2f}")
        print(f"     🚨 Urgency: {prompt.urgency}")
        print(f"     💭 Reasoning: {', '.join(prompt.reasoning)}")
        print()
    
    print(f"🏃 ACTIVITY PROMPTS ({len(activity_prompts)}):")
    for prompt in activity_prompts:
        print(f"  🎯 {prompt.title}")
        print(f"     📝 {prompt.description}")
        print(f"     ⭐ Relevance: {prompt.relevance_score:.2f}")
        print(f"     🚨 Urgency: {prompt.urgency}")
        print(f"     💭 Reasoning: {', '.join(prompt.reasoning)}")
        print()


if __name__ == "__main__":
    print("🧪 LIS System Demo")
    print("=" * 40)
    
    # Run main demo
    demo_lis_system()
    
    # Run specific scenario demo
    demo_specific_scenario()
    
    print("\n✨ Demo completed successfully!")
    print("\n💡 This demonstrates how the LIS system:")
    print("   • Analyzes user profiles and preferences")
    print("   • Considers current location and available options")
    print("   • Generates personalized recommendations")
    print("   • Provides reasoning for each suggestion")
    print("   • Ranks suggestions by relevance and urgency") 