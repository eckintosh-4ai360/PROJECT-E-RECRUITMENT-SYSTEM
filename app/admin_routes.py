from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, send_from_directory
from flask_login import login_required, current_user
from app.models import User, Job, Application, Resume, ApplicationStatus
from app import db
import os
from werkzeug.utils import secure_filename
from app.utils import show_pdf
import logging

admin = Blueprint('admin', __name__)

@admin.route('/users')
@login_required
def list_users():
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

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
    
    # Base query with joins to get all necessary data
    query = Application.query\
        .join(User, Application.candidate_id == User.id)\
        .join(Job, Application.job_id == Job.job_id)\
        .join(Resume, Application.resume_id == Resume.resume_id, isouter=True)
    
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
    
    # Get all unique departments for filter dropdown
    departments = db.session.query(Job.department).distinct().all()
    departments = [dept[0] for dept in departments if dept[0]]
    
    # Get all applications with filters and order by date
    applications = query.order_by(Application.application_date.desc()).all()
    
    return render_template(
        'admin/all_applications.html',
        applications=applications,
        departments=departments,
        ApplicationStatus=ApplicationStatus
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