# simulate_job_submission.py
# Script to populate the jobs table with jobs from the SWF trace file
import pandas as pd
import os
from sqlalchemy import create_engine
from db.db_models import Base, Job
from datetime import datetime
from services.cpu_predictor import CPUPredictor
from services.mem_predictor import MemPredictor

# Paths
DATA_PATH = '/home/tobbaco-inspection-robot/InternProject/zchpc-ai-scheduler/data/HPC2N-2002-2.2-cln.swf'
DB_PATH = os.path.join(os.path.dirname(__file__), 'data/scheduler.db')
engine = create_engine(f'sqlite:///{DB_PATH}')

# Read SWF file
swf_cols = [
    'job_id', 'submit_time', 'wait_time', 'run_time', 'allocated_cpu', 'used_cpu',
    'requested_mem', 'used_mem', 'requested_time', 'status', 'user_id', 'group_id',
    'executable_num', 'queue_name', 'partition', 'preceding_job_id', 'think_time', 'placeholder'
]
df = pd.read_csv(
    DATA_PATH,
    sep=r'\s+',
    comment=';',
    header=None,
    engine='python'
)
df.columns = swf_cols

# Only keep jobs with valid submit_time and requested resources
jobs = df[(df['submit_time'] > 0) & (df['requested_mem'] > 0) & (df['requested_time'] > 0)]

# Convert submit_time to datetime (assuming seconds since epoch)
jobs['submit_time'] = pd.to_datetime(jobs['submit_time'], unit='s', errors='coerce')

cpu_predictor = CPUPredictor()
mem_predictor = MemPredictor()

# Insert jobs into DB
with engine.begin() as conn:
    for _, row in jobs.iterrows():
        # Prepare job dict for prediction
        job_dict = row.to_dict()
        cpu_pred = cpu_predictor.predict(job_dict)
        mem_pred = mem_predictor.predict(job_dict)
        job = Job(
            job_id=int(row['job_id']),
            user=str(row['user_id']),
            req_cpus=int(row['allocated_cpu']) if not pd.isna(row['allocated_cpu']) else 1,
            req_mem_gb=float(row['requested_mem'])/1024 if not pd.isna(row['requested_mem']) else 1.0,
            pred_cpu_cores=cpu_pred.get('pred_cpu_cores', None),
            pred_mem_gb=mem_pred.get('pred_mem_gb', None),
            state='PENDING',
            submit_time=row['submit_time'],
            rl_action='RUN',
            partition=str(row['partition']) if not pd.isna(row['partition']) else None,
            est_run_time=int(row['requested_time']) if not pd.isna(row['requested_time']) else None
        )
        conn.execute(Job.__table__.insert().prefix_with('OR IGNORE'), job.__dict__)
print(f"Inserted {len(jobs)} jobs into the database.")
