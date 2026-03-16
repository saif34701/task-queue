import httpx
import time
import concurrent.futures
from datetime import datetime

API = "http://127.0.0.1:8000"
TOTAL_TASKS = 1000
CONCURRENT_WORKERS = 10

def submit_task(i):
    try:
        response = httpx.post(f"{API}/tasks", json={
            "type": "load_test_task",
            "payload": {"index": i},
            "priority": (i % 10) + 1,
            "max_retries": 1
        }, timeout=10)
        if response.status_code == 201:
            return ("submitted", response.json()["id"])
        return ("failed_submit", None)
    except Exception as e:
        return ("error", str(e))

def wait_for_completion(submitted_ids, timeout=300):
    print(f"\nWaiting for {len(submitted_ids)} tasks to complete...")
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            res = httpx.get(f"{API}/stats", timeout=5)
            stats = res.json()
            
            completed = stats["completed"]
            pending = stats["pending"]
            running = stats["running"]
            failed = stats["failed"]
            
            print(f"  Pending: {pending} | Running: {running} | Completed: {completed} | Failed: {failed}", end="\r")
            
            if pending == 0 and running == 0:
                print()
                return stats
                
        except Exception as e:
            print(f"\nError checking stats: {e}")
        
        time.sleep(2)
    
    print("\nTimeout reached")
    return None

def run_load_test():
    print("=" * 60)
    print(f"LOAD TEST — {TOTAL_TASKS} tasks, {CONCURRENT_WORKERS} concurrent submitters")
    print("=" * 60)

    # Check server is running
    try:
        httpx.get(f"{API}/", timeout=3)
    except Exception:
        print("ERROR: Server is not running. Start it first.")
        return

    # Get baseline stats before test
    baseline = httpx.get(f"{API}/stats").json()
    baseline_completed = baseline["completed"]
    print(f"Baseline completed tasks before test: {baseline_completed}")

    # Submit all tasks concurrently
    print(f"\nSubmitting {TOTAL_TASKS} tasks with {CONCURRENT_WORKERS} concurrent submitters...")
    submit_start = time.time()
    submitted_ids = []
    failed_submissions = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [executor.submit(submit_task, i) for i in range(TOTAL_TASKS)]
        for future in concurrent.futures.as_completed(futures):
            status, task_id = future.result()
            if status == "submitted":
                submitted_ids.append(task_id)
            else:
                failed_submissions += 1

    submit_duration = time.time() - submit_start
    print(f"Submitted {len(submitted_ids)} tasks in {submit_duration:.2f}s")
    print(f"Failed submissions: {failed_submissions}")

    if failed_submissions > 0:
        print("WARNING: Some tasks failed to submit")

    # Wait for all tasks to complete
    process_start = time.time()
    final_stats = wait_for_completion(submitted_ids)
    process_duration = time.time() - process_start

    if final_stats is None:
        print("RESULT: Test timed out")
        return

    # Calculate results
    new_completed = final_stats["completed"] - baseline_completed
    expected = len(submitted_ids)
    lost = max(0, expected - new_completed)
    
    print("\n" + "=" * 60)
    print("LOAD TEST RESULTS")
    print("=" * 60)
    print(f"Tasks submitted:     {expected}")
    print(f"Tasks completed:     {new_completed}")
    print(f"Tasks failed:        {final_stats['failed']}")
    print(f"Tasks lost:          {lost}")
    print(f"Submit time:         {submit_duration:.2f}s")
    print(f"Processing time:     {process_duration:.2f}s")
    print(f"Throughput:          {new_completed / process_duration:.1f} tasks/sec")
    print("=" * 60)

    if lost == 0:
        print("RESULT: PASSED — zero tasks lost")
    else:
        print(f"RESULT: FAILED — {lost} tasks were lost")

if __name__ == "__main__":
    run_load_test()