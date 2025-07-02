import streamlit as st
st.set_page_config(page_title="ADPS Dashboard", layout="wide")

import requests
import pandas as pd
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

st.title(":rocket: ADPS (AI-Driven Predictive Scheduling) Dashboard")
st.markdown("""
Welcome to the **ADPS Dashboard** :computer:.

This dashboard lets you:
- **Monitor** the real-time job queue and resource predictions.
- **Understand** what the AI/ML scheduler would do (shadow mode).
- **Visualize** cluster utilization, wait times, and throughput.
- **Override** AI decisions if needed.

:bulb: *Tip: Use the sidebar to navigate between views. Use auto-refresh for live monitoring!*
""")

# Sidebar navigation
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2721/2721296.png", width=120)
tab = st.sidebar.radio("Go to", ["Current Queue", "RL Decisions", "Simulated Job Log", "History", "Admin Override"])
st.sidebar.markdown("---")
st.sidebar.info("ADPS: AI-Driven Predictive Scheduling for HPC and batch clusters.\n\nContact: admin@adps.example.com")

def fetch_api(endpoint, params=None):
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

if tab == "Current Queue":
    st.header(":clipboard: Current Job Queue (ADPS)")
    st.info("Shows all jobs in the system, with both user-requested and AI-predicted resources. RL action shows what ADPS would do if it controlled the cluster.")
    data = fetch_api("/queue")
    if data:
        if isinstance(data, dict) and 'jobs' in data:
            df = pd.DataFrame(data['jobs'])
        elif isinstance(data, list):
            df = pd.DataFrame([row for row in data if isinstance(row, dict)])
        else:
            st.error("API returned data in an unexpected format.")
            df = pd.DataFrame()
        if not df.empty:
            df = df.rename(columns={
                'job_id': 'Job ID', 'user': 'User', 'req_cpus': 'Req. CPUs', 'pred_cpu_cores': 'Pred. CPUs',
                'req_mem_gb': 'Req. Mem (GB)', 'pred_mem_gb': 'Pred. Mem (GB)', 'state': 'State',
                'submit_time': 'Submit Time', 'rl_action': 'RL Action', 'partition': 'Partition', 'est_run_time': 'Est. Run Time'
            })
            # Ensure prediction columns are always present
            for col in ['Pred. CPUs', 'Pred. Mem (GB)']:
                if col not in df.columns:
                    df[col] = df['Req. CPUs'] if col == 'Pred. CPUs' else df['Req. Mem (GB)']
            # Reorder columns for clarity
            col_order = [
                'Job ID', 'User', 'State', 'Submit Time',
                'Req. CPUs', 'Pred. CPUs', 'Req. Mem (GB)', 'Pred. Mem (GB)',
                'Est. Run Time', 'Partition', 'RL Action'
            ]
            df = df[[c for c in col_order if c in df.columns] + [c for c in df.columns if c not in col_order]]
            # Highlight jobs by RL Action
            def highlight_action(row):
                color = '#00c6ff33' if row['RL Action'] == 'RUN' else '#ff007733'
                return [f'background-color: {color}' for _ in row]
            st.dataframe(df.style.apply(highlight_action, axis=1), use_container_width=True)
            st.caption("**Legend:** RL Action = What the AI would do (RUN/HOLD). Blue = RUN, Red = HOLD. Predicted values are from ML models.")
            st.markdown(f"**Total Jobs:** {len(df)} | **To Run:** {sum(df['RL Action']=='RUN')} | **On Hold:** {sum(df['RL Action']=='HOLD')}")
            st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("No jobs in the queue.")

elif tab == "RL Decisions":
    st.header(":robot_face: ADPS Scheduler Decisions")
    st.info("Shows the latest AI/ML-based scheduling decisions and simulated cluster metrics.")
    data = fetch_api("/rl-decisions")
    if data:
        if isinstance(data, dict) and 'jobs' in data:
            df = pd.DataFrame(data['jobs'])
            metrics = data.get('metrics', {})
        elif isinstance(data, list):
            df = pd.DataFrame([row for row in data if isinstance(row, dict)])
            metrics = {}
        else:
            st.error("API returned data in an unexpected format.")
            df = pd.DataFrame(); metrics = {}
        if not df.empty:
            df = df.rename(columns={
                'job_id': 'Job ID', 'user': 'User', 'req_cpus': 'Req. CPUs', 'pred_cpu_cores': 'Pred. CPUs',
                'req_mem_gb': 'Req. Mem (GB)', 'pred_mem_gb': 'Pred. Mem (GB)', 'state': 'State',
                'submit_time': 'Submit Time', 'rl_action': 'RL Action', 'partition': 'Partition', 'est_run_time': 'Est. Run Time'
            })
            # Highlight jobs by RL Action
            def highlight_action(row):
                color = '#00c6ff33' if row['RL Action'] == 'RUN' else '#ff007733'
                return [f'background-color: {color}' for _ in row]
            st.dataframe(df.style.apply(highlight_action, axis=1), use_container_width=True)
            st.caption("**Legend:** RL Action = What the AI would do (RUN/HOLD). Blue = RUN, Red = HOLD. Predicted values are from ML models.")
            # Show metrics
            if metrics:
                st.subheader(":bar_chart: Simulated Cluster Metrics")
                col1, col2, col3 = st.columns(3)
                col1.metric("Utilization", f"{metrics.get('utilization', 0)*100:.1f}%")
                col2.metric("Avg. Wait Time", f"{metrics.get('avg_wait_time', 0):.1f} s")
                col3.metric("Throughput", f"{metrics.get('throughput', 0)} jobs")
            # Add summary
            st.markdown(f"**Total Jobs:** {len(df)} | **To Run:** {sum(df['RL Action']=='RUN')} | **On Hold:** {sum(df['RL Action']=='HOLD')}")
            st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("No RL decisions available.")

elif tab == "History":
    st.header("Historical Logs & Metrics")
    # Date filter
    start = st.date_input("Start date")
    end = st.date_input("End date")
    job_id_filter = st.text_input("Filter by Job ID (optional)")
    params = {"start": str(start), "end": str(end)}
    if job_id_filter:
        params["job_id"] = job_id_filter
    data = fetch_api("/history", params)
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
        # Example: plot utilization over time if available
        if "utilization" in df:
            st.line_chart(df.set_index("timestamp")["utilization"])
        if "avg_wait_time" in df:
            st.line_chart(df.set_index("timestamp")["avg_wait_time"])

elif tab == "Admin Override":
    st.header("Manual Job/Decision Override")
    job_id = st.text_input("Job ID to override")
    action = st.selectbox("Action", ["APPROVE", "REJECT", "MODIFY"])
    if st.button("Submit Override"):
        try:
            resp = requests.post(f"{API_BASE}/override", json={"job_id": job_id, "action": action})
            if resp.status_code == 200:
                st.success("Override submitted.")
            else:
                st.error(f"Error: {resp.text}")
        except Exception as e:
            st.error(f"API error: {e}")

elif tab == "Simulated Job Log":
    st.header(":page_facing_up: Simulated Job Log")
    data = fetch_api("/simlog")
    if data:
        df = pd.DataFrame(data)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.markdown(f"**Total Jobs:** {len(df)} | **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.info("No simulated job log entries.")
