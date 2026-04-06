"""
Django management command: Train ML models from labeled CSV data.

Usage:
    python manage.py train_models --data path/to/training_data.csv
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
        parser.add_argument("--data", type=str, required=True, help="Path to training CSV")
        parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")

    def handle(self, *args, **options):
        data_path = options["data"]
        test_size = options["test_size"]

        if not os.path.exists(data_path):
            self.stderr.write(f"File not found: {data_path}")
            sys.exit(1)

        self.stdout.write(f"Loading data from: {data_path}")
        df = pd.read_csv(data_path)
        self.stdout.write(f"Loaded {len(df)} rows, columns: {list(df.columns)}")

        if "cv_text" in df.columns and "job_description" in df.columns:
            X, y = self._process_text_data(df)
        elif "label" in df.columns:
            X, y = self._process_structured_data(df)
        else:
            self.stderr.write("CSV must have a 'label' column.")
            sys.exit(1)

        self.stdout.write(f"Features: {X.shape}, Labels: {y.shape}")
        self.stdout.write(f"Class distribution: 0={sum(y==0)}, 1={sum(y==1)}")

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        from ml_engine.ml_models import train_all_models
        results = train_all_models(X_train, y_train)

        self.stdout.write("\n" + "=" * 50 + "\nTRAINING RESULTS\n" + "=" * 50)
        for name, res in results.items():
            if "error" in res:
                self.stdout.write(f"  {name}: ERROR - {res['error']}")
            else:
                self.stdout.write(f"  {name}: {res.get('accuracy','N/A')}% ± {res.get('std','N/A')}%")

        self.stdout.write(self.style.SUCCESS("\nAll models trained and saved!"))

    def _process_text_data(self, df):
        from ml_engine.nlp_processor import process_cv_text
        from ml_engine.feature_engineer import build_feature_vector

        features_list, labels = [], []
        for idx, row in df.iterrows():
            if idx % 50 == 0:
                self.stdout.write(f"  Processing {idx}/{len(df)}...")
            nlp_data = process_cv_text(str(row["cv_text"]))
            features = build_feature_vector(str(row["cv_text"]), str(row["job_description"]), nlp_data, [])
            features_list.append(features)
            labels.append(int(row["label"]))

        max_dim = max(len(f) for f in features_list)
        X = np.array([np.pad(f, (0, max_dim - len(f))) if len(f) < max_dim else f[:max_dim] for f in features_list])
        return X, np.array(labels)

    def _process_structured_data(self, df):
        feature_cols = [c for c in df.columns if c != "label"]
        df_encoded = pd.get_dummies(df[feature_cols], drop_first=True)
        X = np.nan_to_num(df_encoded.values.astype(np.float32), nan=0.0)
        return X, df["label"].values.astype(int)
