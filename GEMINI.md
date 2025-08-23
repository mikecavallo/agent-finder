# Project Issues and Debugging Log (Managed by Gemini)

This document summarizes the key issues encountered during the setup and debugging of the `insurance-agent-scraper` project, along with their current status.

## 1. Backend Docker Build Failure (Initial)
- **Issue:** `playwright install` failed due to Debian "buster" repositories being unavailable (404 errors).
- **Resolution:** Updated base image in `backend/Dockerfile` from `python:3.11-slim-buster` to `python:3.11-slim-bookworm`.
- **Status:** Resolved.

## 2. Frontend Docker Build Failure (Initial)
- **Issue:** `Dockerfile` missing in `frontend` directory.
- **Resolution:** Created a multi-stage `frontend/Dockerfile` to build with Node.js/Vite and serve with Nginx.
- **Status:** Resolved.

## 3. Frontend Docker Compose Port Mapping
- **Issue:** `docker-compose.yml` mapped frontend container port 3000 to host port 3000, but Nginx serves on port 80.
- **Resolution:** Corrected `docker-compose.yml` to map host port 3000 to container port 80 for the frontend service.
- **Status:** Resolved.

## 4. Frontend `ReferenceError: Settings is not defined`
- **Issue:** React component `Settings` was used in `frontend/src/App.jsx` without being imported.
- **Resolution:** Added `import Settings from './pages/Settings';` to `frontend/src/App.jsx`.
- **Status:** Resolved.

## 5. Frontend `vite.svg` 404 Error
- **Issue:** `vite.svg` (favicon) was referenced in `index.html` but not present in the served static files.
- **Resolution:** Removed the `<link>` tag for `vite.svg` from `frontend/index.html` and removed the corresponding `COPY` instruction from `frontend/Dockerfile`.
- **Status:** Resolved.

## 6. Backend `ImportError: attempted relative import beyond top-level package`
- **Issue:** Relative imports like `from ...database import get_db` were used incorrectly in `backend/app/api/` files, causing Python to look beyond the top-level package.
- **Resolution:** Changed relative imports (e.g., `from ...database`) to absolute imports (e.g., `from app.database`) in `backend/app/api/ai.py`, `backend/app/api/auth.py`, and `backend/app/api/email.py`.
- **Status:** Resolved.

## 7. Backend `KeyError: 'ContainerConfig'` (Docker Compose)
- **Issue:** `docker-compose` failed to start backend due to an issue accessing container configuration, possibly related to an old Docker Compose version or corrupted cache.
- **Resolution:** Instructed user to run `docker-compose down --volumes --rmi all` and update Docker Compose.
- **Status:** Resolved (this specific error did not reoccur after cleanup).

## 8. Backend `{"detail":"Not Found"}` for `/api/auth/register` (Persistent)
- **Issue:** `POST` requests to `/api/auth/register` consistently returned "Not Found", even when the endpoint was directly defined in `main.py`. This was a complex issue involving several layers.
- **Diagnosis:**
    - Initial `{"detail":"Not Found"}` was due to incorrect URL (`/register` instead of `/api/auth/register`).
    - Subsequent "Not Found" was due to FastAPI expecting query parameters when JSON body was sent.
- **Resolution (Partial):** Modified `backend/app/api/auth.py` to use a Pydantic model (`UserCreate`) for the `register_user` endpoint, explicitly expecting a JSON request body.
- **Status:** Partially resolved (moved to Internal Server Error).

## 9. Backend `Internal Server Error` (`sqlite3.OperationalError: no such table: users`) (Persistent)
- **Issue:** After fixing the "Not Found" error, attempts to register a user resulted in an internal server error because the `users` table did not exist in the SQLite database. This error has been highly persistent.
- **Diagnosis Steps Taken:**
    - Changed `SQLALCHEMY_DATABASE_URL` to `sqlite:///./data/sql_app.db` to use a mounted volume for persistence.
    - Imported `User` model directly in `backend/app/database.py` to ensure it's registered with `Base.metadata`.
    - Added `print` statements to `create_db_and_tables()` to confirm execution (they showed up).
    - Changed `docker-compose.yml` to use a named Docker volume (`backend_data`) for `/app/data` to bypass host filesystem permission issues.
    - Modified `backend/entrypoint.sh` to explicitly `mkdir -p /app/data` and `touch /app/data/sql_app.db` before table creation.
- **Current Status:** Unresolved. The `create_db_and_tables()` function is called, but the `users` table is still not being created or is immediately lost. This is the primary blocking issue.

## 10. Backend Service Not Starting (Intermittent)
- **Issue:** `docker-compose up --build` sometimes only started the `frontend` service, reporting `backend` as an "orphan" container.
- **Resolution:** Instructed user to run `docker-compose down --remove-orphans` before `docker-compose up --build`.
- **Status:** Resolved.

---
**Next Steps for Debugging (if continuing):**
The persistent `no such table: users` error requires further investigation. Possible causes include:
- Deeper permission issues within the Docker volume.
- A subtle error in the SQLAlchemy model definition that prevents table creation.
- A conflict with existing database files (even with `rm`).
- An issue with the `create_all` method itself in this specific environment.
