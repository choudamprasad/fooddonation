from datetime import timedelta
from app.models import Donation, DonationRequest, DonationStatusHistory, Notification, utcnow
from app.services.lifecycle import (
    safe_accept_request, safe_reject_request, check_and_expire_overdue_donations
)

def test_safe_accept_request_and_quantity_decrement(app, test_donor, test_recipient, test_donation):
    """Test that accepting a request safely decrements remaining quantity and updates states."""
    with app.app_context():
        # Create a pending request
        req = DonationRequest(
            donation_id=test_donation,
            recipient_id=test_recipient,
            requested_quantity=12.0,
            estimated_beneficiaries=30,
            message="Test accept plan.",
            status="Pending"
        )
        db = app.extensions['sqlalchemy']
        db.session.add(req)
        db.session.commit()
        req_id = req.id

        # Accept request as donor
        success, msg = safe_accept_request(req_id, test_donor, pickup_notes="Ring rear dock buzzer")
        assert success is True

        # Check request and donation states
        req_after = DonationRequest.query.get(req_id)
        assert req_after.status == 'Accepted'
        assert req_after.pickup_notes == 'Ring rear dock buzzer'

        donation = Donation.query.get(test_donation)
        assert donation.status == 'Accepted'
        assert donation.remaining_quantity == 8.0  # 20.0 - 12.0 = 8.0

        # Check status history
        history = DonationStatusHistory.query.filter_by(donation_id=test_donation, new_status='Accepted').first()
        assert history is not None

        # Check recipient notification
        notif = Notification.query.filter_by(user_id=test_recipient, notification_type='status_change').first()
        assert notif is not None
        assert 'Accepted' in notif.title

def test_accept_exhausts_quantity_auto_rejects_other_pending(app, test_donor, test_recipient, test_donation):
    """Test that when a request allocates all remaining quantity, other pending requests are rejected."""
    with app.app_context():
        db = app.extensions['sqlalchemy']
        # Request 1: takes entire 20.0 kg
        req1 = DonationRequest(
            donation_id=test_donation,
            recipient_id=test_recipient,
            requested_quantity=20.0,
            estimated_beneficiaries=50,
            message="Requesting full batch.",
            status="Pending"
        )
        # Request 2: another pending request
        req2 = DonationRequest(
            donation_id=test_donation,
            recipient_id=test_recipient,
            requested_quantity=5.0,
            estimated_beneficiaries=10,
            message="Smaller batch request.",
            status="Pending"
        )
        db.session.add_all([req1, req2])
        db.session.commit()
        r1_id, r2_id = req1.id, req2.id

        success, _ = safe_accept_request(r1_id, test_donor)
        assert success is True

        donation = Donation.query.get(test_donation)
        assert donation.remaining_quantity == 0.0

        # req2 should now be automatically Rejected because no quantity remains
        r2_after = DonationRequest.query.get(r2_id)
        assert r2_after.status == 'Rejected'
        assert 'allocated to an earlier accepted request' in r2_after.rejection_reason

def test_safe_reject_restores_available_status(app, test_donor, test_recipient, test_donation):
    """Test that rejecting the only pending request restores donation status to Available."""
    with app.app_context():
        db = app.extensions['sqlalchemy']
        donation = Donation.query.get(test_donation)
        donation.status = 'Request Pending'

        req = DonationRequest(
            donation_id=test_donation,
            recipient_id=test_recipient,
            requested_quantity=10.0,
            estimated_beneficiaries=25,
            message="Request to be declined.",
            status="Pending"
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

        success, _ = safe_reject_request(req_id, test_donor, reason="Capacity conflict.")
        assert success is True

        req_after = DonationRequest.query.get(req_id)
        assert req_after.status == 'Rejected'
        assert req_after.rejection_reason == 'Capacity conflict.'

        # Donation should return to Available
        donation_after = Donation.query.get(test_donation)
        assert donation_after.status == 'Available'

def test_check_and_expire_overdue_donations(app, test_donor, test_recipient):
    """Test that donations past pickup deadline are automatically expired and pending requests rejected."""
    with app.app_context():
        db = app.extensions['sqlalchemy']
        now = utcnow()
        # Overdue donation
        overdue_donation = Donation(
            donor_id=test_donor,
            title="Overdue Cooked Meals",
            description="Test description for overdue donation to satisfy not null constraint.",
            category="Cooked Meals",
            quantity=15.0,
            remaining_quantity=15.0,
            quantity_unit="kg",
            prepared_at=now - timedelta(hours=8),
            pickup_deadline=now - timedelta(hours=1),  # Passed 1 hour ago
            address="100 Main St",
            city="Downtown",
            status="Request Pending",
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=8)
        )
        db.session.add(overdue_donation)
        db.session.flush()

        req = DonationRequest(
            donation_id=overdue_donation.id,
            recipient_id=test_recipient,
            requested_quantity=10.0,
            estimated_beneficiaries=20,
            message="Will collect.",
            status="Pending"
        )
        db.session.add(req)
        db.session.commit()
        d_id, r_id = overdue_donation.id, req.id

        # Run expiration check
        count = check_and_expire_overdue_donations()
        assert count >= 1

        d_after = Donation.query.get(d_id)
        assert d_after.status == 'Expired'

        r_after = DonationRequest.query.get(r_id)
        assert r_after.status == 'Rejected'
        assert 'expired' in r_after.rejection_reason.lower()
