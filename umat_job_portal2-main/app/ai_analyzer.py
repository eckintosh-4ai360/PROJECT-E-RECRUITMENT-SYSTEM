# app/ai_analyzer.py - Improved version with better debugging
import spacy
import nltk
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import logging
import os
import json
from collections import defaultdict
from .work_experience_analyzer import extract_work_experience as extract_enhanced_work_experience

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except Exception as e:
    logging.error(f"Failed to download NLTK data: {e}")

def download_nltk_data():
    """Checks for required NLTK data and downloads if missing."""
    required_data = ["wordnet", "stopwords", "punkt", "averaged_perceptron_tagger", "punkt_tab"]
    nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
    if nltk_data_path not in nltk.data.path:
        nltk.data.path.append(nltk_data_path)
        logger.info(f"Added {nltk_data_path} to NLTK data path.")

    all_found = True
    for resource in required_data:
        try:
            nltk.download(resource, quiet=True)
            logger.info(f"NLTK resource '{resource}' downloaded/verified.")
        except Exception as e:
            logger.error(f"Failed to download NLTK resource '{resource}': {e}")
            all_found = False
    return all_found

# Ensure NLTK data is available at import time
if not download_nltk_data():
    logger.error("Essential NLTK data could not be downloaded or found. AI features may be limited.")

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_md")
    logger.info("spaCy model 'en_core_web_md' loaded successfully.")
except OSError:
    logger.error("spaCy model 'en_core_web_md' not found. Please download it using: python -m spacy download en_core_web_md")
    nlp = None

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Import enhanced skills database
try:
    from .skills_database import get_enhanced_skill_categories, get_skill_patterns, get_case_sensitive_skills, get_partial_match_skills
    SKILL_CATEGORIES = get_enhanced_skill_categories()
    SKILL_PATTERNS = get_skill_patterns()
    CASE_SENSITIVE_SKILLS = get_case_sensitive_skills()
    PARTIAL_MATCH_SKILLS = get_partial_match_skills()
    ENHANCED_SKILLS_AVAILABLE = True
except ImportError:
    # Fallback to basic skills if enhanced database is not available
    SKILL_CATEGORIES = {
        "programming_languages": [
            "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
            "rust", "typescript", "scala", "perl", "r", "matlab", "sql", "bash", "shell", "objective-c"
        ],
        "web_technologies": [
            "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring",
            "express", "jquery", "bootstrap", "sass", "less", "webpack", "graphql", "rest"
        ],
        "databases": [
            "mysql", "postgresql", "mongodb", "oracle", "sql server", "sqlite", "redis", "cassandra",
            "elasticsearch", "dynamodb", "neo4j", "mariadb", "plist", "nsuserdefaults", "core data"
        ],
        "cloud_platforms": [
            "aws", "azure", "google cloud", "heroku", "digitalocean", "kubernetes", "docker",
            "terraform", "jenkins", "gitlab", "github actions"
        ],
        "ai_ml": [
            "machine learning", "deep learning", "tensorflow", "pytorch", "keras", "scikit-learn",
            "pandas", "numpy", "opencv", "nlp", "computer vision", "neural networks"
        ],
        "soft_skills": [
            "communication", "leadership", "teamwork", "problem solving", "critical thinking",
            "time management", "project management", "collaboration", "adaptability"
        ]
    }
    SKILL_PATTERNS = {}
    CASE_SENSITIVE_SKILLS = {}
    PARTIAL_MATCH_SKILLS = {}
    ENHANCED_SKILLS_AVAILABLE = False

# Bias language patterns
BIASED_TERMS = {
    "gender_bias": [
        "chairman", "manpower", "mankind", "man-made", "businessman", "policeman",
        "fireman", "mailman", "stewardess", "waitress", "actress"
    ],
    "age_bias": [
        "young and dynamic", "digital native", "recent graduate", "mature",
        "overqualified", "senior citizen", "retiree"
    ],
    "cultural_bias": [
        "cultural fit", "native speaker", "urban", "ghetto", "ethnic",
        "diverse background", "minority"
    ]
}

# Required resume sections
REQUIRED_SECTIONS = {
    "contact_info": ["email", "phone", "address", "linkedin"],
    "education": ["degree", "university", "college", "school", "gpa", "graduation"],
    "experience": ["work experience", "employment", "job history", "internship"],
    "skills": ["skills", "technical skills", "competencies", "expertise"],
    "projects": ["projects", "portfolio", "github"],
    "achievements": ["achievements", "awards", "certifications", "honors"],
    "summary": ["summary", "objective", "profile", "about me"]
}

