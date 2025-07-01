# """Enhanced resume analysis module with bias detection and skill taxonomy."""

import spacy
import nltk
import json
from collections import defaultdict
import re
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports - advanced NLP
try:
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from flashtext import KeywordProcessor
    
    # Download required NLTK resources
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')
        
    ADVANCED_NLP_AVAILABLE = True
    logger.info("Advanced NLP modules loaded successfully")
except ImportError as e:
    ADVANCED_NLP_AVAILABLE = False
    logger.warning(f"Some advanced NLP features will not be available: {e}")

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
            
        # Initialize advanced features if available
        self.advanced_nlp = ADVANCED_NLP_AVAILABLE
        
        if self.advanced_nlp:
            # Initialize sentence transformer model for semantic analysis
            try:
                self.sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading sentence transformer: {e}")
                self.sentence_model = None
                
            # Initialize keyword processor for efficient keyword matching
            self.keyword_processor = KeywordProcessor()
            self.load_keyword_dictionaries()
            
            # Initialize TF-IDF vectorizer for content analysis
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Load custom NER pipeline components if available
            self.load_custom_ner_components()
        else:
            logger.warning("Advanced NLP features are disabled due to missing dependencies")
            self.sentence_model = None
            self.keyword_processor = None
            self.tfidf_vectorizer = None
    
    def load_keyword_dictionaries(self):
        """Load keyword dictionaries for efficient matching."""
        # Add skills to keyword processor
        for category, skills in SKILL_CATEGORIES.items():
            for skill in skills:
                self.keyword_processor.add_keyword(skill, (skill, category))
                
        # Add job title keywords
        job_titles = [
            "software engineer", "data scientist", "product manager", "project manager",
            "developer", "analyst", "designer", "architect", "director", "manager",
            "coordinator", "specialist", "consultant", "administrator", "engineer",
            "technician", "researcher", "assistant", "associate", "lead", "senior"
        ]
        for title in job_titles:
            self.keyword_processor.add_keyword(title, (title, "job_title"))
    
    def load_custom_ner_components(self):
        """Load custom NER components if available."""
        # This would typically load a custom trained model
        # For now we'll use spaCy's built-in NER with some enhancements
        pass
    
    def analyze_resume(self, text):
        """Perform comprehensive resume analysis."""
        if not text:
            logger.error("Empty resume text provided")
            return None

        # Create base analysis with core features
        analysis = {
            "completeness": self.analyze_completeness(text),
            "skills": self.extract_skills(text),
            "bias_check": self.detect_bias(text),
            "experience": self.extract_experience(text),
            "improvement_suggestions": self.generate_suggestions(text)
        }
        
        # Add advanced analysis if available
        if self.advanced_nlp:
            try:
                # Preprocess text
                processed_text = self.preprocess_text(text)
                
                # Extract structured sections
                sections = self.extract_resume_sections(text)
                
                # Add advanced analysis components
                advanced_analysis = {
                    "skills_advanced": self.extract_skills_advanced(text),
                    "job_titles": self.extract_job_titles(text),
                    "responsibilities": self.extract_responsibilities(text),
                    "achievements": self.extract_achievements(text),
                    "education": self.extract_education(text),
                    "extracted_sections": sections,
                    "key_phrases": self.extract_key_phrases(text)
                }
                
                # Update analysis with advanced results
                analysis.update(advanced_analysis)
                logger.info("Advanced resume analysis completed successfully")
            except Exception as e:
                logger.error(f"Error in advanced resume analysis: {e}")
                logger.info("Falling back to basic analysis")

        return analysis
    
    def preprocess_text(self, text):
        """Advanced text preprocessing for better analysis."""
        if not self.advanced_nlp:
            return text
            
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.replace('\n', ' ')  # Replace newlines
        
        try:
            # Tokenize into sentences
            sentences = sent_tokenize(text)
            
            # Process each sentence
            processed_sentences = []
            for sentence in sentences:
                # Apply spaCy processing
                doc = self.nlp(sentence)
                # Keep only meaningful tokens
                if 'stopwords' in sys.modules:
                    tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
                else:
                    tokens = [token.text for token in doc if not token.is_punct]
                processed_sentences.append(" ".join(tokens))
                
            return " ".join(processed_sentences)
        except Exception as e:
            logger.error(f"Error in text preprocessing: {e}")
            return text
    
    def extract_resume_sections(self, text):
        """Extract structured sections from resume text."""
        if not self.advanced_nlp:
            return {"unknown": text}
            
        # Common section headers in resumes
        section_headers = {
            "education": ["education", "academic background", "academic qualifications", "academic history"],
            "experience": ["experience", "work experience", "employment history", "professional experience", "work history"],
            "skills": ["skills", "technical skills", "core competencies", "expertise", "qualifications", "proficiencies"],
            "projects": ["projects", "project experience", "academic projects", "professional projects"],
            "certifications": ["certifications", "certificates", "professional certifications", "licenses"],
            "summary": ["summary", "professional summary", "career summary", "executive summary", "profile", "about me"],
            "contact": ["contact information", "contact details", "personal details", "personal information"],
            "achievements": ["achievements", "accomplishments", "awards", "honors", "recognition"],
            "references": ["references", "professional references", "recommendations"],
            "languages": ["languages", "language proficiency", "language skills"],
            "interests": ["interests", "hobbies", "activities", "personal interests"],
            "publications": ["publications", "research papers", "articles", "books"],
            "volunteering": ["volunteering", "volunteer experience", "community service"]
        }
        
        try:
            sections = {}
            lines = text.split("\n")
            current_section = "unknown"
            current_content = []
            
            # Process line by line
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this line is a section header
                found_section = False
                for section, headers in section_headers.items():
                    if any(header.lower() in line.lower() for header in headers):
                        # Save previous section content
                        if current_content:
                            sections[current_section] = "\n".join(current_content)
                        
                        # Start new section
                        current_section = section
                        current_content = []
                        found_section = True
                        break
                
                if not found_section:
                    current_content.append(line)
            
            # Add the last section
            if current_content:
                sections[current_section] = "\n".join(current_content)
                
            return sections
        except Exception as e:
            logger.error(f"Error extracting resume sections: {e}")
            return {"unknown": text}
    
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

    def extract_skills_advanced(self, text):
        """Extract skills using advanced NLP techniques."""
        if not self.advanced_nlp:
            logger.warning("Advanced NLP features not available for skill extraction")
            return {}
            
        skills_found = defaultdict(list)
        
        # Method 1: Use FlashText for efficient keyword matching
        if self.keyword_processor:
            keywords_found = self.keyword_processor.extract_keywords(text.lower())
            for skill, category in keywords_found:
                if category != "job_title":  # Filter out job titles
                    skills_found[category].append(skill)
        
        # Method 2: Use NER for detecting potential unnamed skills
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["PRODUCT", "ORG", "GPE", "WORK_OF_ART"]:
                # Check if entity might be a skill/technology not in our list
                if not any(ent.text.lower() in skills for skills_list in skills_found.values() for skills in skills_list):
                    if any(tech_word in ent.text.lower() for tech_word in [
                        "framework", "language", "tool", "platform", "system", "library", 
                        "api", "sdk", "protocol", "standard", "methodology", "technology"
                    ]):
                        skills_found["detected_technologies"].append(ent.text)
        
        # Method 3: Use sentence embeddings for finding skill-related sentences
        if self.sentence_model:
            try:
                # Predefined skill descriptors for embedding comparison
                skill_descriptors = [
                    "I am proficient in", 
                    "My skills include",
                    "I have experience with",
                    "I am skilled at",
                    "Technologies I've worked with",
                    "Tools I use",
                    "Familiar with"
                ]
                
                # Get sentences from the text
                sentences = sent_tokenize(text)
                
                # Only process if we have enough content
                if sentences and len(sentences) > 0:
                    # Encode sentences and skill descriptors
                    sentence_embeddings = self.sentence_model.encode(sentences)
                    descriptor_embeddings = self.sentence_model.encode(skill_descriptors)
                    
                    # Find similarity between sentences and skill descriptors
                    for i, sent_emb in enumerate(sentence_embeddings):
                        for desc_emb in descriptor_embeddings:
                            # Calculate cosine similarity
                            similarity = np.dot(sent_emb, desc_emb) / (np.linalg.norm(sent_emb) * np.linalg.norm(desc_emb))
                            
                            # If similar enough, extract potential skills
                            if similarity > 0.5:  # Threshold can be adjusted
                                sent_doc = self.nlp(sentences[i])
                                for token in sent_doc:
                                    # Look for noun phrases that might be skills
                                    if token.pos_ in ["NOUN", "PROPN"] and token.text.lower() not in stopwords.words('english'):
                                        if len(token.text) > 2:  # Avoid single letters or very short terms
                                            skills_found["semantic_extraction"].append(token.text)
            except Exception as e:
                logger.error(f"Error in semantic skill extraction: {e}")
                
        return dict(skills_found)
    
    def extract_job_titles(self, text):
        """Extract job titles and roles from resume."""
        if not self.advanced_nlp:
            logger.warning("Advanced NLP features not available for job title extraction")
            return []
            
        job_titles = []
        
        # Method 1: Use FlashText for predefined job titles
        if self.keyword_processor:
            keywords_found = self.keyword_processor.extract_keywords(text.lower())
            for title, category in keywords_found:
                if category == "job_title":
                    job_titles.append(title)
        
        # Method 2: Use regex patterns for job title detection
        title_patterns = [
            r'(?:^|\s)(Senior|Junior|Lead|Chief|Principal|Associate|Assistant)?\s*(\w+\s*){1,2}(?:Developer|Engineer|Architect|Analyst|Designer|Manager|Director|Consultant|Specialist|Coordinator|Administrator)',
            r'(?:^|\s)([A-Z][a-z]+\s*)+(?:Developer|Engineer|Architect|Analyst|Designer|Manager|Director|Consultant|Specialist|Coordinator|Administrator)',
            r'(?:job title|position|role|title):\s*([A-Z][a-z]+\s*){1,4}'
        ]
        
        for pattern in title_patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                job_title = match.group(0).strip()
                # Clean up the job title
                job_title = re.sub(r'^[:\s]+', '', job_title)
                job_title = re.sub(r'job title|position|role|title:', '', job_title, flags=re.IGNORECASE).strip()
                if job_title and job_title.lower() not in [t.lower() for t in job_titles]:
                    job_titles.append(job_title)
        
        try:
            # Method 3: Use NER to detect potential job titles
            doc = self.nlp(text)
            job_related_sections = []
            for section_name, content in self.extract_resume_sections(text).items():
                if section_name in ["experience", "summary"]:
                    job_related_sections.append(content)
                    
            for section_text in job_related_sections:
                section_doc = self.nlp(section_text)
                # Look for patterns like "X at Y" where X might be a job title
                for i, token in enumerate(section_doc):
                    if token.text.lower() == "at" and i > 0:
                        # The token before "at" might be part of a job title
                        potential_title = section_doc[i-1].text
                        if len(potential_title) > 3 and 'stopwords' in sys.modules and potential_title not in stopwords.words('english'):
                            # If previous token is an adjective or noun, include it
                            if i > 1 and section_doc[i-2].pos_ in ["ADJ", "NOUN"]:
                                potential_title = section_doc[i-2].text + " " + potential_title
                            job_titles.append(potential_title)
        except Exception as e:
            logger.error(f"Error in NER-based job title extraction: {e}")
                    
        # Remove duplicates while preserving order
        unique_titles = []
        for title in job_titles:
            if title.lower() not in [t.lower() for t in unique_titles]:
                unique_titles.append(title)
                
        return unique_titles
    
    def extract_responsibilities(self, text):
        """Extract job responsibilities from resume."""
        if not self.advanced_nlp:
            return []
            
        try:
            responsibilities = []
            
            # Get experience section if available
            sections = self.extract_resume_sections(text)
            experience_text = sections.get("experience", text)
            
            # Method 1: Look for bullet points or numbered lists
            bullet_patterns = [
                r'[•●○◆■►*-]\s*(.*?)(?=(?:[•●○◆■►*-]|\n|\Z))',
                r'(?:\d+\.|\(\d+\)|\[\d+\])\s*(.*?)(?=(?:\d+\.|\(\d+\)|\[\d+\]|\n|\Z))'
            ]
            
            for pattern in bullet_patterns:
                matches = re.finditer(pattern, experience_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    bullet_text = match.group(1).strip()
                    if len(bullet_text) > 15:  # Filter out very short items
                        # Check if bullet point describes a responsibility
                        if any(action_word in bullet_text.lower() for action_word in [
                            "developed", "implemented", "managed", "designed", "created", 
                            "led", "built", "maintained", "analyzed", "coordinated",
                            "directed", "established", "supervised", "organized", "conducted",
                            "responsible for", "accountable for"
                        ]):
                            responsibilities.append(bullet_text)
            
            # Method 2: Use sentence-level analysis for action verbs
            if 'sent_tokenize' in globals():
                sentences = sent_tokenize(experience_text)
                for sentence in sentences:
                    # Skip sentences that are already captured by bullet points
                    if any(resp in sentence for resp in responsibilities):
                        continue
                        
                    doc = self.nlp(sentence)
                    # Look for sentences that start with an action verb
                    if len(doc) > 0 and doc[0].pos_ == "VERB":
                        responsibilities.append(sentence.strip())
                    # Also look for sentences with action verbs in past tense
                    elif any(token.pos_ == "VERB" and token.tag_ == "VBD" for token in doc):
                        responsibilities.append(sentence.strip())
                        
            return responsibilities[:15]  # Limit to top 15 responsibilities for conciseness
            
        except Exception as e:
            logger.error(f"Error extracting responsibilities: {e}")
            return []
    
    def extract_achievements(self, text):
        """Extract achievements and accomplishments from resume."""
        if not self.advanced_nlp:
            return []
            
        try:
            achievements = []
            
            # Get sections that might contain achievements
            sections = self.extract_resume_sections(text)
            relevant_text = sections.get("achievements", "")
            if not relevant_text:
                # If no dedicated achievements section, look in experience and summary
                relevant_text = sections.get("experience", "") + " " + sections.get("summary", "")
            
            # Method 1: Look for bullet points with achievement indicators
            bullet_patterns = [
                r'[•●○◆■►*-]\s*(.*?)(?=(?:[•●○◆■►*-]|\n|\Z))',
                r'(?:\d+\.|\(\d+\)|\[\d+\])\s*(.*?)(?=(?:\d+\.|\(\d+\)|\[\d+\]|\n|\Z))'
            ]
            
            achievement_indicators = [
                "achieved", "award", "honor", "increased", "improved", "reduced",
                "saved", "delivered", "exceeded", "grew", "led", "won", "recognized",
                "selected", "promoted", "percent", "percentage", "%", "million", "billion",
                "thousand", "award", "scholarship", "patent", "published", "certified"
            ]
            
            for pattern in bullet_patterns:
                matches = re.finditer(pattern, relevant_text, re.MULTILINE | re.DOTALL)
                for match in matches:
                    bullet_text = match.group(1).strip()
                    if any(indicator in bullet_text.lower() for indicator in achievement_indicators):
                        achievements.append(bullet_text)
            
            # Method 2: Look for sentences with metrics or quantifiable results
            if 'sent_tokenize' in globals():
                sentences = sent_tokenize(relevant_text)
                for sentence in sentences:
                    # Skip sentences that are already captured by bullet points
                    if any(ach in sentence for ach in achievements):
                        continue
                        
                    # Check for numbers, percentages, or other metrics
                    if re.search(r'\d+%|\d+\s*percent|\$\s*\d+|increased|decreased|reduced|improved by', sentence):
                        achievements.append(sentence.strip())
                        
            return achievements[:10]  # Limit to top 10 achievements
        
        except Exception as e:
            logger.error(f"Error extracting achievements: {e}")
            return []
    
    def extract_education(self, text):
        """Extract education information from resume."""
        if not self.advanced_nlp:
            return []
            
        try:
            education_info = []
            
            # Get education section if available
            sections = self.extract_resume_sections(text)
            education_text = sections.get("education", text)
            
            # Method 1: Look for degree patterns
            degree_patterns = [
                r'(Bachelor|Master|PhD|Doctorate|BS|MS|BA|MBA|BBA|B\.S\.|M\.S\.|B\.A\.|M\.A\.|B\.Tech|M\.Tech|B\.E\.|M\.E\.|Associate)[\s\.,]+(?:of|in|degree in)?\s+([A-Za-z\s]+)',
                r'([A-Za-z\s]+)\s+(?:University|College|Institute|School)',
                r'(?:University|College|Institute|School)\s+of\s+([A-Za-z\s]+)',
                r'(?:degree|diploma|certification)[\s\:]+([A-Za-z\s]+)'
            ]
            
            for pattern in degree_patterns:
                matches = re.finditer(pattern, education_text)
                for match in matches:
                    education_info.append(match.group(0).strip())
            
            # Method 2: Extract years of study/graduation
            year_pattern = r'(?:19|20)\d{2}(?:\s*[-–—]\s*(?:19|20)\d{2}|(?:present|current|now))?'
            year_matches = re.finditer(year_pattern, education_text)
            years = [match.group(0) for match in year_matches]
            
            # Method 3: Use NER to identify educational institutions
            doc = self.nlp(education_text)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    # Check if it's likely an educational institution
                    if any(edu_term in ent.text.lower() for edu_term in ["university", "college", "institute", "school"]):
                        institution = ent.text.strip()
                        if institution not in education_info:
                            education_info.append(institution)
                            
            # Combine education info with years where appropriate
            structured_education = []
            for edu in education_info:
                # Try to match with a year if available
                for year in years:
                    if abs(education_text.find(edu) - education_text.find(year)) < 100:
                        structured_education.append({"credential": edu, "year": year})
                        break
                else:
                    structured_education.append({"credential": edu})
                    
            return structured_education
            
        except Exception as e:
            logger.error(f"Error extracting education info: {e}")
            return []
    
    def extract_key_phrases(self, text):
        """Extract key phrases from the resume using TF-IDF."""
        if not self.advanced_nlp or not self.tfidf_vectorizer:
            logger.warning("TF-IDF vectorizer not available for key phrase extraction")
            return []
            
        try:
            # Create a corpus of sentences
            sentences = sent_tokenize(text)
            
            if not sentences:
                return []
                
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(sentences)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Get top phrases for each sentence
            key_phrases = []
            for i, sentence in enumerate(sentences):
                if i >= tfidf_matrix.shape[0]:
                    continue
                    
                # Get feature scores for this sentence
                feature_index = tfidf_matrix[i,:].nonzero()[1]
                tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
                
                # Sort phrases by score
                sorted_phrases = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
                
                # Get top phrases
                for idx, score in sorted_phrases[:3]:  # Get top 3 phrases per sentence
                    if score > 0.01:  # Minimum threshold for relevance
                        phrase = feature_names[idx]
                        if len(phrase) > 3 and 'stopwords' in sys.modules and phrase not in stopwords.words('english'):
                            key_phrases.append(phrase)
            
            # Remove duplicates while preserving order
            unique_phrases = []
            for phrase in key_phrases:
                if phrase not in unique_phrases:
                    unique_phrases.append(phrase)
                    
            return unique_phrases[:15]  # Return top 15 key phrases
            
        except Exception as e:
            logger.error(f"Error extracting key phrases: {e}")
            return [] 