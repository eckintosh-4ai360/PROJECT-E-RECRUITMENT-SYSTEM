# Email Notification System for Job Portal
from flask import current_app
from app.utils import send_email
from app.models import User, Job, Application, ApplicationStatus, UserRole
import logging

logger = logging.getLogger(__name__)

def send_application_notification(application, notification_type, **kwargs):
    """
    Send email notifications for application events
    
    Args:
        application: Application instance
        notification_type: Type of notification (status_update, new_application, interview_scheduled, etc.)
        **kwargs: Additional context for email templates
    """
    try:
        candidate = User.query.get(application.candidate_id)
        job = Job.query.get(application.job_id)
        
        if not candidate or not job:
            logger.error(f"Missing candidate or job data for application {application.application_id}")
            return False

        # Map notification types to email templates and subjects
        notification_config = {
            'new_application': {
                'candidate_template': 'email/application_confirmation.html',
                'candidate_subject': f'Application Submitted: {job.title}',
                'admin_template': 'email/new_application_admin.html',
                'admin_subject': f'New Application: {job.title} - {candidate.first_name} {candidate.last_name}'
            },
            'status_update': {
                'candidate_template': 'email/application_status_update.html',
                'candidate_subject': f'Application Status Update: {job.title}',
                'admin_template': None,
                'admin_subject': None
            },
            'accepted': {
                'candidate_template': 'email/application_accepted.html',
                'candidate_subject': f'🎉 Congratulations! Your Application for {job.title} Has Been Accepted',
                'admin_template': None,
                'admin_subject': None
            },
            'rejected': {
                'candidate_template': 'email/application_rejected.html',
                'candidate_subject': f'Application Update: {job.title}',
                'admin_template': None,
                'admin_subject': None
            },
            'interview_scheduled': {
                'candidate_template': 'email/interview_scheduled.html',
                'candidate_subject': f'Interview Scheduled: {job.title}',
                'admin_template': 'email/interview_scheduled_admin.html',
                'admin_subject': f'Interview Scheduled: {job.title} - {candidate.first_name} {candidate.last_name}'
            },
            'under_review': {
                'candidate_template': 'email/application_under_review.html',
                'candidate_subject': f'Application Under Review: {job.title}',
                'admin_template': None,
                'admin_subject': None
            }
        }

        config = notification_config.get(notification_type)
        if not config:
            logger.error(f"Unknown notification type: {notification_type}")
            return False

        success = True

        # Send email to candidate
        if config['candidate_template'] and candidate.email:
            candidate_result = send_email(
                subject=config['candidate_subject'],
                recipients=[candidate.email],
                template=config['candidate_template'],
                user=candidate,
                job=job,
                application=application,
                **kwargs
            )
            if not candidate_result:
                success = False
                logger.error(f"Failed to send candidate notification for application {application.application_id}")

        # Send email to admins if configured
        if config['admin_template']:
            admin_users = User.query.filter_by(role=UserRole.admin).all()
            admin_emails = [admin.email for admin in admin_users if admin.email]
            
            if admin_emails:
                admin_result = send_email(
                    subject=config['admin_subject'],
                    recipients=admin_emails,
                    template=config['admin_template'],
                    candidate=candidate,
                    user=candidate,  # For backward compatibility
                    job=job,
                    application=application,
                    **kwargs
                )
                if not admin_result:
                    success = False
                    logger.error(f"Failed to send admin notification for application {application.application_id}")

        return success

    except Exception as e:
        logger.error(f"Error sending notification for application {application.application_id}: {e}", exc_info=True)
        return False


def send_application_status_change_notification(application, old_status, new_status, feedback=None):
    """
    Send notification when application status changes
    """
    try:
        # Determine notification type based on new status
        notification_type = 'status_update'
        if new_status == ApplicationStatus.accepted:
            notification_type = 'accepted'
        elif new_status == ApplicationStatus.rejected:
            notification_type = 'rejected'
        elif new_status == ApplicationStatus.under_review:
            notification_type = 'under_review'
        elif new_status == ApplicationStatus.interview_scheduled:
            notification_type = 'interview_scheduled'

        return send_application_notification(
            application,
            notification_type,
            old_status=old_status,
            new_status=new_status,
            feedback=feedback
        )

    except Exception as e:
        logger.error(f"Error sending status change notification: {e}", exc_info=True)
        return False


def send_daily_admin_summary():
    """
    Send daily summary of applications to admins
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Get today's stats
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Get application counts
        new_applications_today = Application.query.filter(
            func.date(Application.application_date) == today
        ).count()
        
        pending_applications = Application.query.filter_by(
            status=ApplicationStatus.submitted
        ).count()
        
        under_review = Application.query.filter_by(
            status=ApplicationStatus.under_review
        ).count()
        
        # Send to admins
        admin_users = User.query.filter_by(role=UserRole.admin).all()
        admin_emails = [admin.email for admin in admin_users if admin.email]
        
        if admin_emails and (new_applications_today > 0 or pending_applications > 0):
            return send_email(
                subject=f"Daily Applications Summary - {today.strftime('%B %d, %Y')}",
                recipients=admin_emails,
                template="email/daily_admin_summary.html",
                new_applications_today=new_applications_today,
                pending_applications=pending_applications,
                under_review=under_review,
                summary_date=today
            )
        
        return True

    except Exception as e:
        logger.error(f"Error sending daily admin summary: {e}", exc_info=True)
        return False
