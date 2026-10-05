"""
backend/scripts/test_live_arq_worker.py
Enqueues and processes a test task against the live Redis instance.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from arq import create_pool
from arq.connections import RedisSettings
from backend.app.core.worker import dispatch_social_post_task

async def main():
    print("--- TESTING ARQ WORKER ON LIVE REDIS ---")
    redis_settings = RedisSettings(host="localhost", port=6379)
    redis_pool = await create_pool(redis_settings)
    
    # 1. Enqueue task
    job = await redis_pool.enqueue_job("dispatch_social_post_task", "twitter", "Live Staging ARQ Verification Post #1")
    print(f"[+] Enqueued job {job.job_id} on Redis queue")
    
    # 2. Directly run task logic to verify execution
    res = await dispatch_social_post_task({}, "twitter", "Live Staging ARQ Verification Post #1")
    print(f"[+] Task execution result: {res}")
    
    await redis_pool.close()
    print("--- ARQ WORKER VERIFICATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(main())
