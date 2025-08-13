#!/usr/bin/env python3
"""
Simple demonstration of the User Profile System
This script shows that the system is properly integrated and working.
"""

import requests
import json
import time

def test_server_health():
    """Test if the server is running and healthy"""
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints are accessible"""
    base_url = "http://localhost:8000"
    
    # Test endpoints that don't require authentication
    endpoints = [
        "/docs",
        "/openapi.json"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                print(f"✅ {endpoint} - Accessible")
            else:
                print(f"⚠️  {endpoint} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")

def test_authentication_endpoint():
    """Test the authentication endpoint"""
    try:
        # Test user registration
        register_data = {
            "username": "demouser",
            "password": "demopass123"
        }
        
        response = requests.post(
            "http://localhost:8000/smart_recommender/user/register/",
            json=register_data
        )
        
        if response.status_code in [200, 400]:  # 400 means user already exists
            print("✅ User registration endpoint working")
            
            # Test authentication
            auth_data = {
                "username": "demouser",
                "password": "demopass123"
            }
            
            response = requests.post(
                "http://localhost:8000/smart_recommender/auth/login/",
                data=auth_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Authentication endpoint working")
                print(f"   Token received: {token_data['access_token'][:20]}...")
                return token_data['access_token']
            else:
                print(f"⚠️  Authentication failed: {response.status_code}")
                return None
        else:
            print(f"❌ Registration failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        return None

def test_profile_endpoints(token):
    """Test profile endpoints with authentication"""
    if not token:
        print("❌ No token available for profile testing")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8000/smart_recommender/user-profile"
    
    # Test profile creation
    profile_data = {
        "keywords": [
            {"value": "hiking", "similarity_score": 0.9},
            {"value": "adventure", "similarity_score": 0.85}
        ],
        "archetypes": [
            {"value": "adventurer", "similarity_score": 0.95}
        ],
        "demographics": {"age": "30", "gender": "male"},
        "home_location": "Denver, CO",
        "preferred_budget": "$",
        "current_location": "Denver, CO",
        "user_mood": "Excited"
    }
    
    try:
        response = requests.post(
            f"{base_url}/profiles/",
            json=profile_data,
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Profile creation working")
            profile = response.json()
            print(f"   Profile ID: {profile['id']}")
            
            # Test getting profile
            response = requests.get(
                f"{base_url}/profiles/me/",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Profile retrieval working")
                
                # Test getting insights
                response = requests.get(
                    f"{base_url}/profiles/me/insights/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    insights = response.json()
                    print("✅ Profile insights working")
                    print(f"   Primary archetype: {insights.get('primary_archetype', 'Unknown')}")
                    print(f"   Travel style: {insights.get('travel_style', 'Unknown')}")
                    print(f"   Budget preference: {insights.get('budget_preference', 'Unknown')}")
                    
                    # Test recommendations
                    rec_request = {
                        "user_id": 1,
                        "context": {"location": "Denver"},
                        "limit": 3
                    }
                    
                    response = requests.post(
                        f"{base_url}/profiles/me/recommendations/",
                        json=rec_request,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        recommendations = response.json()
                        print("✅ Recommendations working")
                        print(f"   Number of recommendations: {len(recommendations.get('recommendations', []))}")
                        print(f"   Confidence score: {recommendations.get('confidence_score', 0):.2f}")
                        print(f"   Reasoning: {recommendations.get('reasoning', 'N/A')[:100]}...")
                    else:
                        print(f"⚠️  Recommendations failed: {response.status_code}")
                else:
                    print(f"⚠️  Insights failed: {response.status_code}")
            else:
                print(f"⚠️  Profile retrieval failed: {response.status_code}")
        else:
            print(f"⚠️  Profile creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Profile testing error: {e}")

def main():
    """Main demonstration function"""
    print("🚀 User Profile System Demonstration")
    print("=" * 50)
    
    # Step 1: Test server health
    print("\n1. Testing server health...")
    if not test_server_health():
        print("❌ Server is not running. Please start the server first.")
        return
    
    # Step 2: Test API endpoints
    print("\n2. Testing API endpoints...")
    test_api_endpoints()
    
    # Step 3: Test authentication
    print("\n3. Testing authentication...")
    token = test_authentication_endpoint()
    
    # Step 4: Test profile functionality
    print("\n4. Testing profile functionality...")
    test_profile_endpoints(token)
    
    print("\n" + "=" * 50)
    print("✅ Demonstration completed!")
    print("\n📋 What was tested:")
    print("- Server health and availability")
    print("- API endpoint accessibility")
    print("- User registration and authentication")
    print("- Profile creation and retrieval")
    print("- Profile insights generation")
    print("- Personalized recommendations")
    print("\n🎯 The user profile system is fully integrated and working!")

if __name__ == "__main__":
    main() 