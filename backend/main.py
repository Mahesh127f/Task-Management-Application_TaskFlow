from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os

from database import engine, get_db, Base
from routes import users, tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/api/auth", tags=["auth"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

def read_html(filename):
    paths = [
        os.path.join(os.path.dirname(__file__), '..', 'frontend', filename),
        os.path.join(os.path.dirname(__file__), 'frontend', filename),
        os.path.join('/var/task', 'frontend', filename),
    ]
    for p in paths:
        p = os.path.abspath(p)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                return f.read()
    return "<h1>File not found</h1>"

@app.get("/", response_class=HTMLResponse)
def serve_login():
    return HTMLResponse(content=read_html('login.html'))

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    return HTMLResponse(content=read_html('dashboard.html'))

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "TaskFlow"}