def analyze_resume_completeness(text):
    """Analyzes resume for completeness and required sections."""
    text_lower = text.lower()
    missing_sections = []
    present_sections = []
    
    for section, keywords in REQUIRED_SECTIONS.items():
        found = False
        for keyword in keywords:
            if keyword in text_lower:
                found = True
                present_sections.append(section)
                break
        if not found:
            missing_sections.append(section)
    
    completeness_score = len(present_sections) / len(REQUIRED_SECTIONS)
    
    return {
        "completeness_score": completeness_score,
        "present_sections": present_sections,
        "missing_sections": missing_sections,
        "improvement_tips": generate_improvement_tips(missing_sections)
    }

def extract_skills(text):
    """Extracts and categorizes skills from resume text using enhanced detection."""
    if not text:
        return {}
        
    text_lower = text.lower()
    skills_found = defaultdict(list)
    
    # Enhanced skill extraction with multiple detection methods
    extracted_skills = _extract_skills_comprehensive(text, text_lower)
    
    # Merge all extracted skills
    for category, skill_list in extracted_skills.items():
        skills_found[category].extend(skill_list)
    
    # Remove duplicates while preserving order
    for category in skills_found:
        seen = set()
        unique_skills = []
        for skill in skills_found[category]:
            if skill.lower() not in seen:
                seen.add(skill.lower())
                unique_skills.append(skill)
        skills_found[category] = unique_skills
    
    return dict(skills_found)

def _extract_skills_comprehensive(text, text_lower):
    """Comprehensive skill extraction using multiple detection methods."""
    skills = defaultdict(list)
    
    # Method 1: Basic taxonomy matching
    _extract_skills_taxonomy(text_lower, skills)
    
    # Method 2: Case-sensitive matching
    _extract_skills_case_sensitive(text, skills)
    
    # Method 3: Pattern-based matching
    _extract_skills_patterns(text, skills)
    
    # Method 4: Context-based extraction
    _extract_skills_context(text_lower, skills)
    
    return skills

def _extract_skills_taxonomy(text_lower, skills):
    """Extract skills using the enhanced taxonomy."""
    for category, skill_list in SKILL_CATEGORIES.items():
        for skill in skill_list:
            # Check for exact match
            if skill in text_lower:
                skills[category].append(skill)
            # Check for word boundary matches
            elif f" {skill} " in f" {text_lower} ":
                skills[category].append(skill)
            # Check for skill followed by common words
            elif any(f"{skill} {suffix}" in text_lower for suffix in ["development", "programming", "framework", "tool", "technology", "language"]):
                skills[category].append(skill)

def _extract_skills_case_sensitive(text, skills):
    """Extract case-sensitive skills."""
    if not ENHANCED_SKILLS_AVAILABLE:
        return
        
    for category, skill_list in CASE_SENSITIVE_SKILLS.items():
        for skill in skill_list:
            if skill in text:
                skills[category].append(skill)

def _extract_skills_patterns(text, skills):
    """Extract skills using regex patterns."""
    if not ENHANCED_SKILLS_AVAILABLE:
        return
        
    import re
    for category, patterns in SKILL_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skills[category].append(match.group(0))

def _extract_skills_context(text_lower, skills):
    """Extract skills based on context and surrounding words."""
    # Look for skills mentioned in specific contexts
    context_patterns = [
        (r"experience\s+(?:with|in)\s+([^,\n]+)", "experience_context"),
        (r"proficient\s+(?:in|with)\s+([^,\n]+)", "proficiency_context"),
        (r"skilled\s+(?:in|with)\s+([^,\n]+)", "skill_context"),
        (r"expertise\s+(?:in|with)\s+([^,\n]+)", "expertise_context"),
        (r"knowledge\s+(?:of|in)\s+([^,\n]+)", "knowledge_context"),
        (r"familiar\s+(?:with|in)\s+([^,\n]+)", "familiarity_context"),
        (r"worked\s+(?:with|on)\s+([^,\n]+)", "work_context"),
        (r"developed\s+(?:using|with)\s+([^,\n]+)", "development_context"),
        (r"built\s+(?:with|using)\s+([^,\n]+)", "building_context"),
        (r"implemented\s+(?:using|with)\s+([^,\n]+)", "implementation_context")
    ]
    
    import re
    for pattern, context_type in context_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            context_text = match.group(1).strip()
            # Extract potential skills from context
            _extract_skills_from_context(context_text, skills)

