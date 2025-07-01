# Enhanced Resume Analyzer

This module provides advanced Natural Language Processing (NLP) capabilities for resume analysis in the UMAT Job Portal.

## Features

### Advanced NLP Analysis

- **Section Recognition**: Intelligently identifies resume sections (education, experience, skills, etc.)
- **Skill Extraction**: Uses multiple methods to extract and categorize skills:
  - Taxonomy-based matching
  - Named Entity Recognition (NER)
  - Semantic similarity using transformer models
- **Job Title Recognition**: Extracts current and previous job titles/roles
- **Responsibility Analysis**: Identifies job responsibilities from bullet points and sentences
- **Achievement Extraction**: Recognizes accomplishments and quantifiable achievements
- **Education Details**: Extracts education credentials, institutions, and years
- **Key Phrase Analysis**: Identifies important phrases using TF-IDF analysis

### Implementation Details

The resume analyzer uses multiple complementary techniques:

1. **Keyword Matching**: Fast, dictionary-based keyword extraction using FlashText
2. **Regular Expression Patterns**: For structured information like degrees, dates, and bullet points
3. **Named Entity Recognition**: Using spaCy's NLP models to identify organizations, job titles, etc.
4. **Transformer-Based Models**: Semantic similarity analysis using sentence embeddings
5. **TF-IDF Analysis**: Statistical method to identify important terms/phrases

## Installation

Required libraries:
- spacy
- nltk
- sentence-transformers
- flashtext
- scikit-learn
- pandas
- numpy

## Usage Example

```python
from app.resume_analyzer import ResumeAnalyzer

# Initialize the analyzer
analyzer = ResumeAnalyzer()

# Analyze a resume text
resume_text = "Your resume text here..."
analysis = analyzer.analyze_resume(resume_text)

# Access different analysis components
skills = analysis["skills"]
job_titles = analysis["job_titles"]
responsibilities = analysis["responsibilities"]
achievements = analysis["achievements"]
education = analysis["education"]
```

## Output Format

The analyzer returns a structured dictionary with the following components:

```
{
  "completeness": {
    "present_sections": [...],
    "missing_sections": [...],
    "completeness_score": 0.85
  },
  "skills": {...},
  "skills_advanced": {...},
  "job_titles": [...],
  "responsibilities": [...],
  "achievements": [...],
  "education": [...],
  "bias_check": {...},
  "experience": {...},
  "improvement_suggestions": [...],
  "extracted_sections": {...},
  "key_phrases": [...]
}
``` 