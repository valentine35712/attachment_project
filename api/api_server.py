# api_server.py
# REST API for dashboard and tools
from fastapi import FastAPI, Query, BackgroundTasks
from typing import List, Optional
import uvicorn
import datetime
import threading
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from db.db_models import Base, Job, Decision
from services.slurm_poller import poll_slurm
from services.cpu_predictor import CPUPredictor
from services.mem_predictor import MemPredictor
from services.rl_scheduler import RLScheduler
from services.simulator import simulate
import logging
from threading import Event
from fastapi.openapi.utils import get_openapi

# SQLite DB for simplicity
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/scheduler.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

app = FastAPI()

cpu_predictor = CPUPredictor()
mem_predictor = MemPredictor()
rl_scheduler = RLScheduler()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

poll_stop_event = Event()

# --- Helper: Poll SLURM, predict, RL, store jobs ---
def update_job_queue():
    try:
        jobs = poll_slurm()
        session = Session()
        for job in jobs:
            job = cpu_predictor.predict(job)
            if not job.get('pred_cpu_cores'):
                job['pred_cpu_cores'] = job.get('req_cpus', 0)
            job = mem_predictor.predict(job)
            if not job.get('pred_mem_gb'):
                job['pred_mem_gb'] = job.get('req_mem_gb', 0)
        jobs = rl_scheduler.decide(jobs, cluster_state=None)
        # Store/update jobs in DB
        for job in jobs:
            db_job = session.query(Job).filter_by(job_id=job['job_id']).first()
            if not db_job:
                db_job = Job(job_id=job['job_id'])
            db_job.user = job['user']
            db_job.req_cpus = job['req_cpus']
            db_job.req_mem_gb = job['req_mem_gb']
            db_job.pred_cpu_cores = job['pred_cpu_cores']
            db_job.pred_mem_gb = job['pred_mem_gb']
            db_job.state = job['state']
            db_job.submit_time = datetime.datetime.now()  # Could parse from job['submit_time']
            db_job.rl_action = job['rl_action']
            db_job.partition = job.get('partition')
            db_job.est_run_time = job.get('est_run_time')
            session.merge(db_job)
        session.commit()
        session.close()
        logger.info(f"Updated job queue with {len(jobs)} jobs.")
        return jobs
    except Exception as e:
        logger.error(f"Error updating job queue: {e}")
        return []

# --- Background polling using FastAPI BackgroundTasks ---
def poller_thread():
    import time
    from services.slurm_poller import USE_MOCK
    interval = 5
    try:
        import yaml
        config_path = os.path.join(os.path.dirname(__file__), '../config/service_config.yaml')
        if os.path.exists(config_path):
            with open(config_path) as f:
                config = yaml.safe_load(f)
            interval = config.get('poll_interval_sec', 5)
    except Exception:
        pass
    while not poll_stop_event.is_set():
        update_job_queue()
        time.sleep(interval)

@app.on_event("startup")
def start_background_tasks():
    import threading
    threading.Thread(target=poller_thread, daemon=True).start()

@app.on_event("shutdown")
def stop_background_tasks():
    poll_stop_event.set()

@app.get("/queue")
def get_queue():
    session = Session()
    jobs = session.query(Job).order_by(Job.submit_time.desc()).all()
    result = [
        {
            'job_id': j.job_id,
            'user': j.user,
            'req_cpus': j.req_cpus,
            'pred_cpu_cores': j.pred_cpu_cores,
            'req_mem_gb': j.req_mem_gb,
            'pred_mem_gb': j.pred_mem_gb,
            'state': j.state,
            'submit_time': j.submit_time,
            'rl_action': j.rl_action
        } for j in jobs
    ]
    session.close()
    return result

@app.get("/rl-decisions")
def get_rl_decisions():
    session = Session()
    jobs = session.query(Job).order_by(Job.submit_time.desc()).all()
    # Simulate cluster state and get metrics
    job_dicts = [
        {
            'job_id': j.job_id,
            'user': j.user,
            'req_cpus': j.req_cpus,
            'pred_cpu_cores': j.pred_cpu_cores,
            'req_mem_gb': j.req_mem_gb,
            'pred_mem_gb': j.pred_mem_gb,
            'state': j.state,
            'submit_time': j.submit_time,
            'rl_action': j.rl_action
        } for j in jobs
    ]
    metrics = simulate(job_dicts, cluster_state=None)
    session.close()
    return {'jobs': job_dicts, 'metrics': metrics}

@app.get("/history")
def get_history(start: Optional[str] = Query(None), end: Optional[str] = Query(None)):
    session = Session()
    q = session.query(Decision)
    if start:
        q = q.filter(Decision.timestamp >= start)
    if end:
        q = q.filter(Decision.timestamp <= end)
    decisions = q.order_by(desc(Decision.timestamp)).all()
    result = [
        {
            'job_id': d.job_id,
            'action': d.action,
            'timestamp': d.timestamp,
            'pre_util': d.pre_util,
            'post_util': d.post_util
        } for d in decisions
    ]
    session.close()
    return result

@app.post("/override")
def override_decision(job_id: int, action: str):
    session = Session()
    # Validate input
    if not isinstance(job_id, int) or not isinstance(action, str):
        return {"error": "Invalid input."}
    # Log override as a decision
    decision = Decision(job_id=job_id, action=action, timestamp=datetime.datetime.now(), pre_util=None, post_util=None)
    session.add(decision)
    # Optionally update job action
    job = session.query(Job).filter_by(job_id=job_id).first()
    if job:
        job.rl_action = action
        session.merge(job)
    session.commit()
    session.close()
    logger.info(f"Override: job_id={job_id}, action={action}")
    return {"job_id": job_id, "action": action}

# --- New: Simulated Job Log Endpoint ---
@app.get("/simlog")
def get_simulated_job_log():
    session = Session()
    jobs = session.query(Job).order_by(Job.submit_time.desc()).all()
    result = [
        {
            'job_id': j.job_id,
            'user': j.user,
            'req_cpus': j.req_cpus,
            'pred_cpu_cores': j.pred_cpu_cores,
            'req_mem_gb': j.req_mem_gb,
            'pred_mem_gb': j.pred_mem_gb,
            'state': j.state,
            'submit_time': j.submit_time,
            'rl_action': j.rl_action,
            'partition': j.partition,
            'est_run_time': j.est_run_time
        } for j in jobs
    ]
    session.close()
    return result

@app.get("/openapi.json", include_in_schema=False)
def custom_openapi():
    return get_openapi(
        title="AI-Driven SLURM Scheduler API",
        version="1.0.0",
        routes=app.routes,
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
