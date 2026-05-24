import json
import logging
import os
from typing import Any, Callable

from dotenv import load_dotenv

from app import db
from app.ai_analyzer import (
    analyze_resume_completeness,
    extract_experience_level,
    extract_skills,
)
from app.models import (
    Application,
    AssistantInteraction,
    Event,
    Interview,
    Job,
    JobMatch,
    Resume,
    User,
)
from app.resume_analyzer import ResumeAnalyzer

try:
    from groq import Groq
except ImportError:  # pragma: no cover - fallback path is intentional
    Groq = None


load_dotenv()
logger = logging.getLogger(__name__)


def _to_text(value: Any, limit: int | None = None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if limit and len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def _parse_match_details(match_details: str | None) -> dict[str, Any]:
    if not match_details:
        return {}
    try:
        return json.loads(match_details)
    except (TypeError, ValueError):
        logger.warning("Failed to parse job match details")
        return {}


def _flatten_skill_map(skill_map: dict[str, list[str]] | None, limit: int = 12) -> list[str]:
    if not skill_map:
        return []

    ordered: list[str] = []
    seen: set[str] = set()
    for values in skill_map.values():
        for skill in values:
            skill_text = _to_text(skill)
            if not skill_text:
                continue
            lowered = skill_text.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            ordered.append(skill_text)
            if len(ordered) >= limit:
                return ordered
    return ordered


def _get_application_match(application: Application | None) -> JobMatch | None:
    if not application or not application.resume:
        return None
    return next(
        (match for match in application.resume.matches if match.job_id == application.job_id),
        None,
    )


def _job_summary(job: Job) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "title": job.title,
        "department": job.department,
        "location": job.location,
        "status": job.status,
        "closing_date": job.closing_date.isoformat() if job.closing_date else None,
        "description": _to_text(job.description, 2200),
        "required_skills": _to_text(job.required_skills, 1200),
    }


def _interview_summary(interview: Interview | None) -> dict[str, Any] | None:
    if not interview:
        return None
    return {
        "scheduled_date": interview.scheduled_date.isoformat() if interview.scheduled_date else None,
        "interview_type": interview.interview_type,
        "location_or_link": interview.location_or_link,
        "notes": _to_text(interview.notes, 1000),
        "interview_level": str(interview.interview_level.value if interview.interview_level else ""),
        "level_status": str(interview.level_status.value if interview.level_status else ""),
        "interviewer": (
            f"{interview.interviewer.first_name} {interview.interviewer.last_name}".strip()
            if interview.interviewer
            else None
        ),
    }


