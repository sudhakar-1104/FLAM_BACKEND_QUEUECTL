#!/usr/bin/env python

"""
queuectl - The main entry point for the job queue CLI.
"""

import sys
from job_queue import cli, database

def main():
    """
    The main function.
    1. Initializes the database and config.
    2. Runs the main CLI.
    """
    
    try:
        database.init_db()
    except Exception as e:
        print(f"FATAL: Could not initialize database: {e}", file=sys.stderr)
        sys.exit(1)
    
    cli.cli()

if __name__ == "__main__":
    main()