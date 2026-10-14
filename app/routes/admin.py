from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app.models import db, User, Organization, Donation, DonationRequest, DonationStatusHistory, utcnow
from app.routes.decorators import admin_required
from app.services.lifecycle import cancel_donation as cancel_donation_service, log_status_change, check_and_expire_overdue_donations
from app.services.notifications import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    check_and_expire_overdue_donations()
    
    total_users = User.query.count()
    donors_count = User.query.filter_by(role='donor').count()
    recipients_count = User.query.filter_by(role='recipient').count()
    
    pending_verifications = Organization.query.filter_by(verification_status='pending').count()
    
    active_donations_count = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending', 'Accepted', 'Ready for Pickup'])
    ).count()
    completed_donations_count = Donation.query.filter_by(status='Completed').count()
    cancelled_expired_count = Donation.query.filter(
        Donation.status.in_(['Cancelled', 'Expired'])
    ).count()

    # Recent pending verifications
    pending_orgs = Organization.query.filter_by(verification_status='pending').order_by(Organization.submitted_at.desc()).limit(5).all()

    # Recent status history logs
    recent_logs = DonationStatusHistory.query.order_by(DonationStatusHistory.changed_at.desc()).limit(10).all()

    # Total meals rescued
    completed_donations = Donation.query.filter_by(status='Completed').all()
    total_meals_rescued = sum(d.estimated_meals for d in completed_donations)

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        donors_count=donors_count,
        recipients_count=recipients_count,
        pending_verifications=pending_verifications,
        active_donations_count=active_donations_count,
        completed_donations_count=completed_donations_count,
        cancelled_expired_count=cancelled_expired_count,
        total_meals_rescued=total_meals_rescued,
        pending_orgs=pending_orgs,
        recent_logs=recent_logs
    )

@admin_bp.route('/verifications')
@login_required
@admin_required
def verifications():
    status_filter = request.args.get('status', 'pending')
    query = Organization.query
    if status_filter != 'all':
        query = query.filter_by(verification_status=status_filter)
    orgs = query.order_by(Organization.submitted_at.desc()).all()
    return render_template('admin/verifications.html', orgs=orgs, status_filter=status_filter)

@admin_bp.route('/verification/<int:org_id>/<string:action>', methods=['POST'])
@login_required
@admin_required
def process_verification(org_id, action):
    org = Organization.query.get_or_404(org_id)
    notes = request.form.get('notes', '').strip()

    if action == 'approve':
        org.verification_status = 'verified'
        org.verified_at = utcnow()
        org.verification_notes = notes or "Application verified by administrator."
        flash(f"Organization '{org.organization_name}' has been verified successfully.", 'success')
        
        create_notification(
            org.user_id,
            "Organization Verified!",
            f"Congratulations! Your organization '{org.organization_name}' has been officially verified on FoodBridge.",
            link=url_for('recipient.available_donations'),
            notification_type='verification'
        )
    elif action == 'reject':
        org.verification_status = 'rejected'
        org.verification_notes = notes or "Application declined. Please provide valid documentation."
        flash(f"Organization '{org.organization_name}' verification has been rejected.", 'warning')
        
        create_notification(
            org.user_id,
            "Verification Update",
            f"Your organization verification request was not approved. Reason: {org.verification_notes}",
            link=url_for('recipient.verification'),
            notification_type='verification'
        )
    else:
        abort(400)

    db.session.commit()
    return redirect(url_for('admin.verifications'))

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = request.args.get('role', 'all')
    query = User.query
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)
    users_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users_list, role_filter=role_filter)

@admin_bp.route('/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot suspend your own administrator account.', 'danger')
        return redirect(url_for('admin.users'))

    if user.account_status == 'active':
        user.account_status = 'suspended'
        flash(f"User {user.email} has been suspended.", 'warning')
    else:
        user.account_status = 'active'
        flash(f"User {user.email} has been reactivated.", 'success')

    db.session.commit()
    return redirect(url_for('admin.users'))

@admin_bp.route('/moderation')
@login_required
@admin_required
def moderation():
    status_filter = request.args.get('status', 'all')
    query = Donation.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    donations = query.order_by(Donation.created_at.desc()).all()
    return render_template('admin/moderation.html', donations=donations, status_filter=status_filter)

@admin_bp.route('/donation/<int:donation_id>/remove', methods=['POST'])
@login_required
@admin_required
def remove_donation(donation_id):
    reason = request.form.get('reason', 'Removed by administrator due to moderation guidelines.').strip()
    success, msg = cancel_donation_service(donation_id, current_user.id, reason=f"Admin Moderation: {reason}")
    if success:
        flash(f"Donation #{donation_id} removed by moderation.", 'info')
    else:
        flash(msg, 'danger')
    return redirect(url_for('admin.moderation'))

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    logs = DonationStatusHistory.query.order_by(DonationStatusHistory.changed_at.desc()).limit(100).all()
    return render_template('admin/audit_logs.html', logs=logs)
