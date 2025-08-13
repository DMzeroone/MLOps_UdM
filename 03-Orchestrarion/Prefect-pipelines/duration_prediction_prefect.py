#!/usr/bin/env python
# coding: utf-8

import pickle
from pathlib import Path
from typing import Tuple

import pandas as pd
import xgboost as xgb
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error

import mlflow
from prefect import task, flow
from prefect.artifacts import create_table_artifact, create_markdown_artifact


# Configuración de MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("nyc-taxi-experiment-prefect")


@task(name="load_data", description="Load NYC taxi data from parquet files")
def read_dataframe(year: int, month: int) -> pd.DataFrame:
    """
    Load NYC taxi data for a specific year and month.

    Args:
        year: Year of the data to load
        month: Month of the data to load

    Returns:
        Processed DataFrame with duration feature
    """
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_{year}-{month:02d}.parquet'
    df = pd.read_parquet(url)

    # Feature engineering
    df['duration'] = df.lpep_dropoff_datetime - df.lpep_pickup_datetime
    df.duration = df.duration.apply(lambda td: td.total_seconds() / 60)

    # Filter outliers
    df = df[(df.duration >= 1) & (df.duration <= 60)]

    # Categorical features
    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)
    df['PU_DO'] = df['PULocationID'] + '_' + df['DOLocationID']

    # Create artifact with data summary
    summary_data = [
        ["Total Records", len(df)],
        ["Average Duration", f"{df['duration'].mean():.2f} minutes"],
        ["Min Duration", f"{df['duration'].min():.2f} minutes"],
        ["Max Duration", f"{df['duration'].max():.2f} minutes"],
        ["Unique PU_DO combinations", df['PU_DO'].nunique()]
    ]

    create_table_artifact(
        key=f"data-summary-{year}-{month:02d}",
        table=summary_data,
        description=f"Data summary for {year}-{month:02d}"
    )

    return df


@task(name="create_features", description="Create feature matrix using DictVectorizer")
def create_X(df: pd.DataFrame, dv: DictVectorizer = None) -> Tuple[any, DictVectorizer]:
    """
    Create feature matrix from DataFrame.

    Args:
        df: Input DataFrame
        dv: Pre-fitted DictVectorizer (optional)

    Returns:
        Tuple of (feature matrix, DictVectorizer)
    """
    categorical = ['PU_DO']
    numerical = ['trip_distance']
    dicts = df[categorical + numerical].to_dict(orient='records')

    if dv is None:
        dv = DictVectorizer(sparse=True)
        X = dv.fit_transform(dicts)

        # Create artifact with feature info
        feature_info = [
            ["Total Features", X.shape[1]],
            ["Categorical Features", len(categorical)],
            ["Numerical Features", len(numerical)],
            ["Samples", X.shape[0]]
        ]

        create_table_artifact(
            key="feature-info",
            table=feature_info,
            description="Feature matrix information"
        )
    else:
        X = dv.transform(dicts)

    return X, dv


