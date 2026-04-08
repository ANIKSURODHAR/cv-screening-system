"""
Train ML models for CV Screening.

Supports 3 dataset formats:
  A: resume_data.csv (35 cols — candidate + job + matched_score) ← YOUR DATASET
  B: Category,Resume (multi-class classification)
  C: cv_text,job_description,label (binary match)

Usage:
    python manage.py train_models --data resume_data.csv
    python manage.py train_models --data resume_data.csv --threshold 0.6
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
        parser.add_argument(
            "--threshold", type=float, default=0.6,
            help="matched_score threshold: above=good match, below=not (default 0.6)"
        )
        parser.add_argument("--use-tfidf", action="store_true", help="Use TF-IDF instead of BERT")

    def handle(self, *args, **options):
        data_path = options["data"]
        test_size = options["test_size"]
        threshold = options["threshold"]
        use_tfidf = options["use_tfidf"]

        if not os.path.exists(data_path):
            self.stderr.write(f"File not found: {data_path}")
            sys.exit(1)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  CV SCREENING — ML Model Training")
        self.stdout.write(f"{'='*60}")

        df = pd.read_csv(data_path, low_memory=False)
        self.stdout.write(f"\nLoaded {len(df)} rows, {len(df.columns)} columns")

        if "matched_score" in df.columns:
            self.stdout.write(self.style.SUCCESS(
                "\n  Detected: resume_data.csv (candidate + job + matched_score)"
            ))
            self.stdout.write(f"  Match threshold: {threshold}")
            X, y, label_encoder = self._process_resume_data(df, threshold, use_tfidf)
        elif "Category" in df.columns and "Resume" in df.columns:
            self.stdout.write("\n  Detected: Category + Resume format")
            X, y, label_encoder = self._process_category_resume(df, use_tfidf)
        elif "cv_text" in df.columns:
            self.stdout.write("\n  Detected: cv_text + job_description + label")
            X, y = self._process_text_binary(df, use_tfidf)
            label_encoder = None
        else:
            self.stderr.write(f"\nUnsupported columns: {list(df.columns)[:10]}...")
            sys.exit(1)

        self.stdout.write(f"\n  Feature matrix: {X.shape}")
        unique, counts = np.unique(y, return_counts=True)
        for u, c in zip(unique, counts):
            name = "Good Match" if u == 1 else "Not Match"
            self.stdout.write(f"    {name}: {c} samples ({c/len(y)*100:.1f}%)")

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        self.stdout.write(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")

        results = self._train_all_models(X_train, y_train)

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  TRAINING RESULTS")
        self.stdout.write(f"{'='*60}")
        for name, res in results.items():
            if "error" in res:
                self.stdout.write(self.style.ERROR(f"  {name}: FAILED — {res['error']}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"  {name}: {res['accuracy']}% +/- {res['std']}%"))

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"  TEST SET EVALUATION")
        self.stdout.write(f"{'='*60}")
        self._evaluate_test(X_test, y_test, results)

        if label_encoder:
            path = os.path.join(settings.ML_MODELS_DIR, "label_encoder.pkl")
            with open(path, "wb") as f:
                pickle.dump(label_encoder, f)

        method = "tfidf" if use_tfidf else "bert"
        with open(os.path.join(settings.ML_MODELS_DIR, "feature_method.txt"), "w") as f:
            f.write(method)

        with open(os.path.join(settings.ML_MODELS_DIR, "training_config.pkl"), "wb") as f:
            pickle.dump({
                "method": method, "threshold": threshold,
                "feature_dims": X.shape[1], "n_samples": len(X),
            }, f)

        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"  ALL MODELS TRAINED AND SAVED!"))
        self.stdout.write(self.style.SUCCESS(f"  Method: {method.upper()} | Features: {X.shape[1]} dims"))
        self.stdout.write(self.style.SUCCESS(f"  Location: {settings.ML_MODELS_DIR}"))
        self.stdout.write(self.style.SUCCESS(f"{'='*60}\n"))

    def _process_resume_data(self, df, threshold, use_tfidf):
        self.stdout.write("\n  Building candidate + job text pairs...")

        job_col = None
        for col in df.columns:
            if "job_position_name" in col:
                job_col = col
                break
        if job_col is None:
            self.stderr.write("Could not find job_position_name column")
            sys.exit(1)

        def build_candidate_text(row):
            parts = []
            if pd.notna(row.get("career_objective")):
                parts.append(str(row["career_objective"]))
            if pd.notna(row.get("skills")):
                parts.append(f"Skills: {row['skills']}")
            if pd.notna(row.get("degree_names")):
                parts.append(f"Degree: {row['degree_names']}")
            if pd.notna(row.get("major_field_of_studies")):
                parts.append(f"Field: {row['major_field_of_studies']}")
            if pd.notna(row.get("positions")):
                parts.append(f"Positions: {row['positions']}")
            if pd.notna(row.get("professional_company_names")):
                parts.append(f"Companies: {row['professional_company_names']}")
            if pd.notna(row.get("responsibilities")):
                parts.append(f"Responsibilities: {str(row['responsibilities'])[:500]}")
            if pd.notna(row.get("certification_skills")):
                parts.append(f"Certifications: {row['certification_skills']}")
            return " | ".join(parts) if parts else "No information"

        def build_job_text(row):
            parts = []
            if pd.notna(row.get(job_col)):
                parts.append(f"Position: {row[job_col]}")
            if pd.notna(row.get("skills_required")):
                parts.append(f"Required skills: {row['skills_required']}")
            if pd.notna(row.get("educationaL_requirements")):
                parts.append(f"Education: {row['educationaL_requirements']}")
            if pd.notna(row.get("experiencere_requirement")):
                parts.append(f"Experience: {row['experiencere_requirement']}")
            if pd.notna(row.get("responsibilities.1")):
                parts.append(f"Responsibilities: {str(row['responsibilities.1'])[:500]}")
            return " | ".join(parts) if parts else "No information"

        self.stdout.write("  Processing candidate texts...")
        candidate_texts = df.apply(build_candidate_text, axis=1).tolist()
        self.stdout.write("  Processing job texts...")
        job_texts = df.apply(build_job_text, axis=1).tolist()

        combined_texts = [f"{ct} [SEP] {jt}" for ct, jt in zip(candidate_texts, job_texts)]

        y = (df["matched_score"].fillna(0).values >= threshold).astype(int)
        self.stdout.write(f"  Labels: {sum(y)} good matches, {len(y)-sum(y)} not matches")

        if use_tfidf:
            X, _ = self._encode_tfidf(combined_texts)
        else:
            X = self._encode_bert(combined_texts)

        return X, y, None

    def _process_category_resume(self, df, use_tfidf):
        from sklearn.preprocessing import LabelEncoder
        df = df.dropna(subset=["Category", "Resume"])
        le = LabelEncoder()
        y = le.fit_transform(df["Category"])
        texts = df["Resume"].astype(str).tolist()
        if use_tfidf:
            X, _ = self._encode_tfidf(texts)
        else:
            X = self._encode_bert(texts)
        return X, y, le

    def _process_text_binary(self, df, use_tfidf):
        df = df.dropna(subset=["cv_text", "job_description", "label"])
        combined = (df["cv_text"].astype(str) + " [SEP] " + df["job_description"].astype(str)).tolist()
        y = df["label"].values.astype(int)
        if use_tfidf:
            X, _ = self._encode_tfidf(combined)
        else:
            X = self._encode_bert(combined)
        return X, y

    def _encode_bert(self, texts):
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        self.stdout.write("\n  Loading BERT model (all-MiniLM-L6-v2)...")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
            self.stdout.write(f"  Encoding {len(texts)} texts with BERT...")
            batch_size = 64
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = [str(t)[:3000] if isinstance(t, str) else "empty" for t in texts[i:i+batch_size]]
                embeddings = model.encode(batch, show_progress_bar=False, convert_to_numpy=True, device="cpu")
                all_embeddings.append(embeddings)
                done = min(i + batch_size, len(texts))
                if done % 500 == 0 or done == len(texts):
                    self.stdout.write(f"    {done}/{len(texts)} encoded...")
            X = np.vstack(all_embeddings)
            self.stdout.write(f"  BERT complete: {X.shape}")
            info_path = os.path.join(settings.ML_MODELS_DIR, "bert_model_info.pkl")
            with open(info_path, "wb") as f:
                pickle.dump({"model_name": "all-MiniLM-L6-v2", "dims": X.shape[1]}, f)
            return X
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"\n  BERT failed: {e}, falling back to TF-IDF"))
            X, _ = self._encode_tfidf(texts)
            return X

    def _encode_tfidf(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.stdout.write("\n  Encoding with TF-IDF...")
        texts = [str(t) if isinstance(t, str) else "empty" for t in texts]
        tfidf = TfidfVectorizer(max_features=5000, stop_words="english", ngram_range=(1,2), min_df=2, max_df=0.95, sublinear_tf=True)
        X = tfidf.fit_transform(texts).toarray()
        path = os.path.join(settings.ML_MODELS_DIR, "tfidf_vectorizer.pkl")
        with open(path, "wb") as f:
            pickle.dump(tfidf, f)
        self.stdout.write(f"  TF-IDF complete: {X.shape}")
        return X, tfidf

    def _train_all_models(self, X_train, y_train):
        from sklearn.linear_model import LogisticRegression
        from sklearn.naive_bayes import GaussianNB
        from sklearn.neighbors import KNeighborsClassifier
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from sklearn.model_selection import cross_val_score
        files = {
            "logistic_regression": "logistic_regression.pkl", "naive_bayes": "naive_bayes.pkl",
            "knn": "knn.pkl", "decision_tree": "decision_tree.pkl",
            "random_forest": "random_forest.pkl", "svm": "svm.pkl", "xgboost": "xgboost.pkl",
        }
        models = {
            "logistic_regression": LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced", random_state=42),
            "naive_bayes": GaussianNB(),
            "knn": KNeighborsClassifier(n_neighbors=min(7, len(X_train)-1), weights="distance"),
            "decision_tree": DecisionTreeClassifier(max_depth=15, min_samples_split=10, class_weight="balanced", random_state=42),
            "random_forest": RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=5, class_weight="balanced", random_state=42, n_jobs=-1),
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
                results[name] = {"accuracy": round(scores.mean()*100,1), "std": round(scores.std()*100,1), "saved": path}
                self.stdout.write(f"    Done: {results[name]['accuracy']}% +/- {results[name]['std']}%")
            except Exception as e:
                results[name] = {"error": str(e)}
                self.stdout.write(self.style.ERROR(f"    Failed: {e}"))
        try:
            import xgboost as xgb
            self.stdout.write(f"\n  Training xgboost...")
            xgb_model = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1, eval_metric="logloss")
            cv_folds = max(2, min(5, min(np.bincount(y_train))))
            scores = cross_val_score(xgb_model, X_train, y_train, cv=cv_folds, scoring="accuracy")
            xgb_model.fit(X_train, y_train)
            path = os.path.join(settings.ML_MODELS_DIR, files["xgboost"])
            with open(path, "wb") as f:
                pickle.dump(xgb_model, f)
            results["xgboost"] = {"accuracy": round(scores.mean()*100,1), "std": round(scores.std()*100,1), "saved": path}
            self.stdout.write(f"    Done: {results['xgboost']['accuracy']}% +/- {results['xgboost']['std']}%")
        except ImportError:
            results["xgboost"] = {"error": "Not installed"}
        except Exception as e:
            results["xgboost"] = {"error": str(e)}
        return results

    def _evaluate_test(self, X_test, y_test, results):
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        for name, res in results.items():
            if "error" in res or "saved" not in res:
                continue
            try:
                with open(res["saved"], "rb") as f:
                    model = pickle.load(f)
                y_pred = model.predict(X_test)
                acc = accuracy_score(y_test, y_pred)
                f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
                self.stdout.write(f"  {name}: accuracy={acc*100:.1f}% | f1={f1*100:.1f}%")
            except Exception as e:
                self.stdout.write(f"  {name}: error — {e}")
