# Task Queue System

A distributed task queue built from scratch in Python — no Celery, no Redis,
no shortcuts. Built to understand how background job systems actually work
at the infrastructure level.

## Demo

[Add your YouTube demo link here]

## What problem does this solve?

When an application needs to do work in the background — sending emails,
processing files, running reports — it needs a system that:
- Accepts work and queues it
- Distributes it across multiple workers
- Retries on failure
- Recovers automatically when a worker crashes

This project implements that system from the ground up.

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                  │
│  POST /tasks  GET /tasks  GET /workers  GET /stats      │
│  WebSocket /ws          POST /internal/broadcast        │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  PostgreSQL Database                    │
│                                                         │
│   tasks table              workers table                │
│   ├── id (uuid)            ├── id                       │
│   ├── type                 ├── status                   │
│   ├── payload (JSON)       ├── current_task_id          │
│   ├── status               ├── last_heartbeat           │
│   ├── priority             └── tasks_completed          │
│   ├── retry_count                                       │
│   ├── max_retries                                       │
│   └── error_message                                     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      Workers                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│                                                         │
│  • Poll for PENDING tasks (skip_locked)                 │
│  • Send heartbeat every 5s                              │
│  • Detect and recover dead workers                      │
│  • Retry failed tasks up to max_retries                 │
└───────────────────────────┬─────────────────────────────┘
                            │ WebSocket
┌───────────────────────────▼─────────────────────────────┐
│                  Dashboard (HTML/JS)                    │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │ Pending  │ │ Running  │ │Completed │ │  Failed  │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│                                                         │
│  Live Event Log  │  Tasks Table  │  Workers Table       │
└─────────────────────────────────────────────────────────┘
```
# Task Queue System

A distributed task queue built from scratch in Python — no Celery, no Redis,
no shortcuts. Built to understand how background job systems actually work
at the infrastructure level.

## Demo

[Add your YouTube demo link here]

## What problem does this solve?

When an application needs to do work in the background — sending emails,
processing files, running reports — it needs a system that:
- Accepts work and queues it
- Distributes it across multiple workers
- Retries on failure
- Recovers automatically when a worker crashes

This project implements that system from the ground up.

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                     REST API (FastAPI)                   │
│  POST /tasks  GET /tasks  GET /workers  GET /stats       │
│  WebSocket /ws          POST /internal/broadcast         │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                  PostgreSQL Database                     │
│                                                         │
│   tasks table              workers table                │
│   ├── id (uuid)            ├── id                       │
│   ├── type                 ├── status                   │
│   ├── payload (JSON)       ├── current_task_id          │
│   ├── status               ├── last_heartbeat           │
│   ├── priority             └── tasks_completed          │
│   ├── retry_count                                       │
│   ├── max_retries                                       │
│   └── error_message                                     │
└───────────────────────────┬─────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────┐
│                      Workers                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  • Poll for PENDING tasks (skip_locked)                 │
│  • Send heartbeat every 5s                              │
│  • Detect and recover dead workers                      │
│  • Retry failed tasks up to max_retries                 │
└───────────────────────────┬─────────────────────────────┘
                            │ WebSocket
┌───────────────────────────▼─────────────────────────────┐
│                  Dashboard (HTML/JS)                    │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ Pending  │ │ Running  │ │Completed │ │  Failed  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│                                                         │
│  Live Event Log  │  Tasks Table  │  Workers Table       │
└─────────────────────────────────────────────────────────┘
```

**Four layers:**
- **REST API** — accepts task submissions, exposes stats and monitoring endpoints
- **PostgreSQL** — stores all task state, acts as the coordination layer between workers
- **Workers** — poll for pending tasks, execute them, report results
- **Dashboard** — real-time monitoring via WebSocket, no page refresh needed

## Tech Stack

- Python + FastAPI — REST API and WebSocket server
- PostgreSQL + SQLAlchemy — task state and coordination
- WebSockets — live dashboard updates
- Vanilla HTML/CSS/JS + Chart.js — monitoring dashboard

## Features