def _extract_skills_from_context(context_text, skills):
    """Extract skills from context text."""
    import re
    # Split by common separators
    potential_skills = re.split(r'[,;&|/]', context_text)
    
    for potential_skill in potential_skills:
        skill = potential_skill.strip()
        if len(skill) > 2:  # Filter out very short strings
            # Check if it matches any known skills
            for category, skill_list in SKILL_CATEGORIES.items():
                for known_skill in skill_list:
                    if known_skill in skill.lower() or skill.lower() in known_skill:
                        skills[category].append(known_skill)
                        break

def detect_bias_language(text):
    """Detects potentially biased language in text."""
    text_lower = text.lower()
    biases_found = defaultdict(list)
    
    for bias_type, terms in BIASED_TERMS.items():
        for term in terms:
            if term in text_lower:
                biases_found[bias_type].append(term)
    
    return dict(biases_found)

def extract_work_experience(text):
    """Enhanced work experience extraction using the dedicated analyzer."""
    try:
        # Use the enhanced work experience analyzer
        return extract_enhanced_work_experience(text)
    except Exception as e:
        logger.error(f"Enhanced work experience extraction failed: {e}")
        # Fall back to legacy method
        return extract_experience_level(text)

# Keep the old function name for backward compatibility
def extract_experience_level(text):
    """Legacy function - redirects to enhanced work experience extraction."""
    result = extract_work_experience(text)
    return {
        "total_years": result["total_years"],
        "experience_level": result["experience_level"],
        "matches": [exp.get('position', 'Unknown') for exp in result.get('work_experiences', [])]
    }

def generate_improvement_tips(missing_sections):
    """Generates specific improvement tips based on missing sections."""
    tips = []
    
    section_tips = {
        "contact_info": "Add complete contact information including email, phone, and LinkedIn profile.",
        "education": "Include your educational background with degrees, institutions, and graduation dates.",
        "experience": "Add detailed work experience with company names, dates, and key achievements.",
        "skills": "List relevant technical and soft skills, grouped by category.",
        "projects": "Showcase relevant projects with descriptions and technologies used.",
        "achievements": "Highlight certifications, awards, and notable accomplishments.",
        "summary": "Add a professional summary or objective statement at the top of your resume."
    }
    
    for section in missing_sections:
        if section in section_tips:
            tips.append(section_tips[section])
    
    return tips

# --- Improved Text Preprocessing --- 
def preprocess_text(text):
    """Cleans, tokenizes, removes stopwords, and lemmatizes text."""
    if not text:
        logger.warning("Empty text provided to preprocess_text")
        return ""
    
    try:
        # Convert to string if not already
        text = str(text)
        original_length = len(text)
        
        # Basic cleaning - less aggressive than before
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)  # Replace punctuation with spaces
        text = re.sub(r"\s+", " ", text)      # Normalize whitespace
        text = text.strip()
        
        logger.debug(f"Text length after cleaning: {len(text)} (was {original_length})")
        
        # Tokenization with fallback
        try:
            tokens = nltk.word_tokenize(text)
        except LookupError:
            tokens = text.split()
            logger.warning("Using fallback tokenization method")
        
        # Lemmatization and stopword removal
        lemmatized_tokens = [
            lemmatizer.lemmatize(word) for word in tokens 
            if word not in stop_words and len(word) > 1 and word.isalpha()
        ]
        
        result = " ".join(lemmatized_tokens)
        logger.debug(f"Preprocessed text length: {len(result)}, tokens: {len(lemmatized_tokens)}")
        
        if not result:
            logger.warning("Preprocessing resulted in empty text!")
            # Return a minimally processed version as fallback
            return " ".join([word for word in text.split() if len(word) > 1])
        
        return result
        
    except Exception as e:
        logger.error(f"Error in text preprocessing: {e}")
        # Return minimally processed text as fallback
        return re.sub(r"[^\w\s]", " ", str(text).lower()).strip()

