from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from markupsafe import Markup
from app import db
from datetime import datetime
from app.models import User, UserRole, Candidate, Resume, Job, JobMatch, Application, Interview, ApplicationStatus
from app.forms import RegistrationForm, LoginForm, ResumeUploadForm, JobForm, ApplicationForm, InterviewForm
from flask_login import login_user, logout_user, current_user, login_required
from functools import wraps
import os
from werkzeug.utils import secure_filename
from app.utils import parse_resume, save_profile_image, send_email, show_pdf
from app.ai_analyzer import analyze_resume_and_match
from app.resume_analyzer import ResumeAnalyzer
import logging
from app.models import UserRole
from app.courses import course_recommender, ds_course, web_course, android_course, ios_course, uiux_course
import uuid
import json
from sqlalchemy import and_

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
                        "title": job.title
                    } for job in jobs_to_analyze]
                    
                    # Perform analysis
                    analysis_results = analyze_resume_and_match(new_resume.resume_id, parsed_text, jobs_data)
                    
                    if not analysis_results:
                        flash("Resume uploaded, but analysis could not be completed.", "warning")
                        return redirect(url_for("main.resume_analysis", resume_id=new_resume.resume_id))
                    
                    # Delete old matches
                    JobMatch.query.filter_by(resume_id=new_resume.resume_id).delete()

                    # Save new matches
                    matches_saved = 0
                    for match in analysis_results["matches"]:
                        if match["match_score"] > 0.05:  # 5% minimum threshold
                            db_match = JobMatch(
                                resume_id=match["resume_id"],
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
    # Simple homepage - maybe list some recent jobs 
    jobs = Job.query.filter_by(status="open").order_by(Job.posted_date.desc()).limit(5).all()
    return render_template("index.html", title="Home", jobs=jobs)

# --- Add routes for REGISTRATION --- 
@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Handle profile image upload
        profile_image_path = save_profile_image(form.profile_image.data)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            profile_image=profile_image_path
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Create candidate profile for non-admin users
            if user.role == UserRole.candidate:
                candidate = Candidate(candidate_id=user.id)
                db.session.add(candidate)
                db.session.commit()
            
            flash("Your account has been created! You can now log in.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "danger")
            return redirect(url_for("main.register"))
    
    return render_template("register.html", title="Register", form=form)

# --- Add routes for LOGIN --- 
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password", "danger")
            return redirect(url_for("main.login"))
        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.username}!", "success")
        next_page = request.args.get("next")
        if user.is_admin():
            return redirect(next_page) if next_page else redirect(url_for("main.admin_dashboard"))
        else:
            # Ensure candidate profile exists
            if not user.candidate_profile:
                 try:
                     candidate = Candidate(candidate_id=user.id)
                     db.session.add(candidate)
                     db.session.commit()
                 except Exception as e:
                     db.session.rollback()
                     logger.error(f"Failed to create candidate profile on login for user {user.id}: {e}", exc_info=True)
                     flash("Error accessing profile. Please contact support.", "danger")
                     logout_user() # Log out user if profile creation fails
                     return redirect(url_for("main.login"))
            return redirect(next_page) if next_page else redirect(url_for("main.user_profile"))
    return render_template("auth/login.html", title="Sign In", form=form)

# --- Add routes for LOGOUT --- 
@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))

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
    # This could be optimized, e.g., only fetch for primary or latest resume
    matches = JobMatch.query.join(Resume).filter(Resume.candidate_id == current_user.id).order_by(JobMatch.match_score.desc()).all()

    return render_template("user/profile.html", title="My Profile", upload_form=upload_form, resumes=resumes, matches=matches)

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

        # Log the number of applications fetched for debugging
        logger.info(f"Admin dashboard fetched {recent_applications.total} recent applications")

        # Get monthly statistics for the past 12 months
        now = datetime.utcnow()
        monthly_stats = []
        
        for i in range(12):
            month_start = datetime(now.year, now.month - i if now.month - i > 0 else 12 - (i - now.month), 1)
            month_end = datetime(month_start.year, month_start.month + 1, 1) if month_start.month < 12 else datetime(month_start.year + 1, 1, 1)
            
            applications = Application.query.filter(
                Application.application_date.between(month_start, month_end)
            ).count()
            
            resumes = Resume.query.filter(
                Resume.upload_date.between(month_start, month_end)
            ).count()
            
            jobs = Job.query.filter(
                Job.posted_date.between(month_start, month_end)
            ).count()
            
            monthly_stats.insert(0, {
                'month': month_start.strftime('%B %Y'),
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

        return render_template(
            "admin/dashboard.html",
            title="Admin Dashboard",
            total_users=total_users,
            total_jobs=total_jobs,
            total_applications=total_applications,
            total_resumes=total_resumes,
            monthly_stats=monthly_stats,
            dept_stats=department_stats,
            application_stats=application_stats,
            recent_applications=recent_applications
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
    jobs = Job.query.filter_by(status="open").order_by(Job.posted_date.desc()).all()
    return render_template("view_jobs.html", title="Open Positions", jobs=jobs)

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
        # Delete associated matches first
        JobMatch.query.filter_by(resume_id=resume.resume_id).delete()
        
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
        flash("Resume deleted successfully.", "success")
        logger.info(f"Deleted resume record {resume_id} for user {current_user.id}")
    except Exception as e:
        db.session.rollback()
        flash("Error deleting resume.", "danger")
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
            requirements=form.requirements.data,
            department=form.department.data,
            location=form.location.data,
            salary_range=form.salary_range.data,
            status="open"
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
            job.requirements = form.requirements.data
            job.department = form.department.data
            job.location = form.location.data
            job.salary_range = form.salary_range.data
            
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
        # Initialize analyzers
        resume_analyzer = ResumeAnalyzer()
        
        # Perform resume analysis
        analysis = resume_analyzer.analyze_resume(resume.parsed_text)
        
        # Get job matches for this resume
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
    
    # Check if already applied
    existing_application = Application.query.filter_by(
        candidate_id=current_user.id,
        job_id=job_id
    ).first()
    
    if existing_application:
        flash("You have already applied for this position.", "info")
        return redirect(url_for("main.view_application", application_id=existing_application.application_id))
    
    form = ApplicationForm()
    # Get user's resumes for the dropdown
    form.resume.choices = [(r.resume_id, r.original_filename) 
                          for r in Resume.query.filter_by(candidate_id=current_user.id).all()]
    
    if form.validate_on_submit():
        try:
            application = Application(
                candidate_id=current_user.id,
                job_id=job_id,
                resume_id=form.resume.data,
                cover_letter=form.cover_letter.data,
                status=ApplicationStatus.submitted
            )
            db.session.add(application)
            db.session.commit()
            
            # Log success for debugging
            logger.info(f"Application created successfully for user {current_user.id} and job {job_id}")
            
            # Send email notifications
            try:
                # Notify candidate
                send_email(
                    subject="Application Submitted Successfully",
                    recipients=[current_user.email],
                    template="email/application_submitted.html",
                    user=current_user,
                    job=job
                )
                
                # Notify admin
                admin_users = User.query.filter_by(role=UserRole.admin).all()
                admin_emails = [admin.email for admin in admin_users]
                if admin_emails:
                    send_email(
                        subject=f"New Job Application - {job.title}",
                        recipients=admin_emails,
                        template="email/new_application_admin.html",
                        user=current_user,
                        job=job,
                        application=application
                    )
            except Exception as email_err:
                logger.error(f"Failed to send application notification emails: {email_err}", exc_info=True)
                # Don't block the application process, just log
        except Exception as db_err:
            db.session.rollback()  # Rollback on error to avoid partial saves
            logger.error(f"Error creating application: {str(db_err)}", exc_info=True)
            flash("There was an error submitting your application. Please try again.", "danger")
            return redirect(url_for('main.apply_for_job', job_id=job_id))  # Redirect back to form

        flash("Your application has been submitted successfully!", "success")
        return redirect(url_for("main.view_application", application_id=application.application_id))
    
    return render_template("jobs/apply.html", title=f"Apply - {job.title}", form=form, job=job)

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
            interview = Interview(
                application_id=application_id,
                scheduled_date=form.scheduled_date.data,
                interview_type=form.interview_type.data,
                location_or_link=form.location_or_link.data,
                notes=form.notes.data
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
        "applications/schedule_interview.html",
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
    
    if not new_status or not hasattr(ApplicationStatus, new_status):
        flash("Invalid status provided.", "danger")
        return redirect(url_for("main.view_application", application_id=application_id))
    
    try:
        old_status = application.status
        application.status = getattr(ApplicationStatus, new_status)
        db.session.commit()
        
        # Send email notification
        try:
            candidate = User.query.get(application.candidate_id)
            job = Job.query.get(application.job_id)
            
            send_email(
                subject="Application Status Updated",
                recipients=[candidate.email],
                template="email/application_status_update.html",
                user=candidate,
                job=job,
                application=application,
                old_status=old_status,
                new_status=application.status
            )
        except Exception as email_err:
            logger.error(f"Failed to send status update email: {email_err}", exc_info=True)
            # Don't return here, just log the error
        
        flash("Application status updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating application status: {e}", exc_info=True)
        flash("Error updating application status. Please try again.", "danger")
    
    return redirect(url_for("main.view_application", application_id=application_id)) 