# slurm_poller.py
# Periodically polls SLURM for job queue info and outputs job objects
import time
import subprocess
import json
import logging
import yaml
import os
import pandas as pd
import numpy as np
import datetime

# Load config (mock/real mode)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '../config/service_config.yaml')
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    USE_MOCK = config.get('use_mock_slurm', True)
else:
    USE_MOCK = True

logger = logging.getLogger("slurm_poller")
logging.basicConfig(level=logging.INFO)

SWF_PATH = '/home/tobbaco-inspection-robot/InternProject/zchpc-ai-scheduler/data/RICC-2010-2.swf'

# Helper to parse SWF file and yield jobs in the required format
class SWFJobFeeder:
    def __init__(self, swf_path):
        self.swf_path = swf_path
        self.jobs = self._load_jobs()
        self.idx = 0

    def _load_jobs(self):
        jobs = []
        with open(self.swf_path, 'r') as f:
            for line in f:
                if line.startswith(';') or not line.strip():
                    continue
                fields = line.strip().split()
                if len(fields) < 18:
                    continue
                # Parse fields according to SWF spec
                job_id = int(fields[0])
                submit_time = int(fields[1])
                wait_time = int(fields[2])
                run_time = int(fields[3])
                proc_req = int(fields[4])
                mem_req = float(fields[9]) if fields[9] != '-1' else 1.0  # fallback if missing
                user = f"user{int(fields[11]) if fields[11] != '-1' else 0}"
                state = 'PENDING'  # All jobs start as pending in mock
                partition = 'default'
                # Feature engineering for model input
                req_cpus = proc_req
                req_mem_gb = mem_req / 1024 if mem_req > 32 else mem_req  # SWF is KB, MB, or GB, fallback
                feature3 = float(fields[6]) if fields[6] != '-1' else 0.0  # user est runtime
                feature4 = float(fields[7]) if fields[7] != '-1' else 0.0  # user est proc
                feature5 = float(fields[8]) if fields[8] != '-1' else 0.0  # queue
                feature6 = float(fields[13]) if fields[13] != '-1' else 0.0  # think time from SWF
                est_run_time = run_time if run_time > 0 else 60
                # Use numeric timestamp for submit_time for ML predictors
                jobs.append({
                    "job_id": job_id,
                    "user": user,
                    "user_id": int(fields[11]) if fields[11] != '-1' else 0,
                    "state": state,
                    "req_cpus": req_cpus,
                    "req_mem_gb": req_mem_gb,
                    "requested_mem": req_mem_gb,
                    "requested_time": est_run_time,
                    "feature3": feature3,
                    "feature4": feature4,
                    "feature5": feature5,
                    "feature6": feature6,
                    "partition": partition,
                    "est_run_time": est_run_time,
                    # Use numeric timestamp for submit_time
                    "submit_time": submit_time,
                    "hour_of_day": datetime.datetime.fromtimestamp(submit_time).hour,
                    "day_of_week": datetime.datetime.fromtimestamp(submit_time).weekday(),
                    "queue_name": 0,
                    "group_id": 0,
                    "executable_num": 0,
                    # Set predictions to requested values if not already set
                    "pred_cpu_cores": req_cpus,
                    "pred_mem_gb": req_mem_gb,
                    "rl_action": None
                })
        return jobs

    def get_next_jobs(self, n=5):
        # Return next n jobs, cycling if at end
        if self.idx >= len(self.jobs):
            self.idx = 0
        jobs = self.jobs[self.idx:self.idx+n]
        self.idx += n
        return jobs

# Global feeder instance
swf_feeder = SWFJobFeeder(SWF_PATH)

# NOTE: The predictors expect a 6-feature input vector. We'll use req_cpus, req_mem_gb, feature3-6.
def poll_slurm():
    # Use SWF feeder to mock jobs
    jobs = swf_feeder.get_next_jobs(5)
    logging.getLogger("slurm_poller").info(f"Mock SWF: Returning {len(jobs)} jobs from SWF dataset")
    return jobs

if __name__ == "__main__":
    while True:
        jobs = poll_slurm()
        print(json.dumps(jobs, indent=2))
        time.sleep(5)
