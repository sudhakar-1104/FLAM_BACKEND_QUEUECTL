
# queuectl - CLI Job Queue System

`queuectl` is a robust, CLI-based background job queue system built in Python. It manages background jobs with multiple workers, handles automatic retries with exponential backoff,
and maintains a Dead Letter Queue (DLQ) for permanently failed jobs.

This project includes persistent job storage, concurrent worker support, and several bonus features, including job priorities, command output logging, and execution metrics.


## 🚀 Core Features

* **Persistent Job Queue:** Uses SQLite to ensure jobs and their states are not lost on restart.
* **Multiple Worker Support:** Can run multiple worker processes in parallel to process jobs concurrently.
* **Concurrency Safe:** Prevents race conditions by using database locking (`BEGIN EXCLUSIVE TRANSACTION`).
* **Retry & Backoff:** Automatically retries failed jobs using an exponential backoff delay.
* **Dead Letter Queue (DLQ):** Moves jobs to a `dead` state after all retries are exhausted.
* **Robust Graceful Shutdown:** The `worker stop` command correctly waits for all workers to shut down, preventing "zombie" processes.
* **Configurable:** Key settings (like `max_retries`) can be managed from the CLI.

## ✨ Bonus Features

* **Job Priority Queues:** Workers process higher-priority jobs first.
* **Job Output Logging:** Captures the `stdout` and `stderr` of every job for easy debugging.
* **Metrics & Stats:** A `stats` command provides historical data on job completion.
* **Job Timeout Handling:** Workers will time out jobs that run for longer than 5 minutes.

---

## ⚙️ Setup Instructions

First, clone the repository to your local machine:
```bash
git clone https://github.com/sudhakar-1104/FLAM_BACKEND_QUEUECTL.git
cd FLAM_BACKEND_QUEUECTL

Next, install the required Python dependencies:

#install
pip install -r requirements.txt

Finally, initialize the database by running any command. status is a good first command:

#initialise
python queuectl.py status

```
⌨️ CLI Command Reference
```bash
All commands are run using python queuectl.py.

1.Enqueue (Add a Job) - Adds a new job to the queue. The --priority flag is optional (default is 0).

# Add a normal job (default priority 0)
python queuectl.py enqueue -c "echo 'Normal job'" --id "job-1"

# Add a high-priority job (runs first)
python queuectl.py enqueue -c "echo 'HIGH PRIORITY'" --id "job-2" -p 10

2.Workers (Start/Stop) - Start or stop background workers.

# Start 3 workers in the background
python queuectl.py worker start --count 3

# Stop all workers gracefully
python queuectl.py worker stop

3.Get a real-time summary of the queue.

#status
python queuectl.py status

Example Output:

--- Job Queue Status ---
  Pending:    1
  Processing: 2
  Completed:  10
  Failed:     1   
  Dead (DLQ): 0
------------------------
  Active Workers: 3


4.List Jobs (with Output) - List jobs in any state. Use the --output flag to see the saved command output.

# List failed jobs
python queuectl.py list --state failed

# List completed jobs and see their output
python queuectl.py list --state completed --output

5.DLQ (Dead Letter Queue) - Manage jobs that have permanently failed.

# List all jobs in the DLQ
python queuectl.py dlq list

# See the final error output of a dead job
python queuectl.py dlq list --output

# Retry a job from the DLQ (resets attempts to 0)
python queuectl.py dlq retry <job-id>

6.Stats (Metrics) - Check the historical metrics for your queue.

python queuectl.py stats

Example Output:

--- Execution Stats ---
  Total Jobs Completed: 12
  Total Jobs Failed (DLQ): 3
  Avg. Completion Time: 1530.50 ms


7.Config (Manage Settings) - Manage the system configuration.

# Set the default max retries for new jobs
python queuectl.py config set max_retries 2

# Set the backoff base (e.g., 10^1s, 10^2s...)
python queuectl.py config set backoff_base 10

# View the current configuration
python queuectl.py config show

```

## Architecture & Design
```bash

1.Components:

->CLI (cli.py): The user interface, built with click.
->Database (database.py): The SQLite database layer. It is the single source of truth and the main communication bus between the CLI and workers.
->Worker (worker.py): The background process that polls the database, runs jobs, and handles all retry/DLQ logic.
->Manager (worker_manager.py): Starts, stops, and monitors worker processes robustly, ensuring graceful shutdowns.

2.Job Lifecycle - This system uses a 5-state lifecycle to track jobs:

->pending: Waiting to be picked up.
->processing: A worker has locked the job and is running it.
->completed: The job finished with a 0 exit code.
->failed: The job failed and is waiting in a backoff delay to be retried.
->dead: The job failed all its retries and is in the DLQ.

3.Concurrency & Robustness:

->Locking: To prevent "duplicate processing," the get_next_job function locks the database with BEGIN EXCLUSIVE TRANSACTION.
 This ensures only one worker can "claim" a job, making the system safe for concurrency.
->Graceful Shutdown: The worker stop command now waits for all worker processes to exit.
 This solves the "zombie process" bug on Windows and ensures files (queue.db, logs) are unlocked properly.

```

## Testing Instructions

```bash

1. Clean Up - (First, close any old terminals/editors to kill "zombie" processes.):

#clean
del worker_*.log, .worker_pids, queue.db, config.json

2. Enqueue Test Jobs:

# Low priority job
python queuectl.py enqueue -c "timeout /t 3" --id "job-low" -p 1

# HIGH priority job (will run first)
python queuectl.py enqueue -c "echo HIGH PRIORITY" --id "job-high" -p 10

# Failing job
python queuectl.py enqueue -c "ls /nonexistent" --id "job-fail"

3. Start Workers:

python queuectl.py worker start --count 2

4. Observe - Wait 15-20 seconds. Run python queuectl.py status and you will see:

->job-high move to completed.

->job-low move to processing, then completed.

->job-fail move to failed, then dead (DLQ).

5. Stop Workers (Test Shutdown)

python queuectl.py worker stop

6. Verify Results

->Check Output: python queuectl.py dlq list --output (You will see the error message for job-fail.)

->Check Stats: python queuectl.py stats (You will see Completed: 2, Dead (DLQ): 1.)

Check Robust Shutdown:
#check
del worker_*.log, .worker_pids

```





