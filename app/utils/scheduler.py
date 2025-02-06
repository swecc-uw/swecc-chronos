from contextlib import asynccontextmanager
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from fastapi import FastAPI
from app.services.docker_service import DockerService
from app.utils.docker import callback_from_docker_events
from app.models.container import convert_health_metric_to_dynamo
from app.services.dynamodb_service import db
from app.core.config import settings
import logging

from app.utils.task import update_to_db_task, MAPPING_TASKS_TO_ID, compact_data_task

mapping = {
    "s": "second",
    "m": "minute",
    "h": "hour",
    "w": "week",
}

ALLOWED_JOBS = [settings.POLL_DATA_JOB_ID, settings.COMPACT_DATA_JOB_ID]

class Scheduler:
    """Scheduler class for running periodic or one-time tasks."""
    _instance = None
    _paused_job = []

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Scheduler, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
       if not hasattr(self, "_initialized"):
            self.logger = logging.getLogger("Scheduler")
            self.logger.setLevel(logging.INFO)
            logging.basicConfig(level=logging.INFO)
            self.scheduler = AsyncIOScheduler()
            self._initialized = True

    def add_job_at_timestamp(self, func, run_at: datetime, job_id=None):
        """Schedule a one-time job at a specific timestamp."""
        trigger = DateTrigger(run_date=run_at)
        self.scheduler.add_job(func, trigger, id=job_id)

    def add_job_every(self, func, type: str, interval: int = 1, job_id=None):
        """Schedule a job to run every specified interval."""
        if type not in mapping:
            raise ValueError(f"Invalid interval type: {type}")
        trigger = CronTrigger(**{mapping[type]: f"*/{interval}"})
        self.scheduler.add_job(func, trigger, id=job_id)
    
    def add_job_every_second(self, func, interval: int = 1, job_id=None):
        """Schedule a job to run every specified number of seconds."""
        trigger = CronTrigger(second=f"*/{interval}")
        self.scheduler.add_job(func, trigger, id=job_id)
    
    def add_job_every_minute(self, func, interval: int = 1, job_id=None):
        """Schedule a job to run every specified number of minutes."""
        trigger = CronTrigger(minute=f"*/{interval}")
        self.scheduler.add_job(func, trigger, id=job_id)

    def add_job_every_hour(self, func, interval: int = 1, job_id=None):
        """Schedule a job to run every specified number of hours."""
        trigger = CronTrigger(hour=f"*/{interval}")
        self.scheduler.add_job(func, trigger, id=job_id)

    def add_job_every_week(self, func, interval: int = 1, job_id=None):
        """Schedule a job to run every weeks."""
        trigger = CronTrigger(week=f"*/{interval}")
        self.scheduler.add_job(func, trigger, id=job_id)

    def add_job_daily(self, func, hour: int = 0, minute: int = 0, second: int = 0, job_id=None):
        """Schedule a job to run daily at a specific time."""
        trigger = CronTrigger(hour=hour, minute=minute, second=second)
        self.scheduler.add_job(func, trigger, id=job_id)

    def remove_job(self, job_id):
        """Remove a scheduled job by its ID."""
        self.scheduler.remove_job(id=job_id)
    
    def list_jobs(self):
        """List all active jobs."""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            if(job.id not in ALLOWED_JOBS):
                jobs.remove(job)
        return [job.id for job in jobs]

    def pause_job(self, job_id):
        """Pause a scheduled job."""
        # preliminary hide jobs from the list
        if(job_id in ALLOWED_JOBS):
            self.scheduler.pause_job(job_id)
            self._paused_job.append(job_id)

    def resume_job(self, job_id):
        """Resume a paused job."""
        if(job_id in ALLOWED_JOBS):
            self.scheduler.resume_job(job_id)
            self._paused_job.remove(job_id)

    def get_job_status(self, job_id):
        """Get the status of a job."""
        if(job_id in ALLOWED_JOBS):
            if(job_id in self._paused_job):
                return {job_id: "paused"}
            else:
                return {job_id: "running"}
        else:
            return "Job not found"

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()

    def shutdown(self):
        """Shutdown the scheduler."""
        self.scheduler.shutdown()


# Singleton instance of the Scheduler class
scheduler = Scheduler()
docker_service = DockerService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Docker event listener...")  # Debug
    scheduler.start()
    # run another process
    task = asyncio.create_task(listen_to_docker_events())
    yield
    task.cancel()
    scheduler.shutdown()

scheduler.add_job_every(update_to_db_task, "h", 10, MAPPING_TASKS_TO_ID[update_to_db_task])
scheduler.add_job_every(compact_data_task, "w", 2, MAPPING_TASKS_TO_ID[compact_data_task])

async def listen_to_docker_events():
    """Background task to listen for Docker events asynchronously."""
    def read_events():
        for event in docker_service.get_socket_conenction():
            callback_from_docker_events(event)

    await asyncio.to_thread(read_events)