class RecruitmentAssistantService:
    def __init__(self) -> None:
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.model = groq_model or "llama-3.3-70b-versatile"
        self.client = Groq(api_key=groq_api_key) if Groq and groq_api_key else None
        self.resume_analyzer = ResumeAnalyzer()

    def _complete(
        self,
        *,
        system_prompt: str,
        question: str,
        context: dict[str, Any],
        fallback_builder: Callable[[str, dict[str, Any]], str],
        max_tokens: int = 900,
    ) -> dict[str, str]:
        cleaned_question = _to_text(question) or "Give the most useful guidance from the provided context."
        serialized_context = json.dumps(context, default=str, ensure_ascii=True)

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt.strip()},
                        {
                            "role": "user",
                            "content": (
                                f"Question:\n{cleaned_question}\n\n"
                                f"Context JSON:\n{serialized_context}\n\n"
                                "Answer directly for the user. Use only the context provided."
                            ),
                        },
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
                content = _to_text(response.choices[0].message.content)
                if content:
                    return {"response": content, "source": "groq"}
            except Exception as exc:  # pragma: no cover - network/API path
                logger.error("Assistant completion failed: %s", exc, exc_info=True)

        return {"response": fallback_builder(cleaned_question, context), "source": "fallback"}

    def _build_resume_analysis(self, resume: Resume) -> dict[str, Any]:
        parsed_text = resume.parsed_text or ""
        analysis = self.resume_analyzer.analyze_resume(parsed_text)
        if not analysis:
            analysis = {
                "completeness": analyze_resume_completeness(parsed_text),
                "skills": extract_skills(parsed_text),
                "experience": extract_experience_level(parsed_text),
            }
        return analysis

    def _build_match_context(self, resume: Resume) -> list[dict[str, Any]]:
        matches = (
            JobMatch.query.join(Job)
            .filter(JobMatch.resume_id == resume.resume_id)
            .order_by(JobMatch.match_score.desc())
            .all()
        )
        entries: list[dict[str, Any]] = []
        for match in matches[:8]:
            details = _parse_match_details(match.match_details)
            entries.append(
                {
                    "job_id": match.job_id,
                    "title": match.job.title if match.job else "Unknown role",
                    "department": match.job.department if match.job else None,
                    "match_score_percent": round(match.match_score * 100, 1),
                    "matching_skills": _flatten_skill_map(details.get("matching_skills"), 10),
                    "missing_skills": _flatten_skill_map(details.get("missing_skills"), 10),
                }
            )
        return entries

    def _build_candidate_resume_context(self, resume: Resume, job_id: int | None = None) -> dict[str, Any]:
        analysis = self._build_resume_analysis(resume)
        matches = self._build_match_context(resume)
        focused_match = next((match for match in matches if match["job_id"] == job_id), None) if job_id else None
        focused_job = Job.query.get(job_id) if job_id else None

        return {
            "candidate": {
                "name": f"{resume.candidate.user.first_name} {resume.candidate.user.last_name}".strip()
                if resume.candidate and resume.candidate.user
                else None,
                "profile_summary": _to_text(getattr(resume.candidate, "profile_summary", ""), 800),
                "linkedin_url": getattr(resume.candidate, "linkedin_url", None),
                "portfolio_url": getattr(resume.candidate, "portfolio_url", None),
            },
            "resume": {
                "resume_id": resume.resume_id,
                "filename": resume.original_filename,
                "parsed_text_excerpt": _to_text(resume.parsed_text, 5000),
                "upload_date": resume.upload_date.isoformat() if resume.upload_date else None,
            },
            "analysis": {
                "completeness": analysis.get("completeness", {}),
                "skills": analysis.get("skills", {}),
                "experience": analysis.get("experience", {}),
                "improvement_suggestions": analysis.get("improvement_suggestions", []),
            },
            "top_matches": matches[:5],
            "focused_job": _job_summary(focused_job) if focused_job else None,
            "focused_match": focused_match,
        }

    def candidate_resume_response(self, resume: Resume, question: str, job_id: int | None = None) -> dict[str, str]:
        context = self._build_candidate_resume_context(resume, job_id)
        system_prompt = """
You are the UMaT Candidate Resume Coach.
You help candidates understand their resume analysis, job fit, missing sections, and concrete next steps.
Rules:
- Use only the supplied context.
- Be specific, encouraging, and honest.
- If a job is in focus, explain the fit in terms of skills, experience, and completeness gaps.
- Never invent experience, scores, deadlines, or hiring promises.
- Avoid inferences about protected characteristics.
- Keep the response concise and practical.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            completeness = data["analysis"].get("completeness", {})
            suggestions = data["analysis"].get("improvement_suggestions", [])
            top_match = data["focused_match"] or (data["top_matches"][0] if data["top_matches"] else None)
            skill_map = data["analysis"].get("skills", {})
            skills = ", ".join(_flatten_skill_map(skill_map, 8)) or "No clear skills were extracted yet"
            missing_sections = completeness.get("missing_sections", [])
            if missing_sections and isinstance(missing_sections[0], dict):
                section_text = ", ".join(item.get("section", "").replace("_", " ") for item in missing_sections[:4])
            else:
                section_text = ", ".join(str(item).replace("_", " ") for item in missing_sections[:4])
            lines = [
                f"Your resume currently shows these strongest skill signals: {skills}.",
                (
                    f"Resume completeness is about {round(completeness.get('completeness_score', 0) * 100)}%."
                    if completeness
                    else "A full completeness score is not available yet."
                ),
            ]
            if top_match:
                lines.append(
                    f"Your strongest visible job fit is {top_match['title']} at {top_match['match_score_percent']}% match."
                )
                if top_match.get("missing_skills"):
                    lines.append(
                        "The biggest fit gaps for that role are: "
                        + ", ".join(top_match["missing_skills"][:5])
                        + "."
                    )
            if section_text:
                lines.append(f"The main sections to strengthen are: {section_text}.")
            if suggestions:
                suggestion = suggestions[0]
                if isinstance(suggestion, dict):
                    lines.append(f"One strong next step: {suggestion.get('suggestion', 'Tighten the structure and evidence in the resume.')}")
            lines.append("Ask a more specific follow-up like 'why is this job a weak match?' or 'draft me bullet points for a better summary' for a sharper answer.")
            return "\n\n".join(lines)

        return self._complete(
            system_prompt=system_prompt,
            question=question,
            context=context,
            fallback_builder=fallback,
            max_tokens=900,
        )

    def candidate_cover_letter_response(self, resume: Resume, job: Job, question: str) -> dict[str, str]:
        analysis = self._build_resume_analysis(resume)
        context = {
            "candidate_name": f"{resume.candidate.user.first_name} {resume.candidate.user.last_name}".strip()
            if resume.candidate and resume.candidate.user
            else "Candidate",
            "resume_skills": _flatten_skill_map(analysis.get("skills"), 10),
            "experience": analysis.get("experience", {}),
            "resume_excerpt": _to_text(resume.parsed_text, 3200),
            "job": _job_summary(job),
        }
        system_prompt = """
