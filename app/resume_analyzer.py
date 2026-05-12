
import json
import re
import logging
import os
from groq import Groq
from dotenv import load_dotenv

# Load .env file (if present) so os.getenv() works in all environments
load_dotenv()



logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Groq configuration – read from environment / .env file
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # fallback to best production model

if not GROQ_API_KEY:
    logger.warning("GROQ_API_KEY is not set. Resume analysis via Groq will fall back to keyword scan.")

_groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


ANALYSIS_PROMPT = """You are an expert resume analyst. Analyse the resume text below and return ONLY a valid JSON object – no markdown, no explanation.

The JSON must have EXACTLY this structure:
{{
  "completeness": {{
    "completeness_score": <float 0-1>,
    "present_sections": ["contact_info", "education", ...],
    "missing_sections": [
      {{"section": "projects", "importance": "medium", "tip": "Showcase practical projects."}}
    ],
    "section_scores": {{
      "contact_info": 1.0,
      "education": 1.0,
      "experience": 1.0,
      "skills": 1.0,
      "projects": 0.0,
      "achievements": 0.0,
      "summary": 1.0
    }}
  }},
  "skills": {{
    "programming_languages": ["python", "java"],
    "web_technologies": ["react", "html"],
    "databases": ["mysql"],
    "cloud_platforms": [],
    "ai_ml": [],
    "soft_skills": ["communication", "leadership"]
  }},
  "experience": {{
    "years": <int>,
    "level": "entry|mid|senior",
    "positions": ["Software Engineer at Acme Corp"],
    "domains": ["Finance", "Healthcare"]
  }},
  "improvement_suggestions": [
    {{"category": "structure", "importance": "high", "suggestion": "Add a dedicated Skills section."}}
  ],
  "bias_check": {{}},
  "key_phrases": ["machine learning", "agile development"],
  "education": [
    {{"credential": "BSc Computer Science, MIT", "year": "2021"}}
  ],
  "job_titles": ["Software Engineer", "Backend Developer"],
  "achievements": ["Increased system performance by 40%"],
  "responsibilities": ["Developed REST APIs", "Led a team of 5 engineers"]
}}

Resume text:
---
{resume_text}
---

Return ONLY the JSON object."""


# ---------------------------------------------------------------------------
# Fallback structure (used if the API call fails)
# ---------------------------------------------------------------------------
def _fallback_analysis(text: str) -> dict:
    """Return a minimal analysis dict so the app never crashes."""
    # Simple keyword scan for sections
    text_lower = text.lower()
    present = []
    missing = []
    section_map = {
        "contact_info":  ["email", "phone", "linkedin"],
        "education":     ["education", "university", "degree", "college"],
        "experience":    ["experience", "work", "employment", "internship"],
        "skills":        ["skills", "technical", "competencies"],
        "projects":      ["project", "github", "portfolio"],
        "achievements":  ["award", "achievement", "honor", "certification"],
        "summary":       ["summary", "objective", "profile"],
    }
    scores = {}
    for sec, keywords in section_map.items():
        found = any(kw in text_lower for kw in keywords)
        scores[sec] = 1.0 if found else 0.0
        if found:
            present.append(sec)
        else:
            missing.append({"section": sec, "importance": "medium",
                            "tip": f"Consider adding a {sec.replace('_', ' ')} section."})

    completeness_score = sum(scores.values()) / len(scores)

    return {
        "completeness": {
            "completeness_score": completeness_score,
            "present_sections": present,
            "missing_sections": missing,
            "section_scores": scores,
        },
        "skills": {},
        "experience": {"years": 0, "level": "entry", "positions": [], "domains": []},
        "improvement_suggestions": [],
        "bias_check": {},
        "key_phrases": [],
        "education": [],
        "job_titles": [],
        "achievements": [],
        "responsibilities": [],
    }


# ---------------------------------------------------------------------------
# Main class (keeps the same public interface as the old ResumeAnalyzer)
# ---------------------------------------------------------------------------
class ResumeAnalyzer:
    """
    Drop-in replacement for the original heavy NLP ResumeAnalyzer.
    Uses Groq's LLM API for fast, accurate resume analysis with no local
    model downloads.
    """

    def __init__(self):
        logger.info("ResumeAnalyzer (Groq-powered) initialised – no model download needed.")

    # ------------------------------------------------------------------
    # Public API – called by routes.py
    # ------------------------------------------------------------------
    def analyze_resume(self, text: str) -> dict:
        """
        Perform comprehensive resume analysis using Groq LLM.

        Returns a dict compatible with the original ResumeAnalyzer output
        so no template or route changes are required.
        """
        if not text or not text.strip():
            logger.error("Empty resume text provided.")
            return _fallback_analysis("")

        # If no API key is configured, use the keyword fallback immediately
        if not _groq_client:
            logger.warning("Groq client not available – using keyword fallback analysis.")
            return _fallback_analysis(text)

        # Truncate very long resumes to stay within context limits (~6 000 chars)
        resume_excerpt = text[:6000]

        prompt = ANALYSIS_PROMPT.format(resume_text=resume_excerpt)

        try:
            logger.info("Sending resume to Groq for analysis …")
            response = _groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,       # deterministic output
                max_tokens=2048,
            )

            raw = response.choices[0].message.content.strip()
            logger.info("Groq analysis received successfully.")

            # Strip markdown code fences if the model wraps the JSON
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            analysis = json.loads(raw)
            logger.info("Resume analysis parsed successfully.")
            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq JSON response: {e}\nRaw response: {raw[:500]}")
            return _fallback_analysis(text)

        except Exception as e:
            logger.error(f"Groq API error during resume analysis: {e}", exc_info=True)
            return _fallback_analysis(text)

    # ------------------------------------------------------------------
    # Legacy helper methods (kept so any direct call from old code still
    # works without errors)
    # ------------------------------------------------------------------
    def analyze_completeness(self, text: str) -> dict:
        analysis = self.analyze_resume(text)
        return analysis.get("completeness", {})

    def extract_skills(self, text: str) -> dict:
        analysis = self.analyze_resume(text)
        return analysis.get("skills", {})

    def extract_experience(self, text: str) -> dict:
        analysis = self.analyze_resume(text)
        return analysis.get("experience", {})

    def generate_suggestions(self, text: str) -> list:
        analysis = self.analyze_resume(text)
        return analysis.get("improvement_suggestions", [])

    def detect_bias(self, text: str) -> dict:
        analysis = self.analyze_resume(text)
        return analysis.get("bias_check", {})