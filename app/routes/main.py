from flask import Blueprint, render_template
from sqlalchemy import func
from app.models import db, User, Organization, Donation, utcnow
from app.services.lifecycle import check_and_expire_overdue_donations

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    check_and_expire_overdue_donations()
    
    # Calculate live platform statistics from database
    completed_donations = Donation.query.filter_by(status='Completed').all()
    total_completed = len(completed_donations)
    total_meals = sum(d.estimated_meals for d in completed_donations)
    total_co2 = sum(d.estimated_co2_saved for d in completed_donations)
    
    active_donors = User.query.filter_by(role='donor', account_status='active').count()
    active_recipients = User.query.filter_by(role='recipient', account_status='active').count()
    verified_recipients = Organization.query.filter_by(verification_status='verified').count()
    
    # Active available donations preview for public exploration
    available_donations = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.remaining_quantity > 0,
        Donation.pickup_deadline > utcnow()
    ).order_by(Donation.created_at.desc()).limit(6).all()

    return render_template(
        'index.html',
        total_completed=total_completed,
        total_meals=total_meals,
        total_co2=total_co2,
        active_donors=active_donors,
        active_recipients=active_recipients,
        verified_recipients=verified_recipients,
        available_donations=available_donations
    )

@main_bp.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@main_bp.route('/impact')
def impact():
    check_and_expire_overdue_donations()
    
    # Query database for measured and estimated analytics
    completed_donations = Donation.query.filter_by(status='Completed').all()
    all_donations = Donation.query.all()
    
    total_listings = len(all_donations)
    completed_count = len(completed_donations)
    cancelled_count = Donation.query.filter_by(status='Cancelled').count()
    expired_count = Donation.query.filter_by(status='Expired').count()
    active_count = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending', 'Accepted', 'Ready for Pickup'])
    ).count()

    total_meals_estimated = sum(d.estimated_meals for d in completed_donations)
    total_co2_avoided = sum(d.estimated_co2_saved for d in completed_donations)
    
    # Categories distribution
    cat_counts = (
        db.session.query(Donation.category, func.count(Donation.id))
        .group_by(Donation.category)
        .all()
    )
    categories_labels = [c[0] for c in cat_counts]
    categories_data = [c[1] for c in cat_counts]
    
    # Dietary breakdown
    diet_counts = (
        db.session.query(Donation.dietary_type, func.count(Donation.id))
        .group_by(Donation.dietary_type)
        .all()
    )
    dietary_labels = [d[0] for d in diet_counts]
    dietary_data = [d[1] for d in diet_counts]

    # Donors & Recipient counts
    donors_count = User.query.filter_by(role='donor').count()
    recipients_count = User.query.filter_by(role='recipient').count()

    return render_template(
        'analytics/impact.html',
        total_listings=total_listings,
        completed_count=completed_count,
        cancelled_count=cancelled_count,
        expired_count=expired_count,
        active_count=active_count,
        total_meals_estimated=total_meals_estimated,
        total_co2_avoided=total_co2_avoided,
        categories_labels=categories_labels,
        categories_data=categories_data,
        dietary_labels=dietary_labels,
        dietary_data=dietary_data,
        donors_count=donors_count,
        recipients_count=recipients_count
    )

@main_bp.route('/food-safety')
def food_safety():
    return render_template('safety/checklist.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')
