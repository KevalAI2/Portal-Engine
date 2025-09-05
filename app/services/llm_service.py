"""
LLM Service for generating recommendations
"""
import json
import time
import random
from typing import Dict, Any, List
from core.logging import get_logger
from core.config import settings
import redis

logger = get_logger("llm_service")


class LLMService:
    """Service to generate recommendations from prompts and store in Redis"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=6379,
            db=1,  # Use different DB for recommendations
            decode_responses=True
        )
        # Action weights for ranking score calculation
        self.ACTION_WEIGHTS = {
            "liked": 2.0,
            "saved": 1.5,
            "shared": 1.2,
            "clicked": 0.8,
            "view": 0.4,
            "ignored": -1.0,
            "disliked": -1.5,
        }
        self.BASE_SCORE = 0.5
        self.SCALE = 0.2  # scale for converting weighted sum into [0,1] range
        self._setup_demo_data()
    
    def _normalize_key(self, value: str) -> str:
        """Normalize string keys for comparison"""
        if not isinstance(value, str):
            return ""
        return ''.join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()

    def _setup_demo_data(self):
        """Setup demo recommendation data with complete field structure"""
        self.demo_recommendations = {
            "movies": {
                "barcelona": [
                    {
                        "title": "Vicky Cristina Barcelona",
                        "year": "2008",
                        "genre": "Romance/Drama",
                        "description": "A passionate tale of love, desire, and artistic inspiration in vibrant Barcelona",
                        "director": "Woody Allen",
                        "rating": "7.1",
                        "duration": "96",
                        "streaming_platform": "Netflix",
                        "cast": ["Javier Bardem", "Penélope Cruz", "Scarlett Johansson"],
                        "imdb_id": "tt0497465",
                        "poster_url": "https://image.tmdb.org/t/p/w500/vicky_cristina_barcelona.jpg",
                        "trailer_url": "https://youtube.com/watch?v=VCY5_lUxjXQ",
                        "language": "English/Spanish",
                        "country": "Spain/USA",
                        "box_office": "$96.4M",
                        "awards": "Academy Award Winner - Best Supporting Actress",
                        "age_rating": "PG-13",
                        "keywords": ["romance", "art", "barcelona", "passion"]
                    },
                    {
                        "title": "All About My Mother",
                        "year": "1999",
                        "genre": "Drama",
                        "description": "An emotional journey through grief, identity, and the strength of women",
                        "director": "Pedro Almodóvar",
                        "rating": "7.9",
                        "duration": "101",
                        "streaming_platform": "Amazon Prime",
                        "cast": ["Cecilia Roth", "Marisa Paredes", "Antonia San Juan"],
                        "imdb_id": "tt0185125",
                        "poster_url": "https://image.tmdb.org/t/p/w500/all_about_my_mother.jpg",
                        "trailer_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
                        "language": "Spanish",
                        "country": "Spain",
                        "box_office": "$67.8M",
                        "awards": "Academy Award Winner - Best Foreign Language Film",
                        "age_rating": "R",
                        "keywords": ["drama", "family", "identity", "spanish cinema"]
                    }
                ],
                "international": [
                    {
                        "title": "The Shawshank Redemption",
                        "year": "1994",
                        "genre": "Drama",
                        "description": "A story of hope and friendship within the walls of Shawshank State Penitentiary",
                        "director": "Frank Darabont",
                        "rating": "9.3",
                        "duration": "142",
                        "streaming_platform": "Netflix",
                        "cast": ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
                        "imdb_id": "tt0111161",
                        "poster_url": "https://image.tmdb.org/t/p/w500/shawshank.jpg",
                        "trailer_url": "https://youtube.com/watch?v=6hB3S9bIaco",
                        "language": "English",
                        "country": "USA",
                        "box_office": "$16.3M",
                        "awards": "7 Academy Award nominations",
                        "age_rating": "R",
                        "keywords": ["hope", "friendship", "prison", "redemption"]
                    },
                    {
                        "title": "Inception",
                        "year": "2010",
                        "genre": "Sci-Fi/Thriller",
                        "description": "A mind-bending thriller about entering and manipulating dreams",
                        "director": "Christopher Nolan",
                        "rating": "8.8",
                        "duration": "148",
                        "streaming_platform": "HBO Max",
                        "cast": ["Leonardo DiCaprio", "Marion Cotillard", "Tom Hardy"],
                        "imdb_id": "tt1375666",
                        "poster_url": "https://image.tmdb.org/t/p/w500/inception.jpg",
                        "trailer_url": "https://youtube.com/watch?v=YoHD9XEInc0",
                        "language": "English",
                        "country": "USA/UK",
                        "box_office": "$836.8M",
                        "awards": "4 Academy Awards",
                        "age_rating": "PG-13",
                        "keywords": ["dreams", "reality", "heist", "psychological"]
                    }
                ]
            },
            "music": {
                "barcelona": [
                    {
                        "title": "Barcelona",
                        "artist": "Freddie Mercury & Montserrat Caballé",
                        "genre": "Opera-Rock",
                        "description": "An epic fusion of rock and opera celebrating the Olympic spirit",
                        "release_year": "1987",
                        "album": "Barcelona",
                        "duration": "5:39",
                        "spotify_url": "https://open.spotify.com/track/3Wrjm47oTz2sjIgck5pwaa",
                        "apple_music_url": "https://music.apple.com/album/barcelona",
                        "youtube_url": "https://youtube.com/watch?v=9RG4jbgHNyg",
                        "label": "Polydor Records",
                        "producer": "Mike Moran",
                        "featured_artists": ["Montserrat Caballé"],
                        "lyrics_snippet": "Barcelona, it was the first time that we met",
                        "chart_position": "Top 10 in UK",
                        "monthly_listeners": "5M",
                        "mood": "triumphant",
                        "tempo": "76 BPM",
                        "key": "D Major"
                    },
                    {
                        "title": "Mediterráneo",
                        "artist": "Joan Manuel Serrat",
                        "genre": "Folk",
                        "description": "A poetic ode to the Mediterranean lifestyle and culture",
                        "release_year": "1971",
                        "album": "Mediterráneo",
                        "duration": "4:32",
                        "spotify_url": "https://open.spotify.com/track/mediterraneo",
                        "apple_music_url": "https://music.apple.com/album/mediterraneo",
                        "youtube_url": "https://youtube.com/watch?v=mediterraneo",
                        "label": "Edigsa",
                        "producer": "Joan Manuel Serrat",
                        "featured_artists": [],
                        "lyrics_snippet": "Mediterráneo, que nos vio nacer",
                        "chart_position": "Classic Spanish hit",
                        "monthly_listeners": "2M",
                        "mood": "nostalgic",
                        "tempo": "90 BPM",
                        "key": "G Major"
                    }
                ],
                "international": [
                    {
                        "title": "Blinding Lights",
                        "artist": "The Weeknd",
                        "genre": "Pop/Synth-pop",
                        "description": "A retro-futuristic anthem with irresistible 80s vibes",
                        "release_year": "2019",
                        "album": "After Hours",
                        "duration": "3:20",
                        "spotify_url": "https://open.spotify.com/track/0VjIjW4GlULA8N8OQB9jkI",
                        "apple_music_url": "https://music.apple.com/album/blinding-lights",
                        "youtube_url": "https://youtube.com/watch?v=4NRXx6U8ABQ",
                        "label": "Republic Records",
                        "producer": "Max Martin",
                        "featured_artists": [],
                        "lyrics_snippet": "I can't sleep until I feel your touch",
                        "chart_position": "Billboard Hot 100 #1",
                        "monthly_listeners": "80M",
                        "mood": "euphoric",
                        "tempo": "171 BPM",
                        "key": "F# Minor"
                    },
                    {
                        "title": "Shape of You",
                        "artist": "Ed Sheeran",
                        "genre": "Pop",
                        "description": "A catchy tropical house-influenced love song",
                        "release_year": "2017",
                        "album": "÷ (Divide)",
                        "duration": "3:53",
                        "spotify_url": "https://open.spotify.com/track/7qiZfU4dY1lWllzX7mkmht",
                        "apple_music_url": "https://music.apple.com/album/shape-of-you",
                        "youtube_url": "https://youtube.com/watch?v=JGwWNGJdvx8",
                        "label": "Atlantic Records",
                        "producer": "Steve Mac",
                        "featured_artists": [],
                        "lyrics_snippet": "I'm in love with the shape of you",
                        "chart_position": "Billboard Hot 100 #1",
                        "monthly_listeners": "70M",
                        "mood": "romantic",
                        "tempo": "96 BPM",
                        "key": "C# Minor"
                    }
                ]
            },
            "places": {
                "barcelona": [
                    {
                        "name": "Sagrada Família",
                        "type": "tourist_attraction",
                        "hours": ["Monday: 9:00 – 18:00", "Tuesday: 9:00 – 18:00", "Wednesday: 9:00 – 18:00", "Thursday: 9:00 – 18:00", "Friday: 9:00 – 18:00", "Saturday: 9:00 – 18:00", "Sunday: 10:30 – 18:00"],
                        "query": "Sagrada Família Barcelona",
                        "rating": 4.7,
                        "reviews": "Absolutely breathtaking architecture. Gaudí's masterpiece is a must-see.",
                        "website": "https://sagradafamilia.org",
                        "category": "tourist_attraction",
                        "location": {"lat": 41.4036, "lng": 2.1744},
                        "place_id": "ChIJi_w-0yaqpBIRs22cqV9z8z8",
                        "vicinity": "Carrer de Mallorca, 401, Barcelona",
                        "photo_url": "https://places.googleapis.com/v1/places/sagrada_familia/photos/reference",
                        "time_comments": "Best visited in the morning to avoid crowds",
                        "llmDescription": "Gaudí's architectural marvel combining Gothic and Art Nouveau forms",
                        "preferred_time": "morning",
                        "business_status": "OPERATIONAL",
                        "google_maps_url": "https://maps.google.com/?cid=4614865102743308978",
                        "distance_from_user": 500,
                        "user_ratings_total": 175432,
                        "phone_international": "+34 932 08 04 14",
                        "phone_local": "932 08 04 14",
                        "price_level": 3,
                        "cuisine_type": None,
                        "delivery_available": False,
                        "reservation_required": True,
                        "parking_available": False,
                        "wifi_available": False,
                        "wheelchair_accessible": True,
                        "outdoor_seating": False
                    },
                    {
                        "name": "Park Güell",
                        "type": "park",
                        "hours": ["Monday: 9:30 – 17:30", "Tuesday: 9:30 – 17:30", "Wednesday: 9:30 – 17:30", "Thursday: 9:30 – 17:30", "Friday: 9:30 – 17:30", "Saturday: 9:30 – 17:30", "Sunday: 9:30 – 17:30"],
                        "query": "Park Güell Barcelona",
                        "rating": 4.5,
                        "reviews": "Magical park with stunning city views and Gaudí's colorful mosaics.",
                        "website": "https://parkguell.barcelona",
                        "category": "tourist_attraction",
                        "location": {"lat": 41.4145, "lng": 2.1527},
                        "place_id": "ChIJi_w-0yaqpBIRs22cqV9z999",
                        "vicinity": "Carrer d'Olot, s/n, Barcelona",
                        "photo_url": "https://places.googleapis.com/v1/places/park_guell/photos/reference",
                        "time_comments": "Perfect for afternoon strolls with panoramic views",
                        "llmDescription": "Whimsical park featuring Gaudí's distinctive architectural elements",
                        "preferred_time": "afternoon",
                        "business_status": "OPERATIONAL",
                        "google_maps_url": "https://maps.google.com/?cid=parkguell123",
                        "distance_from_user": 1200,
                        "user_ratings_total": 89234,
                        "phone_international": "+34 934 13 24 00",
                        "phone_local": "934 13 24 00",
                        "price_level": 2,
                        "cuisine_type": None,
                        "delivery_available": False,
                        "reservation_required": True,
                        "parking_available": True,
                        "wifi_available": True,
                        "wheelchair_accessible": False,
                        "outdoor_seating": True
                    }
                ],
                "international": [
                    {
                        "name": "Eiffel Tower",
                        "type": "monument",
                        "hours": ["Monday: 9:00 – 23:45", "Tuesday: 9:00 – 23:45", "Wednesday: 9:00 – 23:45", "Thursday: 9:00 – 23:45", "Friday: 9:00 – 00:45", "Saturday: 9:00 – 00:45", "Sunday: 9:00 – 23:45"],
                        "query": "Eiffel Tower Paris",
                        "rating": 4.6,
                        "reviews": "Iconic symbol of Paris with breathtaking views from the top.",
                        "website": "https://tour-eiffel.paris",
                        "category": "tourist_attraction",
                        "location": {"lat": 48.8584, "lng": 2.2945},
                        "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
                        "vicinity": "Champ de Mars, 5 Avenue Anatole France, Paris",
                        "photo_url": "https://places.googleapis.com/v1/places/eiffel_tower/photos/reference",
                        "time_comments": "Spectacular at sunset and beautifully lit at night",
                        "llmDescription": "The iron lattice tower that has become the global cultural icon of France",
                        "preferred_time": "evening",
                        "business_status": "OPERATIONAL",
                        "google_maps_url": "https://maps.google.com/?cid=eiffel123",
                        "distance_from_user": 800000,
                        "user_ratings_total": 298765,
                        "phone_international": "+33 8 92 70 12 39",
                        "phone_local": "0892 70 12 39",
                        "price_level": 3,
                        "cuisine_type": None,
                        "delivery_available": False,
                        "reservation_required": False,
                        "parking_available": False,
                        "wifi_available": True,
                        "wheelchair_accessible": True,
                        "outdoor_seating": False
                    }
                ]
            },
            "events": {
                "barcelona": [
                    {
                        "name": "La Mercè Festival",
                        "date": "2024-09-20T10:00:00Z",
                        "end_date": "2024-09-24T23:59:00Z",
                        "description": "Barcelona's biggest street festival celebrating the city's patron saint",
                        "venue": "Various locations across Barcelona",
                        "address": "Barcelona City Center, Barcelona, Spain",
                        "price": "Free",
                        "price_min": 0,
                        "price_max": 0,
                        "currency": "EUR",
                        "category": "cultural",
                        "duration": "5 days",
                        "organizer": "Barcelona City Council",
                        "website": "https://lamerce.barcelona.cat",
                        "booking_url": "https://lamerce.barcelona.cat",
                        "age_restriction": "All ages",
                        "capacity": 1000000,
                        "tickets_available": True,
                        "event_type": "festival",
                        "languages": ["Catalan", "Spanish", "English"],
                        "dress_code": "casual",
                        "parking_info": "Limited street parking, public transport recommended",
                        "public_transport": "Metro: Multiple stations throughout the city",
                        "contact_phone": "+34 932 56 25 25",
                        "contact_email": "info@lamerce.barcelona.cat",
                        "social_media": {"facebook": "https://facebook.com/lamercebcn", "instagram": "@lamercebcn"},
                        "weather_dependency": False,
                        "refund_policy": "Free event - no refunds applicable",
                        "accessibility": "Wheelchair accessible at most venues"
                    },
                    {
                        "name": "Primavera Sound",
                        "date": "2024-05-30T16:00:00Z",
                        "end_date": "2024-06-02T04:00:00Z",
                        "description": "World-class music festival featuring indie, electronic, and alternative acts",
                        "venue": "Parc del Fòrum",
                        "address": "Parc del Fòrum, Sant Adrià de Besòs, Barcelona",
                        "price": "€275-€350",
                        "price_min": 275,
                        "price_max": 350,
                        "currency": "EUR",
                        "category": "music",
                        "duration": "4 days",
                        "organizer": "Primavera Sound S.L.",
                        "website": "https://primaverasound.com",
                        "booking_url": "https://tickets.primaverasound.com",
                        "age_restriction": "18+",
                        "capacity": 220000,
                        "tickets_available": False,
                        "event_type": "festival",
                        "languages": ["English", "Spanish", "Catalan"],
                        "dress_code": "casual",
                        "parking_info": "Paid parking available on-site",
                        "public_transport": "Metro: L4 El Maresme-Fòrum station",
                        "contact_phone": "+34 933 20 49 69",
                        "contact_email": "info@primaverasound.com",
                        "social_media": {"facebook": "https://facebook.com/primaverasound", "instagram": "@primavera_sound"},
                        "weather_dependency": True,
                        "refund_policy": "No refunds except for event cancellation",
                        "accessibility": "Wheelchair accessible with special viewing areas"
                    }
                ],
                "international": [
                    {
                        "name": "Coachella Valley Music and Arts Festival",
                        "date": "2024-04-12T14:00:00Z",
                        "end_date": "2024-04-21T02:00:00Z",
                        "description": "Iconic desert music festival featuring top artists across all genres",
                        "venue": "Empire Polo Club",
                        "address": "81-800 Avenue 51, Indio, CA 92201, USA",
                        "price": "$429-$549",
                        "price_min": 429,
                        "price_max": 549,
                        "currency": "USD",
                        "category": "music",
                        "duration": "6 days (2 weekends)",
                        "organizer": "Goldenvoice",
                        "website": "https://coachella.com",
                        "booking_url": "https://coachella.com/passes",
                        "age_restriction": "All ages",
                        "capacity": 250000,
                        "tickets_available": False,
                        "event_type": "festival",
                        "languages": ["English"],
                        "dress_code": "festival fashion",
                        "parking_info": "On-site parking available for fee",
                        "public_transport": "Shuttle services from nearby cities",
                        "contact_phone": "+1 888 512 7469",
                        "contact_email": "info@coachella.com",
                        "social_media": {"facebook": "https://facebook.com/coachella", "instagram": "@coachella"},
                        "weather_dependency": True,
                        "refund_policy": "No refunds, transferable with fees",
                        "accessibility": "ADA accessible with special services"
                    }
                ]
            }
        }

    def _get_user_interaction_history(self, user_id: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Mock retrieval of user's historical interactions from a table.
        Returns interaction data with proper field matching for each category.
        """
        # Use user_id to create deterministic but varied data
        seed = sum(ord(c) for c in user_id) if user_id else 0
        rnd = random.Random(seed)
        
        # Define interaction stats for realism
        interaction_types = ["view", "liked", "saved", "shared", "clicked", "ignored", "disliked"]
        
        history = {
            "movies": [
                {"title": "Inception", "action": "liked", "timestamp": "2024-08-15T10:30:00Z"},
                {"title": "The Dark Knight", "action": "view", "timestamp": "2024-08-14T15:20:00Z"},
                {"title": "Vicky Cristina Barcelona", "action": "ignored", "timestamp": "2024-08-13T09:45:00Z"},
                {"title": "The Shawshank Redemption", "action": rnd.choice(["liked", "view", "saved"]), "timestamp": "2024-08-12T20:10:00Z"},
                {"title": "All About My Mother", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-11T14:30:00Z"},
            ],
            "music": [
                {"title": "Blinding Lights", "action": "liked", "timestamp": "2024-08-16T12:00:00Z"},
                {"title": "Barcelona", "action": "saved", "timestamp": "2024-08-15T18:45:00Z"},
                {"title": "Shape of You", "action": rnd.choice(["view", "liked", "shared"]), "timestamp": "2024-08-14T11:20:00Z"},
                {"title": "Mediterráneo", "action": rnd.choice(["ignored", "view"]), "timestamp": "2024-08-13T16:30:00Z"},
                {"title": "Dance Monkey", "action": rnd.choice(["view", "disliked"]), "timestamp": "2024-08-12T13:15:00Z"},
            ],
            "places": [
                {"name": "Sagrada Família", "action": "liked", "timestamp": "2024-08-17T09:00:00Z"},
                {"name": "Eiffel Tower", "action": "view", "timestamp": "2024-08-16T14:30:00Z"},
                {"name": "Park Güell", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-15T11:45:00Z"},
                {"name": "Big Ben", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T17:20:00Z"},
                {"name": "Colosseum", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-13T10:10:00Z"},
            ],
            "events": [
                {"name": "Primavera Sound", "action": "liked", "timestamp": "2024-08-18T08:30:00Z"},
                {"name": "Coachella Valley Music and Arts Festival", "action": "ignored", "timestamp": "2024-08-17T19:15:00Z"},
                {"name": "La Mercè Festival", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-16T15:45:00Z"},
                {"name": "Oktoberfest", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-15T12:30:00Z"},
                {"name": "Mardi Gras", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T16:00:00Z"},
            ],
        }
        
        # Add some random interactions based on user_id for variety
        for category in history:
            if rnd.random() > 0.3:  # 70% chance to add extra interactions
                extra_interactions = rnd.randint(1, 3)
                for _ in range(extra_interactions):
                    action = rnd.choice(interaction_types)
                    timestamp = f"2024-08-{rnd.randint(10, 18):02d}T{rnd.randint(8, 20):02d}:{rnd.randint(0, 59):02d}:00Z"
                    
                    if category == "movies":
                        title = f"Random Movie {rnd.randint(1, 100)}"
                        history[category].append({"title": title, "action": action, "timestamp": timestamp})
                    elif category == "music":
                        title = f"Random Song {rnd.randint(1, 100)}"
                        history[category].append({"title": title, "action": action, "timestamp": timestamp})
                    elif category == "places":
                        name = f"Random Place {rnd.randint(1, 100)}"
                        history[category].append({"name": name, "action": action, "timestamp": timestamp})
                    elif category == "events":
                        name = f"Random Event {rnd.randint(1, 100)}"
                        history[category].append({"name": name, "action": action, "timestamp": timestamp})
        
        return history

    def _compute_ranking_score(self, item: Dict[str, Any], category: str, history: Dict[str, List[Dict[str, str]]]) -> float:
        """
        Compute ranking score in [0,1] using exact field matching for each category.
        Uses title for movies/music and name for places/events.
        """
        # Get the correct field name for each category
        field_mapping = {
            "movies": "title",
            "music": "title", 
            "places": "name",
            "events": "name"
        }
        
        field_name = field_mapping.get(category, "title")
        item_identifier = self._normalize_key(item.get(field_name, ""))
        
        total_weight = 0.0
        interaction_count = 0
        
        # Look for matching interactions in history
        for interaction in history.get(category, []):
            hist_identifier = self._normalize_key(interaction.get(field_name, ""))
            if hist_identifier and hist_identifier == item_identifier:
                action = interaction.get("action", "view").lower()
                weight = self.ACTION_WEIGHTS.get(action, 0.0)
                total_weight += weight
                interaction_count += 1
        
        # If no interactions found, return base score
        if interaction_count == 0:
            return self.BASE_SCORE
        
        # Convert weighted sum to bounded score
        score = self.BASE_SCORE + self.SCALE * total_weight
        score = max(0.0, min(1.0, score))
        return round(score, 3)
    
    def generate_recommendations(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, Any]:
        """
        Generate recommendations based on prompt and store in Redis
        
        Args:
            prompt: The input prompt
            user_id: Optional user ID for storing results
            current_city: Current city for location-based recommendations
            
        Returns:
            Dictionary with recommendations and metadata
        """
        try:
            logger.info(f"Generating recommendations for prompt: {prompt[:100]}...")
            
            # Simulate LLM processing time
            time.sleep(random.uniform(0.5, 2.0))
            
            # Generate recommendations based on prompt content
            recommendations = self._generate_demo_recommendations(prompt, user_id, current_city)
            
            # Create response structure
            response = {
                "success": True,
                "prompt": prompt,
                "user_id": user_id,
                "current_city": current_city,
                "generated_at": time.time(),
                "processing_time": random.uniform(0.5, 2.0),
                "recommendations": recommendations,
                "metadata": {
                    "total_recommendations": sum(len(cat) for cat in recommendations.values()),
                    "categories": list(recommendations.keys()),
                    "model": "demo-llm-v1.0",
                    "ranking_enabled": user_id is not None
                }
            }
            
            # Store in Redis if user_id provided
            if user_id:
                self._store_in_redis(user_id, response)
            
            logger.info(f"Generated {response['metadata']['total_recommendations']} recommendations for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt,
                "user_id": user_id
            }
    
    def _generate_demo_recommendations(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, List[Dict]]:
        """Generate demo recommendations based on prompt content, annotated with ranking_score and why_would_you_like_this"""
        # Retrieve user interaction history if user_id provided
        history = self._get_user_interaction_history(user_id) if user_id else {}
        
        recommendations = {
            "movies": [],
            "music": [],
            "places": [],
            "events": []
        }
        
        # Analyze prompt to determine preferences
        prompt_lower = prompt.lower()
        
        # Determine cultural preference
        barcelona_weight = 0.5
        if any(word in prompt_lower for word in ["barcelona", "catalan", "gaudí", "sagrada família", "spanish", "spain"]):
            barcelona_weight = 0.8
        elif any(word in prompt_lower for word in ["international", "hollywood", "english", "american", "global"]):
            barcelona_weight = 0.2
        
        # Generate recommendations for each category
        for category in recommendations.keys():
            category_recommendations = []
            
            # Add Barcelona recommendations
            if random.random() < barcelona_weight:
                barcelona_items = random.sample(
                    self.demo_recommendations[category]["barcelona"],
                    min(3, len(self.demo_recommendations[category]["barcelona"]))
                )
                for item in barcelona_items:
                    item_copy = item.copy()
                    item_copy["ranking_score"] = self._compute_ranking_score(item_copy, category, history) if user_id else self.BASE_SCORE
                    item_copy["why_would_you_like_this"] = self._generate_personalized_reason(item_copy, category, prompt, user_id, current_city)
                    category_recommendations.append(item_copy)
            
            # Add International recommendations
            if random.random() < (1 - barcelona_weight):
                international_items = random.sample(
                    self.demo_recommendations[category]["international"],
                    min(3, len(self.demo_recommendations[category]["international"]))
                )
                for item in international_items:
                    item_copy = item.copy()
                    item_copy["ranking_score"] = self._compute_ranking_score(item_copy, category, history) if user_id else self.BASE_SCORE
                    item_copy["why_would_you_like_this"] = self._generate_personalized_reason(item_copy, category, prompt, user_id, current_city)
                    category_recommendations.append(item_copy)
            
            # Ensure we have at least 2 recommendations per category
            if len(category_recommendations) < 2:
                remaining_items = (
                    self.demo_recommendations[category]["barcelona"] + 
                    self.demo_recommendations[category]["international"]
                )
                # Filter out items we already have
                existing_titles = []
                field_name = "title" if category in ["movies", "music"] else "name"
                for existing in category_recommendations:
                    existing_titles.append(existing.get(field_name, ""))
                
                remaining_items = [item for item in remaining_items if item.get(field_name, "") not in existing_titles]
                
                if remaining_items:
                    additional_items = random.sample(
                        remaining_items,
                        min(2 - len(category_recommendations), len(remaining_items))
                    )
                    for item in additional_items:
                        item_copy = item.copy()
                        item_copy["ranking_score"] = self._compute_ranking_score(item_copy, category, history) if user_id else self.BASE_SCORE
                        item_copy["why_would_you_like_this"] = self._generate_personalized_reason(item_copy, category, prompt, user_id, current_city)
                        category_recommendations.append(item_copy)
            
            # Limit to 5 per category and sort by ranking_score (highest first)
            category_recommendations = category_recommendations[:5]
            category_recommendations.sort(key=lambda x: x.get("ranking_score", self.BASE_SCORE), reverse=True)
            recommendations[category] = category_recommendations
        
        return recommendations
    
    def _generate_personalized_reason(self, item: Dict[str, Any], category: str, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> str:
        """Generate personalized reason why user would like this recommendation"""
        
        # Base reasons by category
        base_reasons = {
            "movies": [
                f"Based on your interest in {prompt.lower()}, this {item.get('genre', 'film')} offers compelling storytelling",
                f"The cast featuring {', '.join(item.get('cast', ['talented actors'])[:2])} aligns with quality performances you appreciate",
                f"This {item.get('year', 'recent')} film's themes resonate with your viewing preferences"
            ],
            "music": [
                f"This {item.get('genre', 'track')} matches your musical taste with its {item.get('mood', 'engaging')} energy",
                f"The artist {item.get('artist', 'musician')} creates the perfect soundtrack for your {current_city} lifestyle",
                f"With {item.get('monthly_listeners', 'many')} monthly listeners, this song captures the zeitgeist you're looking for"
            ],
            "places": [
                f"Located in {current_city}, this {item.get('type', 'location')} offers the perfect {item.get('preferred_time', 'anytime')} experience",
                f"With a {item.get('rating', 4.5)} rating and {item.get('user_ratings_total', 'many')} reviews, it's a local favorite",
                f"The {item.get('category', 'venue')} provides exactly what you're seeking in {current_city}"
            ],
            "events": [
                f"This {item.get('category', 'event')} happening in {current_city} perfectly matches your cultural interests",
                f"Organized by {item.get('organizer', 'top promoters')}, it promises a {item.get('duration', 'memorable')} experience",
                f"The {item.get('event_type', 'gathering')} offers {item.get('languages', ['multilingual'])[0]} accessibility in {current_city}"
            ]
        }
        
        # Add user-specific personalization if user_id exists
        if user_id:
            personalized_additions = [
                "your previous positive interactions suggest you'll love this",
                "based on your engagement history, this aligns perfectly with your preferences",
                "your activity pattern indicates this will be a great match",
                "considering your past choices, this recommendation scores highly for you"
            ]
            base_reason = random.choice(base_reasons.get(category, ["This recommendation suits your taste"]))
            personal_touch = random.choice(personalized_additions)
            return f"{base_reason}, and {personal_touch}."
        else:
            return random.choice(base_reasons.get(category, ["This recommendation suits your taste"])) + "."
    
    def _store_in_redis(self, user_id: str, data: Dict[str, Any]):
        """Store recommendations in Redis"""
        try:
            key = f"recommendations:{user_id}"
            # Store for 24 hours
            self.redis_client.setex(
                key,
                86400,  # 24 hours in seconds
                json.dumps(data, default=str)  # Handle datetime serialization
            )
            logger.info(f"Stored recommendations in Redis for user {user_id}")
            # Publish WebSocket notification via Redis Pub/Sub
            try:
                notify_payload = {
                    "type": "notification",
                    "user_id": str(user_id),
                    "message": {"content": "Your new recommendations are ready!"}
                }
                pub_client = redis.Redis(host=settings.redis_host, port=6379, db=0, decode_responses=True)
                pub_client.publish("notifications:user", json.dumps(notify_payload))
                logger.info(f"Published notification for user {user_id} on notifications:user")
            except Exception as pub_err:
                logger.error(f"Failed to publish notification for user {user_id}: {pub_err}")
        except Exception as e:
            logger.error(f"Error storing in Redis: {str(e)}")
            print('failed to store in redis')
    
    def get_recommendations_from_redis(self, user_id: str) -> Dict[str, Any]:
        """Retrieve recommendations from Redis"""
        try:
            key = f"recommendations:{user_id}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving from Redis: {str(e)}")
            return None
    
    def clear_recommendations(self, user_id: str = None):
        """Clear recommendations from Redis"""
        try:
            if user_id:
                key = f"recommendations:{user_id}"
                self.redis_client.delete(key)
                logger.info(f"Cleared recommendations for user {user_id}")
            else:
                # Clear all recommendation keys
                keys = self.redis_client.keys("recommendations:*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared all recommendations ({len(keys)} keys)")
        except Exception as e:
            logger.error(f"Error clearing recommendations: {str(e)}")


# Global instance
llm_service = LLMService()