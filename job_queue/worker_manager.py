import subprocess
import sys
import os
import signal
import time

PID_FILE = '.worker_pids'

def start_workers(count):
    pids = get_running_pids()
    print(f"Starting {count} new worker(s)...")
    for i in range(count):
        stdout_log_file = f"worker_{i}.stdout.log"
        stderr_log_file = f"worker_{i}.stderr.log"
        stdout_log = open(stdout_log_file, "w")
        stderr_log = open(stderr_log_file, "w")
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
        process = subprocess.Popen(
            [sys.executable, 'queuectl.py', 'run-worker-internal'],
            stdout=stdout_log,
            stderr=stderr_log,
            preexec_fn=os.setsid if sys.platform != "win32" else None,
            creationflags=creation_flags
        )
        pids.append(process.pid)
        print(f"  -> Started worker with PID: {process.pid}")
        print(f"     (Check {stderr_log_file} for errors)")
    save_running_pids(pids)

def stop_workers():
    pids = get_running_pids()
    if not pids:
        print("No active workers found.")
        return
    print("Sending graceful shutdown signal to all workers...")
    for pid in pids:
        try:
            if sys.platform == "win32":
                os.kill(pid, signal.CTRL_C_EVENT)
            else:
                os.killpg(pid, signal.SIGTERM)
            print(f"  -> Sent stop signal to worker {pid}")
        except Exception as e:
            print(f"  -> Error sending signal to {pid}: {e}")
    print("Waiting for workers to exit (up to 10 seconds)...")
    timeout = 10
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        if get_worker_status() == 0:
            break
        time.sleep(0.5)
    active_count = get_worker_status()
    if active_count > 0:
        print(f"Warning: {active_count} worker(s) did not shut down gracefully. Forcing stop...")
        pids = get_running_pids()
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                pass
    save_running_pids([])
    print("All workers stopped.")

def get_running_pids():
    if not os.path.exists(PID_FILE):
        return []
    try:
        with open(PID_FILE, 'r') as f:
            pids = [int(pid) for pid in f.read().splitlines() if pid.strip()]
        return pids
    except FileNotFoundError:
        return []

def save_running_pids(pids):
    with open(PID_FILE, 'w') as f:
        for pid in pids:
            f.write(f"{pid}\n")

def get_worker_status():
    pids = get_running_pids()
    active_count = 0
    cleaned_pids = []
    for pid in pids:
        try:
            os.kill(pid, 0)
            active_count += 1
            cleaned_pids.append(pid)
        except Exception:
            pass
    if len(cleaned_pids) != len(pids):
        save_running_pids(cleaned_pids)
    return active_count
