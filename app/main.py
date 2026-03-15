from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Any
from app.database import engine, Base, get_db
from app.models import Task

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Queue System")

class TaskCreate(BaseModel):
    type: str
    payload: Optional[dict] = None
    priority: Optional[int] = 5
    max_retries: Optional[int] = 3

@app.get("/")
def root():
    return {"status": "Task queue is running"}

@app.post("/tasks", status_code=201)
def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        type=task_data.type,
        payload=task_data.payload,
        priority=task_data.priority,
        max_retries=task_data.max_retries
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "type": task.type,
        "status": task.status,
        "priority": task.priority,
        "created_at": task.created_at
    }

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(Task.priority.desc(), Task.created_at.asc()).all()
    return tasks

@app.get("/workers")
def get_workers(db: Session = Depends(get_db)):
    from app.models import Worker
    workers = db.query(Worker).all()
    return workers