from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
from fastapi import FastAPI
from app.services.docker_service import DockerService
from app.models.container import convert_health_metric_to_dynamo
from app.services.dynamodb_service import db
from app.core.config import settings
import logging

mapping = {
    "s": "second",
    "m": "minute",
    "h": "hour"
}

ALLOWED_JOBS = [settings.POLL_DATA_JOB_ID]

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
    scheduler.start()
    yield
    scheduler.shutdown()

def update_to_db_task():
    stats = docker_service.poll_all_container_stats()
    dynamodb_stats = [convert_health_metric_to_dynamo(stat) for stat in stats]

    for stat in dynamodb_stats:
        print(f"Adding item to table: {stat}")
        try:
            db.add_item_to_table("health_metrics", stat.model_dump())
        except Exception as e:
            print(f"Error adding item to table: {e}")

def hidden_task():
    print("This is a hidden task")

def expose_tasks():
    print("This is an exposed task")

scheduler.add_job_every(update_to_db_task, "m", 10, settings.POLL_DATA_JOB_ID)