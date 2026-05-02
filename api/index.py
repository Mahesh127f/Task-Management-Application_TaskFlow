import sys, os, hashlib, hmac, base64, json, time, random, enum
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional

# ── DATABASE ──
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/taskflow.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── MODELS ──
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    avatar_color = Column(String(20), default="#6366f1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(20), default="medium")
    status = Column(String(20), default="todo")
    tag = Column(String(50), default="General")
    due_date = Column(String(20), nullable=True)
    completed = Column(Boolean, default=False)
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="tasks")

Base.metadata.create_all(bind=engine)

# ── AUTH ──
SECRET_KEY = os.getenv("SECRET_KEY", "taskflow-secret-2024")
COLORS = ["#6366f1","#ec4899","#f59e0b","#10b981","#3b82f6","#8b5cf6","#ef4444","#06b6d4"]

def hash_password(password):
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password, stored):
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == hashed
    except: return False

def create_token(user_id, email):
    header = base64.urlsafe_b64encode(json.dumps({"alg":"HS256"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"sub":user_id,"email":email,"exp":int(time.time())+604800}).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET_KEY.encode(), f"{header}.{payload}".encode(), hashlib.sha256).hexdigest()
    return f"{header}.{payload}.{sig}"

def decode_token(token):
    try:
        parts = token.split(".")
        if len(parts) != 3: return None
        p = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(p))
        return None if payload.get("exp",0) < time.time() else payload
    except: return None

# ── DB + AUTH DEPS ──
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(authorization.split(" ")[1])
    if not payload: raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user: raise HTTPException(status_code=401, detail="User not found")
    return user

def task_dict(t):
    return {"id":t.id,"title":t.title,"description":t.description,"priority":t.priority,
            "status":t.status,"tag":t.tag,"due_date":t.due_date,"completed":t.completed,
            "position":t.position,"created_at":t.created_at.isoformat() if t.created_at else None,
            "updated_at":t.updated_at.isoformat() if t.updated_at else None}

# ── APP ──
app = FastAPI(title="TaskFlow")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── HTML FILES ──
def read_html(filename):
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend', filename),
        os.path.join('/var/task', 'frontend', filename),
        os.path.join(os.getcwd(), 'frontend', filename),
    ]:
        p = os.path.abspath(p)
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f: return f.read()
    return "<h1>Not found</h1>"

@app.get("/", response_class=HTMLResponse)
def login(): return HTMLResponse(read_html('login.html'))

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(): return HTMLResponse(read_html('dashboard.html'))

@app.get("/api/health")
def health(): return {"status": "ok"}

# ── AUTH ROUTES ──
class RegReq(BaseModel):
    name: str; email: str; password: str

class LoginReq(BaseModel):
    email: str; password: str

@app.post("/api/auth/register")
def register(req: RegReq, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(name=req.name, email=req.email, password_hash=hash_password(req.password), avatar_color=random.choice(COLORS))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": create_token(user.id, user.email), "user": {"id":user.id,"name":user.name,"email":user.email,"avatar_color":user.avatar_color}}

@app.post("/api/auth/login")
def login_route(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(user.id, user.email), "user": {"id":user.id,"name":user.name,"email":user.email,"avatar_color":user.avatar_color}}

@app.get("/api/auth/me")
def me(u=Depends(get_user)): return {"id":u.id,"name":u.name,"email":u.email,"avatar_color":u.avatar_color}

# ── TASK ROUTES ──
class TaskCreate(BaseModel):
    title: str; description: Optional[str]=""; priority: Optional[str]="medium"
    status: Optional[str]="todo"; tag: Optional[str]="General"; due_date: Optional[str]=None

class TaskUpdate(BaseModel):
    title: Optional[str]=None; description: Optional[str]=None; priority: Optional[str]=None
    status: Optional[str]=None; tag: Optional[str]=None; due_date: Optional[str]=None
    completed: Optional[bool]=None; position: Optional[int]=None

@app.get("/api/tasks/stats/summary")
def stats(u=Depends(get_user), db: Session=Depends(get_db)):
    all_tasks = db.query(Task).filter(Task.user_id==u.id).all()
    total=len(all_tasks); done=sum(1 for t in all_tasks if t.completed)
    return {"total":total,"completed":done,"in_progress":sum(1 for t in all_tasks if t.status=="in_progress"),
            "todo":sum(1 for t in all_tasks if t.status=="todo"),
            "urgent":sum(1 for t in all_tasks if t.priority=="urgent" and not t.completed),
            "completion_rate":round(done/total*100 if total else 0,1)}

@app.get("/api/tasks/")
def get_tasks(status:Optional[str]=None, priority:Optional[str]=None, tag:Optional[str]=None,
              u=Depends(get_user), db:Session=Depends(get_db)):
    q = db.query(Task).filter(Task.user_id==u.id)
    if status: q=q.filter(Task.status==status)
    if priority: q=q.filter(Task.priority==priority)
    if tag: q=q.filter(Task.tag==tag)
    return [task_dict(t) for t in q.order_by(Task.position, Task.created_at.desc()).all()]

@app.post("/api/tasks/")
def create_task(req:TaskCreate, u=Depends(get_user), db:Session=Depends(get_db)):
    count = db.query(Task).filter(Task.user_id==u.id).count()
    t = Task(title=req.title,description=req.description,priority=req.priority,status=req.status,
             tag=req.tag or "General",due_date=req.due_date,user_id=u.id,position=count)
    db.add(t); db.commit(); db.refresh(t)
    return task_dict(t)

@app.put("/api/tasks/{task_id}")
def update_task(task_id:int, req:TaskUpdate, u=Depends(get_user), db:Session=Depends(get_db)):
    t = db.query(Task).filter(Task.id==task_id, Task.user_id==u.id).first()
    if not t: raise HTTPException(404,"Not found")
    for k,v in req.dict(exclude_none=True).items(): setattr(t,k,v)
    db.commit(); db.refresh(t)
    return task_dict(t)

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id:int, u=Depends(get_user), db:Session=Depends(get_db)):
    t = db.query(Task).filter(Task.id==task_id, Task.user_id==u.id).first()
    if not t: raise HTTPException(404,"Not found")
    db.delete(t); db.commit()
    return {"message":"deleted"}