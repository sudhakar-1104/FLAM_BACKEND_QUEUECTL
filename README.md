# queuectl - CLI Job Queue System

`queuectl` is a robust, CLI-based background job queue system built in Python. It manages background jobs with multiple workers, handles automatic retries with exponential backoff, and maintains a Dead Letter Queue (DLQ) for permanently failed jobs.

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
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
cd queuectl_project


Next, install the required Python dependencies:
pip install -r requirements.txt

Finally, initialize the database by running any command. status is a good first command:
python queuectl.py status

```
⌨️ CLI Command Reference
```bash
All commands are run using python queuectl.py.

1.Enqueue (Add a Job)
Adds a new job to the queue. The --priority flag is optional (default is 0).

# Add a normal job (default priority 0)
python queuectl.py enqueue -c "echo 'Normal job'" --id "job-1"

# Add a high-priority job (runs first)
python queuectl.py enqueue -c "echo 'HIGH PRIORITY'" --id "job-2" -p 10

2.Workers (Start/Stop)
Start or stop background workers.

# Start 3 workers in the background
python queuectl.py worker start --count 3

# Stop all workers gracefully
python queuectl.py worker stop

3.Get a real-time summary of the queue.

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

4.List Jobs (with Output)
List jobs in any state. Use the --output flag to see the saved command output.

# List failed jobs
python queuectl.py list --state failed

# List completed jobs and see their output
python queuectl.py list --state completed --output

5.DLQ (Dead Letter Queue)
Manage jobs that have permanently failed.

# List all jobs in the DLQ
python queuectl.py dlq list

# See the final error output of a dead job
python queuectl.py dlq list --output

# Retry a job from the DLQ (resets attempts to 0)
python queuectl.py dlq retry <job-id>

6.Stats (Metrics)
Check the historical metrics for your queue.

python queuectl.py stats

Example Output:

--- Execution Stats ---
  Total Jobs Completed: 12
  Total Jobs Failed (DLQ): 3
  Avg. Completion Time: 1530.50 ms

7.Config (Manage Settings)
Manage the system configuration.

# Set the default max retries for new jobs
python queuectl.py config set max_retries 2

# Set the backoff base (e.g., 10^1s, 10^2s...)
python queuectl.py config set backoff_base 10

# View the current configuration
python queuectl.py config show

```












