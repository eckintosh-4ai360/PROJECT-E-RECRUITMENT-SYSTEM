from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from markupsafe import Markup
from app import db, login_manager
from datetime import datetime
from app.models import User, UserRole, Candidate, Resume, Job, JobMatch, Application, Interview, ApplicationStatus, Event, InterviewLevel
from app.forms import RegistrationForm, LoginForm, ResumeUploadForm, JobForm, ApplicationForm, InterviewForm, ProfileEditForm, EventForm
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
import os
from werkzeug.utils import secure_filename
from app.utils import parse_resume, save_profile_image, send_email, show_pdf
import logging
from app.models import UserRole
from app.courses import course_recommender, ds_course, web_course, android_course, ios_course, uiux_course
import uuid
import json
from sqlalchemy import and_
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email
from app.utils import mail

logger = logging.getLogger(__name__)
bp = Blueprint("main", __name__)

@bp.route("/user/upload_resume", methods=["POST"])
@login_required
def upload_resume():
    if current_user.role != UserRole.candidate:
        flash("Only candidates can upload resumes.", "danger")
        return redirect(url_for("main.index"))

    form = ResumeUploadForm()
    if form.validate_on_submit():
        file = form.resume_file.data
        if file:
            # Generate unique filename
            base_filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{base_filename}"
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

            try:
                file.save(file_path)
                logger.info(f"File saved to: {file_path}")

                parsed_text = parse_resume(file_path)
                if parsed_text is None:
                    flash("Failed to parse the uploaded resume.", "danger")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return redirect(url_for("main.user_profile"))

                # Set other resumes to not primary if this one is
                if form.is_primary.data:
                    Resume.query.filter_by(candidate_id=current_user.id).update({"is_primary": False})

                new_resume = Resume(
                    candidate_id=current_user.id,
                    file_path=unique_filename,
                    original_filename=base_filename,
                    parsed_text=parsed_text,
                    is_primary=form.is_primary.data
                )
                db.session.add(new_resume)
                db.session.commit()
                flash("Resume uploaded and parsed successfully! Starting analysis...", "success")
                logger.info(f"Resume {new_resume.resume_id} added for user {current_user.id}")

                # Enhanced AI Analysis
                try:
                    logger.info(f"Starting enhanced analysis for resume {new_resume.resume_id}")

                    from app.ai_analyzer import analyze_resume_and_match
                    from app.resume_analyzer import ResumeAnalyzer

                    # Initialize analyzers
                    resume_analyzer = ResumeAnalyzer()
                    
                    # Get open jobs
                    jobs_to_analyze = Job.query.filter_by(status="open").all()
                    if not jobs_to_analyze:
                        logger.warning(f"No open jobs found to match against resume {new_resume.resume_id}")
                        flash("Resume uploaded, but no open jobs found for matching.", "info")
                        return redirect(url_for("main.resume_analysis", resume_id=new_resume.resume_id))
                    
                    # Prepare jobs data
                    jobs_data = [{
                        "job_id": job.job_id,
                        "description": job.description,
                        "title": job.title,
                        "requirements": getattr(job, 'requirements', '')  # Use getattr with default empty string
                    } for job in jobs_to_analyze]
                    
                    matches = []
                    semantic_matching_enabled = current_app.config.get("ENABLE_SEMANTIC_MATCHING", False)

                    if semantic_matching_enabled:
                        try:
                            from app.semantic_job_matcher import enhanced_job_matching

                            analysis = resume_analyzer.analyze_resume(parsed_text)
                            matches = enhanced_job_matching(
                                resume_text=parsed_text,
                                resume_analysis=analysis,
                                jobs_data=jobs_data
                            )
                            logger.info(f"Enhanced semantic job matching completed for resume {new_resume.resume_id}")

                        except Exception as semantic_err:
                            logger.warning(
                                "Enhanced semantic job matching failed; using basic matching: %s",
                                semantic_err,
                                exc_info=True
                            )

                    if not matches:
                        analysis_results = analyze_resume_and_match(new_resume.resume_id, parsed_text, jobs_data)

                        if not analysis_results:
                            flash("Resume uploaded, but analysis could not be completed.", "warning")
                            return redirect(url_for("main.resume_analysis", resume_id=new_resume.resume_id))

                        matches = analysis_results.get("matches", [])
                    
                    # Delete old matches
                    JobMatch.query.filter_by(resume_id=new_resume.resume_id).delete()

                    # Save new matches
                    matches_saved = 0
                    for match in matches:
                        if match["match_score"] > 0.05:  # 5% minimum threshold
                            db_match = JobMatch(
                                resume_id=new_resume.resume_id,
                                job_id=match["job_id"],
                                match_score=match["match_score"],
                                match_details=match.get("match_details")
                            )
                            db.session.add(db_match)
                            matches_saved += 1
                    
                    db.session.commit()
                    flash(f"Resume analysis complete. Found {matches_saved} potential job matches!", "success")
                    logger.info(f"Saved {matches_saved} matches for resume {new_resume.resume_id}")
                    
                    # Redirect to analysis page
                    return redirect(url_for("main.resume_analysis", resume_id=new_resume.resume_id))

                except Exception as analysis_err:
                    db.session.rollback()
                    logger.error(f"Analysis failed for resume {new_resume.resume_id}: {analysis_err}", exc_info=True)
                    flash("Resume uploaded, but an error occurred during analysis.", "danger")
                    return redirect(url_for("main.user_profile"))

            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred during upload: {e}", "danger")
                logger.error(f"Resume upload failed for user {current_user.id}: {e}", exc_info=True)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as remove_err:
                        logger.error(f"Failed to remove file after error: {remove_err}")

        return redirect(url_for("main.user_profile"))

