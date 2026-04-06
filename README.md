# CV Screening System — AI-Powered Resume Screening Platform

## Architecture
```
Frontend (React 18 + Tailwind)  ←→  Backend (Django 5 + DRF)  ←→  ML Engine (scikit-learn + XGBoost + BERT)
                                         ↕
                                    PostgreSQL + Redis + Celery
```

## Roles
- **Admin**: Superuser. Approves/rejects job posts, manages recruiters & candidates.
- **Recruiter**: Posts jobs with hard requirements, views AI-ranked applicants.
- **Candidate**: Browses approved jobs, uploads CV (PDF), sees AI match scores + SHAP explanations.

## ML Pipeline (6 Steps)
1. CV Upload → Django stores PDF
2. Text Extraction → pdfminer + PyMuPDF + Tesseract OCR (best output)
3. NLP Processing → spaCy tokenization + BERT embeddings
4. Feature Engineering → TF-IDF (500d) + BERT [CLS] (768d) = 1268d feature vector
5. Hard Requirement Check → regex + NER gate (must pass before ML)
6. ML Ensemble → 8 models weighted vote → SHAP explanation

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Celery (for async ML scoring)
```bash
celery -A cv_screening worker -l info
```

### Train ML Models
```bash
python manage.py train_models --data path/to/training_data.csv
```
