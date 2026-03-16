# Task Queue System

A distributed task queue built from scratch in Python — no Celery, no Redis, 
no shortcuts. Built to understand how background job systems actually work 
at the infrastructure level.

## What problem does this solve?
When an app needs to do multiple jobs in the
background like : sending email, processing files, 
running reports — it needs a system that:
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
- Vanilla HTML/CSS/JS — monitoring dashboard

## How to run it locally

**Requirements:** Python 3.8+, PostgreSQL

**1. Clone the repo**
```bash
git clone [your repo url]
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

## Key Features

**Priority scheduling** — higher priority tasks are always picked up first.

**No race conditions** — uses PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` 
to guarantee each task is executed by exactly one worker, even with 
many workers running simultaneously.

**Automatic retry** — failed tasks are automatically requeued up to 
a configurable maximum retry count, then marked permanently failed 
with the error message stored.

**Dead worker recovery** — every worker sends a heartbeat every 5 seconds. 
A watchdog detects workers whose heartbeat is older than 15 seconds, 
marks them dead, and requeues any tasks they were executing.

**Live monitoring** — WebSocket connection pushes every state change 
to the dashboard instantly. No polling, no page refresh.

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

Reguigui Mohamed saif — IT Student, ISET Rades, Tunisia  
Building motorsport infrastructure and backend systems from scratch.  
[LinkedIn] https://www.linkedin.com/in/saif-reguigui-5a6802341/| [GitHub] https://github.com/saif34701