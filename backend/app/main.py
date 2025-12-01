from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import qa, admin, slack
import os
import logging
from dotenv import load_dotenv
from alembic.config import Config
from alembic import command

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    try:
        logger.info("Запуск миграций Alembic...")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Миграции успешно применены")
    except Exception as e:
        logger.error(f"Ошибка при применении миграций: {e}")

run_migrations()

app = FastAPI(title="FinWiki API", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

allowed_origins = [
    "https://finwiki.vercel.app",
    "http://localhost:3000",
    "http://localhost:8000",
]

if frontend_url and frontend_url not in allowed_origins:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(qa.router)
app.include_router(admin.router)
app.include_router(slack.router)

@app.get("/")
async def root():
    return {"message": "FinWiki API"}

@app.get("/health")
async def health():
    return {"status": "ok"}

