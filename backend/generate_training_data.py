"""
Generate synthetic training data for CV Screening ML models.

Creates a CSV with realistic CV-job pairs labeled as match (1) or no-match (0).

Usage:
    python generate_training_data.py --output training_data.csv --samples 2000
"""
import csv
import random
import argparse

# ─── Skill Pools ─────────────────────────────────────────────
SKILLS = {
    "backend": ["python", "django", "flask", "fastapi", "java", "spring boot", "node.js", "express", "go", "rust", "php", "laravel", "ruby", "rails"],
    "frontend": ["react", "angular", "vue", "next.js", "typescript", "javascript", "html", "css", "tailwind", "svelte", "redux", "webpack"],
    "data": ["pandas", "numpy", "scipy", "matplotlib", "seaborn", "jupyter", "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch"],
    "ml": ["tensorflow", "pytorch", "keras", "scikit-learn", "xgboost", "huggingface", "bert", "nlp", "computer vision", "deep learning", "spacy", "opencv"],
    "devops": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "ci/cd", "linux", "nginx", "ansible", "github actions"],
    "mobile": ["flutter", "react native", "swift", "kotlin", "android", "ios"],
}

EDUCATION = ["diploma", "bachelors", "masters", "phd"]
EDU_LEVELS = {"diploma": 1, "bachelors": 2, "masters": 3, "phd": 4}

JOB_TEMPLATES = [
    {
        "title": "Senior Backend Engineer",
        "category": "backend",
        "required_skills": ["python", "django", "postgresql", "docker"],
        "preferred_skills": ["aws", "redis", "ci/cd", "kubernetes"],
        "min_experience": 5,
        "min_education": "bachelors",
        "description": "Build and maintain scalable backend services using Python and Django. Design REST APIs, manage database schemas, and deploy to cloud infrastructure.",
    },
    {
        "title": "ML Engineer",
        "category": "ml",
        "required_skills": ["python", "tensorflow", "scikit-learn"],
        "preferred_skills": ["pytorch", "bert", "nlp", "docker", "aws"],
        "min_experience": 3,
        "min_education": "masters",
        "description": "Design and deploy machine learning models for production NLP systems. Work with BERT, transformers, and traditional ML algorithms.",
    },
    {
        "title": "Full Stack Developer",
        "category": "frontend",
        "required_skills": ["react", "node.js", "javascript", "postgresql"],
        "preferred_skills": ["typescript", "next.js", "docker", "aws", "mongodb"],
        "min_experience": 3,
        "min_education": "bachelors",
        "description": "Develop full-stack web applications using React and Node.js. Build responsive UIs and scalable APIs.",
    },
    {
        "title": "Data Scientist",
        "category": "data",
        "required_skills": ["python", "pandas", "sql", "scikit-learn"],
        "preferred_skills": ["tensorflow", "matplotlib", "jupyter", "xgboost"],
        "min_experience": 2,
        "min_education": "masters",
        "description": "Analyze large datasets, build predictive models, and communicate insights to stakeholders.",
    },
    {
        "title": "DevOps Engineer",
        "category": "devops",
        "required_skills": ["aws", "docker", "kubernetes", "linux"],
        "preferred_skills": ["terraform", "jenkins", "ci/cd", "ansible", "python"],
        "min_experience": 4,
        "min_education": "bachelors",
        "description": "Manage cloud infrastructure, CI/CD pipelines, and container orchestration on AWS.",
    },
    {
        "title": "Frontend Developer",
        "category": "frontend",
        "required_skills": ["react", "javascript", "css", "html"],
        "preferred_skills": ["typescript", "next.js", "tailwind", "redux", "webpack"],
        "min_experience": 2,
        "min_education": "bachelors",
        "description": "Build modern, responsive web interfaces with React and related technologies.",
    },
    {
        "title": "Data Engineer",
        "category": "data",
        "required_skills": ["python", "sql", "aws", "docker"],
        "preferred_skills": ["spark", "airflow", "postgresql", "mongodb", "kubernetes"],
        "min_experience": 3,
        "min_education": "bachelors",
        "description": "Design and maintain data pipelines, ETL processes, and data warehouses.",
    },
    {
        "title": "Mobile Developer",
        "category": "mobile",
        "required_skills": ["flutter", "dart"],
        "preferred_skills": ["react native", "kotlin", "swift", "firebase"],
        "min_experience": 2,
        "min_education": "bachelors",
        "description": "Build cross-platform mobile applications using Flutter.",
    },
    {
        "title": "NLP Researcher",
        "category": "ml",
        "required_skills": ["python", "pytorch", "bert", "nlp"],
        "preferred_skills": ["huggingface", "spacy", "tensorflow", "deep learning"],
        "min_experience": 3,
        "min_education": "phd",
        "description": "Research and implement state-of-the-art NLP models. Publish findings and deploy models to production.",
    },
    {
        "title": "Cloud Architect",
        "category": "devops",
        "required_skills": ["aws", "terraform", "kubernetes", "docker"],
        "preferred_skills": ["azure", "gcp", "linux", "python", "ci/cd"],
        "min_experience": 6,
        "min_education": "bachelors",
        "description": "Design and implement cloud architecture solutions. Lead cloud migration and infrastructure optimization.",
    },
]