You are the UMaT Candidate Cover Letter Coach.
Draft a polished, role-specific cover letter grounded only in the candidate resume context and job details provided.
Rules:
- Keep it professional and ready to paste into the portal.
- Reflect the candidate's actual skills and experience from context only.
- Do not invent degrees, companies, or accomplishments.
- After the letter, include 2 or 3 short tailoring notes.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            skills = ", ".join(data.get("resume_skills")[:5]) or "relevant academic and professional skills"
            experience = data.get("experience", {})
            years = experience.get("years") or experience.get("total_years") or "my"
            title = data["job"]["title"]
            department = data["job"]["department"] or "the department"
            return (
                f"Dear Hiring Committee,\n\n"
                f"I am writing to express my interest in the {title} role with {department}. "
                f"My background reflects {years} years of experience and strengths in {skills}, which align well with the needs described for this position.\n\n"
                f"Through my resume, I bring practical evidence of technical and professional capability, along with a strong interest in contributing meaningfully to the team's goals. "
                f"I am especially motivated by the opportunity to support the work described in this role and to apply my experience in a setting that values quality, collaboration, and continuous improvement.\n\n"
                f"Thank you for considering my application. I would welcome the opportunity to discuss how my background can support the objectives of this role.\n\n"
                f"Sincerely,\n{data['candidate_name']}\n\n"
                f"Tailoring notes:\n"
                f"- Replace any broad language with one or two achievements from your resume.\n"
                f"- Mirror the job's strongest required skills in your opening paragraph.\n"
                f"- Add one sentence on why this role at UMaT is a fit for you."
            )

        return self._complete(
            system_prompt=system_prompt,
            question=question or "Draft a tailored cover letter for this role.",
            context=context,
            fallback_builder=fallback,
            max_tokens=1100,
        )

    def candidate_interview_prep_response(self, application: Application, question: str) -> dict[str, str]:
        resume = application.resume
        analysis = self._build_resume_analysis(resume) if resume else {}
        match = _get_application_match(application)
        match_details = _parse_match_details(match.match_details) if match else {}
        context = {
            "application": {
                "status": application.status.value if application.status else None,
                "feedback": _to_text(application.feedback, 1200),
                "cover_letter": _to_text(application.cover_letter, 1500),
            },
            "job": _job_summary(application.job),
            "interview": _interview_summary(application.interview),
            "resume_skills": _flatten_skill_map(analysis.get("skills"), 12),
            "experience": analysis.get("experience", {}),
            "match_score_percent": round(match.match_score * 100, 1) if match else None,
            "missing_skills": _flatten_skill_map(match_details.get("missing_skills"), 10),
        }
        system_prompt = """
You are the UMaT Candidate Interview Coach.
Help the candidate prepare for the next interview stage using only the supplied application, resume, and job context.
Rules:
- Focus on likely interviewer questions, talking points, and preparation advice.
- If there is a skills gap, explain how to address it honestly.
- Do not invent hidden company preferences or interview outcomes.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            skills = ", ".join(data.get("resume_skills")[:6]) or "your strongest demonstrated skills"
            missing = data.get("missing_skills") or []
            lines = [
                f"Expect questions that test how you have applied {skills}.",
                "Prepare a short story for your background, a project example, and one example of problem solving under pressure.",
                f"For this role, be ready to explain why your experience fits {data['job']['title']} and what value you would bring to {data['job']['department']}.",
            ]
            if missing:
                lines.append(
                    "You may also be asked about gaps around "
                    + ", ".join(missing[:4])
                    + ". Prepare an honest answer that shows how you are learning or have adjacent experience."
                )
            if data.get("interview"):
                lines.append(
                    f"Interview format note: this is scheduled as a {data['interview']['interview_type']} interview."
                )
            return "\n\n".join(lines)

        return self._complete(
            system_prompt=system_prompt,
            question=question or "Help me prepare for this interview.",
            context=context,
            fallback_builder=fallback,
            max_tokens=950,
        )

    def _application_snapshot(self, application: Application) -> dict[str, Any]:
        resume = application.resume
        parsed_text = resume.parsed_text if resume else ""
        skills = extract_skills(parsed_text) if parsed_text else {}
        completeness = analyze_resume_completeness(parsed_text) if parsed_text else {}
        experience = extract_experience_level(parsed_text) if parsed_text else {}
        match = _get_application_match(application)
        match_details = _parse_match_details(match.match_details) if match else {}

        return {
            "application_id": application.application_id,
            "candidate_name": f"{application.applicant.first_name} {application.applicant.last_name}".strip(),
            "candidate_email": application.applicant.email,
            "status": application.status.value if application.status else None,
            "applied_on": application.application_date.isoformat() if application.application_date else None,
            "resume_filename": resume.original_filename if resume else None,
            "resume_excerpt": _to_text(parsed_text, 2200),
            "top_skills": _flatten_skill_map(skills, 10),
            "experience": experience,
            "completeness_score": round(completeness.get("completeness_score", 0) * 100, 1) if completeness else None,
            "cover_letter_excerpt": _to_text(application.cover_letter, 1000),
            "match_score_percent": round(match.match_score * 100, 1) if match else None,
            "matching_skills": _flatten_skill_map(match_details.get("matching_skills"), 10),
            "missing_skills": _flatten_skill_map(match_details.get("missing_skills"), 10),
            "interview": _interview_summary(application.interview),
        }

    def admin_job_response(self, *, mode: str, job: Job, question: str) -> dict[str, str]:
        applications = (
            Application.query.filter_by(job_id=job.job_id)
            .order_by(Application.application_date.desc())
            .all()
        )
        snapshots = [self._application_snapshot(app) for app in applications]
        snapshots.sort(
            key=lambda item: (
                item.get("match_score_percent") is None,
                -(item.get("match_score_percent") or 0),
            )
        )
        context = {
            "job": _job_summary(job),
            "application_count": len(applications),
            "top_candidates": snapshots[:5],
            "status_breakdown": {
                status: sum(1 for item in snapshots if item.get("status") == status)
                for status in sorted({item.get("status") for item in snapshots if item.get("status")})
            },
        }
        system_prompt = """
