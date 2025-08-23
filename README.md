# Insurance Agent Resume Scraper

This project implements a system for scraping insurance agent resumes, analyzing them with AI, and automating email outreach.

## Project Structure

```
insurance-agent-scraper/
├── backend/             # FastAPI backend
├── frontend/            # React frontend
├── data/                # Storage for resumes, logs, exports
├── proxies/             # Proxy configurations
├── docker-compose.yml   # Docker orchestration
├── .env.example         # Environment variables example
└── README.md
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd insurance-agent-scraper
    ```

2.  **Environment Variables:**
    Copy the example environment file and fill in your details:
    ```bash
    cp .env.example .env
    ```
    Edit the `.env` file with your OpenAI API key, LinkedIn credentials, etc.

3.  **Docker Compose:**
    Build and run the Docker containers:
    ```bash
    docker-compose up --build
    ```

    The backend will be accessible at `http://localhost:8000` and the frontend at `http://localhost:3000`.

## Usage

(To be filled in as features are implemented)

## Development

### Backend
Navigate to the `backend` directory and install dependencies:
```bash
pip install -r requirements.txt
```
Run the FastAPI application:
```bash
uvicorn app.main:app --reload
```

### Frontend
Navigate to the `frontend` directory and install dependencies:
```bash
npm install
```
Run the React development server:
```bash
npm run dev
```
