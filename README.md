# ZCHPC AI-Driven Predictive Scheduling System

An intelligent, AI-powered job scheduling and resource optimization system for the Zimbabwe Centre for High Performance Computing (ZCHPC).

## Overview

This system uses machine learning models to predict job resource requirements, optimize scheduling decisions, and improve overall cluster utilization. By analyzing historical job data, the system makes accurate predictions about job runtime, memory usage, and CPU requirements, leading to better resource allocation and reduced job wait times.

## Features

- **Machine Learning-based Resource Prediction**: Accurately predicts job runtime, memory usage, and CPU requirements
- **Intelligent Job Scheduling**: Uses predictions to optimize scheduling decisions
- **HPC Scheduler Integration**: Works with existing SLURM and PBS/Torque schedulers
- **Simulation Environment**: Test and evaluate different scheduling strategies
- **Shadow Mode**: Run alongside existing schedulers without disrupting production workloads
- **Performance Metrics**: Track prediction accuracy and resource utilization improvements

## Project Structure

```
zchpc-ai-scheduler/
├── config/                     # Configuration files
│   ├── model_config.yaml       # ML model parameters
│   └── scheduler_config.yaml   # Scheduler settings
├── data/                       # Data storage
│   ├── raw/                    # Raw workload trace files
│   ├── processed/              # Cleaned data
│   └── features/               # Feature-engineered datasets
├── models/                     # Trained ML models
├── results/                    # Simulation results
├── src/                        # Source code
│   ├── cli/                    # Command-line interface
│   ├── data/                   # Data processing modules
│   ├── integration/            # HPC scheduler integration
│   ├── middleware/             # AI scheduler middleware
│   ├── models/                 # ML model implementations
│   └── simulation/             # Simulation environment
├── examples/                   # Example job scripts
│   └── scripts/                # Sample job scripts
├── tests/                      # Unit and integration tests
└── notebooks/                  # Jupyter notebooks for analysis
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/zchpc/ai-scheduler.git
   cd zchpc-ai-scheduler
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up the necessary directories:
   ```bash
   mkdir -p data/{raw,processed,features} models results logs history
   ```

## Usage

### Data Preparation

1. Download workload traces:
   ```bash
   python -m src.data.download
   ```

2. Parse SWF files:
   ```bash
   python -m src.data.parser
   ```

3. Clean data:
   ```bash
   python -m src.data.cleaner
   ```

4. Generate features:
   ```bash
   python -m src.data.feature_engineering
   ```

### Model Training

Train the resource prediction models:

```bash
python src/cli/ai_scheduler_cli.py train --data-dir data/features --model-type xgboost
```

### Simulation

Run a simulation to evaluate different scheduling strategies:

```bash
python src/cli/ai_scheduler_cli.py simulate --dataset data/features/combined_features.parquet --scheduler compare
```

### Job Submission

Submit a job with AI-optimized resource allocation:

```bash
python src/cli/ai_scheduler_cli.py submit examples/scripts/cpu_job.sh --params ntasks=16 mem=8G
```

### Monitoring

Monitor running jobs and view performance metrics:

```bash
python src/cli/ai_scheduler_cli.py monitor
```

## Configuration

### Model Configuration (`config/model_config.yaml`)

Contains parameters for the machine learning models, including:

- Model hyperparameters for XGBoost and LightGBM
- Training parameters (number of iterations, early stopping, etc.)
- Feature selection settings

### Scheduler Configuration (`config/scheduler_config.yaml`)

Contains settings for the scheduler, including:

- Scheduler type (SLURM or PBS)
- Shadow mode flag (for testing without affecting production)
- Resource scaling factors (safety margins for predictions)
- Weights for job prioritization

## Components

### Data Processing Pipeline

- **Download Module**: Fetches HPC workload data from public repositories
- **Parser Module**: Converts raw workload traces into structured data
- **Cleaner Module**: Filters and cleans the parsed data
- **Feature Engineering Module**: Creates relevant features for ML models

### Machine Learning Models

- **Resource Prediction Models**: XGBoost and LightGBM models for predicting job runtime, memory usage, and CPU requirements
- **Model Training Framework**: Standardized framework for training and evaluating models

### Simulation Environment

- **Cluster State Simulator**: Simulates a HPC cluster's resources and job execution
- **Scheduler Implementations**: Various scheduling algorithms (FCFS, SJF, ML-Aware)
- **Evaluation Metrics**: Comprehensive metrics for comparing scheduler performance

### HPC Scheduler Integration

- **Scheduler Clients**: Interfaces for interacting with SLURM and PBS/Torque
- **Job Submission Wrappers**: Transparently adds AI-optimized resource requests

### AI Scheduler Middleware

- **Resource Prediction**: Uses ML models to predict job requirements
- **Parameter Optimization**: Adjusts job parameters based on predictions
- **Job Monitoring**: Tracks job outcomes to improve future predictions

## Contributing

Contributions to improve the AI-driven scheduling system are welcome. Please follow the standard fork-and-pull request workflow.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Zimbabwe Centre for High Performance Computing (ZCHPC) for supporting this project
- Parallel Workloads Archive for providing job trace datasets

# zchpc-ai-scheduler

This project is an AI-driven predictive job scheduler for HPC and batch clusters. It features:
- FastAPI backend for job management and simulation
- Streamlit dashboard for monitoring and visualization
- ML models for runtime and memory prediction
- RL-based job scheduling

## How to Use

1. Clone the repository:
   ```bash
   git clone <your-github-url>
   cd zchpc-ai-scheduler
   ```
2. Install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the system:
   ```bash
   python run_all.py
   ```
   This will start both the FastAPI backend and the Streamlit dashboard.

## What is NOT included in this repo
- Large SWF trace files (see `/data/`)
- Trained model binaries (see `/models/`)
- Local database files (see `/data/`)
- Any secrets or private config files

## License
MIT
