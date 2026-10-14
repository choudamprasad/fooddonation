from datetime import timedelta
from app.models import Donation, DonationStatusHistory, utcnow

def test_create_donation_success(client, app, test_donor):
    """Test successful donation creation by an authorized donor."""
    client.post('/auth/login', data={'email': 'donor_test@test.com', 'password': 'pass123'})

    now = utcnow()
    prep_time = (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')
    deadline = (now + timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M')

    res = client.post('/donor/create-donation', data={
        'title': 'Fresh Vegetable Curry & Rice Trays',
        'category': 'Cooked Meals',
        'dietary_type': 'Vegetarian',
        'quantity': 30.0,
        'quantity_unit': 'kg',
        'prepared_at': prep_time,
        'pickup_deadline': deadline,
        'storage_information': 'Hot Holding (>60°C)',
        'allergen_information': 'None',
        'packaging_details': 'Food-grade stainless steel containers',
        'description': 'Delicious freshly prepared curry and jasmine rice for community shelters.',
        'address': '100 Main St',
        'city': 'Downtown',
        'contact_preference': 'Phone Call',
        'donor_phone': '555-100-0001',
        'safety_pledge': 'y'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'published successfully' in res.data

    with app.app_context():
        donation = Donation.query.filter_by(title='Fresh Vegetable Curry & Rice Trays').first()
        assert donation is not None
        assert donation.quantity == 30.0
        assert donation.remaining_quantity == 30.0
        assert donation.status == 'Available'
        assert donation.estimated_meals == 75  # 30kg * 2.5 = 75

        # Check status history
        history = DonationStatusHistory.query.filter_by(donation_id=donation.id).first()
        assert history is not None
        assert history.new_status == 'Available'

def test_create_donation_past_deadline_rejected(client, test_donor):
    """Test that a pickup deadline in the past is rejected."""
    client.post('/auth/login', data={'email': 'donor_test@test.com', 'password': 'pass123'})

    now = utcnow()
    prep_time = (now - timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M')
    past_deadline = (now - timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')

    res = client.post('/donor/create-donation', data={
        'title': 'Expired Bread Loaves',
        'category': 'Bakery & Bread',
        'dietary_type': 'Vegetarian',
        'quantity': 10.0,
        'quantity_unit': 'kg',
        'prepared_at': prep_time,
        'pickup_deadline': past_deadline,
        'storage_information': 'Room Temperature',
        'packaging_details': 'Bags',
        'description': 'Test past deadline rejection.',
        'address': '100 Main St',
        'city': 'Downtown',
        'contact_preference': 'Phone Call',
        'safety_pledge': 'y'
    })
    assert res.status_code == 200
    assert b'Safe pickup deadline must be in the future.' in res.data

def test_cancel_donation(client, app, test_donor, test_donation):
    """Test that donor can cancel an eligible donation."""
    client.post('/auth/login', data={'email': 'donor_test@test.com', 'password': 'pass123'})

    res = client.post(f'/donor/donation/{test_donation}/cancel', data={
        'reason': 'Accidental spoilage in holding facility.'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        donation = Donation.query.get(test_donation)
        assert donation.status == 'Cancelled'

        history = DonationStatusHistory.query.filter_by(donation_id=test_donation).order_by(DonationStatusHistory.changed_at.desc()).first()
        assert history.new_status == 'Cancelled'
        assert 'Accidental spoilage' in history.notes
