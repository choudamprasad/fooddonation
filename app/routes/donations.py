from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app.models import db, Donation, DonationRequest, utcnow
from app.forms import DonationRequestForm, FOOD_CATEGORIES
from app.services.notifications import notify_donor_new_request
from app.services.lifecycle import check_and_expire_overdue_donations

donations_bp = Blueprint('donations', __name__, url_prefix='/donations')

@donations_bp.route('/<int:donation_id>', methods=['GET', 'POST'])
def detail(donation_id):
    check_and_expire_overdue_donations()
    
    donation = Donation.query.get_or_404(donation_id)
    form = DonationRequestForm()

    existing_request = None
    if current_user.is_authenticated and current_user.is_recipient:
        existing_request = DonationRequest.query.filter_by(
            donation_id=donation.id,
            recipient_id=current_user.id
        ).filter(DonationRequest.status.in_(['Pending', 'Accepted'])).first()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('Please log in as a recipient organization to request food donations.', 'info')
            return redirect(url_for('auth.login', next=request.url))

        if not current_user.is_recipient:
            flash('Only registered recipient organizations can request food donations.', 'warning')
            return redirect(url_for('donations.detail', donation_id=donation.id))

        if donation.is_expired:
            flash('This donation has passed its safe pickup deadline and is no longer available.', 'danger')
            return redirect(url_for('donations.detail', donation_id=donation.id))

        if donation.status not in ['Available', 'Request Pending'] or donation.remaining_quantity <= 0:
            flash('This donation is no longer available for requests.', 'danger')
            return redirect(url_for('donations.detail', donation_id=donation.id))

        if existing_request:
            flash(f"You already have an active request ({existing_request.status}) for this donation.", 'warning')
            return redirect(url_for('recipient.my_requests'))

        requested_qty = float(form.requested_quantity.data)
        if requested_qty > donation.remaining_quantity:
            flash(f"Requested quantity ({requested_qty} {donation.quantity_unit}) exceeds available quantity ({donation.remaining_quantity} {donation.quantity_unit}).", 'danger')
            return render_template('donations/detail.html', donation=donation, form=form, existing_request=existing_request)

        # Create request
        req = DonationRequest(
            donation_id=donation.id,
            recipient_id=current_user.id,
            requested_quantity=requested_qty,
            estimated_beneficiaries=form.estimated_beneficiaries.data,
            message=form.message.data.strip(),
            status='Pending',
            created_at=utcnow(),
            updated_at=utcnow()
        )
        db.session.add(req)

        # If currently Available, update to Request Pending
        if donation.status == 'Available':
            donation.status = 'Request Pending'
            donation.updated_at = utcnow()

        db.session.commit()

        # Notify donor
        notify_donor_new_request(donation, req)

        flash(f"Request for {requested_qty} {donation.quantity_unit} submitted successfully! The donor will review your request shortly.", 'success')
        return redirect(url_for('recipient.my_requests'))

    return render_template(
        'donations/detail.html',
        donation=donation,
        form=form,
        existing_request=existing_request
    )

@donations_bp.route('/map')
def map_view():
    check_and_expire_overdue_donations()
    
    city_filter = request.args.get('city', '').strip()
    category_filter = request.args.get('category', 'all')

    query = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.remaining_quantity > 0,
        Donation.pickup_deadline > utcnow()
    )

    if city_filter:
        query = query.filter(Donation.city.ilike(f"%{city_filter}%"))
    if category_filter != 'all':
        query = query.filter(Donation.category == category_filter)

    active_donations = query.all()
    available_cities = [c[0] for c in db.session.query(Donation.city).filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.pickup_deadline > utcnow()
    ).distinct().all()]

    return render_template(
        'donations/map.html',
        donations=active_donations,
        available_cities=available_cities,
        categories=FOOD_CATEGORIES,
        selected_city=city_filter,
        selected_category=category_filter
    )