# --- Improved Similarity Calculation --- 
def calculate_similarity(resume_text, job_description):
    """Calculates TF-IDF cosine similarity between resume and job description."""
    
    # Input validation with detailed logging
    if not resume_text:
        logger.warning("Empty resume text provided to calculate_similarity")
        return 0.0
    if not job_description:
        logger.warning("Empty job description provided to calculate_similarity")
        return 0.0

    logger.info(f"Original resume text length: {len(resume_text)}")
    logger.info(f"Original job description length: {len(job_description)}")

    # Preprocess texts
    processed_resume = preprocess_text(resume_text)
    processed_job = preprocess_text(job_description)

    logger.info(f"Processed resume text sample: {processed_resume[:200]}...")
    logger.info(f"Processed job description sample: {processed_job[:200]}...")

    # Check if preprocessing resulted in empty strings
    if not processed_resume:
        logger.warning("Resume preprocessing resulted in empty text")
        processed_resume = str(resume_text).lower()  # Fallback
    if not processed_job:
        logger.warning("Job description preprocessing resulted in empty text")
        processed_job = str(job_description).lower()  # Fallback

    logger.info(f"Processed resume length: {len(processed_resume)}")
    logger.info(f"Processed job description length: {len(processed_job)}")

    # TF-IDF calculation with better error handling
    try:
        vectorizer = TfidfVectorizer(
            max_features=1000,      # Limit features to avoid memory issues
            min_df=1,               # Include terms that appear at least once
            ngram_range=(1, 2),     # Include unigrams and bigrams
            lowercase=True
        )
        
        tfidf_matrix = vectorizer.fit_transform([processed_resume, processed_job])
        
        # Log the features being compared
        feature_names = vectorizer.get_feature_names_out()
        logger.info(f"Top features being compared: {', '.join(feature_names[:20])}...")
        
        # Check if vectors were created successfully
        if tfidf_matrix.shape[0] < 2:
            logger.warning("TF-IDF matrix has insufficient documents")
            return 0.0
        
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        score = similarity[0][0]
        
        logger.info(f"Calculated similarity score: {score}")
        return score
        
    except ValueError as e:
        logger.error(f"TF-IDF calculation failed: {e}")
        logger.debug(f"Resume sample: '{processed_resume[:100]}...'")
        logger.debug(f"Job sample: '{processed_job[:100]}...'")
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error in similarity calculation: {e}")
        return 0.0

# --- Enhanced Analysis Function --- 
def analyze_resume_and_match(resume_id, resume_text, all_jobs_data):
    """Enhanced resume analysis and job matching."""
    logger.info(f"Starting enhanced analysis for Resume ID: {resume_id}")
    
    if not resume_text or not all_jobs_data:
        logger.error("Missing resume text or job data")
        return []
    
    # Comprehensive resume analysis
    analysis_results = {
        "completeness": analyze_resume_completeness(resume_text),
        "skills": extract_skills(resume_text),
        "bias_check": detect_bias_language(resume_text),
        "experience": extract_experience_level(resume_text)
    }
    
    # Enhanced job matching
    match_results = []
    for job in all_jobs_data:
        if not isinstance(job, dict):
            continue
            
        job_id = job.get("job_id")
        job_description = job.get("description")
        job_title = job.get("title", "N/A")
        
        if not job_id or not job_description:
            continue
        
        # Calculate base similarity score
        similarity_score = calculate_similarity(resume_text, job_description)
        
        # Calculate skill match score
        job_skills = extract_skills(job_description)
        skill_match_score = calculate_skill_match_score(analysis_results["skills"], job_skills)
        
        # Calculate experience match
        exp_match_score = calculate_experience_match_score(
            analysis_results["experience"]["experience_level"],
            job_description
        )
        
        # Weighted final score
        final_score = (
            similarity_score * 0.4 +  # Base similarity
            skill_match_score * 0.4 + # Skill match
            exp_match_score * 0.2     # Experience match
        )
        
        match_details = {
            "base_similarity": similarity_score,
            "skill_match": skill_match_score,
            "experience_match": exp_match_score,
            "matching_skills": get_matching_skills(analysis_results["skills"], job_skills),
            "missing_skills": get_missing_skills(analysis_results["skills"], job_skills)
        }

        match_results.append({
            "resume_id": resume_id,
            "job_id": job_id,
            "match_score": round(final_score, 4),
            "match_details": json.dumps(match_details)
        })
    
    # Sort by final score
    match_results.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "analysis": analysis_results,
        "matches": match_results
    }

def calculate_skill_match_score(resume_skills, job_skills):
    """Calculate weighted skill match score."""
    if not resume_skills or not job_skills:
        return 0.0
    
    total_weight = 0
    matched_weight = 0
    
    # Category weights
    weights = {
        "programming_languages": 0.25,
        "web_technologies": 0.2,
        "databases": 0.15,
        "cloud_platforms": 0.15,
        "ai_ml": 0.15,
        "soft_skills": 0.1
    }
    
    for category, weight in weights.items():
        if category in job_skills and job_skills[category]:
            total_weight += weight
            if category in resume_skills:
                matched_skills = set(resume_skills[category]) & set(job_skills[category])
                if matched_skills:
                    matched_weight += weight * (len(matched_skills) / len(job_skills[category]))
    
    return matched_weight / total_weight if total_weight > 0 else 0.0

