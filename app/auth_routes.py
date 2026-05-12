from flask import Blueprint, render_template, redirect, url_for, flash, request
from app import db
from app.models import User, UserRole, Candidate
from app.forms import RegistrationForm, LoginForm
from flask_login import login_user, logout_user, current_user
from app.utils import save_profile_image
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Handle profile image upload
        profile_image_path = None
        if form.profile_image.data:
            profile_image_path = save_profile_image(form.profile_image.data)
            logger.info(f"Saved profile image: {profile_image_path}")
        
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
                candidate = Candidate(
                    candidate_id=user.id,
                    phone_number=form.phone_number.data
                )
                db.session.add(candidate)
                db.session.commit()
            
            flash("Your account has been created! You can now log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "danger")
            return redirect(url_for("auth.register"))
    
    return render_template("auth/register.html", title="Register", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    logger.info("\n======== LOGIN ROUTE ACCESSED ========")
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    form = LoginForm()
    
    # Check if we can query the database
    try:
        user_count = User.query.count()
        logger.info(f"===DEBUG=== Database connection OK. Found {user_count} users")
        
        # Get all users for debugging
        all_users = User.query.all()
        for user in all_users:
            logger.info(f"===DEBUG=== User in DB: {user.email}, ID: {user.id}, Role: {user.role}, Hash: {user.password_hash}")
        
    except Exception as e:
        logger.error(f"===DEBUG=== Database error: {e}")
    
    if form.validate_on_submit():
        logger.info(f"\n===DEBUG=== Form validated")
        logger.info(f"===DEBUG=== Login attempt for email: {form.email.data}")
        logger.info(f"===DEBUG=== Password length: {len(form.password.data)}")
        logger.info(f"===DEBUG=== First 3 chars of password: {form.password.data[:3]}")
        
        # Try a direct database query
        try:
            # Find the specific user by email
            user = User.query.filter_by(email=form.email.data).first()
            
            if user is None:
                logger.info(f"===DEBUG=== User with email '{form.email.data}' not found in database")
                flash("Invalid email or password", "danger")
                return redirect(url_for("auth.login"))
            
            logger.info(f"===DEBUG=== Found user: {user.email}, ID: {user.id}")
            logger.info(f"===DEBUG=== User role: {user.role}")
            logger.info(f"===DEBUG=== Stored hash: {user.password_hash}")
            
            # Check password
            password_ok = user.check_password(form.password.data)
            logger.info(f"===DEBUG=== Password check result: {password_ok}")
            
            if not password_ok:
                logger.info("===DEBUG=== Password verification failed")
                flash("Invalid email or password", "danger")
                return redirect(url_for("auth.login"))
            
            # Password verified, log in user
            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.first_name}!", "success")
            next_page = request.args.get("next")
            
            # Print user admin status for debug
            logger.info(f"===DEBUG=== User.is_admin() returns: {user.is_admin()}")
            logger.info(f"===DEBUG=== User.role == UserRole.admin: {user.role == UserRole.admin}")
            
            if user.is_admin():
                logger.info("===DEBUG=== User is admin, redirecting to admin dashboard")
                return redirect(next_page) if next_page else redirect(url_for("main.admin_dashboard"))
            else:
                logger.info("===DEBUG=== User is not admin, redirecting to user profile")
                # Ensure candidate profile exists
                if not user.candidate_profile:
                    try:
                        logger.info("===DEBUG=== Creating candidate profile")
                        candidate = Candidate(candidate_id=user.id)
                        db.session.add(candidate)
                        db.session.commit()
                        logger.info("===DEBUG=== Candidate profile created successfully")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"===DEBUG=== Failed to create candidate profile: {e}")
                        logger.error(f"Failed to create candidate profile on login for user {user.id}: {e}", exc_info=True)
                        flash("Error accessing profile. Please contact support.", "danger")
                        logout_user() # Log out user if profile creation fails
                        return redirect(url_for("auth.login"))
                return redirect(next_page) if next_page else redirect(url_for("main.user_profile"))
        except Exception as db_error:
            logger.error(f"===DEBUG=== Database error during login: {db_error}")
            flash("System error during login. Please try again later.", "danger")
            return redirect(url_for("auth.login"))
    
    # If form validation failed, show the form errors
    if form.errors:
        logger.info(f"===DEBUG=== Form validation errors: {form.errors}")
        
    return render_template("auth/login.html", title="Sign In", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index")) 