You are the UMaT Admin Recruitment Copilot.
You support administrators with hiring summaries and comparisons grounded only in the supplied portal data.
Rules:
- Evaluate candidates only on role-relevant evidence in their materials.
- Do not infer or mention protected characteristics.
- Recommendations are advisory and should not be framed as final hiring decisions.
- Be concrete about strengths, risks, and next-step questions.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            top = data.get("top_candidates", [])
            if not top:
                return "No applications are available for this role yet, so there is nothing to summarize or compare."

            if mode == "candidate_compare":
                lines = [f"Top candidates for {data['job']['title']}:"]
                for index, candidate in enumerate(top[:3], start=1):
                    lines.append(
                        f"{index}. {candidate['candidate_name']} - "
                        f"{candidate.get('match_score_percent') or 'No'}% match, "
                        f"skills: {', '.join(candidate.get('top_skills')[:5]) or 'not clearly extracted'}, "
                        f"gaps: {', '.join(candidate.get('missing_skills')[:4]) or 'none highlighted'}."
                    )
                lines.append("Use interviews to test the top skill evidence, depth of experience, and any visible gaps.")
                return "\n".join(lines)

            top_candidate = top[0]
            return (
                f"There are {data['application_count']} applications for {data['job']['title']}.\n\n"
                f"The strongest current paper fit appears to be {top_candidate['candidate_name']} "
                f"with a {top_candidate.get('match_score_percent') or 0}% match score.\n\n"
                f"Across the pool, the main strengths showing up are: "
                f"{', '.join(top_candidate.get('top_skills')[:6]) or 'role-relevant skills not clearly extracted yet'}.\n\n"
                f"Main follow-up areas to probe in screening or interview: "
                f"{', '.join(top_candidate.get('missing_skills')[:4]) or 'depth of experience, role ownership, and concrete outcomes'}."
            )

        prompt = question or (
            "Compare the strongest candidates for this role."
            if mode == "candidate_compare"
            else "Summarize the current applicants for this role."
        )
        return self._complete(
            system_prompt=system_prompt,
            question=prompt,
            context=context,
            fallback_builder=fallback,
            max_tokens=1100,
        )

    def admin_application_response(
        self,
        *,
        mode: str,
        application: Application,
        question: str,
        target_status: str | None = None,
    ) -> dict[str, str]:
        snapshot = self._application_snapshot(application)
        context = {
            "application": snapshot,
            "job": _job_summary(application.job),
            "target_status": target_status,
        }
        system_prompt = """
You are the UMaT Admin Recruitment Copilot.
You help administrators prepare candidate summaries, shortlist notes, candidate-facing feedback, and interview materials.
Rules:
- Use only the supplied context.
- Stay fair, factual, and professional.
- Do not mention protected characteristics or infer them.
- When drafting candidate-facing feedback, keep the tone respectful and actionable.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            candidate = data["application"]["candidate_name"]
            job_title = data["job"]["title"]
            top_skills = ", ".join(data["application"].get("top_skills", [])[:6]) or "their stated skills"
            missing = ", ".join(data["application"].get("missing_skills", [])[:5]) or "no major gaps were captured automatically"
            if mode == "draft_feedback":
                status_label = (data.get("target_status") or "under_review").replace("_", " ").title()
                return (
                    f"Hello {candidate},\n\n"
                    f"Thank you for your application for the {job_title} role. "
                    f"We reviewed your materials and noted strengths around {top_skills}. "
                    f"At the same time, we would benefit from stronger evidence around {missing}.\n\n"
                    f"Your application is currently being considered under the status: {status_label}. "
                    f"We appreciate the effort you put into your submission and encourage you to keep highlighting specific outcomes, responsibilities, and role-relevant examples in future updates.\n\n"
                    f"Regards,\nUMaT Recruitment Team"
                )
            if mode == "shortlist_reasons":
                return (
                    f"Reasons to shortlist {candidate}:\n"
                    f"- Visible strengths in {top_skills}\n"
                    f"- Existing application fit for {job_title}\n"
                    f"- Candidate materials provide enough signal for deeper interview validation\n\n"
                    f"Concerns to validate:\n"
                    f"- {missing}\n"
                    f"- Depth of ownership, outcomes, and role complexity"
                )
            if mode == "interview_notes":
                return (
                    f"Interview notes template for {candidate} - {job_title}\n\n"
                    f"1. Opening summary\n"
                    f"- Candidate background in 2 sentences\n\n"
                    f"2. Evidence to validate\n"
                    f"- {top_skills}\n\n"
                    f"3. Gaps or risks\n"
                    f"- {missing}\n\n"
                    f"4. Scorecard\n"
                    f"- Technical fit\n"
                    f"- Communication\n"
                    f"- Role motivation\n"
                    f"- Depth of examples\n"
                    f"- Recommendation"
                )
            return (
                f"Interview questions for {candidate} should test how they have applied {top_skills} in real work, "
                f"what outcomes they owned, and how they would address gaps around {missing}."
            )

        default_prompt_map = {
            "draft_feedback": "Draft respectful candidate-facing feedback for this application.",
            "shortlist_reasons": "Give shortlist reasons and concerns for this candidate.",
            "interview_questions": "Generate focused interview questions for this candidate and role.",
            "interview_notes": "Draft structured interviewer prep notes for this candidate.",
        }
        return self._complete(
            system_prompt=system_prompt,
            question=question or default_prompt_map.get(mode, "Help with this application."),
            context=context,
            fallback_builder=fallback,
            max_tokens=1100,
        )

    def portal_support_response(
        self,
        *,
        question: str,
        page_context: str | None = None,
        job_id: int | None = None,
        event_id: int | None = None,
    ) -> dict[str, str]:
        open_jobs = Job.query.filter_by(status="open").order_by(Job.posted_date.desc()).limit(6).all()
        upcoming_events = Event.query.filter_by(status="upcoming").order_by(Event.event_date.asc()).limit(6).all()
        focused_job = Job.query.get(job_id) if job_id else None
        focused_event = Event.query.get(event_id) if event_id else None
        faq = {
            "application_steps": [
                "Create an account or sign in.",
                "Upload a resume from the candidate profile area.",
                "Open a job posting and start the application.",
                "Submit a cover letter either by typing it in or uploading a file.",
            ],
            "required_documents": [
                "A resume is required before applying for a role.",
                "A cover letter is also required, either typed into the form or uploaded as a file.",
            ],
            "interview_process": [
                "Applications move through Submitted, Under Review, Interview Scheduled, Accepted, or Rejected.",
                "Interview details are shown inside the candidate application and interview views.",
                "Candidates are notified when an interview is scheduled.",
            ],
        }
        context = {
            "page_context": page_context,
            "focused_job": _job_summary(focused_job) if focused_job else None,
            "focused_event": {
                "title": focused_event.title,
                "date": focused_event.event_date.isoformat() if focused_event else None,
                "location": focused_event.location if focused_event else None,
                "type": focused_event.event_type if focused_event else None,
                "status": focused_event.status if focused_event else None,
                "description": _to_text(focused_event.description, 1800) if focused_event else None,
            }
            if focused_event
            else None,
            "faq": faq,
            "open_jobs": [
                {
                    "job_id": job.job_id,
                    "title": job.title,
                    "department": job.department,
                    "closing_date": job.closing_date.isoformat() if job.closing_date else None,
                }
                for job in open_jobs
            ],
            "upcoming_events": [
                {
                    "event_id": event.event_id,
                    "title": event.title,
                    "date": event.event_date.isoformat() if event.event_date else None,
                    "location": event.location,
                    "type": event.event_type,
                }
                for event in upcoming_events
            ],
        }
        system_prompt = """
