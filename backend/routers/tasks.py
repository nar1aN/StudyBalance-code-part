from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date, timedelta
from ..database import get_db
from ..models import Task, User
from ..schemas import TaskCreate, TaskUpdate, TaskOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

OVERLOAD_THRESHOLD = 4.0


@router.get("/", response_model=List[TaskOut])
def get_tasks(
    completed: Optional[bool] = None,
    subject_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Task).filter(Task.user_id == current_user.id)
    if completed is not None:
        q = q.filter(Task.is_completed == completed)
    if subject_id:
        q = q.filter(Task.subject_id == subject_id)
    if date_from:
        q = q.filter(Task.deadline >= date_from)
    if date_to:
        q = q.filter(Task.deadline <= date_to)
    return q.order_by(Task.deadline).all()


@router.get("/today", response_model=List[TaskOut])
def get_today_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    return (
        db.query(Task)
        .filter(Task.user_id == current_user.id, Task.deadline >= start, Task.deadline <= end)
        .order_by(Task.deadline)
        .all()
    )


@router.get("/week", response_model=List[TaskOut])
def get_week_tasks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today + timedelta(days=6), datetime.max.time())
    return (
        db.query(Task)
        .filter(Task.user_id == current_user.id, Task.deadline >= start, Task.deadline <= end)
        .order_by(Task.deadline)
        .all()
    )


@router.get("/stats/week")
def get_week_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    days_data = []
    for i in range(7):
        day = today + timedelta(days=i)
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        tasks = (
            db.query(Task)
            .filter(Task.user_id == current_user.id, Task.deadline >= start, Task.deadline <= end, Task.is_completed == False)
            .all()
        )
        total_hours = sum(t.estimated_hours for t in tasks)
        days_data.append({
            "date": day.isoformat(),
            "day_name": ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][day.weekday()],
            "total_hours": round(total_hours, 1),
            "task_count": len(tasks),
            "is_overloaded": total_hours > OVERLOAD_THRESHOLD,
        })

    all_tasks = db.query(Task).filter(Task.user_id == current_user.id).count()
    done_tasks = db.query(Task).filter(Task.user_id == current_user.id, Task.is_completed == True).count()
    return {
        "days": days_data,
        "total_tasks": all_tasks,
        "completed_tasks": done_tasks,
        "overloaded_days": sum(1 for d in days_data if d["is_overloaded"]),
    }


@router.get("/stats/subjects")
def get_subject_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    stats = {}
    for task in tasks:
        name = task.subject.name if task.subject else "Без предмета"
        color = task.subject.color if task.subject else "#95A5A6"
        if name not in stats:
            stats[name] = {"name": name, "color": color, "total": 0, "completed": 0, "hours": 0}
        stats[name]["total"] += 1
        stats[name]["hours"] += task.estimated_hours
        if task.is_completed:
            stats[name]["completed"] += 1
    return list(stats.values())


@router.post("/", response_model=TaskOut, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = Task(**data.model_dump(), user_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    if data.is_completed is True and not task.completed_at:
        task.completed_at = datetime.utcnow()
    elif data.is_completed is False:
        task.completed_at = None
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()
