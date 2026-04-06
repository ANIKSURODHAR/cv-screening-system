# CV Screening System — API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
All endpoints (except register/login) require JWT Bearer token.
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/register/
Register as recruiter or candidate.
```json
{
  "username": "rahim_dev",
  "email": "rahim@mail.com",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "first_name": "Rahim",
  "last_name": "Uddin",
  "role": "candidate",
  "company": ""
}
```
**Response 201:** `{ "message": "Registration successful...", "user": {...} }`

### POST /auth/login/
Get JWT tokens.
```json
{ "username": "rahim_dev", "password": "SecurePass123!" }
```
**Response 200:** `{ "access": "<token>", "refresh": "<token>" }`

### POST /auth/token/refresh/
Refresh expired access token.
```json
{ "refresh": "<refresh_token>" }
```

### GET /auth/profile/
Get current user profile.

### PUT /auth/profile/
Update profile.

### GET /auth/users/ (Admin only)
List all users. Query params: `?role=recruiter` or `?role=candidate`

### DELETE /auth/users/{id}/ (Admin only)
Remove a user.

### GET /auth/stats/ (Admin only)
Dashboard statistics.
**Response:** `{ "total_users": 10, "recruiters": 3, "candidates": 7, "total_jobs": 5, "pending_jobs": 1, ... }`

---

## Job Endpoints

### GET /jobs/approved/
Browse all approved (live) jobs. Available to all authenticated users.
Query: `?search=python&page=1`

### GET /jobs/{id}/
Get job details.

### GET /jobs/my-jobs/ (Recruiter only)
List recruiter's own jobs.

### POST /jobs/create/ (Recruiter only)
Create a new job posting (status = pending).
```json
{
  "title": "Senior ML Engineer",
  "company": "TechAI Corp",
  "description": "Build production ML pipelines...",
  "location": "Dhaka, Bangladesh",
  "salary_range": "80K-120K BDT",
  "job_type": "full_time",
  "hard_requirements": [
    {
      "requirement_type": "skill",
      "description": "Python 5+ years",
      "keywords": "python",
      "min_years": 5,
      "is_mandatory": true
    },
    {
      "requirement_type": "skill",
      "description": "TensorFlow",
      "keywords": "tensorflow,tf",
      "is_mandatory": true
    },
    {
      "requirement_type": "education",
      "description": "PhD preferred",
      "keywords": "phd,doctorate",
      "is_mandatory": false
    }
  ]
}
```

### PUT /jobs/{id}/edit/ (Recruiter only)
Edit own job.

### GET /jobs/admin/all/ (Admin only)
List all jobs. Query: `?status=pending`

### GET /jobs/admin/pending/ (Admin only)
List pending jobs awaiting approval.

### PATCH /jobs/admin/{id}/approve/ (Admin only)
Approve or reject a job.
```json
{ "status": "approved", "admin_notes": "Looks good" }
```

---

## Candidate Endpoints

### POST /candidates/apply/ (Candidate only)
Apply to a job with CV upload. **Use multipart/form-data.**
```
job: 1
cv_file: <PDF file>
```
**Response 201:** `{ "message": "Application submitted! AI scoring in progress...", "application_id": 5 }`

### GET /candidates/my-applications/ (Candidate only)
List own applications with scores.

### GET /candidates/my-applications/{id}/ (Candidate only)
Full application detail with CV extraction data, all 8 ML model scores, and SHAP explanation.

### GET /candidates/job/{job_id}/applicants/ (Recruiter/Admin)
AI-ranked applicants for a job (sorted by overall_score DESC).

### GET /candidates/applicant/{id}/ (Recruiter/Admin)
Full applicant details with score breakdown.

### PATCH /candidates/applicant/{id}/status/ (Recruiter/Admin)
Update application status.
```json
{ "status": "shortlisted" }
```
Options: `shortlisted`, `rejected`, `hired`

### GET /candidates/admin/all/ (Admin only)
List all applications.

---

## ML Engine Endpoints

### GET /ml/status/{application_id}/
Check scoring progress for an application.
**Response (processing):** `{ "status": "processing", "message": "AI scoring in progress..." }`
**Response (done):** `{ "status": "scored", "overall_score": 87.5, "label": "high", "hard_req_score": 92, "ensemble_score": 85 }`

### POST /ml/rescore/{job_id}/ (Admin only)
Re-score all applications for a job (async).

### GET /ml/models/ (Admin only)
View loaded ML model info.

---

## ML Pipeline Flow (Internal)

When a candidate applies (`POST /candidates/apply/`), the system:

1. **Saves CV** → `media/cvs/<user_id>/<filename>.pdf`
2. **Triggers Celery task** → `ml_engine.tasks.score_application`
3. **Step 2 - Text Extraction** → Runs pdfminer, PyMuPDF, and Tesseract OCR. Picks best output by quality score.
4. **Step 3 - NLP Processing** → spaCy tokenization, skill/education/experience extraction via taxonomy + regex.
5. **Step 4 - Feature Engineering** → TF-IDF (500d) + BERT embeddings (384d×4+1) + structured features (12d) → concatenated vector.
6. **Step 5 - Hard Requirement Check** → Binary match on recruiter-defined must-haves. If mandatory requirements fail → score capped at 50%.
7. **Step 6 - ML Ensemble** → 8 pre-trained models predict match probability:
   - Logistic Regression (w=0.08)
   - Naïve Bayes (w=0.07)
   - KNN (w=0.08)
   - Decision Tree (w=0.09)
   - Random Forest (w=0.15)
   - SVM (w=0.14)
   - XGBoost (w=0.22) ← highest weight
   - AutoGluon (w=0.17)
   - Weighted ensemble → final ML score
8. **Overall Score** = 0.3 × hard_req_score + 0.7 × ensemble_score
9. **SHAP Explanation** → Human-readable positive/negative factors + improvement suggestions.
10. **Saves to ScreeningScore** → Candidate can see results immediately.

---

## Score Interpretation

| Score Range | Label  | Meaning                        |
|-------------|--------|--------------------------------|
| 80-100%     | High   | Strong match, recommend review |
| 60-79%      | Medium | Partial match, has gaps        |
| 0-59%       | Low    | Below threshold, major gaps    |
