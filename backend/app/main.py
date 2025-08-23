from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_db_and_tables
from .api import ai, auth, email # Import your API routers here

app = FastAPI()

# CORS Middleware
origins = [
    "http://localhost",
    "http://localhost:3000", # Frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include your API routers
app.include_router(ai.router, prefix="/api/ai", tags=["AI Analysis"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(email.router, prefix="/api/email", tags=["Email Automation"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Insurance Agent Resume Scraper Backend!"}