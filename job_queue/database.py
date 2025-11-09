import sqlite3
import json
import uuid
from datetime import datetime, timedelta

DB_NAME = 'queue.db'
CONFIG_FILE = 'config.json'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL,
            run_at DATETIME NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            output TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            final_state TEXT NOT NULL,
            duration_ms INTEGER NOT NULL,
            logged_at DATETIME NOT NULL
        )
        ''')
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_jobs_poll
        ON jobs (state, run_at, priority)
        ''')
        conn.commit()
    try:
        with open(CONFIG_FILE, 'x') as f:
            default_config = {
                'max_retries': 3,
                'backoff_base': 2
            }
            json.dump(default_config, f, indent=2)
    except FileExistsError:
        pass

def get_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def set_config(key, value):
    config = get_config()
    config[key] = value
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    return config

def enqueue_job(command, job_id=None, priority=0):
    config = get_config()
    now = datetime.utcnow()
    job = {
        'id': job_id or str(uuid.uuid4()),
        'command': command,
        'state': 'pending',
        'attempts': 0,
        'max_retries': int(config.get('max_retries', 3)),
        'run_at': now,
        'created_at': now,
        'updated_at': now,
        'priority': priority,
        'output': None
    }
    with get_db_connection() as conn:
        conn.execute('''
        INSERT INTO jobs (id, command, state, attempts, max_retries, run_at, created_at, updated_at, priority, output)
        VALUES (:id, :command, :state, :attempts, :max_retries, :run_at, :created_at, :updated_at, :priority, :output)
        ''', job)
        conn.commit()
    return job['id']

def get_next_job():
    now = datetime.utcnow()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN EXCLUSIVE TRANSACTION")
            cursor.execute('''
            SELECT * FROM jobs
            WHERE (state = 'pending' OR state = 'failed') AND run_at <= ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
            ''', (now,))
            job = cursor.fetchone()
            if job is None:
                conn.commit()
                return None
            cursor.execute('''
            UPDATE jobs
            SET state = 'processing', updated_at = ?
            WHERE id = ?
            ''', (now, job['id']))
            conn.commit()
            return dict(job)
    except sqlite3.OperationalError as e:
        return None

def set_job_completed(job_id, output):
    with get_db_connection() as conn:
        conn.execute('''
        UPDATE jobs
        SET state = 'completed', updated_at = ?, output = ?
        WHERE id = ?
        ''', (datetime.utcnow(), output, job_id))
        conn.commit()

def set_job_failed(job_id, current_attempts, run_at, output):
    with get_db_connection() as conn:
        conn.execute('''
        UPDATE jobs
        SET state = 'failed', attempts = ?, run_at = ?, updated_at = ?, output = ?
        WHERE id = ?
        ''', (current_attempts, run_at, datetime.utcnow(), output, job_id))
        conn.commit()

def set_job_dead(job_id, output):
    with get_db_connection() as conn:
        conn.execute('''
        UPDATE jobs
        SET state = 'dead', updated_at = ?, output = ?
        WHERE id = ?
        ''', (datetime.utcnow(), output, job_id))
        conn.commit()

def get_jobs_by_state(state):
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM jobs WHERE state = ?", (state,))
        return [dict(row) for row in cursor.fetchall()]

def retry_dead_job(job_id):
    with get_db_connection() as conn:
        conn.execute('''
        UPDATE jobs
        SET state = 'pending', attempts = 0, run_at = ?, updated_at = ?, output = NULL
        WHERE id = ? AND state = 'dead'
        ''', (datetime.utcnow(), datetime.utcnow(), job_id))
        conn.commit()
        return conn.total_changes > 0

def get_status_summary():
    with get_db_connection() as conn:
        cursor = conn.execute('''
        SELECT state, COUNT(*) as count
        FROM jobs
        GROUP BY state
        ''')
        summary = {row['state']: row['count'] for row in cursor.fetchall()}
        return summary

def log_job_metric(job_id, final_state, duration_ms):
    with get_db_connection() as conn:
        conn.execute('''
        INSERT INTO job_metrics (job_id, final_state, duration_ms, logged_at)
        VALUES (?, ?, ?, ?)
        ''', (job_id, final_state, duration_ms, datetime.utcnow()))
        conn.commit()

def get_stats():
    with get_db_connection() as conn:
        stats = {}
        avg_time = conn.execute('''
            SELECT AVG(duration_ms) as avg 
            FROM job_metrics 
            WHERE final_state = 'completed'
        ''').fetchone()
        stats['avg_completion_time_ms'] = avg_time['avg'] or 0
        total_completed = conn.execute('''
            SELECT COUNT(*) as count 
            FROM job_metrics 
            WHERE final_state = 'completed'
        ''').fetchone()
        stats['total_completed'] = total_completed['count']
        total_dead = conn.execute('''
            SELECT COUNT(*) as count 
            FROM job_metrics 
            WHERE final_state = 'dead'
        ''').fetchone()
        stats['total_dead'] = total_dead['count']
        return stats
