# """Enhanced resume analysis module with bias detection and skill taxonomy."""

import spacy
import nltk
import json
from collections import defaultdict
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Skill taxonomy data
SKILL_CATEGORIES = {
    "programming_languages": [
        "python", "java", "javascript", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
        "rust", "typescript", "scala", "perl", "r", "matlab", "sql", "bash", "shell"
    ],
    "web_technologies": [
        "html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring",
        "express", "jquery", "bootstrap", "sass", "less", "webpack", "graphql", "rest"
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "oracle", "sql server", "sqlite", "redis", "cassandra",
        "elasticsearch", "dynamodb", "neo4j", "mariadb"
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

# Required resume sections with inclusive alternatives
REQUIRED_SECTIONS = {
    "contact_info": {
        "keywords": ["email", "phone", "address", "linkedin"],
        "importance": "critical",
        "tip": "Ensure your contact information is professional and up-to-date"
    },
    "education": {
        "keywords": ["degree", "university", "college", "school", "gpa", "graduation"],
        "importance": "high",
        "tip": "List relevant education, including non-traditional learning paths"
    },
    "experience": {
        "keywords": ["work experience", "employment", "job history", "internship", "volunteer"],
        "importance": "critical",
        "tip": "Include diverse experiences, both paid and unpaid"
    },
    "skills": {
        "keywords": ["skills", "technical skills", "competencies", "expertise"],
        "importance": "high",
        "tip": "List both technical and transferable skills"
    },
    "projects": {
        "keywords": ["projects", "portfolio", "github", "contributions"],
        "importance": "medium",
        "tip": "Showcase practical applications of your skills"
    },
    "achievements": {
        "keywords": ["achievements", "awards", "certifications", "honors", "recognition"],
        "importance": "medium",
        "tip": "Include relevant accomplishments from various contexts"
    },
    "summary": {
        "keywords": ["summary", "objective", "profile", "about me"],
        "importance": "high",
        "tip": "Write a clear, focused professional summary"
    }
}

class ResumeAnalyzer:
    def __init__(self):
        """Initialize the resume analyzer with required NLP models."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("Downloading spaCy model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def analyze_resume(self, text):
        """Perform comprehensive resume analysis."""
        if not text:
            logger.error("Empty resume text provided")
            return None

        analysis = {
            "completeness": self.analyze_completeness(text),
            "skills": self.extract_skills(text),
            "bias_check": self.detect_bias(text),
            "experience": self.extract_experience(text),
            "improvement_suggestions": self.generate_suggestions(text)
        }

        return analysis

    def analyze_completeness(self, text):
        """Analyze resume completeness and section presence."""
        text_lower = text.lower()
        analysis = {
            "present_sections": [],
            "missing_sections": [],
            "section_scores": {}
        }

        for section, details in REQUIRED_SECTIONS.items():
            found = False
            for keyword in details["keywords"]:
                if keyword in text_lower:
                    found = True
                    break

            if found:
                analysis["present_sections"].append(section)
                analysis["section_scores"][section] = 1.0
            else:
                analysis["missing_sections"].append({
                    "section": section,
                    "importance": details["importance"],
                    "tip": details["tip"]
                })
                analysis["section_scores"][section] = 0.0

        # Calculate weighted completeness score
        weights = {"critical": 0.4, "high": 0.3, "medium": 0.2, "low": 0.1}
        total_weight = 0
        weighted_score = 0

        for section, details in REQUIRED_SECTIONS.items():
            weight = weights[details["importance"]]
            total_weight += weight
            weighted_score += weight * analysis["section_scores"][section]

        analysis["completeness_score"] = weighted_score / total_weight if total_weight > 0 else 0
        return analysis

    def extract_skills(self, text):
        """Extract and categorize skills from resume text."""
        text_lower = text.lower()
        skills = defaultdict(list)
        
        # Extract skills using taxonomy
        for category, skill_list in SKILL_CATEGORIES.items():
            for skill in skill_list:
                if skill in text_lower:
                    skills[category].append(skill)

        # Use spaCy for additional skill extraction
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE"]:
                # Check if entity might be a technology or tool
                if any(tech_word in ent.text.lower() for tech_word in ["framework", "language", "tool", "platform", "system"]):
                    skills["other_technologies"].append(ent.text)

        return dict(skills)

    def detect_bias(self, text):
        """Detect potentially biased language in resume."""
        text_lower = text.lower()
        biases = defaultdict(list)
        
        for bias_type, terms in BIASED_TERMS.items():
            for term in terms:
                if term in text_lower:
                    biases[bias_type].append({
                        "term": term,
                        "suggestion": self.get_inclusive_alternative(term)
                    })

        return dict(biases)

    def extract_experience(self, text):
        """Extract and analyze professional experience details."""
        text_lower = text.lower()
        experience = {
            "years": 0,
            "level": "entry",
            "positions": [],
            "domains": []
        }

        # Extract years of experience
        year_patterns = [
            r'(\d+)\+?\s*years?\s*(of)?\s*experience',
            r'(\d+)\+?\s*years?\s*(in|at)',
            r'experience\s*:\s*(\d+)\+?\s*years?'
        ]

        for pattern in year_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                years = int(match.group(1))
                experience["years"] = max(experience["years"], years)

        # Determine experience level
        if experience["years"] > 8:
            experience["level"] = "senior"
        elif experience["years"] > 3:
            experience["level"] = "mid"

        # Extract position titles and domains
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                experience["domains"].append(ent.text)

        return experience

    def generate_suggestions(self, text):
        """Generate personalized improvement suggestions."""
        suggestions = []
        
        # Analyze completeness
        completeness = self.analyze_completeness(text)
        for missing in completeness["missing_sections"]:
            suggestions.append({
                "category": "structure",
                "importance": missing["importance"],
                "suggestion": missing["tip"]
            })

        # Check for bias
        biases = self.detect_bias(text)
        for bias_type, terms in biases.items():
            for term in terms:
                suggestions.append({
                    "category": "inclusive_language",
                    "importance": "high",
                    "suggestion": f"Consider replacing '{term['term']}' with '{term['suggestion']}'"
                })

        # Analyze skills presentation
        skills = self.extract_skills(text)
        if len(skills.get("soft_skills", [])) < 3:
            suggestions.append({
                "category": "skills",
                "importance": "medium",
                "suggestion": "Add more soft skills to balance your technical expertise"
            })

        return suggestions

    def get_inclusive_alternative(self, term):
        """Get inclusive alternative for biased terms."""
        alternatives = {
            "chairman": "chairperson",
            "manpower": "workforce",
            "mankind": "humanity",
            "man-made": "artificial",
            "businessman": "business person",
            "policeman": "police officer",
            "fireman": "firefighter",
            "mailman": "mail carrier",
            "stewardess": "flight attendant",
            "waitress": "server",
            "actress": "actor",
            "young and dynamic": "motivated",
            "digital native": "digitally proficient",
            "recent graduate": "early career professional",
            "mature": "experienced",
            "overqualified": "highly qualified",
            "senior citizen": "experienced professional",
            "retiree": "professional",
            "cultural fit": "team fit",
            "native speaker": "fluent speaker",
            "urban": "city-based",
            "ghetto": "neighborhood",
            "ethnic": "diverse",
            "diverse background": "varied background",
            "minority": "underrepresented group"
        }
        return alternatives.get(term, "neutral alternative") 