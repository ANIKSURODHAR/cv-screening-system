"""
Django management command: Train ML models from labeled CSV data.

Usage:
    python manage.py train_models --data path/to/training_data.csv

Expected CSV format:
    cv_text,job_description,label
    "Full CV text...","Job description...","1"  (1=good match, 0=not)

Or structured format:
    skills,experience_years,education_level,job_category,label
    "python,django,sql",5,3,"backend",1
"""
import os
import sys
import logging
import numpy as np
import pandas as pd

from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Train ML models for CV screening from labeled data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--data",
            type=str,
            required=True,
            help="Path to training CSV file",
        )
        parser.add_argument(
            "--test-size",
            type=float,
            default=0.2,
            help="Test set proportion (default: 0.2)",
        )

    def handle(self, *args, **options):
        data_path = options["data"]
        test_size = options["test_size"]

        if not os.path.exists(data_path):
            self.stderr.write(f"File not found: {data_path}")
            sys.exit(1)

        self.stdout.write(f"Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        self.stdout.write(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

        # Determine data format
        if "cv_text" in df.columns and "job_description" in df.columns:
            X, y = self._process_text_data(df)
        elif "skills" in df.columns:
            X, y = self._process_structured_data(df)
        else:
            self.stderr.write(
                "CSV must have either (cv_text, job_description, label) "
                "or (skills, experience_years, education_level, label) columns."
            )
            sys.exit(1)

        self.stdout.write(f"Feature matrix: {X.shape}, Labels: {y.shape}")
        self.stdout.write(f"Class distribution: 0={sum(y==0)}, 1={sum(y==1)}")

        # Split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y,
        )

        self.stdout.write(f"Train: {len(X_train)}, Test: {len(X_test)}")

        # Train all models
        from ml_engine.ml_models import train_all_models
        results = train_all_models(X_train, y_train)

        # Print results
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("TRAINING RESULTS")
        self.stdout.write("=" * 60)
        for model_name, result in results.items():
            if "error" in result:
                self.stdout.write(f"  {model_name}: ERROR - {result['error']}")
            else:
                acc = result.get("accuracy", "N/A")
                std = result.get("std", "N/A")
                self.stdout.write(f"  {model_name}: {acc}% ± {std}%")

        # Evaluate on test set
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("TEST SET EVALUATION")
        self.stdout.write("=" * 60)
        self._evaluate_test(X_test, y_test, results)

        self.stdout.write(self.style.SUCCESS("\nAll models trained and saved!"))

    def _process_text_data(self, df):
        """Process text-format training data."""
        from ml_engine.nlp_processor import process_cv_text
        from ml_engine.feature_engineer import build_feature_vector

        self.stdout.write("Processing text data (this may take a while)...")

        features_list = []
        labels = []

        for idx, row in df.iterrows():
            if idx % 50 == 0:
                self.stdout.write(f"  Processing {idx}/{len(df)}...")

            cv_text = str(row["cv_text"])
            job_text = str(row["job_description"])
            label = int(row["label"])

            nlp_data = process_cv_text(cv_text)
            features = build_feature_vector(cv_text, job_text, nlp_data, [])

            features_list.append(features)
            labels.append(label)

        # Pad/truncate to same dimensions
        max_dim = max(len(f) for f in features_list)
        X = np.array([
            np.pad(f, (0, max_dim - len(f))) if len(f) < max_dim else f[:max_dim]
            for f in features_list
        ])
        y = np.array(labels)

        return X, y

    def _process_structured_data(self, df):
        """Process structured-format training data."""
        from ml_engine.nlp_processor import SKILL_TAXONOMY

        self.stdout.write("Processing structured data...")

        feature_columns = [c for c in df.columns if c != "label"]
        # One-hot encode categorical columns
        df_encoded = pd.get_dummies(df[feature_columns], drop_first=True)

        X = df_encoded.values.astype(np.float32)
        y = df["label"].values.astype(int)

        # Handle NaN
        X = np.nan_to_num(X, nan=0.0)

        return X, y

    def _evaluate_test(self, X_test, y_test, train_results):
        """Evaluate trained models on test set."""
        import pickle
        from sklearn.metrics import accuracy_score, classification_report

        for model_name, result in train_results.items():
            if "error" in result or "saved" not in result:
                continue

            try:
                with open(result["saved"], "rb") as f:
                    model = pickle.load(f)

                y_pred = model.predict(X_test)
                acc = accuracy_score(y_test, y_pred)
                self.stdout.write(f"  {model_name}: test accuracy = {acc*100:.1f}%")

            except Exception as e:
                self.stdout.write(f"  {model_name}: eval error - {e}")
