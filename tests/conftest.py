import pytest
from datetime import timedelta
from app import create_app, db
from app.models import User, Organization, Donation, utcnow

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_donor(app):
    with app.app_context():
        user = User(
            name="Test Donor",
            email="donor_test@test.com",
            role="donor",
            phone="555-100-0001",
            account_status="active"
        )
        user.set_password("pass123")
        db.session.add(user)
        db.session.flush()

        org = Organization(
            user_id=user.id,
            organization_name="Test Hotel & Kitchen",
            organization_type="hotel",
            address="100 Main St",
            city="Downtown",
            latitude=40.7128,
            longitude=-74.0060,
            verification_status="verified"
        )
        db.session.add(org)
        db.session.commit()
        return user.id

@pytest.fixture
def test_recipient(app):
    with app.app_context():
        user = User(
            name="Test Recipient",
            email="recipient_test@test.com",
            role="recipient",
            phone="555-200-0002",
            account_status="active"
        )
        user.set_password("pass123")
        db.session.add(user)
        db.session.flush()

        org = Organization(
            user_id=user.id,
            organization_name="Test Community Shelter",
            organization_type="shelter",
            address="200 Broadway",
            city="Downtown",
            latitude=40.7130,
            longitude=-74.0055,
            capacity_servings=100,
            preferred_categories="Cooked Meals",
            verification_status="verified"
        )
        db.session.add(org)
        db.session.commit()
        return user.id

@pytest.fixture
def test_admin(app):
    with app.app_context():
        admin = User(
            name="Test Admin",
            email="admin_test@test.com",
            role="admin",
            phone="555-999-0000",
            account_status="active"
        )
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        return admin.id

@pytest.fixture
def test_donation(app, test_donor):
    with app.app_context():
        now = utcnow()
        donation = Donation(
            donor_id=test_donor,
            title="40 Fresh Meals",
            category="Cooked Meals",
            dietary_type="Vegetarian",
            quantity=20.0,
            remaining_quantity=20.0,
            quantity_unit="kg",
            prepared_at=now - timedelta(hours=1),
            pickup_deadline=now + timedelta(hours=4),
            storage_information="Refrigerated (0-4°C)",
            allergen_information="None",
            packaging_details="Clean sealed boxes",
            description="Freshly prepared test pasta and vegetables.",
            address="100 Main St",
            city="Downtown",
            latitude=40.7128,
            longitude=-74.0060,
            status="Available",
            created_at=now,
            updated_at=now
        )
        db.session.add(donation)
        db.session.commit()
        return donation.id
