import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.core.database import init_db
from app.api.auth import router as auth_router
from app.api.students import router as student_router
from app.api.faculty import router as faculty_router
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.rag import router as rag_router
from app.api.workflows import router as workflows_router
from app.api.voice import router as voice_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campusai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CampusAI backend...")
    init_db()
    try:
        from app.seed import seed_database
        seed_database()
    except Exception as e:
        logger.warning(f"Seed initialization: {e}")
    logger.info("CampusAI backend successfully initialized.")
    yield
    logger.info("CampusAI backend shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CampusAI: Production-Grade Agentic College Assistant with AWS Bedrock, RAG, and LangGraph",
    lifespan=lifespan
)

# CORS Middleware (allows browser access from AWS Load Balancer and all clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# API Routers
api_v1_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_v1_prefix)
app.include_router(student_router, prefix=api_v1_prefix)
app.include_router(faculty_router, prefix=api_v1_prefix)
app.include_router(admin_router, prefix=api_v1_prefix)
app.include_router(chat_router, prefix=api_v1_prefix)
app.include_router(rag_router, prefix=api_v1_prefix)
app.include_router(workflows_router, prefix=api_v1_prefix)
app.include_router(voice_router, prefix=api_v1_prefix)


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to CampusAI API. Access Swagger documentation at /docs",
        "version": settings.APP_VERSION
    }
