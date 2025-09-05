# Enhanced Semantic Job Matching

This module provides advanced job matching capabilities for the UMAT Job Portal using transformer-based models for semantic similarity.

## Features

### Advanced Semantic Similarity
- **BERT-Based Embeddings**: Uses Sentence-BERT to generate high-quality embeddings for resumes and job descriptions
- **Semantic Understanding**: Captures meaning beyond simple keyword matching
- **Content-Based Matching**: Understands related concepts even when exact terms don't match

### Weighted Skill Matching
- **Category Weights**: Applies different weights to various skill categories
- **Importance Weighting**: Supports custom importance weights for specific skills
- **Missing Skill Detection**: Identifies skills required by jobs but missing from resume

### Robust Fallback Mechanisms
- **Multi-Level Fallbacks**: Gracefully degrades to simpler matching methods if advanced ones fail
- **TF-IDF Similarity**: Falls back to TF-IDF based matching when embeddings are unavailable
- **Basic Lexical Matching**: Ultimate fallback uses simple text overlap for maximum compatibility

## Technical Implementation

The matching process uses multiple complementary techniques:
1. **Transformer-Based Semantic Matching**: Primary method using sentence embeddings
2. **Weighted Skill Category Matching**: Compares skills with category-based weighting
3. **Experience Level Matching**: Evaluates if candidate experience matches job requirements
4. **Keyword Relevance**: Identifies industry-specific terminology and key phrases

## Usage

The system can be used through the main helper function:

```python
from app.semantic_job_matcher import enhanced_job_matching

# Get job matches
matches = enhanced_job_matching(
    resume_text=resume_text,
    resume_analysis=analysis_results,
    jobs_data=jobs_list
)
```

## Output Format

The matcher returns a list of job matches with detailed information:

```json
[
  {
    "job_id": 123,
    "job_title": "Software Engineer",
    "match_score": 0.8745,
    "match_details": "{
      \"semantic_similarity\": 0.89,
      \"skill_match\": 0.92,
      \"experience_match\": 0.8,
      \"keyword_relevance\": 0.78,
      \"matching_skills\": {\"programming_languages\": [\"python\", \"java\"]},
      \"missing_skills\": {\"databases\": [\"mongodb\"]},
      \"skill_importance\": {\"python\": 1.5, \"mongodb\": 1.2}
    }"
  },
  ...
]
``` 