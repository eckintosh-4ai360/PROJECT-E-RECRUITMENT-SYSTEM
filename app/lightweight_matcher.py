import json
import math
import re
from collections import Counter, defaultdict


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "in", "is", "it", "its", "of", "on", "or", "that", "the", "to",
    "was", "were", "will", "with", "you", "your"
}

SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
        "swift", "kotlin", "go", "rust", "sql", "r", "matlab"
    ],
    "web_technologies": [
        "html", "css", "react", "angular", "vue", "node", "node.js", "django",
        "flask", "spring", "express", "bootstrap", "graphql", "rest"
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "oracle", "sql server",
        "sqlite", "redis", "mariadb"
    ],
    "cloud_platforms": [
        "aws", "azure", "google cloud", "gcp", "heroku", "docker", "kubernetes",
        "terraform", "jenkins", "github actions"
    ],
    "ai_ml": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "keras",
        "scikit-learn", "pandas", "numpy", "nlp", "computer vision"
    ],
    "soft_skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "critical thinking", "time management", "project management",
        "collaboration", "adaptability"
    ],
}


def _tokens(text):
    return [
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+#.-]*", (text or "").lower())
        if len(token) > 1 and token not in STOP_WORDS
    ]


def _cosine_similarity(text_a, text_b):
    counts_a = Counter(_tokens(text_a))
    counts_b = Counter(_tokens(text_b))
    if not counts_a or not counts_b:
        return 0.0

    shared = set(counts_a) & set(counts_b)
    numerator = sum(counts_a[token] * counts_b[token] for token in shared)
    denominator = math.sqrt(sum(value * value for value in counts_a.values())) * math.sqrt(
        sum(value * value for value in counts_b.values())
    )
    return numerator / denominator if denominator else 0.0


def extract_skills(text):
    text_lower = (text or "").lower()
    found = defaultdict(list)
    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            if skill in text_lower:
                found[category].append(skill)
    return dict(found)


def analyze_resume_completeness(text):
    text_lower = (text or "").lower()
    section_map = {
        "contact_info": ["email", "phone", "linkedin", "github"],
        "education": ["education", "university", "degree", "college", "school"],
        "experience": ["experience", "work", "employment", "internship"],
        "skills": ["skills", "technical", "competencies", "expertise"],
        "projects": ["project", "portfolio"],
        "achievements": ["award", "achievement", "certification", "honor"],
        "summary": ["summary", "objective", "profile"],
    }

    present_sections = []
    missing_sections = []
    section_scores = {}

    for section, keywords in section_map.items():
        is_present = any(keyword in text_lower for keyword in keywords)
        section_scores[section] = 1.0 if is_present else 0.0
        if is_present:
            present_sections.append(section)
        else:
            missing_sections.append({
                "section": section,
                "importance": "medium",
                "tip": f"Consider adding a {section.replace('_', ' ')} section.",
            })

    return {
        "completeness_score": sum(section_scores.values()) / len(section_scores),
        "present_sections": present_sections,
        "missing_sections": missing_sections,
        "section_scores": section_scores,
    }


def extract_experience_level(text):
    text_lower = (text or "").lower()
    years = 0
    for match in re.finditer(r"(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience)?", text_lower):
        years = max(years, int(match.group(1)))

    level = "entry"
    if years > 5:
        level = "senior"
    elif years > 2:
        level = "mid"

    return {
        "years": years,
        "level": level,
        "total_years": years,
        "experience_level": level,
    }


def _skill_match(resume_skills, job_skills):
    matching = defaultdict(list)
    missing = defaultdict(list)
    matched_count = 0
    total_count = 0

    for category, skills in job_skills.items():
        resume_category_skills = set(resume_skills.get(category, []))
        for skill in skills:
            total_count += 1
            if skill in resume_category_skills:
                matched_count += 1
                matching[category].append(skill)
            else:
                missing[category].append(skill)

    score = matched_count / total_count if total_count else 0.0
    return score, dict(matching), dict(missing)


def _experience_match(resume_level, job_text):
    job_text = (job_text or "").lower()
    required_level = "entry"
    if any(term in job_text for term in ["senior", "lead", "architect", "principal"]):
        required_level = "senior"
    elif any(term in job_text for term in ["mid", "intermediate", "experienced"]):
        required_level = "mid"

    order = {"entry": 0, "mid": 1, "senior": 2}
    resume_rank = order.get(resume_level, 0)
    required_rank = order.get(required_level, 0)
    if resume_rank >= required_rank:
        return 1.0
    return 0.5 if required_rank - resume_rank == 1 else 0.25


def analyze_resume_and_match(resume_id, resume_text, all_jobs_data):
    resume_text = resume_text or ""
    resume_skills = extract_skills(resume_text)
    experience = extract_experience_level(resume_text)
    analysis = {
        "completeness": analyze_resume_completeness(resume_text),
        "skills": resume_skills,
        "experience": experience,
        "bias_check": {},
    }

    matches = []
    for job in all_jobs_data or []:
        job_id = job.get("job_id")
        if not job_id:
            continue

        job_text = " ".join([
            str(job.get("title") or ""),
            str(job.get("description") or ""),
            str(job.get("requirements") or ""),
        ]).strip()
        if not job_text:
            continue

        job_skills = extract_skills(job_text)
        similarity_score = _cosine_similarity(resume_text, job_text)
        skill_score, matching_skills, missing_skills = _skill_match(resume_skills, job_skills)
        experience_score = _experience_match(experience["level"], job_text)
        final_score = (similarity_score * 0.45) + (skill_score * 0.4) + (experience_score * 0.15)

        match_details = {
            "base_similarity": round(similarity_score, 4),
            "skill_match": round(skill_score, 4),
            "experience_match": round(experience_score, 4),
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
        }

        matches.append({
            "resume_id": resume_id,
            "job_id": job_id,
            "match_score": round(final_score, 4),
            "match_details": json.dumps(match_details),
        })

    matches.sort(key=lambda item: item["match_score"], reverse=True)
    return {"analysis": analysis, "matches": matches}