# Decorator for admin-only routes
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("Admin access required.", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated_function

# Helper function to check allowed file extensions
def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

# --- Add routes for homepage --- 
@bp.route("/")
@bp.route("/index")
def index():
    # Show homepage with events and jobs for all users
    jobs = Job.query.filter_by(status="open").order_by(Job.posted_date.desc()).limit(5).all()
    
    # Get upcoming events (limit to 6 for the slider)
    upcoming_events = Event.query.filter_by(status="upcoming").order_by(Event.event_date.asc()).limit(6).all()
    
    return render_template("index.html", title="Home", jobs=jobs, events=upcoming_events)

# --- Add routes for USER PROFILE --- 
@bp.route("/user/profile")
@login_required
def user_profile():
    if current_user.role != UserRole.candidate:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    candidate = Candidate.query.get(current_user.id)
    if not candidate:
        flash("Candidate profile not found.", "danger")
        return redirect(url_for("main.index"))

    upload_form = ResumeUploadForm()
    resumes = Resume.query.filter_by(candidate_id=current_user.id).order_by(Resume.upload_date.desc()).all()
    
    # Fetch job matches for the candidate's resumes
    matches = JobMatch.query.join(Resume).filter(Resume.candidate_id == current_user.id).order_by(JobMatch.match_score.desc()).all()

    return render_template("user/profile.html", title="My Profile", upload_form=upload_form, resumes=resumes, matches=matches)

@bp.route("/user/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if current_user.role != UserRole.candidate:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))
    
    form = ProfileEditForm(current_user.username, current_user.email)
    
    if form.validate_on_submit():
        # Update user data
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        
        # Update phone number in candidate profile
        if current_user.candidate_profile:
            current_user.candidate_profile.phone_number = form.phone_number.data
        
        # Handle profile image if provided
        if form.profile_image.data:
            profile_image_path = save_profile_image(form.profile_image.data)
            if profile_image_path:
                current_user.profile_image = profile_image_path
        
        db.session.commit()
        flash("Your profile has been successfully updated!", "success")
        return redirect(url_for("main.user_profile"))
    
    # Pre-populate form with existing data
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        if current_user.candidate_profile:
            form.phone_number.data = current_user.candidate_profile.phone_number
    
    return render_template("user/edit_profile.html", title="Edit Profile", form=form)

@bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Enhanced admin dashboard with charts and statistics."""
    try:
        # Basic statistics
        total_users = User.query.filter_by(role=UserRole.candidate).count()
        total_jobs = Job.query.count()
        total_applications = Application.query.count()
        total_resumes = Resume.query.count()

        # Get active jobs with their applications
        active_jobs = Job.query.filter_by(status='open').order_by(Job.posted_date.desc()).all()
        active_jobs_count = len(active_jobs)

        # Get recent applications with related data
        page = request.args.get('page', 1, type=int)
        recent_applications = (
            Application.query
            .join(User, Application.candidate_id == User.id)
            .join(Job, Application.job_id == Job.job_id)
            .order_by(Application.application_date.desc())
            .paginate(
                page=page,
                per_page=10,
                error_out=False
            )
        )

        # Debug logging for profile images
        for application in recent_applications.items:
            logger.info(f"Application ID: {application.application_id}")
            logger.info(f"Applicant: {application.applicant.first_name} {application.applicant.last_name}")
            logger.info(f"Profile Image Path: {application.applicant.profile_image}")
            if application.applicant.profile_image:
                image_path = os.path.join(current_app.static_folder, 'profile_images', application.applicant.profile_image)
                logger.info(f"Full Image Path: {image_path}")
                logger.info(f"Image exists: {os.path.exists(image_path)}")

        # Log the number of applications fetched for debugging
        logger.info(f"Admin dashboard fetched {recent_applications.total} recent applications")

        # Get monthly statistics for the past 12 months
        now = datetime.utcnow()
        monthly_stats = []

        for offset in range(11, -1, -1):
            year = now.year
            month = now.month - offset

            while month <= 0:
                month += 12
                year -= 1

            month_start = datetime(year, month, 1)
            month_end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

            applications = Application.query.filter(
                Application.application_date >= month_start,
                Application.application_date < month_end
            ).count()

            resumes = Resume.query.filter(
                Resume.upload_date >= month_start,
                Resume.upload_date < month_end
            ).count()

            jobs = Job.query.filter(
                Job.posted_date >= month_start,
                Job.posted_date < month_end
            ).count()

            monthly_stats.append({
                'month': month_start.strftime('%B %Y'),
                'short_month': month_start.strftime('%b'),
                'applications': int(applications),
                'resumes': int(resumes),
                'jobs': int(jobs)
            })

        # Get job statistics by department
        dept_stats = db.session.query(
            Job.department, 
            db.func.count(Job.job_id)
        ).group_by(Job.department).all()
        
        department_stats = {
            'labels': [str(dept[0]) if dept[0] else 'Unspecified' for dept in dept_stats],
            'values': [int(dept[1]) for dept in dept_stats]
        }

        # Get application status statistics
        status_stats = db.session.query(
            Application.status, 
            db.func.count(Application.application_id)
        ).group_by(Application.status).all()
        
        application_stats = {
            'labels': [str(status[0]) if status[0] else 'Unknown' for status in status_stats],
            'values': [int(status[1]) for status in status_stats]
        }

        status_totals = {
            (status.value if hasattr(status, "value") else str(status)): int(count)
            for status, count in status_stats
        }

        submitted_count = status_totals.get(ApplicationStatus.submitted.value, 0)
        review_count = status_totals.get(ApplicationStatus.under_review.value, 0)
        interview_count = status_totals.get(ApplicationStatus.interview_scheduled.value, 0)
        accepted_count = status_totals.get(ApplicationStatus.accepted.value, 0)
        rejected_count = status_totals.get(ApplicationStatus.rejected.value, 0)

        latest_month = monthly_stats[-1] if monthly_stats else None
        peak_month = max(monthly_stats, key=lambda item: item['applications']) if monthly_stats else None
        acceptance_rate = round((accepted_count / total_applications) * 100, 1) if total_applications else 0
        resume_coverage_rate = round((total_resumes / total_users) * 100, 1) if total_users else 0
        department_count = len(department_stats['labels'])

        return render_template(
            "admin/dashboard.html",
            title="Admin Dashboard",
            total_users=total_users,
            total_jobs=total_jobs,
            total_applications=total_applications,
            total_resumes=total_resumes,
            active_jobs_count=active_jobs_count,
            department_count=department_count,
            monthly_stats=monthly_stats,
            dept_stats=department_stats,
            application_stats=application_stats,
            recent_applications=recent_applications,
            active_jobs=active_jobs,
            latest_month=latest_month,
            peak_month=peak_month,
            acceptance_rate=acceptance_rate,
            resume_coverage_rate=resume_coverage_rate,
            submitted_count=submitted_count,
            review_count=review_count,
            interview_count=interview_count,
            accepted_count=accepted_count,
            rejected_count=rejected_count
        )
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}", exc_info=True)
        flash("Error loading dashboard data. Please try again.", "danger")
        return redirect(url_for("main.index"))

@bp.route("/admin/jobs")
@login_required
@admin_required
def list_jobs():
    jobs = Job.query.order_by(Job.posted_date.desc()).all()
    return render_template("admin/list_jobs.html", title="Manage Jobs", jobs=jobs)

@bp.route("/jobs")
def view_jobs():
    # Get filter parameters
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()

    # Base query: only open jobs
    query = Job.query.filter_by(status="open")

    # Apply department filter
    if department:
        query = query.filter(Job.department == department)

    # Apply keyword search (search in title, description, required_skills)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Job.title.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Job.required_skills.ilike(search_pattern)
            )
        )

    jobs = query.order_by(Job.posted_date.desc()).all()

    # Get unique departments for filter dropdown
    departments = db.session.query(Job.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]

    return render_template(
        "view_jobs.html",
        title="Open Positions",
        jobs=jobs,
        departments=departments,
        UserRole=UserRole
    )

@bp.route("/jobs/<int:job_id>")
def view_job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("job_detail.html", title=job.title, job=job, UserRole=UserRole)

@bp.route("/user/delete_resume/<int:resume_id>", methods=["POST"])
@login_required
def delete_resume(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.candidate_id != current_user.id:
        flash("You do not have permission to delete this resume.", "danger")
        return redirect(url_for("main.user_profile"))
    
    try:
        # Check if this is the primary resume and there are other resumes
        if resume.is_primary:
            other_resume = Resume.query.filter(
                Resume.candidate_id == current_user.id,
                Resume.resume_id != resume.resume_id
            ).first()
            if other_resume:
                # Make the other resume primary
                other_resume.is_primary = True

        # Delete associated matches first
        JobMatch.query.filter_by(resume_id=resume.resume_id).delete()
        
        # Update applications to use another resume if available
        applications = Application.query.filter_by(resume_id=resume.resume_id).all()
        if applications:
            # Find another resume to associate with the applications
            alternate_resume = Resume.query.filter(
                Resume.candidate_id == current_user.id,
                Resume.resume_id != resume.resume_id
            ).first()
            
            if alternate_resume:
                # Update applications to use the alternate resume
                for application in applications:
                    application.resume_id = alternate_resume.resume_id
            else:
                # If no alternate resume exists, we need to delete the applications
                for application in applications:
                    db.session.delete(application)
        
        # Delete the file from storage
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], resume.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted resume file: {file_path}")
        else:
            logger.warning(f"Resume file not found for deletion: {file_path}")

        # Delete the resume record
        db.session.delete(resume)
        db.session.commit()
        
        if applications and not alternate_resume:
            flash("Resume deleted successfully. Note: Related job applications were also deleted since no alternate resume was available.", "warning")
        else:
            flash("Resume deleted successfully.", "success")
        
        logger.info(f"Deleted resume record {resume_id} for user {current_user.id}")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting resume. Please try again.", "danger")
        logger.error(f"Error deleting resume {resume_id}: {e}", exc_info=True)
        
    return redirect(url_for("main.user_profile"))

@bp.route("/admin/jobs/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_job():
    form = JobForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            description=form.description.data,
            required_skills=form.required_skills.data,
            department=form.department.data,
            location=form.location.data,
            salary_range=form.salary_range.data,
            status=form.status.data,
            closing_date=form.closing_date.data,
            posted_by=current_user.id
        )
        try:
            db.session.add(job)
            db.session.commit()
            flash("Job posting created successfully!", "success")
            return redirect(url_for("main.list_jobs"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating job posting: {str(e)}", "danger")
            return redirect(url_for("main.create_job"))
    
    return render_template("admin/create_job.html", title="Create Job Posting", form=form)

@bp.route("/admin/jobs/edit/<int:job_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    form = JobForm(obj=job)
    
    if form.validate_on_submit():
        try:
            job.title = form.title.data
            job.description = form.description.data
            job.required_skills = form.required_skills.data
            job.department = form.department.data
            job.location = form.location.data
            job.salary_range = form.salary_range.data
            job.status = form.status.data
            job.closing_date = form.closing_date.data
            
            db.session.commit()
            flash("Job posting updated successfully!", "success")
            return redirect(url_for("main.list_jobs"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating job posting: {str(e)}", "danger")
    
    return render_template("admin/edit_job.html", title="Edit Job Posting", form=form, job=job)

@bp.route("/admin/jobs/delete/<int:job_id>", methods=["POST"])
@login_required
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    try:
        # Delete associated job matches first
        JobMatch.query.filter_by(job_id=job.job_id).delete()
        
        # Delete the job
        db.session.delete(job)
        db.session.commit()
        flash("Job posting deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting job posting: {str(e)}", "danger")
    
    return redirect(url_for("main.list_jobs"))

@bp.route("/resume/analysis/<int:resume_id>")
@login_required
def resume_analysis(resume_id):
    resume = Resume.query.get_or_404(resume_id)
    if resume.candidate_id != current_user.id and not current_user.is_admin():
        flash("You do not have permission to view this resume analysis.", "danger")
        return redirect(url_for("main.user_profile"))
    
    try:
        from app.resume_analyzer import ResumeAnalyzer

        # Initialize analyzers
        resume_analyzer = ResumeAnalyzer()
        
        # Perform resume analysis
        analysis = resume_analyzer.analyze_resume(resume.parsed_text)
        
        # Get all active jobs for matching
        active_jobs = Job.query.filter_by(status='open').all()
        jobs_data = [
            {
                "job_id": job.job_id,
                "title": job.title,
                "description": job.description,
                "requirements": getattr(job, 'requirements', '')  # Use getattr with default empty string
            }
            for job in active_jobs
        ]
        
        # Use enhanced semantic job matching
        try:
            from app.semantic_job_matcher import enhanced_job_matching
            
            # Generate job matches with enhanced algorithm
            enhanced_matches = enhanced_job_matching(
                resume_text=resume.parsed_text,
                resume_analysis=analysis,
                jobs_data=jobs_data
            )
            
            # Update or create JobMatch records
            for match in enhanced_matches:
                job_id = match["job_id"]
                match_score = match["match_score"]
                match_details = match["match_details"]
                
                # Check if match record exists
                existing_match = JobMatch.query.filter_by(
                    resume_id=resume_id,
                    job_id=job_id
                ).first()
                
                if existing_match:
                    # Update existing match
                    existing_match.match_score = match_score
                    existing_match.match_details = match_details
                    existing_match.calculated_at = datetime.utcnow()
                else:
                    # Create new match record
                    new_match = JobMatch(
                        resume_id=resume_id,
                        job_id=job_id,
                        match_score=match_score,
                        match_details=match_details
                    )
                    db.session.add(new_match)
            
            # Commit changes to database
            db.session.commit()
            logger.info(f"Enhanced job matching completed for resume {resume_id}")
            
        except ImportError:
            logger.warning("Enhanced job matching not available, using existing matches")
            
        # Get job matches for this resume from database
        matches = (
            JobMatch.query
            .join(Job)
            .filter(JobMatch.resume_id == resume_id)
            .order_by(JobMatch.match_score.desc())
            .all()
        )
        
        # Get course recommendations based on resume content
        recommended_courses = course_recommender(resume.parsed_text)
        
        # Prepare course details
        course_details = {
            "Data Science": ds_course,
            "Web Development": web_course,
            "Android Development": android_course,
            "iOS Development": ios_course,
            "UI/UX": uiux_course
        }
        
        # Get relevant courses based on recommendations
        courses_to_show = {
            category: course_details.get(category, [])
            for category in recommended_courses
        }

        # Display PDF if it's a PDF file
        pdf_display = None
        if resume.file_path.lower().endswith('.pdf'):
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], resume.file_path)
            if os.path.exists(file_path):
                pdf_display = show_pdf(file_path)
                if pdf_display:
                    pdf_display = Markup(pdf_display)
        
        return render_template(
            "resume/analysis.html",
            title="Resume Analysis",
            resume=resume,
            analysis=analysis,
            matched_jobs=matches,
            recommended_courses=courses_to_show,
            pdf_display=pdf_display
        )
        
    except Exception as e:
        logger.error(f"Error in resume analysis for resume {resume_id}: {e}", exc_info=True)
        flash("Error loading resume analysis. Please try again.", "danger")
        return redirect(url_for("main.user_profile"))

@bp.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
@login_required
def apply_for_job(job_id):
    if current_user.role != UserRole.candidate:
        flash("Only candidates can apply for jobs.", "danger")
        return redirect(url_for("main.view_job_detail", job_id=job_id))
    
    job = Job.query.get_or_404(job_id)
    if job.status != "open":
        flash("This position is no longer accepting applications.", "warning")
        return redirect(url_for("main.view_job_detail", job_id=job_id))
    
    existing_application = Application.query.filter_by(
        candidate_id=current_user.id,
        job_id=job_id
    ).first()
    
    if existing_application:
        flash("You have already applied for this position.", "info")
        return redirect(url_for("main.view_application", application_id=existing_application.application_id))
    
    form = ApplicationForm()
    form.resume.choices = [(r.resume_id, r.original_filename) 
                          for r in Resume.query.filter_by(candidate_id=current_user.id).all()]
    
    if form.validate_on_submit():
        try:
            cover_letter_file_path = None
            if form.cover_letter_file.data:
                file = form.cover_letter_file.data
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                
                cover_letters_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cover_letters')
                os.makedirs(cover_letters_dir, exist_ok=True)
                
                file_path = os.path.join(cover_letters_dir, unique_filename)
                file.save(file_path)
                cover_letter_file_path = f"cover_letters/{unique_filename}"
            
            application = Application(
                candidate_id=current_user.id,
                job_id=job_id,
                resume_id=form.resume.data,
                cover_letter=form.cover_letter.data,
                cover_letter_file=cover_letter_file_path,
                status=ApplicationStatus.submitted
            )
            
            db.session.add(application)
            db.session.commit()
            
            flash("Your application has been submitted successfully!", "success")
            return redirect(url_for("main.view_application", application_id=application.application_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error submitting application: {e}", exc_info=True)
            flash("Error submitting your application. Please try again.", "danger")
    
    return render_template(
        "jobs/apply.html",
        title=f"Apply for {job.title}",
        form=form,
        job=job
    )

@bp.route("/applications/<int:application_id>")
@login_required
def view_application(application_id):
    application = Application.query.get_or_404(application_id)
    if not current_user.is_admin() and application.candidate_id != current_user.id:
        flash("You do not have permission to view this application.", "danger")
        return redirect(url_for("main.index"))
    
    return render_template(
        "applications/view.html",
        title="Application Details",
        application=application
    )

@bp.route("/applications/<int:application_id>/schedule-interview", methods=["GET", "POST"])
@login_required
@admin_required
def schedule_interview(application_id):
    application = Application.query.get_or_404(application_id)
    if application.status not in [ApplicationStatus.submitted, ApplicationStatus.under_review]:
        flash("This application is not in a state where an interview can be scheduled.", "warning")
        return redirect(url_for("main.view_application", application_id=application_id))
    
    form = InterviewForm()
    if form.validate_on_submit():
        try:
            # Combine date and time fields
            from datetime import datetime
            date_str = form.interview_date.data.strftime('%Y-%m-%d')
            time_str = form.interview_time.data
            scheduled_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            
            interview = Interview(
                application_id=application_id,
                scheduled_date=scheduled_datetime,
                interview_type=form.interview_type.data,
                location_or_link=form.location_or_link.data,
                notes=form.notes.data,
                interview_level=getattr(InterviewLevel, form.interview_level.data),
                interviewer_id=form.interviewer.data,
            )
            
            # Update application status
            application.status = ApplicationStatus.interview_scheduled
            
            db.session.add(interview)
            db.session.commit()
            
            # Send email notifications
            try:
                candidate = User.query.get(application.candidate_id)
                job = Job.query.get(application.job_id)
                
                # Notify candidate
                send_email(
                    subject="Interview Scheduled",
                    recipients=[candidate.email],
                    template="email/interview_scheduled.html",
                    user=candidate,
                    job=job,
                    interview=interview,
                    application=application
                )
                
                # Notify admin
                admin_users = User.query.filter_by(role=UserRole.admin).all()
                admin_emails = [admin.email for admin in admin_users]
                if admin_emails:
                    send_email(
                        subject=f"Interview Scheduled - {job.title}",
                        recipients=admin_emails,
                        template="email/interview_scheduled_admin.html",
                        candidate=candidate,
                        job=job,
                        interview=interview,
                        application=application
                    )
            except Exception as email_err:
                logger.error(f"Failed to send interview notification emails: {email_err}", exc_info=True)
                # Don't return here, just log the error
            
            flash("Interview scheduled successfully!", "success")
            return redirect(url_for("main.view_application", application_id=application_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error scheduling interview: {e}", exc_info=True)
            flash("Error scheduling the interview. Please try again.", "danger")
    
    return render_template(
        "schedule_interview.html",
        title="Schedule Interview",
        form=form,
        application=application
    )

@bp.route("/my-applications")
@login_required
def my_applications():
    if current_user.role != UserRole.candidate:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))
    
    # Get filter parameters
    status = request.args.get('status')
    department = request.args.get('department')
    
    # Base query
    query = Application.query.filter_by(candidate_id=current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Application.status == getattr(ApplicationStatus, status))
    if department:
        query = query.join(Job).filter(Job.department == department)
    
    # Get all applications with filters
    applications = query.order_by(Application.application_date.desc()).all()
    
    # Get unique departments for filter dropdown
    departments = db.session.query(Job.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]  # Remove None values
    
    return render_template(
        "applications/my_applications.html",
        title="My Applications",
        applications=applications,
        departments=departments
    )

@bp.route("/applications/<int:application_id>/update-status", methods=["POST"])
@login_required
@admin_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    new_status = request.form.get("status")
    feedback = request.form.get("feedback")
    
    if not new_status or not hasattr(ApplicationStatus, new_status):
        flash("Invalid status provided.", "danger")
        return redirect(url_for("main.view_application", application_id=application_id))
    
    try:
        old_status = application.status
        application.status = getattr(ApplicationStatus, new_status)
        
        # Update the feedback if provided
        if feedback:
            application.feedback = feedback
        
        db.session.commit()
        
        # Send email notification
        try:
            candidate = User.query.get(application.candidate_id)
            job = Job.query.get(application.job_id)
            
            # Select the appropriate email template based on the new status
            template = "email/application_status_update.html"
            subject = "Application Status Updated"
            
            if new_status == "accepted":
                template = "email/application_accepted.html"
                subject = f"Congratulations! Your Application for {job.title} Has Been Accepted"
            elif new_status == "rejected":
                template = "email/application_rejected.html"
                subject = f"Application Status Update for {job.title}"
            
            send_email(
                subject=subject,
                recipients=[candidate.email],
                template=template,
                user=candidate,
                job=job,
                application=application,
                old_status=old_status,
                new_status=application.status
            )
            
            flash("Application status and feedback updated successfully! Notification email sent.", "success")
        except Exception as email_err:
            logger.error(f"Failed to send status update email: {email_err}", exc_info=True)
            flash("Application status updated, but there was an issue sending the notification email.", "warning")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating application status: {e}", exc_info=True)
        flash("Error updating application status. Please try again.", "danger")
    
    return redirect(url_for("main.view_application", application_id=application_id)) 

@bp.route("/admin/fix-profile-images")
@login_required
@admin_required
def fix_profile_images():
    """Fix profile image paths in the database."""
    try:
        # Get all users with profile images
        users_with_images = User.query.filter(User.profile_image.isnot(None)).all()
        fixed_count = 0
        
        for user in users_with_images:
            logger.info(f"Checking user {user.id}: {user.first_name} {user.last_name}")
            logger.info(f"Current profile image: {user.profile_image}")
            
            # Check if image exists in profile_images directory
            profile_images_path = os.path.join(current_app.static_folder, 'profile_images', user.profile_image)
            if os.path.exists(profile_images_path):
                logger.info(f"Image already in correct location: {profile_images_path}")
                continue
                
            # Check if image exists in old location
            old_path = os.path.join(current_app.static_folder, 'img', user.profile_image)
            if os.path.exists(old_path):
                try:
                    # Move file to new location
                    os.rename(old_path, profile_images_path)
                    fixed_count += 1
                    logger.info(f"Moved image from {old_path} to {profile_images_path}")
                except Exception as e:
                    logger.error(f"Error moving file for user {user.id}: {str(e)}")
            else:
                logger.warning(f"Image not found in either location for user {user.id}")
                # If image doesn't exist anywhere, set profile_image to None
                user.profile_image = None
                fixed_count += 1
        
        db.session.commit()
        flash(f"Fixed {fixed_count} profile image paths", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error fixing profile images: {str(e)}")
        flash("Error fixing profile images", "danger")
    
    return redirect(url_for("admin.admin_dashboard")) 

@bp.route("/my-interviews")
@login_required
def my_interviews():
    if current_user.role != UserRole.candidate:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))
    
    # Find all applications with interviews
    applications = Application.query.filter_by(candidate_id=current_user.id)\
        .filter(Application.status == ApplicationStatus.interview_scheduled)\
        .join(Interview)\
        .order_by(Interview.scheduled_date)\
        .all()
    
    # Get upcoming and past interviews
    from datetime import datetime
    now = datetime.utcnow()
    
    upcoming_interviews = []
    past_interviews = []
    
    for app in applications:
        if app.interview and app.interview.scheduled_date > now:
            upcoming_interviews.append(app)
        elif app.interview:
            past_interviews.append(app)
    
    return render_template(
        "user/my_interviews.html",
        title="My Interviews",
        upcoming_interviews=upcoming_interviews,
        past_interviews=past_interviews
    ) 

@bp.route("/admin/email-settings", methods=["GET", "POST"])
@login_required
@admin_required
def email_settings():
    """Configure email settings for the application."""
    # Create a simple form to update email settings
    class EmailSettingsForm(FlaskForm):
        mail_server = StringField("SMTP Server", validators=[DataRequired()], render_kw={"placeholder": "e.g., smtp.gmail.com"})
        mail_port = StringField("SMTP Port", validators=[DataRequired()], render_kw={"placeholder": "e.g., 587 or 465"})
        mail_use_tls = BooleanField("Use TLS")
        mail_username = StringField("Email Username", validators=[DataRequired(), Email()], render_kw={"placeholder": "e.g., registrar@umat.edu.gh"})
        mail_password = PasswordField("Email Password", validators=[DataRequired()], render_kw={"placeholder": "Enter SMTP app password"})
        mail_default_sender = StringField("Default Sender", validators=[DataRequired(), Email()], render_kw={"placeholder": "e.g., registrar@umat.edu.gh"})
        test_recipient = StringField("Test Email Address", validators=[Email()], 
                                    description="Enter an email address to receive a test message",
                                    render_kw={"placeholder": "e.g., test@example.com"})
        submit = SubmitField("Save Settings")
        test_email = SubmitField("Send Test Email")
    
    # Read current settings from .env file if it exists
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    current_settings = {}
    
    try:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        current_settings[key] = value
    except Exception as e:
        logger.error(f"Error reading .env file: {e}")
    
    # Create the form
    form = EmailSettingsForm()
    
    # Pre-fill form with current settings
    if not form.is_submitted():
        form.mail_server.data = current_app.config.get('MAIL_SERVER', '')
        form.mail_port.data = str(current_app.config.get('MAIL_PORT', ''))
        form.mail_use_tls.data = current_app.config.get('MAIL_USE_TLS', True)
        form.mail_username.data = current_app.config.get('MAIL_USERNAME', '')
        form.mail_password.data = current_app.config.get('MAIL_PASSWORD', '')
        form.mail_default_sender.data = current_app.config.get('MAIL_DEFAULT_SENDER', '')
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            # If this is a test email request
            if form.test_email.data and form.test_recipient.data:
                # Save temporary config
                current_app.config['MAIL_SERVER'] = form.mail_server.data
                current_app.config['MAIL_PORT'] = int(form.mail_port.data)
                current_app.config['MAIL_USE_TLS'] = form.mail_use_tls.data
                current_app.config['MAIL_USERNAME'] = form.mail_username.data
                current_app.config['MAIL_PASSWORD'] = form.mail_password.data
                current_app.config['MAIL_DEFAULT_SENDER'] = form.mail_default_sender.data
                
                # Reinitialize the mail extension with new settings
                mail.init_app(current_app)
                
                # Send test email
                test_result = send_email(
                    subject="UMAT Job Portal - Test Email",
                    recipients=[form.test_recipient.data],
                    template="email/test_email.html",
                    user=current_user
                )
                
                if test_result:
                    flash(f"Test email sent to {form.test_recipient.data}!", "success")
                else:
                    flash(f"Failed to send test email. Please check the server logs for details.", "danger")
                
                return redirect(url_for('main.email_settings'))
            
            # If this is a save settings request
            elif form.submit.data:
                # Save settings to .env file
                env_content = []
                
                # Read existing content first
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        for line in f:
                            # Skip the lines we'll be replacing
                            if not line.strip().startswith(('MAIL_SERVER=', 'MAIL_PORT=', 'MAIL_USE_TLS=', 
                                                          'MAIL_USERNAME=', 'MAIL_PASSWORD=', 
                                                          'MAIL_DEFAULT_SENDER=')):
                                env_content.append(line.strip())
                
                # Add new settings
                env_content.append(f"MAIL_SERVER={form.mail_server.data}")
                env_content.append(f"MAIL_PORT={form.mail_port.data}")
                env_content.append(f"MAIL_USE_TLS={'true' if form.mail_use_tls.data else 'false'}")
                env_content.append(f"MAIL_USERNAME={form.mail_username.data}")
                env_content.append(f"MAIL_PASSWORD={form.mail_password.data}")
                env_content.append(f"MAIL_DEFAULT_SENDER={form.mail_default_sender.data}")
                
                # Write the file
                with open(env_file, 'w') as f:
                    f.write('\n'.join(env_content))
                
                # Update current app config
                current_app.config['MAIL_SERVER'] = form.mail_server.data
                current_app.config['MAIL_PORT'] = int(form.mail_port.data)
                current_app.config['MAIL_USE_TLS'] = form.mail_use_tls.data
                current_app.config['MAIL_USERNAME'] = form.mail_username.data
                current_app.config['MAIL_PASSWORD'] = form.mail_password.data
                current_app.config['MAIL_DEFAULT_SENDER'] = form.mail_default_sender.data
                
                # Reinitialize the mail extension
                mail.init_app(current_app)
                
                flash("Email settings saved successfully!", "success")
                return redirect(url_for('main.admin_dashboard'))
        
        except Exception as e:
            logger.error(f"Error saving email settings: {e}", exc_info=True)
            flash(f"Error saving settings: {str(e)}", "danger")
    
    return render_template(
        "admin/email_settings.html",
        title="Email Settings",
        form=form
    )

# ===== EVENT MANAGEMENT ROUTES =====

@bp.route("/admin/events")
@login_required
@admin_required
def list_events():
    """List all events for admin management."""
    events = Event.query.order_by(Event.event_date.desc()).all()
    return render_template("admin/events.html", title="Manage Events", events=events)

@bp.route("/admin/events/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_event():
    """Create a new event."""
    form = EventForm()
    if form.validate_on_submit():
        try:
            # Handle image upload
            image_path = None
            if form.image.data:
                file = form.image.data
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                image_path_full = os.path.join(current_app.static_folder, 'event_images', unique_filename)
                file.save(image_path_full)
                image_path = unique_filename
                logger.info(f"Saved event image: {image_path_full}")
            
            # Handle video upload
            video_path = None
            if form.video.data:
                file = form.video.data
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                video_path_full = os.path.join(current_app.static_folder, 'event_videos', unique_filename)
                file.save(video_path_full)
                video_path = unique_filename
                logger.info(f"Saved event video: {video_path_full}")
            
            event = Event(
                title=form.title.data,
                description=form.description.data,
                event_date=form.event_date.data,
                location=form.location.data,
                event_type=form.event_type.data,
                status=form.status.data,
                image_path=image_path,
                video_path=video_path,
                created_by=current_user.id
            )
            
            db.session.add(event)
            db.session.commit()
            flash("Event created successfully!", "success")
            return redirect(url_for("main.list_events"))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating event: {e}", exc_info=True)
            flash(f"Error creating event: {str(e)}", "danger")
    
    return render_template("admin/create_event.html", title="Create Event", form=form)

@bp.route("/admin/events/edit/<int:event_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_event(event_id):
    """Edit an existing event."""
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)
    form.submit.label.text = "Update Event"
    
    if form.validate_on_submit():
        try:
            # Handle image upload
            if form.image.data:
                # Delete old image if it exists
                if event.image_path:
                    old_image_path = os.path.join(current_app.static_folder, 'event_images', event.image_path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                file = form.image.data
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                image_path_full = os.path.join(current_app.static_folder, 'event_images', unique_filename)
                file.save(image_path_full)
                event.image_path = unique_filename
                logger.info(f"Updated event image: {image_path_full}")
            
            # Handle video upload
            if form.video.data:
                # Delete old video if it exists
                if event.video_path:
                    old_video_path = os.path.join(current_app.static_folder, 'event_videos', event.video_path)
                    if os.path.exists(old_video_path):
                        os.remove(old_video_path)
                
                file = form.video.data
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                video_path_full = os.path.join(current_app.static_folder, 'event_videos', unique_filename)
                file.save(video_path_full)
                event.video_path = unique_filename
                logger.info(f"Updated event video: {video_path_full}")
            
            # Update event fields
            event.title = form.title.data
            event.description = form.description.data
            event.event_date = form.event_date.data
            event.location = form.location.data
            event.event_type = form.event_type.data
            event.status = form.status.data
            event.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash("Event updated successfully!", "success")
            return redirect(url_for("main.list_events"))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating event: {e}", exc_info=True)
            flash(f"Error updating event: {str(e)}", "danger")
    
    return render_template("admin/edit_event.html", title="Edit Event", form=form, event=event)

@bp.route("/admin/events/delete/<int:event_id>", methods=["POST"])
@login_required
@admin_required
def delete_event(event_id):
    """Delete an event."""
    event = Event.query.get_or_404(event_id)
    try:
        # Delete associated files
        if event.image_path:
            image_path = os.path.join(current_app.static_folder, 'event_images', event.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        if event.video_path:
            video_path = os.path.join(current_app.static_folder, 'event_videos', event.video_path)
            if os.path.exists(video_path):
                os.remove(video_path)
        
        db.session.delete(event)
        db.session.commit()
        flash("Event deleted successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting event: {e}", exc_info=True)
        flash(f"Error deleting event: {str(e)}", "danger")
    
    return redirect(url_for("main.list_events"))

@bp.route("/events")
def view_events():
    """Public view of upcoming events."""
    upcoming_events = Event.query.filter_by(status="upcoming").order_by(Event.event_date.asc()).all()
    return render_template("events/events.html", title="Upcoming Events", events=upcoming_events)

@bp.route("/events/<int:event_id>")
def view_event_detail(event_id):
    """View detailed information about a specific event."""
    event = Event.query.get_or_404(event_id)
    return render_template("events/event_detail.html", title=event.title, event=event)
