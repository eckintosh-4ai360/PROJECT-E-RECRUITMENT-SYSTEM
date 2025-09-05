from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, send_from_directory
from flask_login import login_required, current_user
from app.models import User, Job, Application, Resume, ApplicationStatus, Interview, JobMatch
from app import db
from sqlalchemy import and_
import os
from werkzeug.utils import secure_filename
from app.utils import show_pdf
import logging
from datetime import datetime, timezone

admin = Blueprint('admin', __name__)

@admin.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get search and filter parameters
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    sort_by = request.args.get('sort_by', 'created_at').strip()
    sort_order = request.args.get('sort_order', 'desc').strip()
    
    # Start with base query
    query = User.query
    
    # Apply search filter (search in username, full name, and email)
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern),
                db.func.concat(User.first_name, ' ', User.last_name).ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            )
        )
    
    # Apply role filter
    if role_filter:
        from app.models import UserRole
        try:
            # Handle both string values and enum values
            if hasattr(UserRole, role_filter.lower()):
                role_enum = getattr(UserRole, role_filter.lower())
                query = query.filter(User.role == role_enum)
            else:
                flash('Invalid role filter', 'warning')
        except (KeyError, AttributeError):
            flash('Invalid role filter', 'warning')
    
    # Apply date range filter
    try:
        if date_from:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(User.created_at >= date_from_obj)
        
        if date_to:
            from datetime import datetime, timedelta
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(User.created_at < date_to_obj)
    except ValueError:
        flash('Invalid date format. Please use YYYY-MM-DD format.', 'warning')
    
    # Apply sorting
    valid_sort_fields = {
        'username': User.username,
        'email': User.email,
        'full_name': db.func.concat(User.first_name, ' ', User.last_name),
        'role': User.role,
        'created_at': User.created_at
    }
    
    if sort_by in valid_sort_fields:
        sort_field = valid_sort_fields[sort_by]
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
    else:
        query = query.order_by(User.created_at.desc())
    
    # Execute query and get results
    users = query.all()
    
    # Get statistics for display
    from app.models import UserRole
    total_users = User.query.count()
    total_candidates = User.query.filter(User.role == UserRole.candidate).count()
    total_admins = User.query.filter(User.role == UserRole.admin).count()
    
    search_stats = {
        'total_found': len(users),
        'total_users': total_users,
        'total_candidates': total_candidates,
        'total_admins': total_admins
    }
    
    return render_template(
        'admin/users.html', 
        users=users,
        search_stats=search_stats,
        current_filters={
            'search': search_query,
            'role': role_filter,
            'date_from': date_from,
            'date_to': date_to,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    )

@admin.route('/active-jobs')
@login_required
def active_jobs():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    active_jobs = Job.query.filter_by(status='open').order_by(Job.posted_date.desc()).all()
    return render_template('admin/active_jobs.html', active_jobs=active_jobs)

@admin.route('/applications')
@login_required
def all_applications():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get filter parameters
    status = request.args.get('status')
    department = request.args.get('department')
    user_id = request.args.get('user_id')  # New filter for specific user
    
    # Base query with joins to get all necessary data including JobMatch
    query = Application.query\
        .join(User, Application.candidate_id == User.id)\
        .join(Job, Application.job_id == Job.job_id)\
        .join(Resume, Application.resume_id == Resume.resume_id, isouter=True)\
        .outerjoin(JobMatch, and_(JobMatch.resume_id == Resume.resume_id, JobMatch.job_id == Job.job_id))
    
    # Apply filters
    if status:
        try:
            # Convert the status string to enum value
            status_enum = ApplicationStatus[status.lower()]
            query = query.filter(Application.status == status_enum)
        except (KeyError, AttributeError):
            flash('Invalid status filter', 'warning')
    if department:
        query = query.filter(Job.department == department)
    if user_id:
        try:
            user_id_int = int(user_id)
            query = query.filter(Application.candidate_id == user_id_int)
            # Get user info for display context
            filtered_user = User.query.get(user_id_int)
            if filtered_user:
                flash(f'Showing applications for user: {filtered_user.username}', 'info')
        except (ValueError, TypeError):
            flash('Invalid user ID provided', 'warning')
    
    # Get all unique departments for filter dropdown
    departments = db.session.query(Job.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    # Get all applications with filters and order by date
    applications = query.order_by(Application.application_date.desc()).all()
    
    # Create a dictionary to store match scores for easy template access
    match_scores = {}
    for application in applications:
        if application.resume_id and application.job_id:
            # Get the JobMatch for this specific application
            job_match = JobMatch.query.filter_by(
                resume_id=application.resume_id,
                job_id=application.job_id
            ).first()
            
            if job_match:
                match_scores[application.application_id] = {
                    'score': job_match.match_score,
                    'details': job_match.match_details
                }
    
    return render_template(
        'admin/all_applications.html',
        applications=applications,
        departments=departments,
        ApplicationStatus=ApplicationStatus,
        match_scores=match_scores
    )

@admin.route('/view_resume/<int:application_id>')
@login_required
def view_resume(application_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    application = Application.query.get_or_404(application_id)
    if not application.resume:
        flash('No resume found for this application.', 'warning')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], application.resume.file_path)
    if not os.path.exists(resume_path):
        flash('Resume file not found.', 'error')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    # Display PDF using the built-in viewer
    pdf_display = show_pdf(resume_path)
    if not pdf_display:
        flash('Error displaying the PDF.', 'error')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    return render_template('resume/viewer.html', 
                         pdf_display=pdf_display, 
                         resume=application.resume,
                         application=application)

@admin.route('/download_resume/<int:application_id>')
@login_required
def download_resume(application_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    application = Application.query.get_or_404(application_id)
    if not application.resume:
        flash('No resume found for this application.', 'warning')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    resume_path = os.path.join(current_app.config['UPLOAD_FOLDER'], application.resume.file_path)
    if not os.path.exists(resume_path):
        flash('Resume file not found.', 'error')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    return send_file(
        resume_path,
        as_attachment=True,
        download_name=application.resume.original_filename
    )

@admin.route('/applications/<int:application_id>/cover-letter/download')
@login_required
def download_cover_letter(application_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    if not application.cover_letter_file:
        flash('No cover letter file found.', 'warning')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            application.cover_letter_file,
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Error downloading cover letter: {e}", exc_info=True)
        flash('Error downloading cover letter file.', 'danger')
        return redirect(url_for('main.view_application', application_id=application_id))

@admin.route('/applications/<int:application_id>/cover-letter/view')
@login_required
def view_cover_letter(application_id):
    if not current_user.is_admin():
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    application = Application.query.get_or_404(application_id)
    if not application.cover_letter_file:
        flash('No cover letter file found.', 'warning')
        return redirect(url_for('main.view_application', application_id=application_id))
    
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            application.cover_letter_file,
            as_attachment=False
        )
    except Exception as e:
        logger.error(f"Error viewing cover letter: {e}", exc_info=True)
        flash('Error viewing cover letter file.', 'danger')
        return redirect(url_for('main.view_application', application_id=application_id))

@admin.route('/users/<int:user_id>/profile')
@login_required
def view_user_profile(user_id):
    """Admin route to view detailed user profile"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Get additional user statistics
    total_applications = Application.query.filter_by(candidate_id=user_id).count()
    recent_applications = Application.query.filter_by(candidate_id=user_id).order_by(Application.application_date.desc()).limit(5).all()
    
    # Get user's resumes
    resumes = Resume.query.filter_by(candidate_id=user_id).order_by(Resume.upload_date.desc()).all()
    
    # Get interview statistics
    total_interviews = db.session.query(Interview).join(Application).filter(Application.candidate_id == user_id).count()
    
    # Handle timezone mismatch by making member_since timezone-aware if it's naive
    member_since = user.created_at
    if member_since and member_since.tzinfo is None:
        # If the datetime is naive, assume it's UTC and make it timezone-aware
        member_since = member_since.replace(tzinfo=timezone.utc)
    
    user_stats = {
        'total_applications': total_applications,
        'total_interviews': total_interviews,
        'total_resumes': len(resumes),
        'member_since': member_since
    }
    
    return render_template(
        'admin/user_profile.html',
        user=user,
        user_stats=user_stats,
        recent_applications=recent_applications,
        resumes=resumes
    )

@admin.route('/users/<int:user_id>/applications')
@login_required
def view_user_applications(user_id):
    """Admin route to view all applications by a specific user"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    # Get all applications by this user with related data
    applications = Application.query\
        .filter_by(candidate_id=user_id)\
        .join(Job)\
        .join(Resume, Application.resume_id == Resume.resume_id, isouter=True)\
        .order_by(Application.application_date.desc())\
        .all()
    
    return render_template(
        'admin/user_applications.html',
        user=user,
        applications=applications,
        ApplicationStatus=ApplicationStatus
    )

@admin.route('/users/<int:user_id>/send-email', methods=['GET', 'POST'])
@login_required
def send_user_email(user_id):
    """Admin route to send email to a specific user"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return render_template('admin/send_email.html', user=user)
    
    # Handle POST request - send email
    subject = request.form.get('subject', '').strip()
    message = request.form.get('message', '').strip()
    email_type = request.form.get('email_type', 'general')  # general, interview, application
    
    if not subject or not message:
        flash('Subject and message are required.', 'warning')
        return render_template('admin/send_email.html', user=user, 
                             subject=subject, message=message, email_type=email_type)
    
    # Import send_email utility
    from app.utils import send_email
    
    # Prepare email data
    email_data = {
        'user': user,
        'message': message,
        'sender_name': f"{current_user.first_name} {current_user.last_name}" or current_user.username,
        'email_type': email_type
    }
    
    # Send email
    try:
        success = send_email(
            subject=f"[UMAT Job Portal] {subject}",
            recipients=[user.email],
            template='emails/admin_message.html',
            **email_data
        )
        
        if success:
            flash(f'Email sent successfully to {user.username} ({user.email})', 'success')
        else:
            flash('Email configuration not set up. Email preview saved for development.', 'info')
        
        return redirect(url_for('admin.list_users'))
    
    except Exception as e:
        flash(f'Error sending email: {str(e)}', 'danger')
        return render_template('admin/send_email.html', user=user, 
                             subject=subject, message=message, email_type=email_type)

@admin.route('/regenerate-job-matches', methods=['POST'])
@login_required
def regenerate_job_matches():
    """Admin utility to regenerate job matches for all applications"""
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        from app.resume_analyzer import ResumeAnalyzer
        from app.semantic_job_matcher import enhanced_job_matching
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get all applications with resumes
        applications = Application.query.join(Resume).join(Job).all()
        
        if not applications:
            flash('No applications with resumes found.', 'info')
            return redirect(url_for('admin.all_applications'))
        
        # Initialize analyzer
        resume_analyzer = ResumeAnalyzer()
        matches_created = 0
        matches_updated = 0
        
        for application in applications:
            try:
                if not application.resume or not application.resume.parsed_text:
                    continue
                
                # Check if JobMatch already exists
                existing_match = JobMatch.query.filter_by(
                    resume_id=application.resume_id,
                    job_id=application.job_id
                ).first()
                
                # Perform analysis
                analysis = resume_analyzer.analyze_resume(application.resume.parsed_text)
                
                # Prepare job data
                job_data = [{
                    "job_id": application.job.job_id,
                    "title": application.job.title,
                    "description": application.job.description,
                    "requirements": getattr(application.job, 'required_skills', '')
                }]
                
                # Generate matches
                matches = enhanced_job_matching(
                    resume_text=application.resume.parsed_text,
                    resume_analysis=analysis,
                    jobs_data=job_data
                )
                
                if matches and len(matches) > 0:
                    match = matches[0]
                    
                    if existing_match:
                        # Update existing match
                        existing_match.match_score = match["match_score"]
                        existing_match.match_details = match["match_details"]
                        existing_match.calculated_at = datetime.utcnow()
                        matches_updated += 1
                    else:
                        # Create new match
                        new_match = JobMatch(
                            resume_id=application.resume_id,
                            job_id=application.job_id,
                            match_score=match["match_score"],
                            match_details=match["match_details"]
                        )
                        db.session.add(new_match)
                        matches_created += 1
                
            except Exception as e:
                logger.error(f"Error processing application {application.application_id}: {e}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        flash(f'Job matching complete! Created {matches_created} new matches, updated {matches_updated} existing matches.', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error regenerating job matches: {e}", exc_info=True)
        flash('Error regenerating job matches. Please try again.', 'danger')
    
    return redirect(url_for('admin.all_applications'))
