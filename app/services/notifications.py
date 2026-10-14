from app.models import db, Notification, utcnow

def create_notification(user_id, title, message, link=None, notification_type='system'):
    """Creates and persists an in-app notification."""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        link=link,
        notification_type=notification_type,
        created_at=utcnow()
    )
    db.session.add(notif)
    db.session.commit()
    return notif

def notify_donor_new_request(donation, request_obj):
    """Notifies donor that an organization has requested their donation."""
    org_name = request_obj.recipient.organization.organization_name if request_obj.recipient.organization else request_obj.recipient.name
    title = f"New Request: {donation.title}"
    msg = (f"{org_name} has requested {request_obj.requested_quantity} {donation.quantity_unit} "
           f"of '{donation.title}'. Target beneficiaries: {request_obj.estimated_beneficiaries} people.")
    link = f"/donor/manage-donations#donation-{donation.id}"
    return create_notification(donation.donor_id, title, msg, link=link, notification_type='request')

def notify_recipient_request_status(request_obj, new_status, reason=None):
    """Notifies recipient when their request is accepted or rejected."""
    donation = request_obj.donation
    if new_status == 'Accepted':
        title = f"Request Accepted: {donation.title}"
        msg = (f"Great news! Your request for {request_obj.requested_quantity} {donation.quantity_unit} "
               f"of '{donation.title}' has been accepted. Pickup Address: {donation.address}, {donation.city}.")
        link = f"/recipient/my-requests"
    elif new_status == 'Rejected':
        title = f"Request Declined: {donation.title}"
        reason_text = f" Reason: {reason}" if reason else ""
        msg = f"Your request for '{donation.title}' could not be accepted.{reason_text}"
        link = f"/recipient/my-requests"
    else:
        title = f"Request Update: {donation.title}"
        msg = f"Status of your request for '{donation.title}' is now: {new_status}."
        link = f"/recipient/my-requests"
        
    return create_notification(request_obj.recipient_id, title, msg, link=link, notification_type='status_change')

def notify_status_change_to_parties(donation, new_status, notes=None):
    """Notifies both donor and active accepted recipients of lifecycle status change."""
    notes_str = f" Notes: {notes}" if notes else ""
    
    # Notify accepted recipients
    accepted_requests = donation.requests.filter_by(status='Accepted').all()
    for req in accepted_requests:
        title = f"Donation Status: {new_status} ({donation.title})"
        msg = f"Donation '{donation.title}' is now marked as '{new_status}'.{notes_str}"
        create_notification(req.recipient_id, title, msg, link="/recipient/my-requests", notification_type='status_change')
        
    # Notify donor
    title = f"Status Updated: {new_status} ({donation.title})"
    msg = f"Your donation '{donation.title}' status changed to '{new_status}'.{notes_str}"
    create_notification(donation.donor_id, title, msg, link=f"/donor/manage-donations#donation-{donation.id}", notification_type='status_change')

def mark_notification_as_read(notification_id, user_id):
    """Marks a single notification as read if it belongs to user."""
    notif = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False

def mark_all_notifications_read(user_id):
    """Marks all unread notifications for a user as read."""
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
