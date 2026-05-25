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
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            
            if user is None:
                flash("Invalid email or password", "danger")
                return redirect(url_for("auth.login"))

            password_ok = user.check_password(form.password.data)
            
            if not password_ok:
                flash("Invalid email or password", "danger")
                return redirect(url_for("auth.login"))
            
            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.first_name}!", "success")
            next_page = request.args.get("next")
            
            if user.is_admin():
                return redirect(next_page) if next_page else redirect(url_for("main.admin_dashboard"))
            else:
                if not user.candidate_profile:
                    try:
                        candidate = Candidate(candidate_id=user.id)
                        db.session.add(candidate)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Failed to create candidate profile on login for user {user.id}: {e}", exc_info=True)
                        flash("Error accessing profile. Please contact support.", "danger")
                        logout_user()
                        return redirect(url_for("auth.login"))
                return redirect(next_page) if next_page else redirect(url_for("main.user_profile"))
        except Exception as db_error:
            logger.error(f"Database error during login: {db_error}", exc_info=True)
            flash("System error during login. Please try again later.", "danger")
            return redirect(url_for("auth.login"))
        
    return render_template("auth/login.html", title="Sign In", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index")) 
