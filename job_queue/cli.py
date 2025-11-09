import click
import json
from . import database, worker as worker_logic, worker_manager

@click.group()
def cli():
    pass

@cli.command()
@click.option('--command', '-c', 'command', required=True, help='The shell command to execute.')
@click.option('--id', 'job_id', default=None, help='A specific ID for the job (optional).')
@click.option('--priority', '-p', 'priority', type=int, default=0, help='Job priority (e.g., 10 > 0). Default: 0.')
def enqueue(command, job_id, priority):
    try:
        enqueued_id = database.enqueue_job(command, job_id=job_id, priority=priority)
        click.echo(f"✅ Job '{enqueued_id}' enqueued successfully.")
    except Exception as e:
        click.echo(f"Error enqueuing job: {e}", err=True)

@cli.group()
def worker():
    pass

@worker.command(name='start')
@click.option('--count', default=1, help='Number of workers to start.')
def start(count):
    worker_manager.start_workers(count)

@worker.command(name='stop')
def stop():
    worker_manager.stop_workers()

@cli.command()
def status():
    summary = database.get_status_summary()
    active_workers = worker_manager.get_worker_status()
    click.echo("--- Job Queue Status ---")
    click.echo(f"  Pending:    {summary.get('pending', 0)}")
    click.echo(f"  Processing: {summary.get('processing', 0)}")
    click.echo(f"  Completed:  {summary.get('completed', 0)}")
    click.echo(f"  Failed:     {summary.get('failed', 0)}")
    click.echo(f"  Dead (DLQ): {summary.get('dead', 0)}")
    click.echo("------------------------")
    click.echo(f"  Active Workers: {active_workers}")

@cli.command(name='list')
@click.option('--state', 
              type=click.Choice(['pending', 'processing', 'completed', 'dead', 'failed'], case_sensitive=False),
              required=True,
              help='Filter jobs by state.')
@click.option('--output', is_flag=True, help='Show the output of the jobs.')
def list_jobs(state, output):
    jobs = database.get_jobs_by_state(state.lower())
    if not jobs:
        click.echo(f"No jobs found with state '{state}'.")
        return
    click.echo(f"--- Jobs ({state.upper()}) ---")
    for job in jobs:
        click.echo(f"  ID: {job['id']} | Attempts: {job['attempts']} | Priority: {job['priority']} | Command: {job['command']}")
        if output and job['output']:
            click.echo("    --- Output ---")
            for line in job['output'].strip().splitlines():
                click.echo(f"    {line}")
            click.echo("    --------------")

@cli.group()
def dlq():
    pass

@dlq.command(name='list')
@click.option('--output', is_flag=True, help='Show the output of the jobs.')
def dlq_list(output):
    jobs = database.get_jobs_by_state('dead')
    if not jobs:
        click.echo("DLQ is empty.")
        return
    click.echo("--- Dead Letter Queue (DLQ) ---")
    for job in jobs:
        click.echo(f"  ID: {job['id']} | Attempts: {job['attempts']} | Priority: {job['priority']} | Command: {job['command']}")
        if output and job['output']:
            click.echo("    --- Output ---")
            for line in job['output'].strip().splitlines():
                click.echo(f"    {line}")
            click.echo("    --------------")

@dlq.command(name='retry')
@click.argument('job_id')
def dlq_retry(job_id):
    success = database.retry_dead_job(job_id)
    if success:
        click.echo(f"✅ Job '{job_id}' moved from DLQ back to 'pending'.")
    else:
        click.echo(f"Error: Job '{job_id}' not found in DLQ.", err=True)

@cli.group()
def config():
    pass

@config.command(name='set')
@click.argument('key', type=click.Choice(['max_retries', 'backoff_base']))
@click.argument('value')
def config_set(key, value):
    try:
        value_to_set = int(value)
    except ValueError:
        click.echo("Error: Value must be an integer.", err=True)
        return
    database.set_config(key, value_to_set)
    click.echo(f"✅ Config updated: {key} = {value_to_set}")

@config.command(name='show')
def config_show():
    config = database.get_config()
    click.echo(json.dumps(config, indent=2))

@cli.command()
def stats():
    stats = database.get_stats()
    click.echo("--- Execution Stats ---")
    click.echo(f"  Total Jobs Completed: {stats.get('total_completed', 0)}")
    click.echo(f"  Total Jobs Failed (DLQ): {stats.get('total_dead', 0)}")
    click.echo(f"  Avg. Completion Time: {stats.get('avg_completion_time_ms', 0):.2f} ms")

@cli.command(hidden=True)
def run_worker_internal():
    worker_logic.start_worker()