**Queue Engine**
- Priority scheduling — higher priority tasks always picked up first
- No race conditions — PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` guarantees each task is executed by exactly one worker
- Automatic retry — failed tasks requeued up to configurable max retries
- Permanent failure handling — error message stored on final failure
- Dead worker recovery — heartbeat detection requeues stuck tasks automatically
- Task cancellation — cancel any pending task before it gets picked up
- Task type registry — each task type maps to a dedicated handler function

**Monitoring Dashboard**
- Live stats — pending, running, completed, failed, cancelled, active workers
- Real-time updates via WebSocket — no page refresh needed
- Submit tasks directly from the dashboard with registered type hints
- Filter tasks by status — All, Pending, Running, Completed, Failed, Cancelled
- Search tasks by type or ID
- Paginated tasks table — 20 tasks per page
- Click any task row for full detail modal — payload, result, error, timestamps
- Retry failed tasks with one click
- Cancel pending tasks with one click
- Toast notifications on every state change
- Throughput chart — tasks completed per time window
- Light and dark mode

**API Endpoints**
- `POST /tasks` — submit a new task
- `GET /tasks` — list all tasks
- `POST /tasks/{id}/retry` — retry a failed task
- `POST /tasks/{id}/cancel` — cancel a pending task
- `GET /workers` — list all workers and their status
- `GET /stats` — queue statistics
- `GET /registry` — list registered task types
- `WebSocket /ws` — live event stream

## How to run it locally

**Requirements:** Python 3.8+, PostgreSQL

**1. Clone the repo**
```bash
git clone https://github.com/saif34701/task-queue
cd task-queue
```

**2. Install dependencies**
```bash
pip install fastapi uvicorn psycopg2-binary sqlalchemy httpx websockets
```

**3. Create the database**
```bash
psql -U postgres
CREATE DATABASE taskqueue;
\q
```

**4. Start the server**
```bash
python -m uvicorn app.main:app --reload
```

**5. Start one or more workers**
```bash
python -m app.worker
```

**6. Open the dashboard**

Open `dashboard.html` directly in your browser.
Visit `http://127.0.0.1:8000/docs` for the interactive API.

**7. Scale workers**

Open additional terminals and run `python -m app.worker` in each.
Each worker runs independently — no configuration needed.

## Test Results

### Load Test — 1000 tasks
```
Tasks submitted:     1000
Tasks completed:     1000
Tasks lost:          0
Throughput:          3.9 tasks/sec
RESULT: PASSED — zero tasks lost
```

### Failure Test — Dead worker recovery
```
Tasks submitted:     50
Tasks completed:     50
Dead workers detected: 2
Tasks lost:          0
RESULT: PASSED — dead worker detected, all tasks recovered
```

## Adding a new task type

Register a handler in `app/handlers.py`:
```python
def handle_my_task(payload: dict) -> dict:
    # your logic here
    return {"status": "done"}

TASK_REGISTRY = {
    "my_task": handle_my_task,
    # existing handlers...
}
```

That's it. The worker picks it up automatically.

## Design Decisions

**Why PostgreSQL instead of Redis?**

Most task queues use Redis as the broker because it's fast. I chose
PostgreSQL deliberately — it gave me `SELECT FOR UPDATE SKIP LOCKED`
which solves the concurrent worker problem cleanly without any additional
infrastructure. For a project focused on understanding the fundamentals,
having one system handle both storage and coordination made the architecture
cleaner and easier to reason about.

**Why polling instead of pub/sub?**

Polling is simpler to implement correctly and reason about under failure.
With pub/sub, if a worker crashes while processing a message, the message
is gone. With polling and database state, the task always exists in
PostgreSQL — a crashed worker just means the task stays RUNNING until
the watchdog requeues it.

**Why build this instead of using Celery?**

Because using Celery teaches you the API. Building it teaches you
the problem. Every design decision in this project — the heartbeat interval,
the skip locked pattern, the retry logic — was made deliberately after
understanding why it was necessary.

## Author

Reguigui Mohamed Saif — IT Student, ISET Rades, Tunisia
Building motorsport infrastructure and backend systems from scratch.
[LinkedIn](https://www.linkedin.com/in/saif-reguigui-5a6802341/) | [GitHub](https://github.com/saif34701)