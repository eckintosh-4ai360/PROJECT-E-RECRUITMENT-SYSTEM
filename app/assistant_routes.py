import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.models import Application, Job, Resume, UserRole
from app.assistant_service import RecruitmentAssistantService


logger = logging.getLogger(__name__)
assistant_bp = Blueprint("assistant", __name__, url_prefix="/assistant")
assistant_service = RecruitmentAssistantService()


def _payload() -> dict:
    return request.get_json(silent=True) or request.form.to_dict()


def _as_int(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


@assistant_bp.route("/candidate", methods=["POST"])
@login_required
def candidate_assistant():
    if getattr(current_user.role, "value", current_user.role) != UserRole.candidate.value:
        return _json_error("Candidate assistant access is limited to candidate accounts.", 403)

    data = _payload()
    mode = (data.get("mode") or "").strip()
    question = (data.get("question") or "").strip()

    try:
        if mode == "resume_coach":
            resume_id = _as_int(data.get("resume_id"))
            if not resume_id:
                return _json_error("Select a resume before using the resume coach.")

            resume = Resume.query.get_or_404(resume_id)
            if resume.candidate_id != current_user.id:
                return _json_error("You can only use the coach with your own resumes.", 403)

            job_id = _as_int(data.get("job_id"))
            result = assistant_service.candidate_resume_response(resume, question, job_id=job_id)
            assistant_service.log_interaction(
                user=current_user,
                scope="candidate",
                mode=mode,
                prompt=question or "General resume coaching request",
                response=result["response"],
                resume_id=resume.resume_id,
                job_id=job_id,
                metadata={"source": result["source"]},
            )
            return jsonify({"ok": True, **result})

        if mode == "cover_letter":
            resume_id = _as_int(data.get("resume_id"))
            job_id = _as_int(data.get("job_id"))
            if not resume_id or not job_id:
                return _json_error("Choose both a resume and a job before generating a cover letter.")

            resume = Resume.query.get_or_404(resume_id)
            if resume.candidate_id != current_user.id:
                return _json_error("You can only use your own resumes here.", 403)

            job = Job.query.get_or_404(job_id)
            result = assistant_service.candidate_cover_letter_response(resume, job, question)
            assistant_service.log_interaction(
                user=current_user,
                scope="candidate",
                mode=mode,
                prompt=question or "Draft a cover letter for this role",
                response=result["response"],
                resume_id=resume.resume_id,
                job_id=job.job_id,
                metadata={"source": result["source"]},
            )
            return jsonify({"ok": True, **result})

        if mode == "interview_prep":
            application_id = _as_int(data.get("application_id"))
            if not application_id:
                return _json_error("Choose an application before generating interview preparation.")

            application = Application.query.get_or_404(application_id)
            if application.candidate_id != current_user.id:
                return _json_error("You can only use interview prep for your own applications.", 403)

            result = assistant_service.candidate_interview_prep_response(application, question)
            assistant_service.log_interaction(
                user=current_user,
                scope="candidate",
                mode=mode,
                prompt=question or "Help me prepare for this interview",
                response=result["response"],
                resume_id=application.resume_id,
                job_id=application.job_id,
                application_id=application.application_id,
                metadata={"source": result["source"]},
            )
            return jsonify({"ok": True, **result})

        return _json_error("Unsupported candidate assistant mode.")
    except Exception as exc:
        logger.error("Candidate assistant request failed: %s", exc, exc_info=True)
        return _json_error("The candidate assistant could not finish that request right now.", 500)


@assistant_bp.route("/admin", methods=["POST"])
@login_required
def admin_assistant():
    if not current_user.is_admin():
        return _json_error("Admin assistant access is limited to administrators.", 403)

    data = _payload()
    mode = (data.get("mode") or "").strip()
    question = (data.get("question") or "").strip()

    try:
        if mode in {"job_summary", "candidate_compare"}:
            job_id = _as_int(data.get("job_id"))
            if not job_id:
                return _json_error("Choose a job before using this admin assistant action.")

            job = Job.query.get_or_404(job_id)
            result = assistant_service.admin_job_response(mode=mode, job=job, question=question)
            assistant_service.log_interaction(
                user=current_user,
                scope="admin",
                mode=mode,
                prompt=question or mode.replace("_", " "),
                response=result["response"],
                job_id=job.job_id,
                metadata={"source": result["source"]},
            )
            return jsonify({"ok": True, **result})

        if mode in {"draft_feedback", "shortlist_reasons", "interview_questions", "interview_notes"}:
            application_id = _as_int(data.get("application_id"))
            if not application_id:
                return _json_error("Choose an application before using this admin assistant action.")

            application = Application.query.get_or_404(application_id)
            target_status = (data.get("target_status") or "").strip() or None
            result = assistant_service.admin_application_response(
                mode=mode,
                application=application,
                question=question,
                target_status=target_status,
            )
            assistant_service.log_interaction(
                user=current_user,
                scope="admin",
                mode=mode,
                prompt=question or mode.replace("_", " "),
                response=result["response"],
                resume_id=application.resume_id,
                job_id=application.job_id,
                application_id=application.application_id,
                metadata={"source": result["source"], "target_status": target_status},
            )
            return jsonify({"ok": True, **result})

        return _json_error("Unsupported admin assistant mode.")
    except Exception as exc:
        logger.error("Admin assistant request failed: %s", exc, exc_info=True)
        return _json_error("The admin assistant could not finish that request right now.", 500)


@assistant_bp.route("/portal", methods=["POST"])
def portal_assistant():
    data = _payload()
    question = (data.get("question") or "").strip()
    page_context = (data.get("page_context") or "").strip() or None
    job_id = _as_int(data.get("job_id"))
    event_id = _as_int(data.get("event_id"))

    try:
        result = assistant_service.portal_support_response(
            question=question or "How do I use this portal?",
            page_context=page_context,
            job_id=job_id,
            event_id=event_id,
        )
        assistant_service.log_interaction(
            user=current_user if current_user.is_authenticated else None,
            scope="portal",
            mode="support",
            prompt=question or "How do I use this portal?",
            response=result["response"],
            job_id=job_id,
            metadata={"source": result["source"], "page_context": page_context, "event_id": event_id},
        )
        return jsonify({"ok": True, **result})
    except Exception as exc:
        logger.error("Portal assistant request failed: %s", exc, exc_info=True)
        return _json_error("The portal assistant could not finish that request right now.", 500)
