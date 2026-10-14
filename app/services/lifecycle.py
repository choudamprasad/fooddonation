from datetime import datetime
from app.models import db, Donation, DonationRequest, DonationStatusHistory, utcnow
from app.services.notifications import notify_recipient_request_status, notify_status_change_to_parties, create_notification

# Valid transitions map
VALID_TRANSITIONS = {
    'Available': ['Request Pending', 'Cancelled', 'Expired'],
    'Request Pending': ['Available', 'Accepted', 'Cancelled', 'Expired'],
    'Accepted': ['Ready for Pickup', 'Cancelled', 'Expired'],
    'Ready for Pickup': ['Collected', 'Cancelled', 'Expired'],
    'Collected': ['Completed', 'Cancelled'],
    'Completed': [],
    'Cancelled': [],
    'Expired': []
}

def can_transition(current_status, new_status):
    """Checks whether the requested state transition is valid."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed

def log_status_change(donation_id, previous_status, new_status, changed_by=None, notes=None):
    """Creates a persistent audit record of donation lifecycle change."""
    history = DonationStatusHistory(
        donation_id=donation_id,
        changed_by=changed_by,
        previous_status=previous_status,
        new_status=new_status,
        notes=notes,
        changed_at=utcnow()
    )
    db.session.add(history)
    return history

def transition_donation_status(donation, new_status, user_id=None, notes=None):
    """
    Safely transitions donation status if permitted, creates audit record,
    and dispatches relevant notifications.
    """
    if not can_transition(donation.status, new_status):
        return False, f"Invalid transition from '{donation.status}' to '{new_status}'."

    prev_status = donation.status
    donation.status = new_status
    donation.updated_at = utcnow()

    log_status_change(donation.id, prev_status, new_status, changed_by=user_id, notes=notes)
    db.session.commit()

    # Dispatches notifications to stakeholders
    notify_status_change_to_parties(donation, new_status, notes)
    return True, f"Status updated to '{new_status}'."

def check_and_expire_overdue_donations():
    """
    Scans for donations where pickup_deadline has passed and marks them Expired.
    Rejects any pending requests with clear reasoning.
    """
    now = utcnow()
    overdue_donations = Donation.query.filter(
        Donation.pickup_deadline <= now,
        Donation.status.in_(['Available', 'Request Pending'])
    ).all()

    count = 0
    for donation in overdue_donations:
        prev = donation.status
        donation.status = 'Expired'
        donation.updated_at = now
        
        log_status_change(
            donation.id,
            prev,
            'Expired',
            changed_by=None,
            notes='Auto-expired: Safe pickup deadline exceeded.'
        )

        # Notify donor
        create_notification(
            donation.donor_id,
            f"Listing Expired: {donation.title}",
            f"The safe pickup deadline for '{donation.title}' has passed. The listing is now marked as Expired to protect food safety.",
            link=f"/donor/manage-donations#donation-{donation.id}",
            notification_type='deadline'
        )

        # Reject any pending requests
        for req in donation.requests.filter_by(status='Pending').all():
            req.status = 'Rejected'
            req.rejection_reason = "Donation safe pickup deadline expired before acceptance."
            req.updated_at = now
            notify_recipient_request_status(req, 'Rejected', req.rejection_reason)

        count += 1

    if count > 0:
        db.session.commit()
    return count

def safe_accept_request(request_id, donor_user_id, pickup_notes=None):
    """
    Atomically accepts a recipient's donation request, adjusts remaining quantity,
    and manages donation status.
    """
    req = DonationRequest.query.get(request_id)
    if not req:
        return False, "Request not found."

    donation = req.donation
    if donation.donor_id != donor_user_id:
        return False, "Unauthorized: You are not the donor for this listing."

    if donation.status in ['Completed', 'Cancelled', 'Expired']:
        return False, f"Cannot accept request for a donation that is {donation.status}."

    if donation.is_expired:
        donation.status = 'Expired'
        db.session.commit()
        return False, "This donation has expired past its safe pickup deadline."

    if req.status != 'Pending':
        return False, f"Request is already '{req.status}'."

    # Validate quantity
    if req.requested_quantity > donation.remaining_quantity:
        return False, f"Requested quantity ({req.requested_quantity}) exceeds remaining available quantity ({donation.remaining_quantity})."

    # Accept the request
    req.status = 'Accepted'
    if pickup_notes:
        req.pickup_notes = pickup_notes
    req.updated_at = utcnow()

    # Decrement remaining quantity
    donation.remaining_quantity = max(0.0, donation.remaining_quantity - req.requested_quantity)
    
    # Update donation status
    prev_status = donation.status
    donation.status = 'Accepted'
    donation.updated_at = utcnow()

    log_status_change(
        donation.id,
        prev_status,
        'Accepted',
        changed_by=donor_user_id,
        notes=f"Accepted request from recipient #{req.recipient_id} for {req.requested_quantity} {donation.quantity_unit}."
    )

    # If remaining quantity is 0, auto-reject any other remaining pending requests
    if donation.remaining_quantity <= 0:
        other_pending = donation.requests.filter(
            DonationRequest.id != req.id,
            DonationRequest.status == 'Pending'
        ).all()
        for other in other_pending:
            other.status = 'Rejected'
            other.rejection_reason = "All available quantity has been allocated to an earlier accepted request."
            other.updated_at = utcnow()
            notify_recipient_request_status(other, 'Rejected', other.rejection_reason)

    db.session.commit()

    # Send in-app notification to accepted recipient
    notify_recipient_request_status(req, 'Accepted')

    return True, f"Request accepted successfully for {req.requested_quantity} {donation.quantity_unit}."

def safe_reject_request(request_id, donor_user_id, reason):
    """
    Rejects a request with an explicit reason. If no other active requests remain,
    restores donation status to Available.
    """
    req = DonationRequest.query.get(request_id)
    if not req:
        return False, "Request not found."

    donation = req.donation
    if donation.donor_id != donor_user_id:
        return False, "Unauthorized: You are not the donor for this listing."

    if req.status != 'Pending':
        return False, f"Cannot reject a request that is already '{req.status}'."

    req.status = 'Rejected'
    req.rejection_reason = reason or "Declined by donor."
    req.updated_at = utcnow()

    # Check if there are other pending or accepted requests
    active_accepted = donation.requests.filter_by(status='Accepted').count()
    active_pending = donation.requests.filter(DonationRequest.id != req.id, DonationRequest.status == 'Pending').count()

    if active_accepted == 0 and active_pending == 0 and donation.remaining_quantity > 0:
        if donation.status == 'Request Pending':
            prev_status = donation.status
            donation.status = 'Available'
            donation.updated_at = utcnow()
            log_status_change(donation.id, prev_status, 'Available', changed_by=donor_user_id, notes="All requests closed; returned to Available.")

    db.session.commit()
    notify_recipient_request_status(req, 'Rejected', req.rejection_reason)
    return True, "Request rejected."

def cancel_donation(donation_id, user_id, reason="Cancelled by user"):
    """
    Cancels a donation listing, records audit trail, and rejects any open requests.
    """
    donation = Donation.query.get(donation_id)
    if not donation:
        return False, "Donation not found."

    if donation.status in ['Completed', 'Cancelled']:
        return False, f"Cannot cancel donation that is already {donation.status}."

    prev_status = donation.status
    donation.status = 'Cancelled'
    donation.updated_at = utcnow()

    log_status_change(donation.id, prev_status, 'Cancelled', changed_by=user_id, notes=reason)

    # Cancel or reject pending/accepted requests
    for req in donation.requests.filter(DonationRequest.status.in_(['Pending', 'Accepted'])).all():
        req.status = 'Cancelled'
        req.rejection_reason = f"Donation was cancelled: {reason}"
        req.updated_at = utcnow()
        notify_recipient_request_status(req, 'Cancelled', req.rejection_reason)

    db.session.commit()
    return True, "Donation cancelled successfully."
