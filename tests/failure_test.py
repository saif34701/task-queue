import httpx
import time
import subprocess
import sys

API = "http://127.0.0.1:8000"

def get_stats():
    return httpx.get(f"{API}/stats", timeout=5).json()

def get_workers():
    return httpx.get(f"{API}/workers", timeout=5).json()

def submit_tasks(count, task_type="failure_test_task"):
    ids = []
    for i in range(count):
        res = httpx.post(f"{API}/tasks", json={
            "type": task_type,
            "payload": {"index": i},
            "priority": 5,
            "max_retries": 3
        }, timeout=5)
        if res.status_code == 201:
            ids.append(res.json()["id"])
    return ids

def run_failure_test():
    print("=" * 60)
    print("FAILURE TEST — Dead worker recovery under pressure")
    print("=" * 60)

    # Check server
    try:
        httpx.get(f"{API}/", timeout=3)
    except Exception:
        print("ERROR: Server not running.")
        return

    # Baseline
    baseline = get_stats()
    baseline_completed = baseline["completed"]
    print(f"Baseline completed: {baseline_completed}")

    # Step 1 — Submit 50 tasks
    print("\nStep 1 — Submitting 50 tasks...")
    ids = submit_tasks(50)
    print(f"Submitted {len(ids)} tasks")

    # Step 2 — Let workers pick them up
    print("\nStep 2 — Letting workers start processing...")
    time.sleep(3)

    stats = get_stats()
    print(f"After 3s — Pending: {stats['pending']} | Running: {stats['running']} | Completed: {stats['completed'] - baseline_completed}")

    # Step 3 — Check active workers
    workers = get_workers()
    active = [w for w in workers if w["status"] == "ACTIVE"]
    print(f"\nStep 3 — Active workers detected: {len(active)}")
    for w in active:
        print(f"  Worker {w['id']} — completed {w['tasks_completed']} tasks")

    if len(active) == 0:
        print("ERROR: No active workers found. Start at least one worker first.")
        return

    # Step 4 — Instruct user to kill a worker
    print(f"\nStep 4 — ACTION REQUIRED:")
    print(f"  Close one of your worker terminals RIGHT NOW")
    print(f"  You have 10 seconds...")

    for i in range(10, 0, -1):
        print(f"  {i}...", end="\r")
        time.sleep(1)

    print("\n  Time's up.")

    # Step 5 — Wait for dead worker detection
    print(f"\nStep 5 — Waiting for dead worker detection (up to 30s)...")
    detected = False

    for _ in range(15):
        time.sleep(2)
        workers = get_workers()
        dead = [w for w in workers if w["status"] == "DEAD"]
        if dead:
            print(f"  Dead worker detected: {dead[0]['id']}")
            detected = True
            break
        else:
            active_now = [w for w in workers if w["status"] == "ACTIVE"]
            print(f"  Waiting... active workers: {len(active_now)}", end="\r")

    if not detected:
        print("  WARNING: No dead worker detected yet — may need more time")

    # Step 6 — Wait for remaining tasks to complete
    print(f"\nStep 6 — Waiting for surviving workers to complete all tasks...")
    start = time.time()

    while time.time() - start < 120:
        stats = get_stats()
        pending = stats["pending"]
        running = stats["running"]
        completed_now = stats["completed"] - baseline_completed
        print(f"  Pending: {pending} | Running: {running} | Completed: {completed_now}/50", end="\r")

        if pending == 0 and running == 0:
            print()
            break
        time.sleep(2)

    # Final results
    final_stats = get_stats()
    final_workers = get_workers()
    dead_workers = [w for w in final_workers if w["status"] == "DEAD"]
    completed_total = final_stats["completed"] - baseline_completed

    print("\n" + "=" * 60)
    print("FAILURE TEST RESULTS")
    print("=" * 60)
    print(f"Tasks submitted:       50")
    print(f"Tasks completed:       {completed_total}")
    print(f"Dead workers detected: {len(dead_workers)}")
    print(f"Tasks lost:            {max(0, 50 - completed_total)}")
    print("=" * 60)

    if completed_total >= 50 and len(dead_workers) > 0:
        print("RESULT: PASSED — dead worker detected, all tasks recovered")
    elif completed_total >= 50:
        print("RESULT: PASSED — all tasks completed (worker may have finished before dying)")
    else:
        print(f"RESULT: FAILED — {50 - completed_total} tasks not completed")

if __name__ == "__main__":
    run_failure_test()