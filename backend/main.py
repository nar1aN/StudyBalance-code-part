from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from .database import engine, Base
from .models import User
from .schemas import UserOut
from .auth import get_current_user
from .routers import auth, tasks, subjects

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StudyBalance API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
index_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

def get_index_html():
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

app.include_router(tasks.router)
app.include_router(subjects.router)
app.include_router(auth.router)

@app.get("/api/auth/me", response_model=UserOut, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=get_index_html())

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_frontend(full_path: str):
    return HTMLResponse(content=get_index_html())