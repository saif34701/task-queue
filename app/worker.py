import time
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Task, Worker

def notify(event_type: str, task: Task):
    try:
        import httpx
        httpx.post("http://127.0.0.1:8000/internal/broadcast", json={
            "event": event_type,
            "task_id": task.id,
            "type": task.type,
            "status": task.status,
            "retry_count": task.retry_count,
            "error_message": task.error_message
        }, timeout=1)
    except Exception:
        pass

WORKER_ID = str(uuid.uuid4())[:8]
HEARTBEAT_INTERVAL = 5
DEAD_WORKER_THRESHOLD = 15

def register_worker(db: Session):
    worker = Worker(id=WORKER_ID)
    db.add(worker)
    db.commit()
    print(f"[Worker {WORKER_ID}] Registered")

def send_heartbeat(db: Session, current_task_id=None):
    worker = db.query(Worker).filter(Worker.id == WORKER_ID).first()
    if worker:
        worker.last_heartbeat = datetime.utcnow()
        worker.current_task_id = current_task_id
        db.commit()

def recover_dead_workers(db: Session):
    threshold = datetime.utcnow() - timedelta(seconds=DEAD_WORKER_THRESHOLD)
    
    dead_workers = db.query(Worker).filter(
        Worker.status == "ACTIVE",
        Worker.last_heartbeat < threshold
    ).all()

    for worker in dead_workers:
        print(f"[Worker {WORKER_ID}] Detected dead worker {worker.id} — recovering tasks")
        
        stuck_tasks = db.query(Task).filter(
            Task.status == "RUNNING"
        ).all()

        for task in stuck_tasks:
            task.status = "PENDING"
            task.started_at = None
            print(f"[Worker {WORKER_ID}] Re-queued stuck task {task.id}")

        worker.status = "DEAD"
        db.commit()

def get_next_task(db: Session):
    task = db.query(Task).filter(
        Task.status == "PENDING"
    ).order_by(
        Task.priority.desc(),
        Task.created_at.asc()
    ).with_for_update(skip_locked=True).first()

    if task:
        task.status = "RUNNING"
        task.started_at = datetime.utcnow()
        db.commit()
        db.refresh(task)

    return task

def execute_task(task: Task):
    print(f"[Worker {WORKER_ID}] Executing task {task.id} of type '{task.type}'")
    return {"message": f"Task {task.type} completed successfully"}

def handle_success(db: Session, task: Task, result: dict):
    task.status = "COMPLETED"
    task.completed_at = datetime.utcnow()
    task.result = result

    worker = db.query(Worker).filter(Worker.id == WORKER_ID).first()
    if worker:
        worker.tasks_completed += 1
        worker.current_task_id = None

    db.commit()
    print(f"[Worker {WORKER_ID}] Task {task.id} COMPLETED")
    notify("task_completed", task)

def handle_failure(db: Session, task: Task, error: str):
    task.retry_count += 1
    task.error_message = error

    if task.retry_count >= task.max_retries:
        task.status = "FAILED"
        print(f"[Worker {WORKER_ID}] Task {task.id} FAILED permanently after {task.retry_count} retries")
    else:
        task.status = "PENDING"
        task.started_at = None
        print(f"[Worker {WORKER_ID}] Task {task.id} failed — retrying ({task.retry_count}/{task.max_retries})")

    db.commit()
    notify("task_failed", task)

def run_worker():
    print(f"[Worker {WORKER_ID}] Started and polling for tasks...")
    db = SessionLocal()
    register_worker(db)

    last_heartbeat_time = time.time()

    try:
        while True:
            now = time.time()
            if now - last_heartbeat_time >= HEARTBEAT_INTERVAL:
                send_heartbeat(db)
                recover_dead_workers(db)
                last_heartbeat_time = now

            task = get_next_task(db)

            if task:
                send_heartbeat(db, current_task_id=task.id)
                try:
                    result = execute_task(task)
                    handle_success(db, task, result)
                except Exception as e:
                    handle_failure(db, task, str(e))
                send_heartbeat(db, current_task_id=None)
            else:
                time.sleep(1)

    except KeyboardInterrupt:
        print(f"[Worker {WORKER_ID}] Shutting down")
        worker = db.query(Worker).filter(Worker.id == WORKER_ID).first()
        if worker:
            worker.status = "STOPPED"
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run_worker()