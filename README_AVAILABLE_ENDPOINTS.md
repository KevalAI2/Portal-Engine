## Available API Endpoints

- **Base prefix**: `/smart_recommender`
- **Docs**: Swagger UI at `/docs`, ReDoc at `/redoc`
- **CORS**: All origins allowed (intended for dev; restrict in production)

### Summary

| Method | Path                                               | Auth       | Description                                   |
|-------:|----------------------------------------------------|------------|-----------------------------------------------|
|  POST  | /smart_recommender/auth/login/                     | No         | Obtain bearer token via username/password     |
|  POST  | /smart_recommender/user/register/                  | No         | Register a new user                           |
|   GET  | /smart_recommender/user/me/                        | Bearer     | Get current authenticated user                |
|   GET  | /smart_recommender/scheduler/                      | No         | Health/test endpoint                          |
|   GET  | /smart_recommender/scheduler/task                  | No         | List all active scheduled tasks               |
|  POST  | /smart_recommender/scheduler/task                  | No         | Create a scheduled task                       |
|   PUT  | /smart_recommender/scheduler/task/{id}             | No         | Update a scheduled task                       |
| DELETE | /smart_recommender/scheduler/task/{id}             | No         | Delete a scheduled task                       |
|   GET  | /smart_recommender/scheduler/task/{task_id}/history| No         | Get run history for a scheduled task          |
|   GET  | /smart_recommender/scheduler/celery-task           | No         | List registered Celery tasks                  |

Notes:
- For protected endpoints, send `Authorization: Bearer <token>`.
- The login endpoint expects `application/x-www-form-urlencoded` with `username` and `password`.

---

## Auth

### POST /smart_recommender/auth/login/
- Form fields: `username`, `password` (OAuth2PasswordRequestForm)
- Response:
  ```json
  { "access_token": "<JWT>", "token_type": "bearer" }
  ```
- Example:
  ```bash
  curl -X POST "http://localhost:8000/smart_recommender/auth/login/" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=alice&password=secret"
  ```

## User

### POST /smart_recommender/user/register/
- Body (JSON):
  ```json
  { "username": "alice", "password": "secret" }
  ```
- Example:
  ```bash
  curl -X POST "http://localhost:8000/smart_recommender/user/register/" \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"secret"}'
  ```

### GET /smart_recommender/user/me/
- Requires header: `Authorization: Bearer <token>`
- Example:
  ```bash
  curl "http://localhost:8000/smart_recommender/user/me/" \
    -H "Authorization: Bearer $TOKEN"
  ```

## Scheduler

### GET /smart_recommender/scheduler/
- Returns a simple message (health/test).

### GET /smart_recommender/scheduler/task
- List all active scheduled tasks.
- Example:
  ```bash
  curl "http://localhost:8000/smart_recommender/scheduler/task"
  ```

### POST /smart_recommender/scheduler/task
- Query params: `name` (str), `task` (str), `cron` (str)
- Body (JSON): `args` (dict) — parameters to pass to the task
- Example:
  ```bash
  curl -X POST "http://localhost:8000/smart_recommender/scheduler/task?name=report&task=app.tasks.generate_report&cron=*/5 * * * *" \
    -H "Content-Type: application/json" \
    -d '{"args":{"user_id":123}}'
  ```

### PUT /smart_recommender/scheduler/task/{id}
- Query params: `name` (str), `task` (str), `cron` (str)
- Example:
  ```bash
  curl -X PUT "http://localhost:8000/smart_recommender/scheduler/task/1?name=report_v2&task=app.tasks.generate_report&cron=0 * * * *"
  ```

### DELETE /smart_recommender/scheduler/task/{id}
- Example:
  ```bash
  curl -X DELETE "http://localhost:8000/smart_recommender/scheduler/task/1"
  ```

### GET /smart_recommender/scheduler/task/{task_id}/history
- Example:
  ```bash
  curl "http://localhost:8000/smart_recommender/scheduler/task/1/history"
  ```

### GET /smart_recommender/scheduler/celery-task
- Lists all registered Celery tasks (excluding internal `celery.*`).
- Example:
  ```bash
  curl "http://localhost:8000/smart_recommender/scheduler/celery-task"
  ```