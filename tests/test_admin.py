from app.models import User, Organization, Donation

def test_admin_dashboard_access_control(client, test_donor, test_admin):
    """Test that only administrators can access the admin dashboard."""
    # Donor attempt: forbidden
    client.post('/auth/login', data={'email': 'donor_test@test.com', 'password': 'pass123'})
    donor_res = client.get('/admin/dashboard')
    assert donor_res.status_code in [403, 302]
    client.get('/auth/logout')

    # Admin attempt: allowed
    client.post('/auth/login', data={'email': 'admin_test@test.com', 'password': 'adminpass'})
    admin_res = client.get('/admin/dashboard')
    assert admin_res.status_code == 200
    assert b'Platform Administration' in admin_res.data

def test_admin_approve_and_reject_verification(client, app, test_admin, test_recipient):
    """Test admin approving and rejecting organization verification."""
    client.post('/auth/login', data={'email': 'admin_test@test.com', 'password': 'adminpass'})

    with app.app_context():
        user = User.query.get(test_recipient)
        org = user.organization
        org.verification_status = 'pending'
        app.extensions['sqlalchemy'].session.commit()
        org_id = org.id

    # Approve
    res_app = client.post(f'/admin/verification/{org_id}/approve', data={
        'notes': 'All tax exemption documentation verified.'
    }, follow_redirects=True)
    assert res_app.status_code == 200

    with app.app_context():
        org = Organization.query.get(org_id)
        assert org.verification_status == 'verified'

    # Reject
    res_rej = client.post(f'/admin/verification/{org_id}/reject', data={
        'notes': 'Expired certificate.'
    }, follow_redirects=True)
    assert res_rej.status_code == 200

    with app.app_context():
        org = Organization.query.get(org_id)
        assert org.verification_status == 'rejected'

def test_admin_toggle_user_suspension(client, app, test_admin, test_donor):
    """Test admin suspending and re-activating a user."""
    client.post('/auth/login', data={'email': 'admin_test@test.com', 'password': 'adminpass'})

    # Suspend
    res = client.post(f'/admin/user/{test_donor}/toggle-status', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        donor = User.query.get(test_donor)
        assert donor.account_status == 'suspended'

    # Reactivate
    res2 = client.post(f'/admin/user/{test_donor}/toggle-status', follow_redirects=True)
    assert res2.status_code == 200

    with app.app_context():
        donor = User.query.get(test_donor)
        assert donor.account_status == 'active'

def test_admin_remove_donation(client, app, test_admin, test_donation):
    """Test admin moderating and removing a donation."""
    client.post('/auth/login', data={'email': 'admin_test@test.com', 'password': 'adminpass'})

    res = client.post(f'/admin/donation/{test_donation}/remove', data={
        'reason': 'Violated food packaging standard.'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        donation = Donation.query.get(test_donation)
        assert donation.status == 'Cancelled'
