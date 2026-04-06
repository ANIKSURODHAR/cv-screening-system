# CV Screening System — Complete Setup Guide

## Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Tesseract OCR

---

## Option 1: Docker Setup (Recommended)

```bash
# Clone project
cd cv-screening-system

# Start all services
docker-compose up --build

# In another terminal, create admin superuser
docker-compose exec backend python manage.py createsuperuser

# Generate training data
docker-compose exec backend python generate_training_data.py --output training_data.csv --samples 2000

# Train ML models
docker-compose exec backend python manage.py train_models --data training_data.csv
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Django Admin: http://localhost:8000/admin

---

## Option 2: Manual Setup

### 1. Database Setup
```bash
# Create PostgreSQL database
createdb cv_screening_db
# Or via psql:
psql -U postgres -c "CREATE DATABASE cv_screening_db;"
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Install Tesseract OCR
# Ubuntu: sudo apt install tesseract-ocr
# Mac: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# Create .env file
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py makemigrations accounts jobs candidates ml_engine
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser
# When prompted:
#   Username: admin
#   Email: admin@cvscreen.com
#   Password: (your choice)
#   Role will be set in Django admin → set role to "admin"

# Start Redis (required for Celery)
redis-server

# Start Celery worker (in separate terminal)
celery -A cv_screening worker -l info

# Start Django server
python manage.py runserver
```

### 3. Train ML Models
```bash
# Generate synthetic training data
python generate_training_data.py --output training_data.csv --samples 2000

# Train all 8 models
python manage.py train_models --data training_data.csv
```

Expected output:
```
Loading data from: training_data.csv
Loaded 2000 rows
Features: (2000, 1268), Labels: (2000,)
Training logistic_regression...
  logistic_regression: 78.3% ± 2.1%
Training naive_bayes...
  naive_bayes: 74.5% ± 3.2%
...
All models trained and saved!
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

---

## First-Time Usage Walkthrough

### Step 1: Create Admin Account
```bash
python manage.py createsuperuser
```
Then go to Django Admin (http://localhost:8000/admin), find the user, and set role = "admin".

### Step 2: Register a Recruiter
1. Go to http://localhost:3000/register
2. Select "Recruiter"
3. Fill in details + company name
4. Submit

### Step 3: Recruiter Posts a Job
1. Login as recruiter
2. Click "Post Job" tab
3. Fill in title, description, hard requirements
4. Submit → job goes to admin for approval

### Step 4: Admin Approves the Job
1. Login as admin
2. Go to "Pending Jobs" tab
3. Click "Approve" on the job
4. Job is now live for candidates

### Step 5: Register a Candidate
1. Go to http://localhost:3000/register
2. Select "Candidate"
3. Fill in details
4. Submit

### Step 6: Candidate Applies
1. Login as candidate
2. Browse approved jobs
3. Click "Apply" → upload CV (PDF)
4. Wait for AI scoring (10-30 seconds)
5. View score breakdown + SHAP explanation

### Step 7: Recruiter Reviews AI-Ranked Applicants
1. Login as recruiter
2. Click on a job → see applicants ranked by AI score
3. Shortlist or reject candidates

---

## Project Structure
```
cv-screening-system/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── generate_training_data.py
│   ├── .env.example
│   ├── cv_screening/          # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── accounts/              # User auth + roles
│   │   ├── models.py          # Custom User (admin/recruiter/candidate)
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py     # Role-based permissions
│   │   └── urls.py
│   ├── jobs/                  # Job management
│   │   ├── models.py          # Job + HardRequirement
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── candidates/            # Applications + scores
│   │   ├── models.py          # Application, CVText, ScreeningScore
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── ml_engine/             # ML Pipeline (core)
│   │   ├── text_extractor.py  # Step 2: PDF → text
│   │   ├── nlp_processor.py   # Step 3: NLP + NER
│   │   ├── feature_engineer.py # Step 4: TF-IDF + BERT
│   │   ├── hard_req_checker.py # Step 5: Hard req gate
│   │   ├── ml_models.py       # Step 6: 8 ML models + ensemble
│   │   ├── explainer.py       # SHAP explanations
│   │   ├── pipeline.py        # Full pipeline orchestrator
│   │   ├── tasks.py           # Celery async tasks
│   │   └── management/commands/train_models.py
│   ├── ml_models/             # Trained model files (.pkl)
│   └── media/cvs/             # Uploaded CVs
├── frontend/
│   ├── package.json
│   ├── Dockerfile
│   ├── public/index.html
│   └── src/
│       ├── App.js             # Router + role-based protection
│       ├── context/AuthContext.js
│       ├── utils/api.js       # Axios + JWT interceptor
│       └── pages/
│           ├── LoginPage.js
│           ├── RegisterPage.js
│           ├── AdminDashboard.js
│           ├── RecruiterDashboard.js
│           └── CandidateDashboard.js
└── docs/
    ├── API_DOCUMENTATION.md
    └── SETUP_GUIDE.md
```

---

## Troubleshooting

**"No module named 'accounts'"** → Make sure you're running from the `backend/` directory.

**"Tesseract not found"** → Install Tesseract OCR for your OS.

**"Redis connection refused"** → Start Redis: `redis-server` or `docker run -d -p 6379:6379 redis:7-alpine`

**"Models not loaded"** → Run `python manage.py train_models --data training_data.csv` first.

**"CORS error"** → Check `CORS_ALLOWED_ORIGINS` in settings.py matches your frontend URL.

**Scoring stuck at "Processing"** → Check Celery worker is running: `celery -A cv_screening worker -l info`