@task(name="train_model", description="Train XGBoost model with MLflow tracking")
def train_model(X_train, y_train, X_val, y_val, dv: DictVectorizer) -> str:
    """
    Train XGBoost model and log to MLflow.

    Args:
        X_train: Training features
        y_train: Training targets
        X_val: Validation features
        y_val: Validation targets
        dv: Fitted DictVectorizer

    Returns:
        MLflow run ID
    """
    # Ensure models directory exists
    models_folder = Path('models')
    models_folder.mkdir(exist_ok=True)

    with mlflow.start_run() as run:
        train = xgb.DMatrix(X_train, label=y_train)
        valid = xgb.DMatrix(X_val, label=y_val)

        best_params = {
            'learning_rate': 0.09585355369315604,
            'max_depth': 30,
            'min_child_weight': 1.060597050922164,
            'objective': 'reg:squarederror',  # Updated from deprecated 'reg:linear'
            'reg_alpha': 0.018060244040060163,
            'reg_lambda': 0.011658731377413597,
            'seed': 42
        }

        mlflow.log_params(best_params)

        booster = xgb.train(
            params=best_params,
            dtrain=train,
            num_boost_round=30,
            evals=[(valid, 'validation')],
            early_stopping_rounds=50
        )

        y_pred = booster.predict(valid)
        rmse = root_mean_squared_error(y_val, y_pred)
        mlflow.log_metric("rmse", rmse)

        # Save preprocessor
        with open("models/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact("models/preprocessor.b", artifact_path="preprocessor")

        # Log model
        mlflow.xgboost.log_model(booster, artifact_path="models_mlflow")

        # Create Prefect artifact with model performance
        performance_data = [
            ["RMSE", f"{rmse:.4f}"],
            ["Learning Rate", best_params['learning_rate']],
            ["Max Depth", best_params['max_depth']],
            ["Num Boost Rounds", 30],
            ["MLflow Run ID", run.info.run_id]
        ]

        create_table_artifact(
            key="model-performance",
            table=performance_data,
            description=f"Model performance metrics - RMSE: {rmse:.4f}"
        )

        # Create markdown artifact with training summary
        markdown_content = f"""
        # Model Training Summary

        ## Performance
        - **RMSE**: {rmse:.4f}
        - **MLflow Run ID**: {run.info.run_id}

        ## Parameters
        - Learning Rate: {best_params['learning_rate']}
        - Max Depth: {best_params['max_depth']}
        - Min Child Weight: {best_params['min_child_weight']}
        - Regularization Alpha: {best_params['reg_alpha']}
        - Regularization Lambda: {best_params['reg_lambda']}

        ## Training Details
        - Boost Rounds: 30
        - Early Stopping: 50 rounds
        - Objective: {best_params['objective']}
        """

        create_markdown_artifact(
            key="training-summary",
            markdown=markdown_content,
            description="Detailed training summary"
        )

        return run.info.run_id


@flow(name="NYC Taxi Duration Prediction Pipeline", description="End-to-end ML pipeline for taxi duration prediction")
def duration_prediction_flow(year: int, month: int) -> str:
    """
    Main flow for NYC taxi duration prediction.

    Args:
        year: Year of training data
        month: Month of training data

    Returns:
        MLflow run ID
    """
    # Load training data
    df_train = read_dataframe(year=year, month=month)

    # Calculate validation data period
    next_year = year if month < 12 else year + 1
    next_month = month + 1 if month < 12 else 1

    # Load validation data
    df_val = read_dataframe(year=next_year, month=next_month)

    # Create features
    X_train, dv = create_X(df_train)
    X_val, _ = create_X(df_val, dv)

    # Prepare targets
    target = 'duration'
    y_train = df_train[target].values
    y_val = df_val[target].values

    # Train model
    run_id = train_model(X_train, y_train, X_val, y_val, dv)

    # Create final pipeline artifact
    pipeline_summary = f"""
    # Pipeline Execution Summary

    ## Data
    - **Training Period**: {year}-{month:02d}
    - **Validation Period**: {next_year}-{next_month:02d}
    - **Training Samples**: {len(y_train):,}
    - **Validation Samples**: {len(y_val):,}

    ## Results
    - **MLflow Run ID**: {run_id}
    - **MLflow Experiment**: nyc-taxi-experiment-prefect

    ## Next Steps
    1. Review model performance in MLflow UI: http://localhost:5000
    2. Compare with previous runs
    3. Consider model deployment if performance is satisfactory
    """

    create_markdown_artifact(
        key="pipeline-summary",
        markdown=pipeline_summary,
        description="Complete pipeline execution summary"
    )

    return run_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train a model to predict taxi trip duration using Prefect.')
    parser.add_argument('--year', type=int, required=True, help='Year of the data to train on')
    parser.add_argument('--month', type=int, required=True, help='Month of the data to train on')
    args = parser.parse_args()

    # Run the flow
    run_id = duration_prediction_flow(year=args.year, month=args.month)
    print(f"Pipeline completed! MLflow run_id: {run_id}")

    # Save run ID for reference
    with open("prefect_run_id.txt", "w") as f:
        f.write(run_id)
