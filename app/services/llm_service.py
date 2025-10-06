import json
import time
import random
import httpx
from typing import Dict, Any, List, Optional
from app.core.logging import get_logger, log_api_call, log_api_response, log_exception
from app.core.config import settings
import redis
from datetime import datetime, timezone
import math
from dataclasses import dataclass

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TWO_TOWER_TORCH_AVAILABLE = True
except Exception:
    TWO_TOWER_TORCH_AVAILABLE = False

logger = get_logger("llm_service")


class LLMService:
    """Service to generate recommendations from prompts and store in Redis"""
    
    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        logger.info("Initializing LLM service",
                   timeout=timeout,
                   redis_host=settings.redis_host,
                   redis_port=6379,
                   redis_db=1)
        
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=getattr(settings, "redis_port", 6379),
                db=1,  # Use different DB for recommendations
                password=getattr(settings, "redis_password", None),
                socket_connect_timeout=3,
                socket_timeout=5,
                health_check_interval=30,
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully",
                       service="llm_service",
                       redis_host=settings.redis_host)
        except Exception as e:
            logger.error("Failed to connect to Redis",
                        service="llm_service",
                        redis_host=settings.redis_host,
                        error=str(e))
            raise
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
        self.HALF_LIFE_DAYS = 30  # recency half-life for interactions
        # Two-Tower model (lazy init)
        self._two_tower_model = None
        self._two_tower_device = "cpu"

    def _validate_cached_payload(self, payload: Any) -> bool:
        """Basic schema checks for cached recommendation payloads."""
        try:
            if not isinstance(payload, dict):
                return False
            if "success" in payload and payload.get("success") is False:
                return True  # explicit failure is acceptable to cache briefly
            if "recommendations" not in payload or not isinstance(payload["recommendations"], dict):
                return False
            if "metadata" in payload and not isinstance(payload["metadata"], dict):
                return False
            return True
        except Exception:
            return False
    
    def _normalize_key(self, value: str) -> str:
        """Normalize string keys for comparison"""
        if not isinstance(value, str):
            return ""
        return ''.join(ch.lower() for ch in value if ch.isalnum() or ch.isspace()).strip()

    def _tokenize(self, value: str) -> List[str]:
        """Tokenize normalized value into words for partial matching."""
        norm = self._normalize_key(value)
        return [t for t in norm.split() if t]

    def _recency_weight(self, iso_timestamp: str) -> float:
        """Compute exponential recency weight in (0,1], newer -> closer to 1."""
        try:
            if iso_timestamp and isinstance(iso_timestamp, str):
                ts = iso_timestamp.replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                age_days = max(0.0, (now - dt).total_seconds() / 86400.0)
                lam = math.log(2) / max(1.0, float(self.HALF_LIFE_DAYS))
                weight = math.exp(-lam * age_days)
                return max(0.1, min(1.0, weight))
        except Exception:
            pass
        return 0.5

    # ---------------- Two-Tower embedding utilities (user/item encoders) ---------------- #
    def _hashing_vectorizer(self, text: str, dim: int = 128) -> List[float]:
        """Simple deterministic hashing vectorizer for text into fixed-size vector.
        Avoids external deps; suitable for similarity features.
        """
        if not isinstance(text, str) or not text:
            return [0.0] * dim
        vec = [0.0] * dim
        for token in text.lower().split():
            h = hash(token) % dim
            sign = 1.0 if (hash(token + "_") % 2 == 0) else -1.0
            vec[h] += sign
        return vec

    def _l2_normalize(self, vec: List[float]) -> List[float]:
        mag = math.sqrt(sum(v * v for v in vec))
        if mag == 0.0:
            return vec
        return [v / mag for v in vec]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def _bucketize(self, value: Optional[float], thresholds: List[float]) -> int:
        """Return bucket index for numeric value given ascending thresholds."""
        if value is None:
            return -1
        for idx, th in enumerate(thresholds):
            if value < th:
                return idx
        return len(thresholds)

    def _build_user_embedding(
        self,
        user_profile: Optional[Dict[str, Any]],
        location_data: Optional[Dict[str, Any]],
        history: Dict[str, List[Dict[str, str]]],
        interaction_data: Optional[Dict[str, Any]]
    ) -> List[float]:
        dim = 128
        accum = [0.0] * dim

        # Profile-based signals
        if user_profile:
            age = user_profile.get("age")
            if isinstance(age, (int, float)):
                age_bucket = self._bucketize(float(age), [18, 25, 35, 45, 55, 65])
                age_vec = self._hashing_vectorizer(f"age_bucket_{age_bucket}", dim)
                accum = [a + b for a, b in zip(accum, age_vec)]
            interests = user_profile.get("interests", [])
            if isinstance(interests, list) and interests:
                txt = " ".join(str(i) for i in interests[:20])
                accum = [a + b for a, b in zip(accum, self._hashing_vectorizer("interests " + txt, dim))]
            # Keywords from preferences (legacy)
            prefs = user_profile.get("preferences", {})
            kw_values = []
            try:
                kw = prefs.get("Keywords (legacy)", {})
                for ev in kw.get("example_values", [])[:20]:
                    val = ev.get("value")
                    if val:
                        kw_values.append(str(val))
            except Exception:
                pass
            if kw_values:
                accum = [a + b for a, b in zip(accum, self._hashing_vectorizer("keywords " + " ".join(kw_values), dim))]

        # Location-based signals
        if location_data:
            cur = location_data.get("current_location")
            if isinstance(cur, dict):
                city = cur.get("city") or cur.get("name") or ""
            else:
                city = cur if isinstance(cur, str) else ""
            if city:
                accum = [a + b for a, b in zip(accum, self._hashing_vectorizer("city " + city, dim))]

        # Interaction history signals
        action_weights = {
            'liked': 2.0, 'saved': 1.5, 'shared': 1.2, 'clicked': 0.8,
            'view': 0.4, 'ignored': -1.0, 'disliked': -1.5
        }
        for category, items in history.items():
            for inter in items[:200]:
                text_bits = []
                if category in ["movies", "music"]:
                    text_bits.append(inter.get("title", ""))
                    text_bits.append(inter.get("genre", ""))
                else:
                    text_bits.append(inter.get("name", ""))
                    text_bits.append(inter.get("type", "") if category == "places" else inter.get("category", ""))
                action = inter.get("action", "view").lower()
                weight = action_weights.get(action, 0.2)
                rec = self._recency_weight(inter.get("timestamp", ""))
                v = self._hashing_vectorizer(" ".join(text_bits), dim)
                accum = [a + weight * rec * b for a, b in zip(accum, v)]

        # Engagement level (optional)
        if interaction_data:
            es = interaction_data.get("engagement_score")
            if isinstance(es, (int, float)):
                bucket = self._bucketize(float(es), [0.2, 0.4, 0.6, 0.8])
                accum = [a + b for a, b in zip(accum, self._hashing_vectorizer(f"engagement_{bucket}", dim))]

        return self._l2_normalize(accum)

    def _build_item_embedding(self, item: Dict[str, Any], category: str) -> List[float]:
        dim = 128
        parts: List[str] = []
        # Common textual fields
        parts.append(str(item.get("title") or item.get("name") or ""))
        parts.append(str(item.get("description", "")))
        genre_key = {"movies": "genre", "music": "genre", "places": "type", "events": "category"}.get(category, "genre")
        parts.append(str(item.get(genre_key, "")))
        # Keywords
        if isinstance(item.get("keywords"), list):
            parts.append(" ".join(map(str, item.get("keywords"))))

        vec = self._hashing_vectorizer(" ".join(parts), dim)

        # Numeric/popularity features via bucket tags
        # rating
        rating_raw = item.get("rating")
        try:
            rating_val = float(str(rating_raw).replace('/10', '').replace('/5', '')) if rating_raw is not None else None
        except Exception:
            rating_val = None
        if rating_val is not None:
            rb = self._bucketize(rating_val, [2, 3, 3.5, 4, 4.5, 8, 9])
            vec = [v + u for v, u in zip(vec, self._hashing_vectorizer(f"rating_bucket_{rb}", dim))]

        # listeners/popularity
        listeners_raw = item.get("monthly_listeners")
        try:
            listeners = float(str(listeners_raw).rstrip('M').replace(',', '')) if listeners_raw is not None and 'M' in str(listeners_raw) else None
        except Exception:
            listeners = None
        if listeners is not None:
            lb = self._bucketize(listeners, [1, 5, 10, 25, 50, 100])
            vec = [v + u for v, u in zip(vec, self._hashing_vectorizer(f"listeners_bucket_{lb}", dim))]

        # distance/location relevance
        dist = item.get("distance_from_user")
        if isinstance(dist, (int, float)):
            db = self._bucketize(float(dist), [1, 5, 10, 20, 50, 100, 500])
            vec = [v + u for v, u in zip(vec, self._hashing_vectorizer(f"distance_bucket_{db}", dim))]

        # recency
        now = datetime.now(timezone.utc)
        recency_val = None
        if category == "movies":
            try:
                y = int(item.get("year")) if item.get("year") else None
                if y:
                    recency_val = max(0, now.year - y)
            except Exception:
                recency_val = None
        elif category == "music":
            try:
                y = int(item.get("release_year")) if item.get("release_year") else None
                if y:
                    recency_val = max(0, now.year - y)
            except Exception:
                recency_val = None
        elif category == "events":
            try:
                date_str = item.get("date")
                if date_str:
                    d = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
                    if d.tzinfo is None:
                        d = d.replace(tzinfo=timezone.utc)
                    recency_val = (d - now).days
            except Exception:
                recency_val = None
        if recency_val is not None:
            rb = self._bucketize(float(recency_val), [0, 7, 30, 90, 365, 5 * 365])
            vec = [v + u for v, u in zip(vec, self._hashing_vectorizer(f"recency_bucket_{rb}", dim))]

        return self._l2_normalize(vec)

    def _category_prior(self, item: Dict[str, Any], category: str) -> float:
        """Small prior boost based on intrinsic item quality/popularity."""
        try:
            if category in ["movies", "music"]:
                # rating often string; monthly_listeners may exist for music
                rating_raw = item.get("rating")
                rating = float(rating_raw) if isinstance(rating_raw, (int, float, str)) and str(rating_raw).replace('.', '', 1).isdigit() else None
                listeners_raw = item.get("monthly_listeners")
                listeners = float(str(listeners_raw).replace('M', '').replace(',', '')) if listeners_raw and isinstance(listeners_raw, (int, float, str)) and str(listeners_raw) else None
                prior = 0.0
                if rating is not None:
                    prior += (max(0.0, min(10.0, rating)) - 5.0) / 50.0  # up to ±0.1
                if listeners is not None:
                    prior += min(0.1, listeners / 1e7)  # cap at 0.1
                return prior
            if category in ["places", "events"]:
                rating_raw = item.get("rating")
                rating = float(rating_raw) if isinstance(rating_raw, (int, float, str)) and str(rating_raw).replace('.', '', 1).isdigit() else None
                total_raw = item.get("user_ratings_total")
                total = float(total_raw) if isinstance(total_raw, (int, float)) else None
                prior = 0.0
                if rating is not None:
                    prior += (max(0.0, min(5.0, rating)) - 3.0) / 20.0  # up to ±0.1
                if total is not None:
                    prior += min(0.1, total / 5000.0)
                return prior
        except Exception:
            return 0.0
        return 0.0

    def _setup_demo_data(self) -> None:
        """Setup demo data (placeholder for test compatibility)"""
        logger.info("Setting up demo data")
        return None

    def _generate_demo_recommendations(self, prompt: str) -> Dict[str, List[Dict]]:
        """Generate demo recommendations for testing purposes"""
        logger.info(f"Generating demo recommendations for prompt: {prompt}")
        return {
            "movies": [
                {"title": "Demo Movie 1", "genre": "Action", "year": "2023"},
                {"title": "Demo Movie 2", "genre": "Drama", "year": "2022"},
            ],
            "music": [
                {"title": "Demo Song 1", "artist": "Artist 1", "genre": "Pop"},
                {"title": "Demo Song 2", "artist": "Artist 2", "genre": "Rock"},
            ],
            "places": [
                {"name": "Demo Place 1", "type": "Park", "rating": 4.5},
                {"name": "Demo Place 2", "type": "Museum", "rating": 4.0},
            ],
            "events": [
                {"name": "Demo Event 1", "date": "2025-01-01", "venue": "Venue 1"},
                {"name": "Demo Event 2", "date": "2025-02-01", "venue": "Venue 2"},
            ]
        }

    def _get_user_interaction_history(self, user_id: str) -> Dict[str, List[Dict[str, str]]]:
        """
        Mock retrieval of user's historical interactions from a table.
        Returns interaction data with proper field matching for each category.
        """
        seed = sum(ord(c) for c in user_id) if user_id else 0
        rnd = random.Random(seed)
        
        interaction_types = ["view", "liked", "saved", "shared", "clicked", "ignored", "disliked"]
        
        history = {
            "movies": [
                {"title": "Inception", "genre": "Science Fiction/Action", "action": "liked", "timestamp": "2024-08-15T10:30:00Z"},
                {"title": "The Dark Knight", "genre": "Action/Crime", "action": "view", "timestamp": "2024-08-14T15:20:00Z"},
                {"title": "Vicky Cristina Barcelona", "genre": "Drama/Romance", "action": "ignored", "timestamp": "2024-08-13T09:45:00Z"},
                {"title": "The Shawshank Redemption", "genre": "Drama", "action": rnd.choice(["liked", "view", "saved"]), "timestamp": "2024-08-12T20:10:00Z"},
                {"title": "All About My Mother", "genre": "Drama", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-11T14:30:00Z"},
            ],
            "music": [
                {"title": "Blinding Lights", "genre": "Pop/Electronic", "action": "liked", "timestamp": "2024-08-16T12:00:00Z"},
                {"title": "Barcelona", "genre": "Pop", "action": "saved", "timestamp": "2024-08-15T18:45:00Z"},
                {"title": "Shape of You", "genre": "Pop", "action": rnd.choice(["view", "liked", "shared"]), "timestamp": "2024-08-14T11:20:00Z"},
                {"title": "Mediterráneo", "genre": "Folk", "action": rnd.choice(["ignored", "view"]), "timestamp": "2024-08-13T16:30:00Z"},
                {"title": "Dance Monkey", "genre": "Pop", "action": rnd.choice(["view", "disliked"]), "timestamp": "2024-08-12T13:15:00Z"},
            ],
            "places": [
                {"name": "Sagrada Família", "type": "attraction", "action": "liked", "timestamp": "2024-08-17T09:00:00Z"},
                {"name": "Eiffel Tower", "type": "attraction", "action": "view", "timestamp": "2024-08-16T14:30:00Z"},
                {"name": "Park Güell", "type": "park", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-15T11:45:00Z"},
                {"name": "Big Ben", "type": "attraction", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T17:20:00Z"},
                {"name": "Colosseum", "type": "attraction", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-13T10:10:00Z"},
            ],
            "events": [
                {"name": "Primavera Sound", "category": "music", "action": "liked", "timestamp": "2024-08-18T08:30:00Z"},
                {"name": "Coachella Valley Music and Arts Festival", "category": "music", "action": "ignored", "timestamp": "2024-08-17T19:15:00Z"},
                {"name": "La Mercè Festival", "category": "festival", "action": rnd.choice(["liked", "saved"]), "timestamp": "2024-08-16T15:45:00Z"},
                {"name": "Oktoberfest", "category": "festival", "action": rnd.choice(["view", "clicked"]), "timestamp": "2024-08-15T12:30:00Z"},
                {"name": "Mardi Gras", "category": "festival", "action": rnd.choice(["view", "ignored"]), "timestamp": "2024-08-14T16:00:00Z"},
            ],
        }
        
        genres_list = {
            "movies": ["Action", "Drama", "Comedy", "Science Fiction", "Adventure"],
            "music": ["Pop", "Electronic", "R&B", "Singer-Songwriter", "Folk"],
            "places": ["attraction", "restaurant", "park", "museum", "trail"],
            "events": ["music", "sports", "art", "festival"]
        }
        
        for category in history:
            if rnd.random() > 0.3:
                extra_interactions = rnd.randint(1, 3)
                for _ in range(extra_interactions):
                    action = rnd.choice(interaction_types)
                    timestamp = f"2024-08-{rnd.randint(10, 18):02d}T{rnd.randint(8, 20):02d}:{rnd.randint(0, 59):02d}:00Z"
                    genre_field = "genre" if category in ["movies", "music"] else "type" if category == "places" else "category"
                    item_name = "title" if category in ["movies", "music"] else "name"
                    item_value = f"Random {category.capitalize()} {rnd.randint(1, 100)}"
                    genre_value = rnd.choice(genres_list[category])
                    history[category].append({item_name: item_value, genre_field: genre_value, "action": action, "timestamp": timestamp})
        
        return history

    # ---------------- PyTorch Two-Tower Model Definitions ---------------- #
    def _torch_available(self) -> bool:
        return bool(TWO_TOWER_TORCH_AVAILABLE)

    def _hash_tokens(self, text: str, vocab_size: int) -> List[int]:
        if not isinstance(text, str) or not text:
            return []
        tokens = [t for t in text.lower().split() if t]
        return [abs(hash(t)) % vocab_size for t in tokens[:256]]

    def _extract_user_numeric_features(
        self,
        user_profile: Dict[str, Any],
        location_data: Dict[str, Any],
        interaction_data: Dict[str, Any],
        history: Dict[str, List[Dict[str, str]]]
    ) -> List[float]:
        # Stable ordering of features
        age = user_profile.get("age")
        age_norm = float(age) / 100.0 if isinstance(age, (int, float)) else 0.0
        engagement = interaction_data.get("engagement_score") if isinstance(interaction_data, dict) else None
        engagement = float(engagement) if isinstance(engagement, (int, float)) else 0.0
        # History sizes
        h_movies = len(history.get("movies", []))
        h_music = len(history.get("music", []))
        h_places = len(history.get("places", []))
        h_events = len(history.get("events", []))
        total_h = h_movies + h_music + h_places + h_events
        h_movies_n = min(1.0, h_movies / 200.0)
        h_music_n = min(1.0, h_music / 200.0)
        h_places_n = min(1.0, h_places / 200.0)
        h_events_n = min(1.0, h_events / 200.0)
        total_h_n = min(1.0, total_h / 800.0)
        # Location presence flags
        cur_loc = location_data.get("current_location") if isinstance(location_data, dict) else None
        has_city = 1.0 if (isinstance(cur_loc, dict) and cur_loc.get("city")) or isinstance(cur_loc, str) else 0.0
        return [age_norm, engagement, h_movies_n, h_music_n, h_places_n, h_events_n, total_h_n, has_city]

    def _extract_item_numeric_features(self, item: Dict[str, Any], category: str) -> List[float]:
        def to_float(value: Any) -> Optional[float]:
            try:
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                s = str(value)
                s = s.replace(",", "").replace("$", "").replace("€", "")
                s = s.replace("/10", "").replace("/5", "")
                if s.endswith("M"):
                    return float(s[:-1]) * 1e6
                return float(s)
            except Exception:
                return None

        rating = to_float(item.get("rating"))
        rating_scale = 10.0 if category in ["movies", "music"] else 5.0
        rating_n = max(0.0, min(1.0, (rating or 0.0) / rating_scale))
        box_office = to_float(item.get("box_office")) or 0.0
        box_office_n = min(1.0, (math.log1p(max(0.0, box_office)) / 20.0))
        capacity = to_float(item.get("capacity")) or 0.0
        capacity_n = min(1.0, capacity / 100000.0)
        listeners = to_float(item.get("monthly_listeners")) or 0.0
        listeners_n = min(1.0, math.log1p(listeners) / 20.0)
        chart_pos = to_float(item.get("chart_position"))
        chart_pos_n = 1.0 - min(1.0, max(0.0, (chart_pos or 100.0) / 100.0))
        price_min = to_float(item.get("price_min")) or 0.0
        price_min_n = 1.0 - min(1.0, price_min / 500.0)
        age_rating = to_float(item.get("age_rating"))
        age_restriction = to_float(item.get("age_restriction"))
        age_gate_n = 1.0 - min(1.0, ((age_rating or age_restriction or 0.0) / 21.0))
        dist = to_float(item.get("distance_from_user")) or 0.0
        dist_n = 1.0 - min(1.0, dist / 100.0)
        return [rating_n, box_office_n, capacity_n, listeners_n, chart_pos_n, price_min_n, age_gate_n, dist_n]

    def _preference_alignment_boost(self, item: Dict[str, Any], category: str, user_profile: Dict[str, Any]) -> float:
        """Compute a deterministic preference-alignment boost in [0, 0.2].
        Emphasizes 'very likely' traits by scanning item metadata fields.
        """
        try:
            prefs_texts: List[str] = []
            # gather declared interests from profile
            interests = (user_profile or {}).get("interests")
            if isinstance(interests, list):
                prefs_texts.extend([str(x).lower() for x in interests])
            # also scan preferences free-form keys/values
            prefs = (user_profile or {}).get("preferences", {})
            if isinstance(prefs, dict):
                prefs_texts.extend([str(k).lower() for k in list(prefs.keys())[:20]])
                for v in list(prefs.values())[:20]:
                    if isinstance(v, (str, int, float)):
                        prefs_texts.append(str(v).lower())

            # Extract item text pieces
            parts: List[str] = []
            parts.append(str(item.get("title") or item.get("name") or ""))
            parts.append(str(item.get("description", "")))
            genre_key = {"movies": "genre", "music": "genre", "places": "type", "events": "category"}.get(category, "genre")
            parts.append(str(item.get(genre_key, "")))
            if isinstance(item.get("keywords"), list):
                parts.extend([str(k) for k in item.get("keywords")])
            item_text = (" ".join(parts)).lower()

            # Heuristic: count strong matches of salient cues
            strong_terms = [
                "african-american", "hispanic", "latin", "latino", "afrobeats", "jazz", "urban",
                "dance", "dancing", "sunset", "solitary", "minimalist", "museum", "park",
                "action", "drama", "science fiction", "festival"
            ]
            # Expand with profile-derived cues (words following 'very likely') if present
            for t in list(prefs_texts):
                if "very likely" in t:
                    strong_terms.append(t.replace("very likely", "").strip())

            match_score = 0.0
            for term in strong_terms:
                t = term.strip()
                if not t:
                    continue
                if t in item_text:
                    match_score += 1.0

            # Cap and scale. Multiple matches → stronger boost
            match_score = min(match_score, 5.0)
            # Map 0..5 → 0..0.2
            return 0.04 * match_score
        except Exception:
            return 0.0

    # Define placeholders first to satisfy static analysis; override with real impls if torch is available
    class HashingTextEncoder:  # type: ignore
        pass

    class UserTower:  # type: ignore
        pass

    class ItemTower:  # type: ignore
        pass

    class TwoTowerModel:  # type: ignore
        pass

    if TWO_TOWER_TORCH_AVAILABLE:
        class HashingTextEncoder(nn.Module):  # type: ignore
            def __init__(self, vocab_size: int, embed_dim: int):
                super().__init__()
                self.emb = nn.EmbeddingBag(vocab_size, embed_dim, mode="mean")

            def forward(self, token_indices: torch.Tensor) -> torch.Tensor:
                if token_indices is None or token_indices.numel() == 0:
                    return torch.zeros(self.emb.embedding_dim, device=next(self.parameters()).device)
                offsets = torch.tensor([0], device=token_indices.device, dtype=torch.long)
                return self.emb(token_indices, offsets).squeeze(0)

        class UserTower(nn.Module):  # type: ignore
            def __init__(self, vocab_size: int = 50000, text_embed_dim: int = 64, numeric_dim: int = 8, out_dim: int = 64):
                super().__init__()
                self.text = HashingTextEncoder(vocab_size, text_embed_dim)  # type: ignore[name-defined]
                self.numeric = nn.Sequential(
                    nn.Linear(numeric_dim, 64), nn.ReLU(), nn.Linear(64, out_dim)
                )
                self.proj = nn.Linear(text_embed_dim + out_dim, out_dim)

            def forward(self, token_indices: torch.Tensor, numeric: torch.Tensor) -> torch.Tensor:
                t = self.text(token_indices)
                n = self.numeric(numeric)
                x = torch.cat([t, n], dim=-1)
                x = self.proj(x)
                return F.normalize(x, p=2, dim=-1)

        class ItemTower(nn.Module):  # type: ignore
            def __init__(self, vocab_size: int = 50000, text_embed_dim: int = 64, numeric_dim: int = 8, out_dim: int = 64):
                super().__init__()
                self.text = HashingTextEncoder(vocab_size, text_embed_dim)  # type: ignore[name-defined]
                self.numeric = nn.Sequential(
                    nn.Linear(numeric_dim, 64), nn.ReLU(), nn.Linear(64, out_dim)
                )
                self.proj = nn.Linear(text_embed_dim + out_dim, out_dim)

            def forward(self, token_indices: torch.Tensor, numeric: torch.Tensor) -> torch.Tensor:
                t = self.text(token_indices)
                n = self.numeric(numeric)
                x = torch.cat([t, n], dim=-1)
                x = self.proj(x)
                return F.normalize(x, p=2, dim=-1)

        class TwoTowerModel(nn.Module):  # type: ignore
            def __init__(self, vocab_size: int = 50000, text_embed_dim: int = 64, user_numeric_dim: int = 8, item_numeric_dim: int = 8, out_dim: int = 64):
                super().__init__()
                self.user = UserTower(vocab_size, text_embed_dim, user_numeric_dim, out_dim)  # type: ignore[name-defined]
                self.item = ItemTower(vocab_size, text_embed_dim, item_numeric_dim, out_dim)  # type: ignore[name-defined]

            def forward(self, u_tokens: torch.Tensor, u_numeric: torch.Tensor, i_tokens: torch.Tensor, i_numeric: torch.Tensor) -> torch.Tensor:
                ue = self.user(u_tokens, u_numeric)
                ie = self.item(i_tokens, i_numeric)
                sim = F.cosine_similarity(ue, ie, dim=-1)  # [-1, 1]
                return sim

    def _init_two_tower_if_needed(self) -> None:
        if not self._torch_available():
            return
        if self._two_tower_model is None:
            try:
                device = "cuda" if hasattr(torch, "cuda") and torch.cuda.is_available() else "cpu"
                self._two_tower_device = device
                model_cls = globals().get("TwoTowerModel")
                if model_cls is None:
                    return
                self._two_tower_model = model_cls(
                    vocab_size=50000, text_embed_dim=64, user_numeric_dim=8, item_numeric_dim=8, out_dim=64
                ).to(device)
                self._two_tower_model.eval()
                logger.info("Initialized Two-Tower model", device=device)
            except Exception as e:
                logger.warning("Failed to initialize Two-Tower model", error=str(e))
                self._two_tower_model = None

    def train_two_tower_mock(
        self,
        user_id: str,
        catalog: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        epochs: int = 1,
        lr: float = 1e-3,
        negatives: int = 2
    ) -> None:
        """Optional mock training using interaction history as positives and sampled negatives.
        This is a lightweight, single-sample-at-a-time trainer intended for quick bootstrapping.
        """
        if not self._torch_available():
            logger.info("PyTorch not available; skipping mock training")
            return
        self._init_two_tower_if_needed()
        if self._two_tower_model is None:
            return
        model = self._two_tower_model
        model.train()
        opt = torch.optim.Adam(model.parameters(), lr=lr)

        history = self._get_user_interaction_history(user_id)

        # Build a simple catalog if not provided
        if catalog is None:
            catalog = {k: v for k, v in history.items()}  # very small; real use should pass a richer catalog

        def sample_negatives(cat: str, k: int) -> List[Dict[str, Any]]:
            pool = catalog.get(cat, [])
            if not pool:
                return []
            return random.sample(pool, min(k, len(pool)))

        for _ in range(epochs):
            for cat, items in history.items():
                for pos in items:
                    try:
                        # Positive sample featurization
                        u_text = []
                        # Collect user text signals
                        interests = (history.get("movies", []) + history.get("music", []))[:10]
                        for it in interests:
                            title = it.get("title") or it.get("name") or ""
                            u_text.extend(self._hash_tokens(title, 50000))
                        u_num = torch.tensor(self._extract_user_numeric_features({}, {}, {}, history), dtype=torch.float32)
                        i_text = []
                        title = pos.get("title") or pos.get("name") or ""
                        genre = pos.get("genre") or pos.get("type") or pos.get("category") or ""
                        i_text.extend(self._hash_tokens(title + " " + genre, 50000))
                        i_num = torch.tensor(self._extract_item_numeric_features(pos, cat), dtype=torch.float32)

                        # Move to device
                        device = self._two_tower_device
                        u_tokens = torch.tensor(u_text if u_text else [0], dtype=torch.long, device=device)
                        u_num = u_num.to(device)
                        i_tokens = torch.tensor(i_text if i_text else [0], dtype=torch.long, device=device)
                        i_num = i_num.to(device)

                        # Positive label 1.0
                        sim_pos = model(u_tokens, u_num, i_tokens, i_num)
                        loss = (1.0 - sim_pos).clamp_min(0).mean()  # encourage high cosine

                        # Negatives
                        for neg in sample_negatives(cat, negatives):
                            n_text = []
                            n_title = neg.get("title") or neg.get("name") or ""
                            n_genre = neg.get("genre") or neg.get("type") or neg.get("category") or ""
                            n_text.extend(self._hash_tokens(n_title + " " + n_genre, 50000))
                            n_num = torch.tensor(self._extract_item_numeric_features(neg, cat), dtype=torch.float32).to(device)
                            n_tokens = torch.tensor(n_text if n_text else [0], dtype=torch.long, device=device)
                            sim_neg = model(u_tokens, u_num, n_tokens, n_num)
                            loss = loss + (sim_neg.clamp_min(-1) + 1.0).mean()  # push negatives down

                        opt.zero_grad()
                        loss.backward()
                        opt.step()
                    except Exception:
                        continue
        model.eval()

    def _compute_ranking_score(
        self,
        item: Dict[str, Any],
        category: str,
        history: Dict[str, List[Dict[str, str]]],
        user_profile: Dict[str, Any] = None,
        location_data: Dict[str, Any] = None,
        interaction_data: Dict[str, Any] = None
    ) -> float:
        """Compute a ranking score using a PyTorch Two-Tower model if available.

        Falls back to the deterministic two-tower hashing encoder if PyTorch or model is unavailable.
        Keeps output compatible with existing downstream normalization (~[0.1, 1.5]).
        """
        try:
            # Prefer PyTorch model if available
            if self._torch_available():
                self._init_two_tower_if_needed()
                if self._two_tower_model is not None:
                    device = self._two_tower_device

                    # Build user tokens (from profile interests, prefs, location, and history titles/genres)
                    user_tokens: List[int] = []
                    try:
                        if isinstance(user_profile, dict):
                            interests = user_profile.get("interests", [])
                            if isinstance(interests, list):
                                user_tokens.extend(self._hash_tokens(" ".join(map(str, interests)), 50000))
                            prefs = user_profile.get("preferences", {})
                            if isinstance(prefs, dict):
                                user_tokens.extend(self._hash_tokens(" ".join(map(str, prefs.keys())), 50000))
                        if isinstance(location_data, dict):
                            city = ""
                            cur = location_data.get("current_location")
                            if isinstance(cur, dict):
                                city = cur.get("city") or cur.get("name") or ""
                            elif isinstance(cur, str):
                                city = cur
                            if city:
                                user_tokens.extend(self._hash_tokens(city, 50000))
                        for cat, items in (history or {}).items():
                            for inter in items[:50]:
                                title = inter.get("title") or inter.get("name") or ""
                                genre = inter.get("genre") or inter.get("type") or inter.get("category") or ""
                                user_tokens.extend(self._hash_tokens(title + " " + genre, 50000))
                    except Exception:
                        pass

                    # Build user numeric features
                    u_numeric_list = self._extract_user_numeric_features(
                        user_profile or {}, location_data or {}, interaction_data or {}, history or {}
                    )

                    # Build item tokens and numeric features
                    item_tokens: List[int] = []
                    try:
                        title = item.get("title") or item.get("name") or ""
                        desc = item.get("description", "")
                        genre_key = {"movies": "genre", "music": "genre", "places": "type", "events": "category"}.get(category, "genre")
                        genre = item.get(genre_key, "")
                        kw = item.get("keywords")
                        kw_text = " ".join(map(str, kw)) if isinstance(kw, list) else ""
                        cat_text = str(category or "")
                        item_tokens.extend(self._hash_tokens(" ".join([title, desc, genre, kw_text, cat_text]), 50000))
                    except Exception:
                        pass
                    i_numeric_list = self._extract_item_numeric_features(item or {}, category)

                    # Convert to tensors
                    u_tokens_t = torch.tensor(user_tokens if user_tokens else [0], dtype=torch.long, device=device)
                    i_tokens_t = torch.tensor(item_tokens if item_tokens else [0], dtype=torch.long, device=device)
                    u_num_t = torch.tensor(u_numeric_list, dtype=torch.float32, device=device)
                    i_num_t = torch.tensor(i_numeric_list, dtype=torch.float32, device=device)

                    with torch.no_grad():
                        sim = self._two_tower_model(u_tokens_t, u_num_t, i_tokens_t, i_num_t).item()  # [-1, 1]
                    sim01 = (sim + 1.0) / 2.0  # [0, 1]

                    # Optional small priors as before
                    prior = 0.0
                    rating_raw = item.get("rating")
                    try:
                        rating_val = float(str(rating_raw).replace("/10", "").replace("/5", "")) if rating_raw is not None else None
                        if rating_val is not None:
                            scale = 10.0 if category in ["movies", "music"] else 5.0
                            prior += min(0.1, max(0.0, rating_val) / scale * 0.1)
                    except Exception:
                        pass
                    dist = item.get("distance_from_user")
                    if isinstance(dist, (int, float)) and dist >= 0:
                        if dist < 5:
                            prior += 0.08
                        elif dist < 20:
                            prior += 0.04

                    # Preference alignment booster
                    pref_boost = self._preference_alignment_boost(item or {}, category, user_profile or {})
                    score = 0.1 + 1.4 * sim01 + prior + pref_boost
                    return max(0.0, min(1.5, score))

            # Fallback to deterministic two-tower hashing encoder-based similarity
            user_embed = self._build_user_embedding(
                user_profile or {},
                location_data or {},
                history or {},
                interaction_data or {}
            )
            item_embed = self._build_item_embedding(item or {}, category)
            sim = self._cosine_similarity(user_embed, item_embed)
            sim01 = (sim + 1.0) / 2.0
            prior = 0.0
            rating_raw = item.get("rating")
            try:
                rating_val = float(str(rating_raw).replace("/10", "").replace("/5", "")) if rating_raw is not None else None
                if rating_val is not None:
                    scale = 10.0 if category in ["movies", "music"] else 5.0
                    prior += min(0.1, max(0.0, rating_val) / scale * 0.1)
            except Exception:
                pass
            dist = item.get("distance_from_user")
            if isinstance(dist, (int, float)) and dist >= 0:
                if dist < 5:
                    prior += 0.08
                elif dist < 20:
                    prior += 0.04
            pref_boost = self._preference_alignment_boost(item or {}, category, user_profile or {})
            score = 0.1 + 1.4 * sim01 + prior + pref_boost
            return max(0.0, min(1.5, score))
        except Exception:
            return 0.5

    async def generate_recommendations(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, Any]:
        """
        Generate recommendations based on prompt and store in Redis
        """
        try:
            logger.info(f"Generating recommendations for prompt: {prompt[:100]}...")
            
            start_time = time.time()
            
            recommendations = await self._call_llm_api(prompt, user_id, current_city)
            
            processing_time = time.time() - start_time
            
            response = {
                "success": True,
                "prompt": prompt,
                "user_id": user_id,
                "current_city": current_city,
                "generated_at": time.time(),
                "processing_time": processing_time,
                "recommendations": recommendations,
                "metadata": {
                    "total_recommendations": sum(len(cat) for cat in recommendations.values()) if recommendations else 0,
                    "categories": list(recommendations.keys()) if recommendations else [],
                    "model": "llm-api-v1.0",
                    "ranking_enabled": user_id is not None
                }
            }
            
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
    
    async def _call_llm_api(self, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> Dict[str, List[Dict]]:
        """
        Call the actual LLM API to generate recommendations
        """
        start_time = time.time()
        
        # Log API call initiation
        log_api_call(
            service_name="llm_api",
            endpoint="/process-text",
            method="POST",
            user_id=user_id,
            prompt_length=len(prompt),
            provider=settings.recommendation_api_provider
        )
        
        try:
            payload = {
                "text": prompt,
                "provider": settings.recommendation_api_provider
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.recommendation_api_url}/process-text",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                result = response.json()
                raw_result = result.get("result")
                
                response_time = time.time() - start_time
                
                if raw_result is None:
                    logger.warning("Empty result field from LLM API",
                                 user_id=user_id,
                                 response_time_ms=response_time * 1000)
                    log_api_response("llm_api", "/process-text", False, 
                                   status_code=response.status_code, 
                                   response_time=response_time,
                                   user_id=user_id,
                                   error="empty_result")
                    return self._get_fallback_recommendations()
                
                if isinstance(raw_result, dict):
                    log_api_response("llm_api", "/process-text", True,
                                   status_code=response.status_code,
                                   response_time=response_time,
                                   user_id=user_id)
                    return self._process_llm_recommendations(raw_result, user_id, current_city)
                
                if isinstance(raw_result, str):
                    parsed = self._robust_parse_json(raw_result)
                    if parsed is not None:
                        log_api_response("llm_api", "/process-text", True,
                                       status_code=response.status_code,
                                       response_time=response_time,
                                       user_id=user_id)
                        return self._process_llm_recommendations(parsed, user_id, current_city)
                    
                    logger.info("LLM response is not valid JSON, attempting text parsing",
                               user_id=user_id,
                               response_time_ms=response_time * 1000)
                    recommendations = self._parse_text_response(raw_result)
                    log_api_response("llm_api", "/process-text", True,
                                   status_code=response.status_code,
                                   response_time=response_time,
                                   user_id=user_id,
                                   parsing_method="text")
                    return self._process_llm_recommendations(recommendations, user_id, current_city)
                
                logger.error("Unexpected type for LLM result",
                           user_id=user_id,
                           result_type=type(raw_result).__name__,
                           response_time_ms=response_time * 1000)
                log_api_response("llm_api", "/process-text", False,
                               status_code=response.status_code,
                               response_time=response_time,
                               user_id=user_id,
                               error="unexpected_result_type")
                return self._get_fallback_recommendations()
                    
        except httpx.TimeoutException as e:
            response_time = time.time() - start_time
            logger.error("Timeout calling LLM API",
                        user_id=user_id,
                        timeout_seconds=self.timeout,
                        response_time_ms=response_time * 1000)
            log_api_response("llm_api", "/process-text", False,
                           response_time=response_time,
                           user_id=user_id,
                           error="timeout")
            return self._get_fallback_recommendations()
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            logger.error("HTTP error calling LLM API",
                        user_id=user_id,
                        status_code=e.response.status_code,
                        response_text=e.response.text,
                        response_time_ms=response_time * 1000)
            log_api_response("llm_api", "/process-text", False,
                           status_code=e.response.status_code,
                           response_time=response_time,
                           user_id=user_id,
                           error="http_error")
            return self._get_fallback_recommendations()
        except Exception as e:
            response_time = time.time() - start_time
            logger.error("Unexpected error calling LLM API",
                        user_id=user_id,
                        error=str(e),
                        response_time_ms=response_time * 1000)
            log_exception("llm_service", e, {"user_id": user_id, "response_time": response_time})
            log_api_response("llm_api", "/process-text", False,
                           response_time=response_time,
                           user_id=user_id,
                           error="unexpected_error")
            return self._get_fallback_recommendations()
    
    def _parse_text_response(self, response_text: str) -> Dict[str, List[Dict]]:
        """Parse text response from LLM and convert to structured format"""
        try:
            recommendations = {
                "movies": [],
                "music": [],
                "places": [],
                "events": []
            }
            return recommendations
        except Exception as e:
            logger.error(f"Error parsing text response: {str(e)}")
            return self._get_fallback_recommendations()
    
    def _extract_items_from_text(self, text: str, category: str) -> List[Dict]:
        """
        Extract individual items from text section
        """
        items = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
                
            item_text = line.split('.', 1)[1].strip() if '.' in line else line
            title = self._extract_title(item_text)
            
            if title:
                item = {
                    "title" if category in ["movies", "music"] else "name": title,
                    "description": item_text,
                    "category": category
                }
                
                if category == "movies":
                    item.update({
                        "year": "Unknown",
                        "genre": "Unknown",
                        "rating": "Unknown"
                    })
                elif category == "music":
                    item.update({
                        "artist": "Unknown",
                        "genre": "Unknown",
                        "release_year": "Unknown"
                    })
                elif category == "places":
                    item.update({
                        "type": "Unknown",
                        "rating": 4.0,
                        "location": {"lat": 0, "lng": 0}
                    })
                elif category == "events":
                    item.update({
                        "date": "Unknown",
                        "venue": "Unknown",
                        "price": "Unknown"
                    })
                
                items.append(item)
        
        return items
    
    def _extract_title(self, text: str) -> str:
        """
        Extract title/name from item text
        """
        import re
        bold_match = re.search(r'\*\*(.*?)\*\*', text)
        if bold_match:
            return bold_match.group(1).strip()
        
        quote_match = re.search(r'"([^"]*)"', text)
        if quote_match:
            return quote_match.group(1).strip()
        
        title = text.split('(')[0].split(' - ')[0].strip()
        
        if len(title) > 100:
            title = title[:100] + "..."
            
        return title
    
    def _robust_parse_json(self, raw: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse JSON that may be wrapped in code fences or include extra prose.
        """
        try:
            text = raw.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
            
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                candidate = text[start_idx:end_idx + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    pass
            return None
        except Exception:
            return None
    
    def _process_llm_recommendations(self, recommendations: Dict[str, Any], user_id: str = None, current_city: str = "Barcelona") -> Dict[str, List[Dict]]:
        """
        Process and enhance recommendations from the LLM API with normalized scores
        """
        try:
            processed = {
                "movies": recommendations.get("movies", []),
                "music": recommendations.get("music", []),
                "places": recommendations.get("places", []),
                "events": recommendations.get("events", [])
            }
            
            history = self._get_user_interaction_history(user_id) if user_id else {}
            
            user_profile = None
            location_data = None
            interaction_data = None
            
            if user_id:
                try:
                    from app.services.user_profile import UserProfileService
                    from app.services.lie_service import LIEService
                    from app.services.cis_service import CISService
                    import asyncio
                    
                    user_service = UserProfileService(timeout=10)
                    lie_service = LIEService(timeout=10)
                    cis_service = CISService(timeout=10)
                    
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        user_profile = loop.run_until_complete(user_service.get_user_profile(user_id))
                        location_data = loop.run_until_complete(lie_service.get_location_data(user_id))
                        interaction_data = loop.run_until_complete(cis_service.get_interaction_data(user_id))
                        
                        if user_profile:
                            user_profile = user_profile.safe_dump() if hasattr(user_profile, 'safe_dump') else user_profile.model_dump()
                        if location_data:
                            location_data = location_data.safe_dump() if hasattr(location_data, 'safe_dump') else location_data.model_dump()
                        if interaction_data:
                            interaction_data = interaction_data.safe_dump() if hasattr(interaction_data, 'safe_dump') else interaction_data.model_dump()
                            
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.warning(f"Could not fetch user data for enhanced scoring: {str(e)}")
            
            for category, items in processed.items():
                if not isinstance(items, list) or not items:
                    continue
                    
                # Compute raw scores
                raw_scores = []
                for item in items:
                    if isinstance(item, dict):
                        raw = self._compute_ranking_score(
                            item, category, history, user_profile, location_data, interaction_data
                        )
                        item['_raw_score'] = raw
                        raw_scores.append(raw)
                
                # Normalize to 0.1-1.0 range per category
                if raw_scores:
                    min_s = min(raw_scores)
                    max_s = max(raw_scores)
                    if max_s == min_s:
                        norm_score = 0.5
                        for item in items:
                            item["ranking_score"] = round(norm_score, 2)
                    else:
                        for item in items:
                            norm = 0.1 + 0.9 * (item['_raw_score'] - min_s) / (max_s - min_s)
                            item["ranking_score"] = round(norm, 2)
                    # Clean up
                    for item in items:
                        del item['_raw_score']
                
                # Generate reasons if missing
                for item in items:
                    if not item.get("why_would_you_like_this"):
                        item["why_would_you_like_this"] = self._generate_personalized_reason(
                            item, category, "", user_id, current_city
                        )
                
                # Sort by ranking_score descending
                items.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)
            
            return processed
        except Exception as e:
            logger.error(f"Error processing LLM recommendations: {str(e)}")
            return self._get_fallback_recommendations()

    def _get_fallback_recommendations(self) -> Dict[str, List[Dict]]:
        """
        Get fallback recommendations when LLM API fails
        """
        logger.info("Using fallback recommendations due to API failure")
        return {
            "movies": [],
            "music": [],
            "places": [],
            "events": []
        }
    
    def _generate_personalized_reason(self, item: Dict[str, Any], category: str, prompt: str, user_id: str = None, current_city: str = "Barcelona") -> str:
        """Generate detailed personalized reason why user would like this recommendation (3-5 sentences)"""
        prompt_text = prompt.lower() if prompt else "your interests"
        
        # Enhanced base reasons with more detailed explanations
        detailed_reasons = {
            "movies": [
                f"Based on your interest in {prompt_text}, this {item.get('genre', 'film') if item else 'film'} offers compelling storytelling that perfectly matches your viewing preferences. The cast featuring {', '.join(item.get('cast', ['talented actors'])[:2]) if item else 'talented actors'} delivers performances that align with the quality content you typically enjoy. This {item.get('year', 'recent') if item else 'recent'} film's themes and narrative structure resonate deeply with your cultural interests and entertainment choices. The cinematography and direction create an immersive experience that will captivate you throughout the entire viewing. Given your appreciation for well-crafted narratives, this recommendation stands out as an excellent choice for your next movie night in {current_city}.",
                f"This {item.get('genre', 'film') if item else 'film'} represents exactly the type of content that appeals to your sophisticated taste in cinema. The storyline weaves together complex themes that will engage your intellectual curiosity while providing pure entertainment value. With {item.get('runtime', '120') if item else '120'} minutes of runtime, it offers the perfect length for an immersive viewing experience that matches your typical entertainment patterns. The film's critical acclaim and audience reception suggest it will exceed your expectations for quality entertainment. Your previous positive interactions with similar content indicate this recommendation will be a perfect match for your preferences in {current_city}."
            ],
            "music": [
                f"This {item.get('genre', 'track') if item else 'track'} perfectly captures the musical energy and mood that aligns with your current listening preferences. The artist {item.get('artist', 'musician') if item else 'musician'} has crafted a sound that resonates with your musical taste and lifestyle in {current_city}. With {item.get('monthly_listeners', 'thousands of') if item else 'thousands of'} monthly listeners, this track represents both quality and popularity that matches your music discovery patterns. The production quality and artistic vision behind this piece will provide the perfect soundtrack for your daily activities and moments of relaxation. Your engagement history with similar artists and genres strongly suggests this recommendation will become a favorite in your music collection.",
                f"The musical composition and arrangement of this track demonstrate the artistic depth you appreciate in your music choices. This {item.get('genre', 'song') if item else 'song'} offers the perfect blend of melody and rhythm that will enhance your listening experience throughout the day. The artist's unique style and creative approach align perfectly with your musical preferences and cultural interests in {current_city}. The track's emotional resonance and thematic content will provide meaningful moments of connection and enjoyment. Based on your music consumption patterns and previous positive interactions, this recommendation is perfectly tailored to your taste and listening habits."
            ],
            "places": [
                f"Located in the heart of {current_city}, this {item.get('type', 'location') if item else 'location'} offers an exceptional experience that perfectly matches your lifestyle and preferences. With a {item.get('rating', 4.5) if item else 4.5} rating and {item.get('user_ratings_total', 'hundreds of') if item else 'hundreds of'} positive reviews, it has established itself as a local favorite that consistently delivers quality service. The {item.get('category', 'venue') if item else 'venue'} provides exactly the atmosphere and amenities you're seeking for your {item.get('preferred_time', 'leisure') if item else 'leisure'} activities. The location's accessibility and convenience make it an ideal choice for your regular visits and special occasions. Your previous positive experiences with similar venues in {current_city} indicate this recommendation will exceed your expectations and become a regular destination.",
                f"This {item.get('type', 'establishment') if item else 'establishment'} represents the perfect blend of quality, atmosphere, and service that aligns with your discerning taste and preferences. The venue's reputation for excellence and attention to detail ensures every visit will be memorable and satisfying. Located in a prime area of {current_city}, it offers both convenience and an authentic local experience that matches your cultural interests. The {item.get('category', 'place') if item else 'place'} provides the ideal setting for your social activities and personal enjoyment. Based on your location preferences and past positive interactions with similar venues, this recommendation perfectly complements your lifestyle and entertainment choices in {current_city}."
            ],
            "events": [
                f"This {item.get('category', 'event') if item else 'event'} happening in {current_city} perfectly matches your cultural interests and provides an excellent opportunity for meaningful experiences. Organized by {item.get('organizer', 'renowned promoters') if item else 'renowned promoters'}, it promises a {item.get('duration', 'memorable') if item else 'memorable'} experience that will exceed your expectations for quality entertainment. The {item.get('event_type', 'gathering') if item else 'gathering'} offers {item.get('languages', ['multilingual'])[0] if item else 'multilingual'} accessibility, ensuring you can fully engage with the content and activities. The event's timing and location make it convenient for your schedule while providing the cultural enrichment you value. Your previous positive experiences with similar events in {current_city} strongly suggest this recommendation will be a highlight of your social calendar.",
                f"The {item.get('category', 'event') if item else 'event'} represents exactly the type of cultural experience that appeals to your sophisticated interests and social preferences. This carefully curated event offers unique opportunities for learning, networking, and personal growth that align with your values and aspirations. The organizers have designed the program to provide both entertainment and intellectual stimulation, creating a well-rounded experience for attendees. The event's location and timing in {current_city} make it easily accessible while offering an authentic local cultural experience. Based on your engagement history with similar cultural events and your appreciation for quality programming, this recommendation perfectly matches your interests and will provide lasting value and enjoyment."
            ]
        }
        
        # Select a detailed reason based on category
        selected_reason = random.choice(detailed_reasons.get(category, [f"This recommendation perfectly suits your taste and preferences in {current_city}. The quality and appeal of this suggestion align with your interests and lifestyle choices. Your previous positive interactions with similar content indicate this will be an excellent match for your preferences. The recommendation offers both immediate enjoyment and long-term value that matches your expectations. This suggestion represents the perfect balance of quality, relevance, and appeal for your personal interests and cultural preferences in {current_city}."]))
        
        return selected_reason
    
    def _store_in_redis(self, user_id: str, data: Dict[str, Any]):
        """Store recommendations in Redis"""
        try:
            if not self._validate_cached_payload(data):
                logger.warning("Skipping cache store: payload failed validation", user_id=user_id)
                return
            key = f"recommendations:{user_id}"
            data_size = len(json.dumps(data, default=str))
            
            logger.info("Storing recommendations in Redis",
                       user_id=user_id,
                       key=key,
                       data_size_bytes=data_size,
                       ttl_seconds=86400)
            
            payload = json.dumps(data, default=str)
            # Store directly for test compatibility
            self.redis_client.setex(key, 86400, payload)
            
            logger.info("Recommendations stored successfully in Redis",
                       user_id=user_id,
                       key=key,
                       data_size_bytes=data_size)
            
            # Publish notification
            try:
                notify_payload = {
                    "type": "notification",
                    "user_id": str(user_id),
                    "message": {"content": "Your new recommendations are ready!"}
                }
                pub_client = redis.Redis(
                    host=settings.redis_host,
                    port=getattr(settings, "redis_port", 6379),
                    password=getattr(settings, "redis_password", None),
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=5,
                )
                pub_client.publish("notifications:user", json.dumps(notify_payload))
                
                logger.info("Notification published successfully",
                           user_id=user_id,
                           channel="notifications:user",
                           notification_type="recommendations_ready")
            except Exception as pub_err:
                logger.error("Failed to publish notification",
                            user_id=user_id,
                            error=str(pub_err),
                            channel="notifications:user")
        except Exception as e:
            logger.error("Error storing recommendations in Redis",
                        user_id=user_id,
                        key=key,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "store_redis"})
    
    def get_recommendations_from_redis(self, user_id: str) -> Dict[str, Any]:
        """Retrieve recommendations from Redis with pipelining support"""
        try:
            key = f"recommendations:{user_id}"
            logger.info("Retrieving recommendations from Redis",
                       user_id=user_id,
                       key=key)
            
            # Use direct call for test compatibility
            data = self.redis_client.get(key)
            if data:
                data_size = len(data)
                logger.info("Recommendations retrieved successfully from Redis",
                           user_id=user_id,
                           key=key,
                           data_size_bytes=data_size)
                obj = json.loads(data)
                if not self._validate_cached_payload(obj):
                    logger.warning("Cached payload failed validation, ignoring", user_id=user_id)
                    return None
                return obj
            else:
                logger.info("No recommendations found in Redis",
                           user_id=user_id,
                           key=key)
                return None
        except Exception as e:
            logger.error("Error retrieving recommendations from Redis",
                        user_id=user_id,
                        key=key,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "get_redis"})
            return None

    def get_multiple_recommendations(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Retrieve recommendations for multiple users using pipelining"""
        try:
            if not user_ids:
                return {}
            
            keys = [f"recommendations:{user_id}" for user_id in user_ids]
            logger.info("Retrieving multiple recommendations from Redis",
                       user_count=len(user_ids),
                       keys=keys)
            
            # Use pipeline for batch retrieval
            with self.redis_client.pipeline(transaction=False) as pipe:
                for key in keys:
                    pipe.get(key)
                results = pipe.execute()
            
            recommendations = {}
            for i, (user_id, data) in enumerate(zip(user_ids, results)):
                if data:
                    try:
                        obj = json.loads(data)
                        if self._validate_cached_payload(obj):
                            recommendations[user_id] = obj
                        else:
                            logger.warning("Cached payload failed validation, skipping", user_id=user_id)
                    except Exception as e:
                        logger.warning("Failed to parse cached data", user_id=user_id, error=str(e))
            
            logger.info("Multiple recommendations retrieved",
                       requested_count=len(user_ids),
                       retrieved_count=len(recommendations))
            return recommendations
            
        except Exception as e:
            logger.error("Error retrieving multiple recommendations from Redis",
                        user_count=len(user_ids),
                        error=str(e))
            log_exception("llm_service", e, {"user_ids": user_ids, "operation": "get_multiple_redis"})
            return {}
    
    def clear_recommendations(self, user_id: str = None):
        """Clear recommendations from Redis"""
        try:
            if user_id:
                key = f"recommendations:{user_id}"
                logger.info("Clearing recommendations for specific user",
                           user_id=user_id,
                           key=key)
                
                deleted_count = self.redis_client.delete(key)
                logger.info("Recommendations cleared successfully",
                           user_id=user_id,
                           key=key,
                           deleted_count=deleted_count)
            else:
                logger.info("Clearing all recommendations from Redis")
                keys = self.redis_client.keys("recommendations:*")
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
                    logger.info("All recommendations cleared successfully",
                               total_keys=len(keys),
                               deleted_count=deleted_count)
                else:
                    logger.info("No recommendation keys found to clear")
        except Exception as e:
            logger.error("Error clearing recommendations from Redis",
                        user_id=user_id,
                        error=str(e))
            log_exception("llm_service", e, {"user_id": user_id, "operation": "clear_redis"})

    async def generate_recommendations_async(
        self, 
        prompt: str, 
        user_context: Dict[str, Any], 
        recommendation_type: str
    ) -> Dict[str, List[Dict]]:
        """Async version of generate_recommendations for Celery tasks"""
        try:
            user_id = user_context.get("user_id")
            current_city = user_context.get("current_city", "Barcelona")
            
            logger.info(f"Generating async recommendations for user {user_id}")
            
            start_time = time.time()
            
            recommendations = await self._call_llm_api(prompt, user_id, current_city)
            
            processing_time = time.time() - start_time
            
            response = {
                "success": True,
                "prompt": prompt,
                "user_id": user_id,
                "current_city": current_city,
                "generated_at": time.time(),
                "processing_time": processing_time,
                "recommendations": recommendations,
                "metadata": {
                    "total_recommendations": sum(len(cat) for cat in recommendations.values()) if recommendations else 0,
                    "categories": list(recommendations.keys()) if recommendations else [],
                    "model": "llm-api-v1.0",
                    "ranking_enabled": user_id is not None
                }
            }
            
            if user_id:
                self._store_in_redis(user_id, response)
            
            logger.info(f"Generated {response['metadata']['total_recommendations']} async recommendations for user {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating async recommendations: {str(e)}")
            return self._get_fallback_recommendations()

    async def store_recommendations_async(
        self, 
        user_id: str, 
        recommendation_type: str, 
        recommendations: List[Dict[str, Any]]
    ) -> bool:
        """Async version of storing recommendations for Celery tasks"""
        try:
            logger.info(f"Storing async recommendations for user {user_id}")
            
            # Store in Redis
            key = f"recommendations:{user_id}:{recommendation_type}"
            data = {
                "recommendations": recommendations,
                "recommendation_type": recommendation_type,
                "generated_at": time.time(),
                "user_id": user_id
            }
            
            self.redis_client.setex(
                key,
                86400,  # 24 hours TTL
                json.dumps(data, default=str)
            )
            
            logger.info(f"Async recommendations stored successfully for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing async recommendations: {str(e)}")
            return False


llm_service = LLMService(timeout=120)