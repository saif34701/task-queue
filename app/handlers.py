import time

def handle_send_email(payload: dict) -> dict:
    to = payload.get("to", "unknown")
    subject = payload.get("subject", "no subject")
    print(f"  Sending email to {to} — subject: {subject}")
    time.sleep(1)
    return {"sent_to": to, "subject": subject, "status": "delivered"}

def handle_generate_report(payload: dict) -> dict:
    report_type = payload.get("type", "unknown")
    print(f"  Generating report: {report_type}")
    time.sleep(2)
    return {"report_type": report_type, "pages": 12, "status": "generated"}

def handle_process_file(payload: dict) -> dict:
    filename = payload.get("filename", "unknown")
    print(f"  Processing file: {filename}")
    time.sleep(1.5)
    return {"filename": filename, "rows_processed": 1042, "status": "done"}

def handle_send_notification(payload: dict) -> dict:
    user_id = payload.get("user_id", "unknown")
    message = payload.get("message", "")
    print(f"  Sending notification to user {user_id}: {message}")
    time.sleep(0.5)
    return {"user_id": user_id, "delivered": True}

# Registry — maps task type strings to handler functions
TASK_REGISTRY = {
    "send_email": handle_send_email,
    "generate_report": handle_generate_report,
    "process_file": handle_process_file,
    "send_notification": handle_send_notification,
}

def execute_registered_task(task_type: str, payload: dict) -> dict:
    handler = TASK_REGISTRY.get(task_type)
    if handler is None:
        raise ValueError(f"Unknown task type: '{task_type}' — register a handler in handlers.py")
    return handler(payload or {})