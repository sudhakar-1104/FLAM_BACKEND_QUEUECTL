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










