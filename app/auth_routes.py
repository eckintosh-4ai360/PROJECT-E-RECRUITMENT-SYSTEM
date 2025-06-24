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
            print(f"Saved profile image: {profile_image_path}")
        
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
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating account: {str(e)}", "danger")
            return redirect(url_for("main.register"))
    
    return render_template("auth/register.html", title="Register", form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index")) 