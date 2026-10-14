import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app.models import db, Donation, DonationRequest, Organization, utcnow
from app.forms import OrganizationVerificationForm, FOOD_CATEGORIES, DIETARY_TYPES
from app.routes.decorators import recipient_required
from app.services.matching import rank_donations_for_recipient
from app.services.lifecycle import (
    transition_donation_status, log_status_change, check_and_expire_overdue_donations
)
from app.services.notifications import notify_status_change_to_parties, create_notification

recipient_bp = Blueprint('recipient', __name__, url_prefix='/recipient')

@recipient_bp.route('/dashboard')
@login_required
@recipient_required
def dashboard():
    check_and_expire_overdue_donations()
    
    # Recipient stats
    requests_query = DonationRequest.query.filter_by(recipient_id=current_user.id)
    active_requests_count = requests_query.filter(DonationRequest.status.in_(['Pending', 'Accepted'])).count()
    awaiting_pickup_count = (
        requests_query
        .join(Donation)
        .filter(DonationRequest.status == 'Accepted', Donation.status.in_(['Accepted', 'Ready for Pickup']))
        .count()
    )
    completed_requests_count = requests_query.filter_by(status='Completed').count()
    
    # Calculate meals distributed
    completed_requests = requests_query.filter_by(status='Completed').all()
    total_meals_distributed = sum(r.estimated_beneficiaries for r in completed_requests)
    
    # Top smart matches for recipient
    smart_matches = rank_donations_for_recipient(current_user, limit=4)
    
    # Active requests list
    active_requests = (
        requests_query
        .order_by(DonationRequest.updated_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'recipient/dashboard.html',
        active_requests_count=active_requests_count,
        awaiting_pickup_count=awaiting_pickup_count,
        completed_requests_count=completed_requests_count,
        total_meals_distributed=total_meals_distributed,
        smart_matches=smart_matches,
        active_requests=active_requests,
        org=current_user.organization
    )

@recipient_bp.route('/available-donations')
@login_required
@recipient_required
def available_donations():
    check_and_expire_overdue_donations()
    
    category = request.args.get('category', 'all')
    dietary = request.args.get('dietary', 'all')
    city = request.args.get('city', '').strip()
    search = request.args.get('search', '').strip().lower()
    sort_by = request.args.get('sort', 'match')  # 'match', 'urgency', 'quantity'

    ranked = rank_donations_for_recipient(
        current_user,
        limit=None,
        category_filter=category if category != 'all' else None,
        dietary_filter=dietary if dietary != 'all' else None,
        city_filter=city if city else None
    )

    # Optional text search filter
    if search:
        ranked = [r for r in ranked if (
            search in r['donation'].title.lower() or
            search in r['donation'].description.lower() or
            search in r['donation'].city.lower()
        )]

    # Sorting
    if sort_by == 'urgency':
        ranked.sort(key=lambda x: x['donation'].hours_remaining)
    elif sort_by == 'quantity':
        ranked.sort(key=lambda x: x['donation'].remaining_quantity, reverse=True)
    # default sort_by == 'match' is already sorted descending by match_score

    # Unique cities for filter dropdown
    available_cities = [c[0] for c in db.session.query(Donation.city).filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.pickup_deadline > utcnow()
    ).distinct().all()]

    return render_template(
        'recipient/available_donations.html',
        recommendations=ranked,
        categories=FOOD_CATEGORIES,
        dietary_types=DIETARY_TYPES,
        selected_category=category,
        selected_dietary=dietary,
        selected_city=city,
        search_query=search,
        selected_sort=sort_by,
        available_cities=available_cities,
        org=current_user.organization
    )

