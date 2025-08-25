#!/usr/bin/env python3
"""
Simple test script to demonstrate the content recommendation API.
This script shows how to use the basic endpoints for the content recommendation system.
"""

import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000/smart_recommender"

# Test user credentials (you'll need to create a user first)
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"

# Global variables to store tokens and user data
access_token = None
user_id = None


def print_response(response: requests.Response, title: str = "Response"):
    """Print formatted API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def login_user():
    """Login and get access token"""
    global access_token, user_id
    
    print("Logging in user...")
    
    # First, try to register the user
    register_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print_response(response, "Register Response")
    
    # Then login
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    print_response(response, "Login Response")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print(f"Access token: {access_token[:20]}..." if access_token else "No access token")
    else:
        print("Failed to login")
        return False
    
    return True


def get_headers():
    """Get headers with authentication"""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


def test_create_user_profile():
    """Test creating a user profile"""
    print("\nTesting user profile creation...")
    
    profile_data = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "location_name": "New York, NY",
        "interests": ["music", "movies", "events", "places"],
        "keywords": ["date night", "wellness", "adventure"],
        "archetypes": ["wellness", "foodie", "adventurer"],
        "age_group": "30s",
        "relationship_status": "partnered",
        "travel_history": [
            {"destination": "Paris", "year": 2023},
            {"destination": "Tokyo", "year": 2022}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/content/profile",
        json=profile_data,
        headers=get_headers()
    )
    print_response(response, "Create Profile Response")


def test_get_user_profile():
    """Test getting user profile"""
    print("\nTesting get user profile...")
    
    response = requests.get(
        f"{BASE_URL}/content/profile",
        headers=get_headers()
    )
    print_response(response, "Get Profile Response")


def test_get_content_recommendations():
    """Test getting content recommendations"""
    print("\nTesting get content recommendations...")
    
    # Get all content types
    response = requests.get(
        f"{BASE_URL}/content/content",
        headers=get_headers()
    )
    print_response(response, "Get All Recommendations Response")
    
    # Get specific content types
    response = requests.get(
        f"{BASE_URL}/content/content?content_types=music&content_types=movie&limit=5",
        headers=get_headers()
    )
    print_response(response, "Get Music & Movie Recommendations Response")


def test_log_interaction():
    """Test logging user interaction"""
    print("\nTesting log interaction...")
    
    interaction_data = {
        "content_id": 1,  # This should be a real content ID from recommendations
        "interaction_type": "click",
        "interaction_data": {
            "duration": 30,
            "source": "recommendation_feed"
        },
        "device_info": {
            "platform": "web",
            "browser": "chrome"
        },
        "location": {
            "latitude": 40.7128,
            "longitude": -74.0060
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/content/interaction",
        json=interaction_data,
        headers=get_headers()
    )
    print_response(response, "Log Interaction Response")


def test_refresh_recommendations():
    """Test refreshing recommendations"""
    print("\nTesting refresh recommendations...")
    
    response = requests.post(
        f"{BASE_URL}/content/refresh",
        headers=get_headers()
    )
    print_response(response, "Refresh Recommendations Response")


def test_health_check():
    """Test health check endpoint"""
    print("\nTesting health check...")
    
    response = requests.get(f"{BASE_URL}/content/health")
    print_response(response, "Health Check Response")


def main():
    """Main test function"""
    print("Content Recommendation API Test")
    print("="*50)
    
    # Test login
    if not login_user():
        print("Failed to login. Exiting.")
        return
    
    # Test endpoints
    test_create_user_profile()
    test_get_user_profile()
    test_get_content_recommendations()
    test_log_interaction()
    test_refresh_recommendations()
    test_health_check()
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)
    print("="*50)


if __name__ == "__main__":
    main() 