# ─── Candidate Generator ─────────────────────────────────────
FIRST_NAMES = ["Rahim", "Fatima", "Arif", "Nusrat", "Kamal", "Ayesha", "Tanvir", "Sabrina", "Hasan", "Momena",
               "Zahid", "Farzana", "Imran", "Razia", "Masud", "Taslima", "Shahid", "Nasrin", "Jahangir", "Salma",
               "Alex", "Maria", "John", "Sarah", "Chen", "Priya", "Ahmed", "Lina", "Omar", "Yuki"]
LAST_NAMES = ["Uddin", "Akter", "Hasan", "Jahan", "Islam", "Rahman", "Khan", "Begum", "Chowdhury", "Ahmed",
              "Smith", "Garcia", "Lee", "Kim", "Singh", "Patel", "Chen", "Ali", "Das", "Roy"]


def generate_candidate_skills(job, match_level):
    """Generate candidate skills based on desired match level."""
    all_skills = []
    for cat_skills in SKILLS.values():
        all_skills.extend(cat_skills)

    required = job["required_skills"]
    preferred = job["preferred_skills"]
    candidate_skills = set()

    if match_level == "high":
        # Match all required + most preferred + some extras
        candidate_skills.update(required)
        candidate_skills.update(random.sample(preferred, min(len(preferred), random.randint(2, len(preferred)))))
        extras = [s for s in all_skills if s not in candidate_skills]
        candidate_skills.update(random.sample(extras, min(len(extras), random.randint(2, 5))))

    elif match_level == "medium":
        # Match some required + some preferred
        num_req = random.randint(max(1, len(required) - 2), len(required) - 1)
        candidate_skills.update(random.sample(required, num_req))
        if preferred:
            candidate_skills.update(random.sample(preferred, min(len(preferred), random.randint(1, 3))))
        extras = [s for s in all_skills if s not in candidate_skills]
        candidate_skills.update(random.sample(extras, min(len(extras), random.randint(1, 4))))

    else:  # low
        # Match few/no required, random skills
        if required and random.random() > 0.4:
            candidate_skills.update(random.sample(required, random.randint(0, max(1, len(required) // 3))))
        # Add random skills from other categories
        other_cats = [cat for cat in SKILLS.keys() if cat != job["category"]]
        for cat in random.sample(other_cats, min(2, len(other_cats))):
            candidate_skills.update(random.sample(SKILLS[cat], min(len(SKILLS[cat]), random.randint(1, 3))))

    return list(candidate_skills)


def generate_cv_text(name, skills, education, experience_years, job_title):
    """Generate realistic CV text content."""
    edu_details = {
        "phd": f"PhD in Computer Science from University of Dhaka, 2015-2019",
        "masters": f"MSc in Computer Science from BUET, 2017-2019",
        "bachelors": f"BSc in CSE from BRAC University, 2015-2019",
        "diploma": f"Diploma in IT from Dhaka Polytechnic, 2016-2018",
    }

    companies = ["TechBD", "DataSoft", "Brain Station 23", "Therap Services", "Pathao",
                 "Grameenphone", "bKash", "Samsung R&D", "TigerIT", "Chaldal"]

    cv_parts = [
        f"RESUME - {name}",
        f"Email: {name.lower().replace(' ', '.')}@email.com",
        f"Phone: +880 1{random.randint(300000000, 999999999)}",
        "",
        "SUMMARY",
        f"Experienced software professional with {experience_years} years of experience in software development and technology.",
        f"Skilled in {', '.join(random.sample(skills, min(5, len(skills))))}.",
        "",
        "EDUCATION",
        edu_details.get(education, "BSc in Computer Science"),
        "",
        "SKILLS",
        f"Programming & Tools: {', '.join(skills)}",
        "",
        "EXPERIENCE",
    ]

    # Generate work experience entries
    years_left = experience_years
    for i in range(min(3, max(1, int(experience_years / 2)))):
        company = random.choice(companies)
        role_years = max(1, min(years_left, random.randint(1, 4)))
        end_year = 2026 - sum(range(i))
        start_year = end_year - role_years
        cv_parts.extend([
            f"  {random.choice(['Software Engineer', 'Senior Developer', 'ML Engineer', 'Full Stack Developer', 'Data Scientist'])} at {company}",
            f"  {start_year} - {end_year if i > 0 else 'Present'}",
            f"  - Worked with {', '.join(random.sample(skills, min(3, len(skills))))}",
            f"  - Delivered {random.randint(3, 15)} projects",
            "",
        ])
        years_left -= role_years
        if years_left <= 0:
            break

    # Projects
    cv_parts.extend([
        "PROJECTS",
        f"  - Built a {random.choice(['web app', 'ML model', 'API service', 'data pipeline'])} using {', '.join(random.sample(skills, min(3, len(skills))))}",
        f"  - Developed {random.choice(['automated testing suite', 'CI/CD pipeline', 'recommendation engine', 'analytics dashboard'])}",
    ])

    return "\n".join(cv_parts)


def calculate_match_score(candidate_skills, job, education, experience):
    """Calculate a realistic match score."""
    required = set(job["required_skills"])
    preferred = set(job["preferred_skills"])
    cand_set = set(candidate_skills)

    # Hard requirement match (0-40 points)
    req_match = len(required.intersection(cand_set)) / max(len(required), 1)
    hard_score = req_match * 40

    # Preferred skill match (0-20 points)
    pref_match = len(preferred.intersection(cand_set)) / max(len(preferred), 1)
    pref_score = pref_match * 20

    # Education match (0-15 points)
    min_edu = EDU_LEVELS.get(job["min_education"], 2)
    cand_edu = EDU_LEVELS.get(education, 2)
    edu_score = min(cand_edu / max(min_edu, 1), 1.0) * 15

    # Experience match (0-15 points)
    exp_ratio = min(experience / max(job["min_experience"], 1), 1.5)
    exp_score = min(exp_ratio, 1.0) * 15

    # Skill diversity bonus (0-10 points)
    diversity_score = min(len(cand_set) / 10, 1.0) * 10

    total = hard_score + pref_score + edu_score + exp_score + diversity_score
    # Add some noise
    total += random.uniform(-5, 5)
    return max(0, min(100, round(total, 1)))


def generate_dataset(num_samples=2000):
    """Generate the complete training dataset."""
    data = []

    for i in range(num_samples):
        # Pick a random job
        job = random.choice(JOB_TEMPLATES)

        # Decide match level (balanced dataset)
        match_level = random.choices(
            ["high", "medium", "low"],
            weights=[0.3, 0.35, 0.35],
            k=1,
        )[0]

        # Generate candidate
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        skills = generate_candidate_skills(job, match_level)

        # Education based on match level
        if match_level == "high":
            edu_idx = max(EDUCATION.index(job["min_education"]), random.randint(1, 3))
        elif match_level == "medium":
            edu_idx = random.randint(max(0, EDUCATION.index(job["min_education"]) - 1), 3)
        else:
            edu_idx = random.randint(0, max(1, EDUCATION.index(job["min_education"]) - 1))
        education = EDUCATION[min(edu_idx, 3)]

        # Experience based on match level
        if match_level == "high":
            experience = job["min_experience"] + random.randint(0, 5)
        elif match_level == "medium":
            experience = max(1, job["min_experience"] + random.randint(-2, 2))
        else:
            experience = max(0, random.randint(0, max(1, job["min_experience"] - 2)))

        # Generate CV text
        cv_text = generate_cv_text(name, skills, education, experience, job["title"])
        job_description = f"{job['title']}: {job['description']} Required: {', '.join(job['required_skills'])}. Preferred: {', '.join(job['preferred_skills'])}. Min {job['min_experience']} years experience. {job['min_education']} degree required."

        # Calculate score and label
        score = calculate_match_score(skills, job, education, experience)
        label = 1 if score >= 55 else 0  # Binary: suitable or not

        data.append({
            "cv_text": cv_text,
            "job_description": job_description,
            "job_title": job["title"],
            "job_category": job["category"],
            "candidate_name": name,
            "skills": ",".join(skills),
            "education": education,
            "experience_years": experience,
            "skill_match_count": len(set(skills).intersection(set(job["required_skills"]))),
            "total_required": len(job["required_skills"]),
            "score": score,
            "label": label,
        })

    return data


def main():
    parser = argparse.ArgumentParser(description="Generate training data for CV screening")
    parser.add_argument("--output", type=str, default="training_data.csv", help="Output CSV path")
    parser.add_argument("--samples", type=int, default=2000, help="Number of samples")
    args = parser.parse_args()

    print(f"Generating {args.samples} samples...")
    data = generate_dataset(args.samples)

    # Write CSV
    fieldnames = list(data[0].keys())
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    # Stats
    labels = [d["label"] for d in data]
    print(f"Dataset saved to: {args.output}")
    print(f"Total samples: {len(data)}")
    print(f"Positive (match): {sum(labels)} ({sum(labels)/len(labels)*100:.1f}%)")
    print(f"Negative (no match): {len(labels)-sum(labels)} ({(len(labels)-sum(labels))/len(labels)*100:.1f}%)")
    print(f"Job categories: {set(d['job_category'] for d in data)}")


if __name__ == "__main__":
    main()
