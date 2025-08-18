
# MLOps Course: Experiment Tracking with MLflow

This project provides a hands-on introduction to experiment tracking with MLflow, using the NYC Green Taxi Trip dataset as an example.

## Project Structure

```
.
├── data/
│   └── processed/
├── notebooks/
│   ├── 01_experiment_tracking_intro.ipynb
│   ├── 02_mlflow_basics.ipynb
│   └── 03_mlflow_advanced.ipynb
├── scripts/
│   ├── preprocess_data.py
│   ├── train_no_mlflow.py
│   ├── train_with_basic_mlflow.py
│   └── train_with_full_mlflow.py
├── mlflow.db
└── README.md
```

*   **data/:** Stores the raw and processed dataset.
*   **notebooks/:** Contains Jupyter notebooks that explain the concepts.
*   **scripts/:** Contains the Python scripts for data preprocessing and model training.
*   **mlflow.db:** A SQLite database that serves as the MLflow tracking server.

## Getting Started

### 1. Installation

This project uses `uv` for package management. To install the dependencies, run:

```bash
uv add "pandas" "scikit-learn" "mlflow" "optuna" "numpy" "pyarrow"
```

### 2. Data Preprocessing

First, run the data preprocessing script to download the NYC Green Taxi Trip dataset and prepare it for training:

```bash
uv run python scripts/preprocess_data.py
```

This will download the data to the `data/` directory and save the processed data to `data/processed/`.

### 3. Running the Examples

#### a. Baseline (No Experiment Tracking)

To train a model without any experiment tracking, run:

```bash
uv run python scripts/train_no_mlflow.py
```

This will train a RandomForestRegressor and print the RMSE to the console.

#### b. Basic MLflow

To train a model with basic MLflow experiment tracking, run:

```bash
uv run python scripts/train_with_basic_mlflow.py
```

This will log the model's parameters and metrics to the MLflow tracking server.

#### c. Advanced MLflow (Hyperparameter Optimization)

To run hyperparameter optimization with Optuna and log the results to MLflow, run:

```bash
uv run python scripts/train_with_full_mlflow.py
```

### 4. Viewing the Results in the MLflow UI

To view the results of your experiments, launch the MLflow UI:

```bash
mlflow ui
```

Then, open your web browser and navigate to `http://127.0.0.1:5000`.

## Notebooks

The `notebooks/` directory contains three notebooks that provide a more in-depth explanation of the concepts:

*   **01_experiment_tracking_intro.ipynb:** A conceptual overview of experiment tracking.
*   **02_mlflow_basics.ipynb:** A hands-on introduction to MLflow.
*   **03_mlflow_advanced.ipynb:** Covers more advanced MLflow features like hyperparameter optimization and model registration.
