from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import Task, User
from routes.users import get_current_user

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    status: Optional[str] = "todo"
    tag: Optional[str] = "General"
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    tag: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None
    position: Optional[int] = None


def task_to_dict(task: Task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "tag": task.tag,
        "due_date": task.due_date,
        "completed": task.completed,
        "position": task.position,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }


@router.get("/")
def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Task).filter(Task.user_id == current_user.id)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    if tag:
        q = q.filter(Task.tag == tag)
    tasks = q.order_by(Task.position, Task.created_at.desc()).all()
    return [task_to_dict(t) for t in tasks]


@router.post("/")
def create_task(req: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    count = db.query(Task).filter(Task.user_id == current_user.id).count()
    task = Task(
        title=req.title,
        description=req.description,
        priority=req.priority,
        status=req.status,
        tag=req.tag,
        due_date=req.due_date,
        user_id=current_user.id,
        position=count
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_to_dict(task)


@router.put("/{task_id}")
def update_task(task_id: int, req: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in req.dict(exclude_none=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task_to_dict(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}


@router.get("/stats/summary")
def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    all_tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.completed)
    in_progress = sum(1 for t in all_tasks if t.status == "in_progress")
    todo = sum(1 for t in all_tasks if t.status == "todo")
    urgent = sum(1 for t in all_tasks if t.priority == "urgent" and not t.completed)
    return {
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "todo": todo,
        "urgent": urgent,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 1)
    }
