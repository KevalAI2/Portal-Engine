# Personalized Content Recommendation Engine

## 📌 Overview
This system is a **personalized content recommendation platform** — the backend brain for a portal (web or mobile) that delivers highly relevant places, music, movies, workshops, and other activities to users based on their **profile, location, and past behavior**.

It **continuously learns** from user interactions, **prefetches content** in advance, caches it for instant loading, and **pushes notifications** when something valuable appears.

Think of it as **Spotify Discover Weekly + Google Maps Explore + Netflix recommendations** rolled into one.

---

## 🎯 What It Does
1. **Understands the user**  
   Maintains a detailed profile — preferences, demographics, travel history, keywords, and relationship status.

2. **Predicts what they might like now**  
   Uses triggers like time, location, or manual refresh to decide what to fetch.

3. **Fetches content in advance**  
   Generates LLM-powered prompts for specialized fetchers (places, music, movies, workshops, etc.).

4. **Stores in Redis for instant access**  
   Prefetched results are cached with TTLs to keep content fresh.

5. **Ranks and filters results**  
   Applies relevance, diversity, and freshness rules before sending to the client.

6. **Sends push notifications**  
   Notifies users when high-value new content appears.

7. **Learns from interactions**  
   Every click, view, or ignore improves future recommendations.

---

## 📖 Example Use Case
**Alex** (29 years old, loves jazz, hiking, and cooking workshops, currently in NYC):

- It’s Friday night — Alex opens the app.
- The system **already prefetched**:
  - Jazz events in NYC
  - Cooking workshops for the weekend
  - Nearby hiking trails
- Results are **ranked**:
  1. "Tonight only: Jazz night at Blue Note"
  2. "Saturday cooking masterclass with Chef X"
- Alex clicks on the jazz event → logged → jazz recommendations get more priority in the future.
- Tomorrow, if a new top-rated jazz event appears, Alex receives a push notification.

---

## 🏗 Architecture Components

### 1. **FastAPI API Gateway**
- Main entry point for all client requests.
- Validates authentication tokens (JWT).
- Forwards requests to Retrieval Service, Results Algorithm, or Content Interaction Service.
- Passes user profile context downstream.

### 2. **Retrieval Service**
- Listens for triggers (time-based, location updates, manual refresh).
- Builds user-specific prompts for fetching recommendations.
- Enqueues tasks into RabbitMQ via Celery.

### 3. **Celery + RabbitMQ**
- Handles async task execution for prefetching.
- Calls LLM-based prefetch servers.
- Stores results in Redis.

### 4. **Redis Cache**
- Caches prefetched results for instant client responses.
- Uses category-based TTLs.
- Avoids caching location-sensitive "places" without geospatial awareness.

### 5. **Results Algorithm**
- Aggregates, ranks, deduplicates cached recommendations.
- Orders content for maximum relevance and engagement.

### 6. **Content Interaction Service (CIS)**
- Logs user actions (clicks, views, ignores).
- Provides historical interaction data for personalization.

### 7. **Push Notification Service**
- Sends personalized alerts for high-value content.
- Respects user preferences and quiet hours.

### 8. **Portal UI**
- Displays personalized content.
- Sends interaction data to backend.
- Handles push notifications and deep linking.

---

## 🔄 Typical Workflow

1. **Trigger Event** — Time, location update, or manual refresh.
2. **Auth & Context** — API Gateway validates token and enriches with user profile.
3. **Retrieval** — Retrieval Service generates prompts and sends tasks to RabbitMQ.
4. **Prefetch** — Celery workers fetch recommendations from LLM servers.
5. **Cache** — Results stored in Redis with per-category TTL.
6. **Ranking** — Results Algorithm applies relevance, diversity, and freshness filters.
7. **Response** — API Gateway returns ranked recommendations to the Portal UI.
8. **Notifications** — High-value content triggers push notifications.
9. **Feedback Loop** — User interactions refine the personalization model.

---

## 🗝 Redis Key Examples

| Key | Purpose | TTL |
|-----|---------|-----|
| `prefetch:{user_id}:music` | Cached recommended music playlists | 30 min |
| `prefetch:{user_id}:movies` | Cached recommended movies | 30 min |
| `interaction_log:{user_id}` | Recent interaction history for filtering | 1 day rolling |

---

## 📡 Planned Endpoints

### **API Gateway**
- `GET /content` – Fetch personalized recommendations.
- `POST /interaction` – Log user content interactions.
- `POST /retrieve` – Manually trigger content retrieval.
- `POST /notifications/send` – Trigger push notification.

### **Retrieval Service**
- `POST /retrieve` – Trigger retrieval for one user.
- `POST /retrieve/batch` – Trigger retrieval for multiple users.
- `GET /prompts/{user_id}` – View generated prompts (debug).

### **Results Algorithm**
- `GET /results/{user_id}` – Get ranked recommendations.
- `POST /results/re-rank` – Re-rank a given list.

### **CIS**
- `POST /interaction` – Log single interaction.
- `POST /interaction/batch` – Bulk log interactions.
- `GET /interaction/{user_id}` – View interaction history.
- `GET /interaction/aggregate/{user_id}` – View aggregated stats.

### **Push Notification Service**
- `POST /push/send` – Send a push notification.
- `POST /push/batch` – Send to multiple users.
- `POST /push/register` – Register device token & preferences.
- `GET /push/preferences/{user_id}` – Get notification preferences.

### **Admin / Internal**
- `GET /health` – Service health check.
- `GET /metrics` – Performance & queue metrics.
- `POST /admin/cache/clear/{user_id}` – Clear user cache.
- `GET /admin/cache/view/{user_id}` – View current cache.

---

## ⚙️ Tech Stack
- **FastAPI** – API services
- **Celery + RabbitMQ** – Background tasks
- **Redis** – Caching layer
- **PostgreSQL / PostGIS** – Persistent storage (location-aware)
- **LLM-based Prefetch Servers** – Content retrieval
- **Firebase Cloud Messaging (FCM)** – Push notifications
- **Docker & Docker Compose** – Service orchestration

---

## 🚀 Getting Started
*(Setup instructions will be added once base project structure is created.)*
