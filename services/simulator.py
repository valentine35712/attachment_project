# simulator.py
# Simulates cluster state and computes metrics

import logging

def simulate(jobs, cluster_state):
    # Simulate a simple bin-packing cluster with 64 CPUs, 256GB RAM
    logger = logging.getLogger("simulator")
    total_cpus = 64
    total_mem = 256.0
    used_cpus = 0
    used_mem = 0.0
    wait_times = []
    running_jobs = 0
    for job in jobs:
        # Use predicted values if available, else fallback to requested
        cpu_cores = job.get('pred_cpu_cores')
        mem_gb = job.get('pred_mem_gb')
        if cpu_cores is None:
            cpu_cores = job.get('req_cpus', 0)
        if mem_gb is None:
            mem_gb = job.get('req_mem_gb', 0.0)
        # Only consider jobs with RL action RUN
        if job.get('rl_action', 'RUN') == 'RUN' and job['state'] == 'PENDING':
            if used_cpus + cpu_cores <= total_cpus and used_mem + mem_gb <= total_mem:
                used_cpus += cpu_cores
                used_mem += mem_gb
                running_jobs += 1
                wait_times.append(0)  # Assume instant start for simplicity
            else:
                wait_times.append(10)  # Simulate wait if not enough resources
        else:
            wait_times.append(0)
    utilization = used_cpus / total_cpus if total_cpus else 0
    avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
    throughput = running_jobs
    logger.info(f"Simulated utilization: {utilization:.2f}, avg_wait: {avg_wait_time}, throughput: {throughput}")
    metrics = {
        "utilization": utilization,
        "avg_wait_time": avg_wait_time,
        "throughput": throughput
    }
    return metrics
