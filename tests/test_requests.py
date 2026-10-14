from app.models import Donation, DonationRequest

def test_submit_valid_request(client, app, test_recipient, test_donation):
    """Test successful submission of a donation request by a recipient NGO."""
    client.post('/auth/login', data={'email': 'recipient_test@test.com', 'password': 'pass123'})

    res = client.post(f'/donations/{test_donation}', data={
        'requested_quantity': 15.0,
        'estimated_beneficiaries': 40,
        'message': 'We will collect using an insulated cooler van to serve our homeless dinner program.',
        'safety_commitment': 'y'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        req = DonationRequest.query.filter_by(donation_id=test_donation, recipient_id=test_recipient).first()
        assert req is not None
        assert req.requested_quantity == 15.0
        assert req.status == 'Pending'
        assert req.estimated_beneficiaries == 40

        # Donation status should update to Request Pending
        donation = Donation.query.get(test_donation)
        assert donation.status == 'Request Pending'

def test_request_quantity_exceeding_available_rejected(client, test_recipient, test_donation):
    """Test that requesting more than remaining available quantity is rejected."""
    client.post('/auth/login', data={'email': 'recipient_test@test.com', 'password': 'pass123'})

    # Donation has 20.0 kg available; attempt to request 35.0 kg
    res = client.post(f'/donations/{test_donation}', data={
        'requested_quantity': 35.0,
        'estimated_beneficiaries': 90,
        'message': 'Requesting oversized volume.',
        'safety_commitment': 'y'
    }, follow_redirects=True)
    assert b'exceeds available quantity' in res.data

def test_prevent_duplicate_active_requests(client, test_recipient, test_donation):
    """Test that a recipient cannot submit duplicate active requests for the same donation."""
    client.post('/auth/login', data={'email': 'recipient_test@test.com', 'password': 'pass123'})

    # First request
    client.post(f'/donations/{test_donation}', data={
        'requested_quantity': 10.0,
        'estimated_beneficiaries': 25,
        'message': 'First request message for testing duplicate prevention.',
        'safety_commitment': 'y'
    }, follow_redirects=True)

    # Second duplicate request
    res2 = client.post(f'/donations/{test_donation}', data={
        'requested_quantity': 10.0,
        'estimated_beneficiaries': 25,
        'message': 'Duplicate second request.',
        'safety_commitment': 'y'
    }, follow_redirects=True)
    assert b'already have an active request' in res2.data
