"""
Train ML models using BERT embeddings for best accuracy.

Supports:
  Format A: Category,Resume (multi-class — your dataset)
  Format B: cv_text,job_description,label (binary match)

Usage:
    python manage.py train_models --data dataset.csv
    python manage.py train_models --data dataset.csv --use-tfidf  # fallback if BERT fails
"""
import os
import sys
import logging
import numpy as np
import pandas as pd
import pickle
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Train ML models for CV screening."

    def add_arguments(self, parser):
        parser.add_argument("--data", type=str, required=True)
        parser.add_argument("--test-size", type=float, default=0.2)
        parser.add_argument("--use-tfidf", action="store_true", help="Use TF-IDF instead of BERT")

    def handle(self, *args, **options):
        data_path = options["data"]
        test_size = options["test_size"]
        use_tfidf = options["use_tfidf"]

        if not os.path.exists(data_path):
            self.stderr.write(f"File not found: {data_path}")
            sys.exit(1)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  CV SCREENING — ML Model Training")
        self.stdout.write(f"  Method: {'TF-IDF' if use_tfidf else 'BERT (best accuracy)'}")
        self.stdout.write(f"{'='*60}")

        df = pd.read_csv(data_path)
        self.stdout.write(f"\nLoaded {len(df)} rows, columns: {list(df.columns)}")

        # Detect format and process
        if "Category" in df.columns and "Resume" in df.columns:
            self.stdout.write("\nFormat: Category + Resume (multi-class)")
            if use_tfidf:
                X, y, label_encoder = self._process_tfidf(df)
            else:
                X, y, label_encoder = self._process_bert(df)
        elif "cv_text" in df.columns:
            self.stdout.write("\nFormat: cv_text + job_description + label")
            X, y = self._process_text_binary(df, use_tfidf)
            label_encoder = None
        else:
            self.stderr.write(f"Unsupported columns: {list(df.columns)}")
            sys.exit(1)

        self.stdout.write(f"\nFeatures: {X.shape}")
        self.stdout.write(f"Classes: {len(np.unique(y))}")
        unique, counts = np.unique(y, return_counts=True)
        for u, c in zip(unique, counts):
            name = label_encoder.inverse_transform([u])[0] if label_encoder else f"Class {u}"
            self.stdout.write(f"  {name}: {c} samples")

        # Split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        self.stdout.write(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")

        # Train
        results = self._train_all_models(X_train, y_train)

        # Results
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  TRAINING RESULTS")
        self.stdout.write(f"{'='*60}")
        for name, res in results.items():
            if "error" in res:
                self.stdout.write(self.style.ERROR(f"  {name}: FAILED — {res['error']}"))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"  {name}: {res['accuracy']}% +/- {res['std']}%"
                ))

        # Test evaluation
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  TEST SET EVALUATION")
        self.stdout.write(f"{'='*60}")
        self._evaluate_test(X_test, y_test, results)

        # Save label encoder
        if label_encoder:
            path = os.path.join(settings.ML_MODELS_DIR, "label_encoder.pkl")
            with open(path, "wb") as f:
                pickle.dump(label_encoder, f)
            self.stdout.write(f"\nCategories: {list(label_encoder.classes_)}")

        # Save feature method flag
        method_path = os.path.join(settings.ML_MODELS_DIR, "feature_method.txt")
        with open(method_path, "w") as f:
            f.write("tfidf" if use_tfidf else "bert")

        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"  ALL MODELS TRAINED AND SAVED!"))
        self.stdout.write(self.style.SUCCESS(f"  Method: {'TF-IDF' if use_tfidf else 'BERT'}"))
        self.stdout.write(self.style.SUCCESS(f"  Location: {settings.ML_MODELS_DIR}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))

    # ─── BERT Processing ─────────────────────────────────

    def _process_bert(self, df):
        """Process Category+Resume using BERT embeddings."""
        from sklearn.preprocessing import LabelEncoder
        import torch
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

        self.stdout.write("\nGenerating BERT embeddings (this takes a few minutes)...")

        df = df.dropna(subset=["Category", "Resume"])
        df["Resume"] = df["Resume"].astype(str)

        le = LabelEncoder()
        y = le.fit_transform(df["Category"])

        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

            texts = df["Resume"].tolist()
            batch_size = 32
            all_embeddings = []

            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_truncated = [t[:5000] for t in batch]
                embeddings = model.encode(
                    batch_truncated,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    device="cpu",
                )
                all_embeddings.append(embeddings)
                if (i // batch_size) % 10 == 0:
                    self.stdout.write(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)} resumes...")

            X = np.vstack(all_embeddings)
            self.stdout.write(f"  BERT embeddings: {X.shape} (384 dims per resume)")

            # Save the model info for scoring
            info_path = os.path.join(settings.ML_MODELS_DIR, "bert_model_info.pkl")
            with open(info_path, "wb") as f:
                pickle.dump({"model_name": "all-MiniLM-L6-v2", "dims": 384}, f)

            return X, y, le

        except Exception as e:
            self.stdout.write(self.style.WARNING(f"\n  BERT failed: {e}"))
            self.stdout.write(self.style.WARNING(f"  Falling back to TF-IDF..."))
            return self._process_tfidf(df)

    # ─── TF-IDF Processing (fallback) ────────────────────

    def _process_tfidf(self, df):
        """Process using TF-IDF (fallback if BERT unavailable)."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import LabelEncoder

        self.stdout.write("\nGenerating TF-IDF features...")
        df = df.dropna(subset=["Category", "Resume"])
        df["Resume"] = df["Resume"].astype(str)

        le = LabelEncoder()
        y = le.fit_transform(df["Category"])

        tfidf = TfidfVectorizer(
            max_features=5000, stop_words="english",
            ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True,
        )
        X = tfidf.fit_transform(df["Resume"]).toarray()

        path = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")
        with open(path, "wb") as f:
            pickle.dump(tfidf, f)

        return X, y, le

    def _process_text_binary(self, df, use_tfidf):
        """Process cv_text + job_description format."""
        df = df.dropna(subset=["cv_text", "job_description", "label"])

        if use_tfidf:
            from sklearn.feature_extraction.text import TfidfVectorizer
            combined = df["cv_text"].astype(str) + " [SEP] " + df["job_description"].astype(str)
            tfidf = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1, 2))
            X = tfidf.fit_transform(combined).toarray()
            path = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")
            with open(path, "wb") as f:
                pickle.dump(tfidf, f)
        else:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            cv_embs = model.encode(df["cv_text"].tolist(), device="cpu", show_progress_bar=True)
            job_embs = model.encode(df["job_description"].tolist(), device="cpu", show_progress_bar=True)
            X = np.hstack([cv_embs, job_embs, cv_embs * job_embs, np.abs(cv_embs - job_embs)])

        return X, df["label"].values.astype(int)

    # ─── Model Training ──────────────────────────────────

    def _train_all_models(self, X_train, y_train):
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import GaussianNB
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from sklearn.model_selection import cross_val_score

        files = {
            "logistic_regression": "logistic_regression.pkl",
            "naive_bayes": "naive_bayes.pkl",
            "knn": "knn.pkl",
            "decision_tree": "decision_tree.pkl",
            "random_forest": "random_forest.pkl",
            "svm": "svm.pkl",
            "xgboost": "xgboost.pkl",
        }
        models = {
            "logistic_regression": LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42),
            "naive_bayes": GaussianNB(),
            "knn": KNeighborsClassifier(n_neighbors=min(5, len(X_train) - 1), weights="distance"),
            "decision_tree": DecisionTreeClassifier(max_depth=15, min_samples_split=5, class_weight="balanced", random_state=42),
            "random_forest": RandomForestClassifier(n_estimators=200, max_depth=20, class_weight="balanced", random_state=42, n_jobs=-1),
            "svm": SVC(kernel="rbf", C=1.0, gamma="scale", probability=True, class_weight="balanced", random_state=42),
        }

        results = {}
        for name, model in models.items():
            self.stdout.write(f"\n  Training {name}...")
            try:
                cv_folds = max(2, min(5, min(np.bincount(y_train))))
                scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring="accuracy")
                model.fit(X_train, y_train)
                path = os.path.join(settings.ML_MODELS_DIR, files[name])
                with open(path, "wb") as f:
                    pickle.dump(model, f)
                results[name] = {
                    "accuracy": round(scores.mean() * 100, 1),
                    "std": round(scores.std() * 100, 1),
                    "saved": path,
                }
                self.stdout.write(f"    Done: {results[name]['accuracy']}%")
            except Exception as e:
                results[name] = {"error": str(e)}
                self.stdout.write(self.style.ERROR(f"    Failed: {e}"))

        # XGBoost
        try:
            import xgboost as xgb
            self.stdout.write(f"\n  Training xgboost...")
            n_classes = len(np.unique(y_train))
            xgb_model = xgb.XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1,
                eval_metric="mlogloss" if n_classes > 2 else "logloss",
            )
            cv_folds = max(2, min(5, min(np.bincount(y_train))))
            scores = cross_val_score(xgb_model, X_train, y_train, cv=cv_folds, scoring="accuracy")
            xgb_model.fit(X_train, y_train)
            path = os.path.join(settings.ML_MODELS_DIR, files["xgboost"])
            with open(path, "wb") as f:
                pickle.dump(xgb_model, f)
            results["xgboost"] = {
                "accuracy": round(scores.mean() * 100, 1),
                "std": round(scores.std() * 100, 1),
                "saved": path,
            }
            self.stdout.write(f"    Done: {results['xgboost']['accuracy']}%")
        except ImportError:
            results["xgboost"] = {"error": "Not installed"}
        except Exception as e:
            results["xgboost"] = {"error": str(e)}

        return results

    def _evaluate_test(self, X_test, y_test, results):
        from sklearn.metrics import accuracy_score, classification_report
        for name, res in results.items():
            if "error" in res or "saved" not in res:
                continue
            try:
                with open(res["saved"], "rb") as f:
                    model = pickle.load(f)
                y_pred = model.predict(X_test)
                acc = accuracy_score(y_test, y_pred)
                self.stdout.write(f"  {name}: test accuracy = {acc * 100:.1f}%")
            except Exception as e:
                self.stdout.write(f"  {name}: error — {e}")
