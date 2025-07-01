# Semantic Job Matching module with transformer-based embeddings and advanced similarity metrics
import logging
import re
import json
import numpy as np
from collections import defaultdict
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional imports for advanced NLP
try:
    from sentence_transformers import SentenceTransformer, util
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize
    
    # Download required NLTK resources
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
        
    ADVANCED_NLP_AVAILABLE = True
    logger.info("Advanced NLP modules loaded successfully for semantic job matching")
except ImportError as e:
    ADVANCED_NLP_AVAILABLE = False
    logger.warning(f"Some advanced semantic matching features will not be available: {e}")


class SemanticJobMatcher:
    """Advanced job matching using transformer-based models and semantic analysis."""
    
    def __init__(self):
        """Initialize the semantic job matcher with required models."""
        self.advanced_nlp = ADVANCED_NLP_AVAILABLE
        
        if self.advanced_nlp:
            try:
                # Initialize sentence transformer model
                self.sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded successfully for job matching")
                
                # Initialize TF-IDF vectorizer as fallback
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=5000,
                    stop_words='english',
                    ngram_range=(1, 2)
                )
            except Exception as e:
                logger.error(f"Error initializing semantic models: {e}")
                self.sentence_model = None
                self.advanced_nlp = False
        else:
            logger.warning("Using basic similarity matching (advanced NLP not available)")
            self.sentence_model = None

    def calculate_semantic_similarity(self, text1, text2, precomputed_embedding1=None):
        """
        Calculate semantic similarity between two texts using transformer embeddings.
        Falls back to TF-IDF cosine similarity if transformer model is unavailable.
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            precomputed_embedding1: Optional precomputed embedding for text1
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
            
        # Clean and normalize texts
        text1 = self._clean_text(text1)
        text2 = self._clean_text(text2)
        
        try:
            # Use transformer embeddings if available
            if self.advanced_nlp and self.sentence_model:
                # Use precomputed embedding if provided
                if precomputed_embedding1 is not None:
                    embedding1 = precomputed_embedding1
                else:
                    embedding1 = self.sentence_model.encode(text1, convert_to_tensor=True)
                
                embedding2 = self.sentence_model.encode(text2, convert_to_tensor=True)
                
                # Calculate cosine similarity
                similarity = util.pytorch_cos_sim(embedding1, embedding2).item()
                return float(similarity)  # Convert tensor to float
            else:
                # Fall back to TF-IDF cosine similarity
                return self._tfidf_similarity(text1, text2)
                
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            # Ultimate fallback - basic TF-IDF
            return self._tfidf_similarity(text1, text2)
    
    def _tfidf_similarity(self, text1, text2):
        """Calculate TF-IDF cosine similarity between two texts."""
        try:
            if self.advanced_nlp and self.tfidf_vectorizer:
                # Fit vectorizer on both texts
                tfidf_matrix = self.tfidf_vectorizer.fit_transform([text1, text2])
                
                # Calculate cosine similarity
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
                return float(similarity)
            else:
                # Very basic similarity - word overlap
                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())
                
                if not words1 or not words2:
                    return 0.0
                    
                # Jaccard similarity
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                
                return intersection / union if union > 0 else 0.0
                
        except Exception as e:
            logger.error(f"Error in TF-IDF similarity calculation: {e}")
            return 0.0
            
    def _clean_text(self, text):
        """Basic text cleaning and normalization."""
        if not text:
            return ""
        
        # Convert to string and clean
        text = str(text)
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.replace('\n', ' ')     # Replace newlines
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        
        return text.strip()

    def calculate_weighted_skill_match(self, resume_skills, job_skills, skill_importance=None):
        """
        Calculate weighted skill match score with custom importance.
        
        Args:
            resume_skills (dict): Skills extracted from resume
            job_skills (dict): Skills extracted from job description
            skill_importance (dict): Custom importance weights for skills
            
        Returns:
            tuple: (score, details_dict)
        """
        if not resume_skills or not job_skills:
            return 0.0, {"matching": {}, "missing": {}, "importance": {}}
        
        # Default category weights
        category_weights = {
            "programming_languages": 0.25,
            "web_technologies": 0.20,
            "databases": 0.15,
            "cloud_platforms": 0.15,
            "ai_ml": 0.15,
            "soft_skills": 0.10,
            "other": 0.05
        }
        
        total_weight = 0.0
        matched_weight = 0.0
        matching_skills = defaultdict(list)
        missing_skills = defaultdict(list)
        skill_weights = {}
        
        # Process each skill category
        for category, skills in job_skills.items():
            if not skills:
                continue
                
            # Get category weight
            category_weight = category_weights.get(category, 0.05)
            total_weight += category_weight
            
            # Process each skill in this category
            matched_count = 0
            
            for skill in skills:
                # Get importance of this specific skill (default to 1.0)
                skill_weight = 1.0
                if skill_importance and skill in skill_importance:
                    skill_weight = skill_importance[skill]
                
                skill_weights[skill] = skill_weight
                
                # Check if resume has this skill
                if category in resume_skills and skill in resume_skills[category]:
                    matching_skills[category].append(skill)
                    matched_count += skill_weight
                else:
                    missing_skills[category].append(skill)
            
            # Calculate match for this category, weighted by skill importance
            if skills:
                total_skill_weights = sum(skill_weights.get(s, 1.0) for s in skills)
                if total_skill_weights > 0:
                    matched_weight += category_weight * (matched_count / total_skill_weights)
        
        # Calculate final score
        final_score = matched_weight / total_weight if total_weight > 0 else 0.0
        
        return final_score, {
            "matching": dict(matching_skills),
            "missing": dict(missing_skills),
            "importance": skill_weights
        }
    
    def calculate_keyword_relevance(self, resume_text, job_text):
        """
        Calculate keyword relevance score between resume and job description.
        Focuses on industry-specific and role-specific terminology.
        
        Args:
            resume_text (str): Resume text
            job_text (str): Job description text
            
        Returns:
            float: Relevance score between 0 and 1
        """
        if not resume_text or not job_text:
            return 0.0
            
        try:
            # Clean texts
            resume_text = self._clean_text(resume_text).lower()
            job_text = self._clean_text(job_text).lower()
            
            # Extract key phrases from job description
            if self.advanced_nlp and 'sent_tokenize' in globals():
                job_sentences = sent_tokenize(job_text)
                
                # Extract most important sentences from job description
                if self.tfidf_vectorizer:
                    # Use TF-IDF to find important terms
                    tfidf_matrix = self.tfidf_vectorizer.fit_transform(job_sentences)
                    feature_names = self.tfidf_vectorizer.get_feature_names_out()
                    
                    # Get top terms
                    important_terms = []
                    for i in range(len(job_sentences)):
                        if i >= tfidf_matrix.shape[0]:
                            continue
                        feature_index = tfidf_matrix[i,:].nonzero()[1]
                        tfidf_scores = zip(feature_index, [tfidf_matrix[i, x] for x in feature_index])
                        sorted_items = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
                        
                        # Get top 5 terms per sentence
                        for idx, score in sorted_items[:5]:
                            term = feature_names[idx]
                            if len(term) > 3 and term not in stopwords.words('english'):
                                important_terms.append((term, score))
                    
                    # Sort by overall importance
                    important_terms.sort(key=lambda x: x[1], reverse=True)
                    keywords = [term for term, _ in important_terms[:30]]  # Top 30 keywords
                else:
                    # Simple fallback
                    job_words = job_text.split()
                    resume_words = resume_text.split()
                    
                    # Find words that appear more in job than typical text
                    job_freq = defaultdict(int)
                    for word in job_words:
                        if len(word) > 3:
                            job_freq[word] += 1
                    
                    # Sort by frequency
                    keywords = [word for word, _ in sorted(job_freq.items(), 
                                                         key=lambda x: x[1], 
                                                         reverse=True)[:30]]
            else:
                # Simplest approach - just use common words
                job_words = set(job_text.split())
                stop_words_set = set() if 'stopwords' not in sys.modules else set(stopwords.words('english'))
                keywords = [w for w in job_words if len(w) > 3 and w not in stop_words_set][:30]
            
            # Calculate how many important keywords are in resume
            keyword_hits = sum(1 for keyword in keywords if keyword in resume_text)
            
            # Calculate score
            return keyword_hits / len(keywords) if keywords else 0.0
            
        except Exception as e:
            logger.error(f"Error in keyword relevance calculation: {e}")
            return 0.0

    def match_resume_to_jobs(self, resume_text, resume_skills, resume_experience_level, all_jobs_data):
        """
        Match a resume to multiple jobs using advanced semantic analysis.
        
        Args:
            resume_text (str): The full resume text
            resume_skills (dict): Skills extracted from resume
            resume_experience_level (str): Experience level (entry, mid, senior)
            all_jobs_data (list): List of job dictionaries
            
        Returns:
            list: Sorted list of job matches with scores and details
        """
        if not resume_text or not all_jobs_data:
            logger.warning("Empty resume text or job data provided")
            return []
        
        match_results = []
        
        try:
            # Precompute resume embeddings if possible
            resume_embedding = None
            if self.advanced_nlp and self.sentence_model:
                resume_embedding = self.sentence_model.encode(resume_text, convert_to_tensor=True)
                
            # Process each job
            for job in all_jobs_data:
                if not isinstance(job, dict):
                    continue
                    
                job_id = job.get("job_id")
                job_description = job.get("description", "")
                job_title = job.get("title", "N/A")
                job_requirements = job.get("requirements", "")
                job_skills = job.get("extracted_skills", {})  # If skills are pre-extracted
                job_importance = job.get("skills_importance", {})  # Custom importance weights
                
                if not job_id or not job_description:
                    continue
                
                # Get combined job text (title + description + requirements)
                combined_job_text = f"{job_title}. {job_description}"
                if job_requirements:
                    combined_job_text += f" {job_requirements}"
                
                # Calculate semantic similarity score
                semantic_score = self.calculate_semantic_similarity(
                    resume_text, 
                    combined_job_text,
                    resume_embedding
                )
                
                # Calculate detailed skill match score with importance weighting
                if not job_skills:
                    # If skills not provided, extract from description
                    from app.ai_analyzer import extract_skills
                    job_skills = extract_skills(combined_job_text)
                
                skill_match_score, skill_match_details = self.calculate_weighted_skill_match(
                    resume_skills, 
                    job_skills,
                    job_importance
                )
                
                # Calculate experience match
                from app.ai_analyzer import calculate_experience_match_score
                exp_match_score = calculate_experience_match_score(
                    resume_experience_level,
                    combined_job_text
                )
                
                # Calculate keyword relevance score
                keyword_score = self.calculate_keyword_relevance(resume_text, combined_job_text)
                
                # Calculate final weighted score
                final_score = (
                    semantic_score * 0.4 +       # Semantic similarity (40%)
                    skill_match_score * 0.35 +   # Skill match (35%)
                    exp_match_score * 0.15 +     # Experience match (15%) 
                    keyword_score * 0.10         # Keyword relevance (10%)
                )
                
                # Prepare match details
                match_details = {
                    "semantic_similarity": round(semantic_score, 4),
                    "skill_match": round(skill_match_score, 4),
                    "experience_match": round(exp_match_score, 4),
                    "keyword_relevance": round(keyword_score, 4),
                    "matching_skills": skill_match_details["matching"],
                    "missing_skills": skill_match_details["missing"],
                    "skill_importance": skill_match_details["importance"]
                }

                # Add to results
                match_results.append({
                    "job_id": job_id,
                    "job_title": job_title,
                    "match_score": round(final_score, 4),
                    "match_details": json.dumps(match_details)
                })
                
        except Exception as e:
            logger.error(f"Error in resume-job matching: {e}")
            
        # Sort by match score
        match_results.sort(key=lambda x: x["match_score"], reverse=True)
        return match_results


# Helper function for easier integration with existing code
def enhanced_job_matching(resume_text, resume_analysis, jobs_data):
    """
    Enhanced job matching function that can be called from routes.py
    
    Args:
        resume_text (str): Full resume text
        resume_analysis (dict): Analysis results from ResumeAnalyzer
        jobs_data (list): List of job dictionaries
        
    Returns:
        list: Sorted job matches with scores and details
    """
    try:
        # Initialize the matcher
        matcher = SemanticJobMatcher()
        
        # Extract required info from resume analysis
        resume_skills = resume_analysis.get("skills", {})
        resume_experience = resume_analysis.get("experience", {})
        experience_level = resume_experience.get("level", "entry") if isinstance(resume_experience, dict) else "entry"
        
        # Get enhanced job matches
        matches = matcher.match_resume_to_jobs(
            resume_text,
            resume_skills,
            experience_level,
            jobs_data
        )
        
        return matches
        
    except Exception as e:
        logger.error(f"Error in enhanced job matching: {e}")
        
        # Fall back to basic matching if available
        try:
            from app.ai_analyzer import analyze_resume_and_match
            
            # Format jobs_data for backward compatibility
            formatted_jobs = []
            for job in jobs_data:
                if isinstance(job, dict):
                    formatted_jobs.append({
                        "job_id": job.get("job_id"),
                        "title": job.get("title", ""),
                        "description": job.get("description", "")
                    })
            
            basic_results = analyze_resume_and_match(
                resume_id=0,  # Placeholder
                resume_text=resume_text,
                all_jobs_data=formatted_jobs
            )
            
            # Extract matches from results
            if isinstance(basic_results, dict) and "matches" in basic_results:
                return basic_results["matches"]
            return []
            
        except Exception as nested_e:
            logger.error(f"Fallback matching also failed: {nested_e}")
            return []