You are the UMaT Portal Support Assistant.
You answer questions about using the recruitment portal, required documents, jobs, events, and the interview flow.
Rules:
- Use only the supplied portal context.
- If the answer is not shown in the portal context, say that clearly.
- Give short, direct steps when explaining how to use the portal.
- Do not invent policies, deadlines, or contact channels.
"""

        def fallback(user_question: str, data: dict[str, Any]) -> str:
            question_lower = user_question.lower()
            if "document" in question_lower or "resume" in question_lower or "cover letter" in question_lower:
                return "\n".join(data["faq"]["required_documents"])
            if "interview" in question_lower:
                return "\n".join(data["faq"]["interview_process"])
            if "apply" in question_lower or "application" in question_lower:
                return "\n".join(data["faq"]["application_steps"])
            if "event" in question_lower:
                upcoming = data.get("upcoming_events", [])
                if not upcoming:
                    return "There are no upcoming events listed right now."
                event = upcoming[0]
                return (
                    f"The next visible upcoming event is {event['title']} on {event['date']}."
                    + (f" Location: {event['location']}." if event.get("location") else "")
                )
            if data.get("focused_job"):
                return (
                    f"You are looking at {data['focused_job']['title']}. "
                    "To apply, sign in, upload a resume from your profile if needed, and submit the application form with a cover letter."
                )
            return (
                "You can use this portal to browse jobs, upload resumes, apply with a cover letter, track interview stages, "
                "and view upcoming UMaT events."
            )

        return self._complete(
            system_prompt=system_prompt,
            question=question,
            context=context,
            fallback_builder=fallback,
            max_tokens=850,
        )

    def log_interaction(
        self,
        *,
        user: User | None,
        scope: str,
        mode: str,
        prompt: str,
        response: str,
        resume_id: int | None = None,
        job_id: int | None = None,
        application_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        interaction = AssistantInteraction(
            user_id=user.id if user else None,
            scope=scope,
            mode=mode,
            prompt=_to_text(prompt, 12000),
            response=_to_text(response, 20000),
            resume_id=resume_id,
            job_id=job_id,
            application_id=application_id,
            metadata_json=json.dumps(metadata or {}, default=str),
        )
        db.session.add(interaction)
        db.session.commit()

