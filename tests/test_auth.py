from app.models import User, Organization

def test_donor_registration(client, app):
    """Test successful donor registration and linked organization creation."""
    res = client.post('/auth/register', data={
        'name': 'New Donor Chef',
        'email': 'new_donor@restaurant.com',
        'role': 'donor',
        'phone': '555-444-3322',
        'password': 'securepassword',
        'confirm_password': 'securepassword',
        'organization_name': 'New Bistro Kitchen',
        'organization_type': 'restaurant',
        'address': '123 Market St',
        'city': 'Downtown',
        'state': 'NY',
        'postal_code': '10001'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email='new_donor@restaurant.com').first()
        assert user is not None
        assert user.role == 'donor'
        assert user.check_password('securepassword')
        assert user.organization is not None
        assert user.organization.organization_name == 'New Bistro Kitchen'

def test_duplicate_email_registration(client, test_donor):
    """Test that registering with an existing email fails validation."""
    res = client.post('/auth/register', data={
        'name': 'Another User',
        'email': 'donor_test@test.com',
        'role': 'donor',
        'phone': '555-999-1111',
        'password': 'password123',
        'confirm_password': 'password123',
        'organization_name': 'Another Hotel',
        'organization_type': 'hotel',
        'address': '500 5th Ave',
        'city': 'Downtown'
    })
    assert res.status_code == 200
    assert b'An account with this email address already exists.' in res.data

def test_login_success_and_logout(client, test_donor):
    """Test logging in with valid credentials and logging out."""
    res = client.post('/auth/login', data={
        'email': 'donor_test@test.com',
        'password': 'pass123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'Welcome back' in res.data

    logout_res = client.get('/auth/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b'logged out safely' in logout_res.data

def test_login_invalid_password(client, test_donor):
    """Test that login fails with incorrect password."""
    res = client.post('/auth/login', data={
        'email': 'donor_test@test.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b'Invalid email address or password' in res.data

def test_suspended_user_cannot_login(client, app, test_donor):
    """Test that a suspended account is blocked from signing in."""
    with app.app_context():
        user = User.query.get(test_donor)
        user.account_status = 'suspended'
        app.extensions['sqlalchemy'].session.commit()

    res = client.post('/auth/login', data={
        'email': 'donor_test@test.com',
        'password': 'pass123'
    }, follow_redirects=True)
    assert b'Your account has been suspended' in res.data

def test_role_based_access_protection(client, test_donor, test_recipient):
    """Test that donors cannot access recipient routes and vice-versa."""
    # Login as donor
    client.post('/auth/login', data={'email': 'donor_test@test.com', 'password': 'pass123'})
    
    # Attempt to access recipient dashboard
    res = client.get('/recipient/dashboard', follow_redirects=True)
    assert b'Access denied: Recipient organization privileges required.' in res.data

    # Attempt to access admin dashboard
    admin_res = client.get('/admin/dashboard')
    assert admin_res.status_code in [403, 302]