def calculate_experience_match_score(resume_level, job_description):
    """Calculate experience level match score."""
    job_desc_lower = job_description.lower()
    
    # Extract required experience level from job description
    required_level = "entry"
    if any(term in job_desc_lower for term in ["senior", "lead", "architect", "principal"]):
        required_level = "senior"
    elif any(term in job_desc_lower for term in ["mid", "intermediate", "experienced"]):
        required_level = "mid"
    
    # Score based on match
    if resume_level == required_level:
        return 1.0
    elif resume_level == "senior" and required_level in ["mid", "entry"]:
        return 0.8
    elif resume_level == "mid" and required_level == "entry":
        return 0.9
    elif resume_level == "mid" and required_level == "senior":
        return 0.6
    elif resume_level == "entry" and required_level == "mid":
        return 0.4
    elif resume_level == "entry" and required_level == "senior":
        return 0.2
    
    return 0.0

def get_matching_skills(resume_skills, job_skills):
    """Get list of matching skills between resume and job."""
    matching = defaultdict(list)
    
    for category in SKILL_CATEGORIES.keys():
        if category in resume_skills and category in job_skills:
            matching[category] = list(
                set(resume_skills[category]) & set(job_skills[category])
            )
    
    return dict(matching)

def get_missing_skills(resume_skills, job_skills):
    """Get list of skills required by job but missing from resume."""
    missing = defaultdict(list)
    
    for category in SKILL_CATEGORIES.keys():
        if category in job_skills:
            if category not in resume_skills:
                missing[category] = job_skills[category]
            else:
                missing[category] = list(
                    set(job_skills[category]) - set(resume_skills[category])
                )
    
    return dict(missing)

# Add a debugging function
def debug_analyze_resume(resume_text, job_description):
    """Debug function to test individual resume-job matching"""
    print(f"=== DEBUGGING RESUME ANALYSIS ===")
    print(f"Resume text length: {len(resume_text)}")
    print(f"Job description length: {len(job_description)}")
    
    processed_resume = preprocess_text(resume_text)
    processed_job = preprocess_text(job_description)
    
    print(f"Processed resume length: {len(processed_resume)}")
    print(f"Processed job length: {len(processed_job)}")
    print(f"Processed resume sample: {processed_resume[:200]}...")
    print(f"Processed job sample: {processed_job[:200]}...")
    
    similarity = calculate_similarity(resume_text, job_description)
    print(f"Similarity score: {similarity}")
    
    return similarity

# --- Example Usage (for testing) --- 
if __name__ == "__main__":
    logger.info("Running AI Analyzer test...")
    
    sample_resume_text = """
    Highly motivated Software Engineer with 3+ years of experience in Python, Django, and SQL.
    Developed web applications using Flask and React. Familiar with AWS cloud services and Docker.
    Seeking a challenging role in data science or machine learning. BSc Computer Science.
    Skills: Python, SQL, Django, Flask, React, JavaScript, HTML, CSS, Git, Docker, AWS, Machine Learning.
    """
    
    sample_jobs = [
        {
            "job_id": 101, 
            "title": "Backend Python Developer", 
            "description": "Looking for a Python developer proficient in Django or Flask. Experience with SQL databases (MySQL/PostgreSQL) and REST APIs required. Cloud experience (AWS) is a plus."
        },
        {
            "job_id": 102, 
            "title": "Frontend Developer (React)", 
            "description": "Seeking a skilled Frontend Developer with strong experience in React, JavaScript, HTML, and CSS. Must be able to build responsive user interfaces. Node.js knowledge is beneficial."
        },
        {
            "job_id": 103, 
            "title": "Data Scientist", 
            "description": "Join our data science team! We need experts in machine learning, Python (pandas, scikit-learn), and data analysis. Experience with NLP or deep learning is highly valued. Requires MSc or PhD."
        }
    ]
    
    sample_resume_id = 999
    
    # Test individual matching first
    print("\n=== INDIVIDUAL MATCHING TEST ===")
    for job in sample_jobs:
        score = debug_analyze_resume(sample_resume_text, job["description"])
        print(f"Job {job['job_id']}: {score:.4f}\n")
    
    # Test full analysis
    print("\n=== FULL ANALYSIS TEST ===")
    results = analyze_resume_and_match(sample_resume_id, sample_resume_text, sample_jobs)
    
    print("\n--- Match Results ---")
    if results:
        for result in results:
            job_title = next((job['title'] for job in sample_jobs if job['job_id'] == result['job_id']), 'N/A')
            print(f"  Job ID: {result['job_id']} ('{job_title}') - Score: {result['match_score']}")
    else:
        print("No matches found or error occurred.")