@recipient_bp.route('/my-requests')
@login_required
@recipient_required
def my_requests():
    check_and_expire_overdue_donations()
    
    status_filter = request.args.get('status', 'all')
    query = DonationRequest.query.filter_by(recipient_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
        
    requests_list = query.order_by(DonationRequest.created_at.desc()).all()

    return render_template(
        'recipient/my_requests.html',
        requests_list=requests_list,
        status_filter=status_filter
    )

@recipient_bp.route('/request/<int:request_id>/confirm-collection', methods=['POST'])
@login_required
@recipient_required
def confirm_collection(request_id):
    req = DonationRequest.query.get_or_404(request_id)
    if req.recipient_id != current_user.id and not current_user.is_admin:
        abort(403)

    if req.status != 'Accepted':
        flash('Only accepted donations can be confirmed for collection.', 'warning')
        return redirect(url_for('recipient.my_requests'))

    req.status = 'Collected'
    req.updated_at = utcnow()

    donation = req.donation
    donation.status = 'Collected'
    donation.updated_at = utcnow()

    log_status_change(
        donation.id,
        'Ready for Pickup',
        'Collected',
        changed_by=current_user.id,
        notes=f"Food safely collected by recipient {current_user.name}."
    )
    db.session.commit()

    notify_status_change_to_parties(donation, 'Collected', "Recipient has confirmed pickup of food.")
    flash('Food collection confirmed! Please ensure safe transport and storage.', 'success')
    return redirect(url_for('recipient.my_requests'))

@recipient_bp.route('/request/<int:request_id>/confirm-completed', methods=['POST'])
@login_required
@recipient_required
def confirm_completed(request_id):
    req = DonationRequest.query.get_or_404(request_id)
    if req.recipient_id != current_user.id and not current_user.is_admin:
        abort(403)

    if req.status not in ['Collected', 'Accepted']:
        flash('Cannot mark this request as completed in its current state.', 'warning')
        return redirect(url_for('recipient.my_requests'))

    req.status = 'Completed'
    req.updated_at = utcnow()

    donation = req.donation
    donation.status = 'Completed'
    donation.updated_at = utcnow()

    log_status_change(
        donation.id,
        'Collected',
        'Completed',
        changed_by=current_user.id,
        notes=f"Food redistribution completed by {current_user.name}. Impact recorded!"
    )
    db.session.commit()

    notify_status_change_to_parties(donation, 'Completed', "Food redistribution successfully completed!")
    flash(f'Awesome work! Distribution marked as completed. Impact statistics have been updated.', 'success')
    return redirect(url_for('recipient.my_requests'))

@recipient_bp.route('/request/<int:request_id>/cancel', methods=['POST'])
@login_required
@recipient_required
def cancel_request(request_id):
    req = DonationRequest.query.get_or_404(request_id)
    if req.recipient_id != current_user.id and not current_user.is_admin:
        abort(403)

    if req.status != 'Pending':
        flash('Only pending requests can be cancelled.', 'warning')
        return redirect(url_for('recipient.my_requests'))

    req.status = 'Cancelled'
    req.rejection_reason = "Cancelled by recipient organization."
    req.updated_at = utcnow()

    donation = req.donation
    # If no other requests pending, return to Available
    if donation.requests.filter_by(status='Pending').count() == 0 and donation.status == 'Request Pending':
        donation.status = 'Available'

    db.session.commit()
    flash('Your request has been cancelled.', 'info')
    return redirect(url_for('recipient.my_requests'))

@recipient_bp.route('/verification', methods=['GET', 'POST'])
@login_required
@recipient_required
def verification():
    org = current_user.organization
    form = OrganizationVerificationForm(obj=org)

    if form.validate_on_submit():
        if not org:
            org = Organization(user_id=current_user.id)
            db.session.add(org)

        org.organization_name = form.organization_name.data.strip()
        org.organization_type = form.organization_type.data
        org.registration_number = form.registration_number.data.strip()
        org.contact_person = form.contact_person.data.strip()
        org.address = form.address.data.strip()
        org.city = form.city.data.strip()
        org.state = form.state.data.strip() if form.state.data else ''
        org.postal_code = form.postal_code.data.strip() if form.postal_code.data else ''
        org.capacity_servings = form.capacity_servings.data
        org.preferred_categories = form.preferred_categories.data.strip() if form.preferred_categories.data else 'Cooked Meals'
        org.verification_notes = form.verification_notes.data.strip() if form.verification_notes.data else ''
        org.verification_status = 'pending'
        org.submitted_at = utcnow()

        if form.verification_document.data:
            doc = form.verification_document.data
            safe_name = secure_filename(doc.filename)
            unique_name = f"doc_{uuid.uuid4().hex[:8]}_{safe_name}"
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            doc.save(os.path.join(upload_dir, unique_name))
            org.verification_document = unique_name

        db.session.commit()
        flash('Verification application submitted! An administrator will review your documents promptly.', 'success')
        return redirect(url_for('recipient.dashboard'))

    return render_template('recipient/verification.html', form=form, org=org)
