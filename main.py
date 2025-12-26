import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, courses, content, books
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MyLMS Backend",
    description="Python backend for MyLMS Dashboard - Moodle API integration",
    version="0.1.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Very permissive for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(courses.router, prefix="/api/courses", tags=["courses"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(books.router, prefix="/api/books", tags=["books"])

@app.get("/")
async def root():
    return {"message": "MyLMS Backend is running"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info"
    )
