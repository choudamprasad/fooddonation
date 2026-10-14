import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models import db, Donation, DonationRequest, DonationStatusHistory, utcnow
from app.forms import DonationForm, CancelDonationForm, RejectRequestForm
from app.routes.decorators import donor_required
from app.services.lifecycle import (
    safe_accept_request, safe_reject_request, transition_donation_status,
    cancel_donation as cancel_donation_service, log_status_change, check_and_expire_overdue_donations
)

donor_bp = Blueprint('donor', __name__, url_prefix='/donor')

def allowed_file(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in current_app.config['ALLOWED_EXTENSIONS']

@donor_bp.route('/dashboard')
@login_required
@donor_required
def dashboard():
    check_and_expire_overdue_donations()
    
    donations_query = Donation.query.filter_by(donor_id=current_user.id)
    total_donations = donations_query.count()
    
    # Counts
    available_count = donations_query.filter_by(status='Available').count()
    pending_requests_count = (
        DonationRequest.query
        .join(Donation)
        .filter(Donation.donor_id == current_user.id, DonationRequest.status == 'Pending')
        .count()
    )
    accepted_count = donations_query.filter(Donation.status.in_(['Accepted', 'Ready for Pickup'])).count()
    completed_count = donations_query.filter_by(status='Completed').count()
    
    # Recent donations
    recent_donations = donations_query.order_by(Donation.created_at.desc()).limit(5).all()
    
    # Recent requests needing attention
    pending_requests = (
        DonationRequest.query
        .join(Donation)
        .filter(Donation.donor_id == current_user.id, DonationRequest.status == 'Pending')
        .order_by(DonationRequest.created_at.desc())
        .limit(5)
        .all()
    )
    
    # Estimated impact
    completed_donations = donations_query.filter_by(status='Completed').all()
    total_meals_rescued = sum(d.estimated_meals for d in completed_donations)
    total_co2_avoided = sum(d.estimated_co2_saved for d in completed_donations)

    return render_template(
        'donor/dashboard.html',
        total_donations=total_donations,
        available_count=available_count,
        pending_requests_count=pending_requests_count,
        accepted_count=accepted_count,
        completed_count=completed_count,
        recent_donations=recent_donations,
        pending_requests=pending_requests,
        total_meals_rescued=total_meals_rescued,
        total_co2_avoided=total_co2_avoided
    )

@donor_bp.route('/create-donation', methods=['GET', 'POST'])
@login_required
@donor_required
def create_donation():
    form = DonationForm()
    
    # Pre-fill address and phone from organization profile if available
    if request.method == 'GET' and current_user.organization:
        org = current_user.organization
        form.address.data = org.address
        form.city.data = org.city
        form.latitude.data = org.latitude
        form.longitude.data = org.longitude
        form.donor_phone.data = current_user.phone

    if form.validate_on_submit():
        filename = None
        if form.image.data:
            file = form.image.data
            if allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex[:10]}_{safe_name}"
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, unique_filename))
                filename = unique_filename

        donation = Donation(
            donor_id=current_user.id,
            title=form.title.data.strip(),
            category=form.category.data,
            dietary_type=form.dietary_type.data,
            quantity=float(form.quantity.data),
            remaining_quantity=float(form.quantity.data),
            quantity_unit=form.quantity_unit.data,
            prepared_at=form.prepared_at.data,
            pickup_deadline=form.pickup_deadline.data,
            storage_information=form.storage_information.data,
            allergen_information=form.allergen_information.data.strip() if form.allergen_information.data else 'None reported',
            packaging_details=form.packaging_details.data.strip(),
            description=form.description.data.strip(),
            address=form.address.data.strip(),
            city=form.city.data.strip(),
            latitude=form.latitude.data if form.latitude.data else None,
            longitude=form.longitude.data if form.longitude.data else None,
            image_filename=filename,
            contact_preference=form.contact_preference.data,
            donor_phone=form.donor_phone.data.strip() if form.donor_phone.data else current_user.phone,
            status='Available',
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.session.add(donation)
        db.session.flush()

        # Audit history
        log_status_change(
            donation.id,
            'Draft',
            'Available',
            changed_by=current_user.id,
            notes='Listing published by donor.'
        )
        db.session.commit()

        flash(f"Donation '{donation.title}' published successfully! Recipient NGOs will now be able to discover and request it.", 'success')
        return redirect(url_for('donor.manage_donations'))

    return render_template('donor/create_donation.html', form=form)

@donor_bp.route('/manage-donations')
@login_required
@donor_required
def manage_donations():
    check_and_expire_overdue_donations()
    
    status_filter = request.args.get('status', 'all')
    query = Donation.query.filter_by(donor_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
        
    donations = query.order_by(Donation.created_at.desc()).all()
    cancel_form = CancelDonationForm()
    reject_form = RejectRequestForm()

    return render_template(
        'donor/manage_donations.html',
        donations=donations,
        status_filter=status_filter,
        cancel_form=cancel_form,
        reject_form=reject_form
    )

@donor_bp.route('/request/<int:request_id>/accept', methods=['POST'])
@login_required
@donor_required
def accept_request(request_id):
    pickup_notes = request.form.get('pickup_notes', '').strip()
    success, msg = safe_accept_request(request_id, current_user.id, pickup_notes=pickup_notes)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.manage_donations'))

@donor_bp.route('/request/<int:request_id>/reject', methods=['POST'])
@login_required
@donor_required
def reject_request(request_id):
    reason = request.form.get('reason', 'Declined by donor').strip()
    success, msg = safe_reject_request(request_id, current_user.id, reason=reason)
    if success:
        flash(msg, 'info')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.manage_donations'))

@donor_bp.route('/donation/<int:donation_id>/status/<string:new_status>', methods=['POST'])
@login_required
@donor_required
def update_status(donation_id, new_status):
    donation = Donation.query.get_or_404(donation_id)
    if donation.donor_id != current_user.id and not current_user.is_admin:
        abort(403)

    notes = request.form.get('notes', f"Status updated to {new_status} by donor.")
    success, msg = transition_donation_status(donation, new_status, user_id=current_user.id, notes=notes)
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.manage_donations'))

@donor_bp.route('/donation/<int:donation_id>/cancel', methods=['POST'])
@login_required
@donor_required
def cancel_donation_route(donation_id):
    donation = Donation.query.get_or_404(donation_id)
    if donation.donor_id != current_user.id and not current_user.is_admin:
        abort(403)

    reason = request.form.get('reason', 'Cancelled by donor.').strip()
    success, msg = cancel_donation_service(donation_id, current_user.id, reason=reason)
    if success:
        flash('Donation has been cancelled.', 'info')
    else:
        flash(msg, 'danger')
    return redirect(url_for('donor.manage_donations'))
