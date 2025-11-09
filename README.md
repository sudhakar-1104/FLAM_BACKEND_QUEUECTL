# FLAM_BACKEND_QUEUECTL

Queuectl is a powerful command-line tool built in Python that helps you manage background jobs with ease. It can run multiple workers at once, automatically retry failed jobs using exponential backoff, and move permanently failed ones to a Dead Letter Queue (DLQ) for later review.

With persistent job storage, support for concurrent processing, and handy extras like job prioritization, output logging, and performance metrics, Queuectl makes reliable and efficient background job management simple and intuitive.

-> Core Features

1.Persistent Job Queue: Queuectl uses SQLite to store all jobs and their statuses, so nothing gets lost even if the system restarts.

2.Multiple Worker Support: You can run several workers simultaneously, allowing multiple jobs to be processed in parallel.

3.Concurrency Safety: Built-in safeguards prevent duplicate work and race conditions by using exclusive transactions for atomic job retrieval.

4.Retry and Backoff: Failed jobs are automatically retried with an exponential delay, giving each subsequent attempt a longer wait time before running again.

5.Dead Letter Queue (DLQ): Jobs that still fail after all retries are moved to a special queue for review and manual handling.

6.Graceful Shutdown: When stopped, workers finish their current tasks cleanly before shutting down, so there are no half-finished or “zombie” processes left behind.

7.Configurable Settings: You can tweak key parameters—like retry limits or concurrency—from the command line, making Queuectl flexible and easy to control.

->Bonus Features

1.Job Priority Queues: You can assign priority levels to jobs so workers always pick up high-priority tasks first.

2.Job Output Logging: Every job’s standard output and error messages are automatically captured and stored in the database, making debugging straightforward.

3.Metrics and Statistics: A built-in stats command gives you useful insights like total jobs completed, failures, and average completion times.

4.Job Timeout Handling: Workers automatically stop any job that runs too long—by default, anything that exceeds 5 minutes—to keep the system efficient and responsive.

->Setup Instructions
To run this project locally, follow these steps:

1.Clone the Repository:

git clone https://github.com/your-username/your-repo-name.git
cd queuectl_project



