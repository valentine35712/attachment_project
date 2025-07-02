# simulate_and_connect.py

# simulate and connect all components: job submission, prediction, RL scheduling, simulation
import os
import sys
import time
from services.slurm_poller import poll_slurm
from services.cpu_predictor import CPUPredictor
from services.mem_predictor import MemPredictor
from services.rl_scheduler import RLScheduler
from services.simulator import simulate

def simulate_and_connect():
    cpu_predictor = CPUPredictor()
    mem_predictor = MemPredictor()
    rl_scheduler = RLScheduler()

    # Simulate a batch of jobs through the full pipeline
    for _ in range(3):  # Simulate 3 batches
        jobs = poll_slurm()
        # Predict resources
        for job in jobs:
            job = cpu_predictor.predict(job)
            job = mem_predictor.predict(job)
        # RL scheduling
        jobs = rl_scheduler.decide(jobs, cluster_state=None)
        # Simulate cluster
        metrics = simulate(jobs, cluster_state=None)
        print("Jobs after RL scheduling:")
        for job in jobs:
            print(job)
        print("Simulated cluster metrics:", metrics)
        print("-"*40)
        time.sleep(2)

if __name__ == "__main__":
    simulate_and_connect()