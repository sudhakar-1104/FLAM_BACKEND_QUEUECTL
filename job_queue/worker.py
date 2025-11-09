import subprocess
import time
import signal
import sys
import os
from datetime import datetime, timedelta
from . import database

shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    if not shutdown_flag:
        print(f"\n[Worker PID: {os.getpid()}] Shutdown signal received. Finishing current job...", flush=True)
        shutdown_flag = True
    else:
        print(f"[Worker PID: {os.getpid()}] Forced shutdown.", flush=True)
        sys.exit(1)

def run_job(job):
    print(f"[Worker PID: {os.getpid()}] Running job {job['id']}: {job['command']}", flush=True)
    try:
        result = subprocess.run(
            job['command'],
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return (True, result.stdout)
        else:
            print(f"[Worker PID: {os.getpid()}] Job {job['id']} failed. Exit code: {result.returncode}", flush=True)
            return (False, result.stderr)
    except subprocess.TimeoutExpired:
        print(f"[Worker PID: {os.getpid()}] Job {job['id']} timed out.", flush=True)
        return (False, "Error: Job exceeded 5-minute timeout.")
    except Exception as e:
        print(f"[Worker PID: {os.getpid()}] Job {job['id']} had an execution error: {e}", flush=True)
        return (False, str(e))

def process_job_success(job, output, duration_ms):
    print(f"[Worker PID: {os.getpid()}] Job {job['id']} completed successfully.", flush=True)
    database.set_job_completed(job['id'], output)
    database.log_job_metric(job['id'], 'completed', duration_ms)

def process_job_failure(job, output, duration_ms):
    config = database.get_config()
    current_attempts = job['attempts'] + 1
    max_retries = job['max_retries']
    if current_attempts > max_retries:
        print(f"[Worker PID: {os.getpid()}] Job {job['id']} failed {current_attempts - 1} times. Moving to DLQ.", flush=True)
        database.set_job_dead(job['id'], output)
        database.log_job_metric(job['id'], 'dead', duration_ms)
    else:
        base = int(config.get('backoff_base', 2))
        delay_seconds = base ** current_attempts
        next_run_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        print(f"[Worker PID: {os.getpid()}] Job {job['id']} failed (Attempt {current_attempts}/{max_retries}). Retrying in {delay_seconds}s...", flush=True)
        database.set_job_failed(job['id'], current_attempts, next_run_at, output)

def start_worker():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print(f"[Worker] Worker started. Polling for jobs... (PID: {os.getpid()})", flush=True)
    while not shutdown_flag:
        job = None
        try:
            job = database.get_next_job()
            if job:
                start_time = time.monotonic()
                (success, output) = run_job(job)
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if success:
                    process_job_success(job, output, duration_ms)
                else:
                    process_job_failure(job, output, duration_ms)
            else:
                time.sleep(1)
        except Exception as e:
            print(f"[Worker PID: {os.getpid()}] CRITICAL: Error in worker loop: {e}", flush=True)
            if job:
                process_job_failure(job, str(e), 0)
            time.sleep(5)
    print(f"[Worker PID: {os.getpid()}] Worker shutting down gracefully.", flush=True)
