from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Organization, utcnow
from app.forms import LoginForm, RegistrationForm, ProfileForm
from app.services.notifications import create_notification

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_donor:
            return redirect(url_for('donor.dashboard'))
        else:
            return redirect(url_for('recipient.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data,
            phone=form.phone.data.strip(),
            account_status='active',
            created_at=utcnow()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # obtain user.id

        # Create linked organization record
        org = Organization(
            user_id=user.id,
            organization_name=form.organization_name.data.strip(),
            organization_type=form.organization_type.data,
            address=form.address.data.strip(),
            city=form.city.data.strip(),
            state=form.state.data.strip() if form.state.data else '',
            postal_code=form.postal_code.data.strip() if form.postal_code.data else '',
            verification_status='pending' if user.role == 'recipient' else 'verified',
            submitted_at=utcnow()
        )
        db.session.add(org)
        db.session.commit()

        # Welcome notification
        create_notification(
            user.id,
            "Welcome to FoodBridge!",
            "Thank you for joining our mission to eliminate food waste and feed communities.",
            link=url_for('auth.profile'),
            notification_type='system'
        )

        login_user(user)
        flash('Account created successfully! Welcome to FoodBridge.', 'success')

        if user.is_donor:
            return redirect(url_for('donor.dashboard'))
        elif user.is_recipient:
            flash('Your organization profile has been submitted for verification. You can browse donations and complete your verification details.', 'info')
            return redirect(url_for('recipient.dashboard'))
        else:
            return redirect(url_for('main.index'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        elif current_user.is_donor:
            return redirect(url_for('donor.dashboard'))
        else:
            return redirect(url_for('recipient.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been suspended by an administrator. Please contact support.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
                
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            elif user.is_donor:
                return redirect(url_for('donor.dashboard'))
            else:
                return redirect(url_for('recipient.dashboard'))
        else:
            flash('Invalid email address or password. Please try again.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    org = current_user.organization

    if request.method == 'GET' and org:
        form.address.data = org.address
        form.city.data = org.city

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None
        
        if org:
            if form.address.data:
                org.address = form.address.data.strip()
            if form.city.data:
                org.city = form.city.data.strip()
                
        db.session.commit()
        flash('Profile settings updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('profile/settings.html', form=form, org=org)
