# TaskFlow — Task Management Application
> Full-stack web app | FastAPI + SQLite + Vanilla JS

## Features
- ✅ JWT Authentication (Register / Login)
- 📋 Full CRUD for tasks
- 🏷️ Priority levels: Low / Medium / High / Urgent
- 🗂️ Custom tags & categories
- 📅 Due dates with overdue detection
- 🔀 Kanban board with drag & drop
- 📊 Stats dashboard (total, completed, in-progress, urgent)
- 🔍 Search + priority filter
- ☰ List & Kanban view toggle
- 🌙 Dark theme, fully responsive

---

## Run Locally (Windows PowerShell)

```powershell
# 1. Go into backend folder
cd taskflow\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start the server
uvicorn main:app --reload --port 8000
```

Then open: **http://localhost:8000**

---

## Deploy to Vercel (Free)

### Step 1 — Push to GitHub
```powershell
cd taskflow
git init
git add .
git commit -m "Initial commit - TaskFlow"
# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/taskflow.git
git push -u origin main
```

### Step 2 — Deploy on Vercel
1. Go to **https://vercel.com** → Sign up with GitHub
2. Click **"Add New Project"**
3. Import your `taskflow` repository
4. Set **Root Directory** to: `./` (leave default)
5. Set these **Environment Variables**:
   - `SECRET_KEY` → `your-super-secret-key-change-this`
6. Click **Deploy** ✅

> **Note:** For production, replace SQLite with a cloud database.
> Vercel recommends: **Supabase** (free PostgreSQL) → set `DATABASE_URL` env variable.

---

## Project Structure
```
taskflow/
├── backend/
│   ├── main.py          # FastAPI app entry point
│   ├── database.py      # SQLAlchemy + SQLite config
│   ├── models.py        # User & Task models
│   ├── auth.py          # JWT + password hashing
│   ├── requirements.txt
│   └── routes/
│       ├── users.py     # /api/auth endpoints
│       └── tasks.py     # /api/tasks endpoints
├── frontend/
│   ├── login.html       # Auth page
│   └── dashboard.html   # Main app
├── vercel.json          # Vercel deployment config
└── README.md
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/login | Login & get token |
| GET | /api/auth/me | Get current user |
| GET | /api/tasks/ | Get all tasks (filterable) |
| POST | /api/tasks/ | Create task |
| PUT | /api/tasks/{id} | Update task |
| DELETE | /api/tasks/{id} | Delete task |
| GET | /api/tasks/stats/summary | Dashboard stats |

---
Built with FastAPI · SQLAlchemy · SQLite · Vanilla JS
