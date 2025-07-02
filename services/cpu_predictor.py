# cpu_predictor.py
# Loads XGBoost CPU model and predicts usage
import joblib
import numpy as np
import os

class CPUPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), '../models/xgb_runtime_model.joblib')
        self.model = joblib.load(model_path)

    def predict(self, job):
        # Use 10 features for prediction (order must match model training)
        import pandas as pd
        job = job.copy()
        if 'requested_time' not in job:
            job['requested_time'] = job.get('est_run_time', 0)
        if 'requested_mem' not in job:
            job['requested_mem'] = job.get('req_mem_gb', 0)
        if 'user_id' not in job:
            job['user_id'] = job.get('user', 0)
        # Ensure all features are numeric, convert or default as needed
        def safe_numeric(val):
            try:
                return float(val)
            except Exception:
                return 0.0
        feature_names = [
            'submit_time',
            'requested_mem',
            'requested_time',
            'user_id',
            'group_id',
            'executable_num',
            'queue_name',
            'partition',
            'hour_of_day',
            'day_of_week'
        ]
        features = pd.DataFrame([{name: safe_numeric(job.get(name, 0)) for name in feature_names}])
        pred = self.model.predict(features)[0]
        job['pred_cpu_cores'] = float(pred)
        return job
