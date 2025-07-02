# rl_scheduler.py
# Loads PPO agent and outputs scheduling actions
import os
from stable_baselines3 import PPO
import numpy as np

class RLScheduler:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '../models/ppo_hpc_scheduler.zip')
        self.model_path = model_path
        self.model = PPO.load(self.model_path)

    def decide(self, jobs, cluster_state):
        # Prepare state for PPO: flatten job features into a single array
        # For simplicity, use [pred_cpu_cores, pred_mem_gb, est_run_time, state] for each job
        max_jobs = 10
        features_per_job = 4
        obs_len = 42
        job_features = []
        for job in jobs:
            job_vec = [
                job.get('pred_cpu_cores', 0),
                job.get('pred_mem_gb', 0),
                job.get('est_run_time', 0),
                1 if job.get('state', 'PENDING') == 'PENDING' else 0
            ]
            job_features.append(job_vec)
        while len(job_features) < max_jobs:
            job_features.append([0, 0, 0, 0])
        obs = np.array(job_features, dtype=np.float32).flatten()
        # Pad to 42 if needed
        if obs.shape[0] < obs_len:
            obs = np.pad(obs, (0, obs_len - obs.shape[0]))
        obs = obs[None, :]
        # PPO model outputs an action (index of job to run)
        # If obs contains only zeros, avoid calling model to prevent NaN
        # Check for NaNs in obs and handle gracefully
        if np.any(np.isnan(obs)) or np.all(obs == 0):
            action = 0
        else:
            action, _ = self.model.predict(obs, deterministic=True)
        for i, job in enumerate(jobs):
            job['rl_action'] = 'RUN' if i == action else 'HOLD'
        return jobs
