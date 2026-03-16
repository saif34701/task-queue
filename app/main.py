from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.database import engine, Base, get_db
from app.models import Task, Worker
import json

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Queue System")

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class TaskCreate(BaseModel):
    type: str
    payload: Optional[dict] = None
    priority: Optional[int] = 5
    max_retries: Optional[int] = 3

@app.get("/")
def root():
    return {"status": "Task queue is running"}

@app.post("/tasks", status_code=201)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        type=task_data.type,
        payload=task_data.payload,
        priority=task_data.priority,
        max_retries=task_data.max_retries
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    await manager.broadcast({
        "event": "task_created",
        "task_id": task.id,
        "type": task.type,
        "status": task.status,
        "priority": task.priority,
        "created_at": str(task.created_at)
    })

    return {
        "id": task.id,
        "type": task.type,
        "status": task.status,
        "priority": task.priority,
        "created_at": task.created_at
    }

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    tasks = db.query(Task).order_by(
        Task.priority.desc(),
        Task.created_at.asc()
    ).all()
    return tasks

@app.get("/workers")
def get_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).all()
    return workers

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func

    total_pending = db.query(Task).filter(Task.status == "PENDING").count()
    total_running = db.query(Task).filter(Task.status == "RUNNING").count()
    total_completed = db.query(Task).filter(Task.status == "COMPLETED").count()
    total_failed = db.query(Task).filter(Task.status == "FAILED").count()
    active_workers = db.query(Worker).filter(Worker.status == "ACTIVE").count()

    avg_duration = db.query(
        func.avg(
            func.extract('epoch', Task.completed_at) -
            func.extract('epoch', Task.started_at)
        )
    ).filter(Task.status == "COMPLETED").scalar()

    return {
        "pending": total_pending,
        "running": total_running,
        "completed": total_completed,
        "failed": total_failed,
        "active_workers": active_workers,
        "avg_execution_seconds": round(avg_duration or 0, 2)
    }

@app.post("/internal/broadcast")
async def internal_broadcast(event: dict):
    await manager.broadcast(event)
    return {"ok": True}