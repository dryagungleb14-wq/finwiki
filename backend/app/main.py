from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import qa, admin, slack
import os
from dotenv import load_dotenv

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinWiki API", version="1.0.0")

frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

allowed_origins = [
    frontend_url,
    "http://localhost:3000",
    "http://localhost:8000",
]

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

