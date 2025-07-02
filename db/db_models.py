# db_models.py
# SQLAlchemy models for jobs and decisions
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'
    job_id = Column(Integer, primary_key=True)
    user = Column(String)
    req_cpus = Column(Integer)
    req_mem_gb = Column(Float)
    pred_cpu_cores = Column(Float)
    pred_mem_gb = Column(Float)
    state = Column(String)
    submit_time = Column(DateTime)
    rl_action = Column(String)
    partition = Column(String)
    est_run_time = Column(Integer)

class Decision(Base):
    __tablename__ = 'decisions'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer)
    action = Column(String)
    timestamp = Column(DateTime)
    pre_util = Column(Float)
    post_util = Column(Float)
