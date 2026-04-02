from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from .models import TaskType, DifficultyLevel, PriorityLevel


#Auth
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


# Subject
class SubjectCreate(BaseModel):
    name: str
    color: Optional[str] = "#4A90D9"

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class SubjectOut(BaseModel):
    id: int
    name: str
    color: str
    class Config:
        from_attributes = True


#Task
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type: TaskType = TaskType.homework
    difficulty: DifficultyLevel = DifficultyLevel.medium
    deadline: datetime
    estimated_hours: float = 1.0
    subject_id: Optional[int] = None
    priority: Optional[PriorityLevel] = PriorityLevel.medium

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type: Optional[TaskType] = None
    difficulty: Optional[DifficultyLevel] = None
    deadline: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    subject_id: Optional[int] = None
    is_completed: Optional[bool] = None
    priority: Optional[PriorityLevel] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    task_type: TaskType
    difficulty: DifficultyLevel
    deadline: datetime
    estimated_hours: float
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime
    priority: PriorityLevel
    subject: Optional[SubjectOut]
    class Config:
        from_attributes = True



# Stats
class DayLoad(BaseModel):
    date: str
    total_hours: float
    task_count: int
    is_overloaded: bool

class WeekStats(BaseModel):
    days: List[DayLoad]
    total_tasks: int
    completed_tasks: int
    overloaded_days: int
