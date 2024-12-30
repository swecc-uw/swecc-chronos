from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router as api_router
from app.utils.scheduler import lifespan, scheduler

def ticker():
    print("Tick")

scheduler.add_job_every(ticker, "s", 2, job_id="ticker")


app = FastAPI(
    title="Docker Stats API",
    description="API for monitoring Docker container statistics",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="")