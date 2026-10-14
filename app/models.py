from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utcnow():
    """Returns naive UTC datetime for standard database storage."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='donor')  # 'donor', 'recipient', 'admin'
    phone = db.Column(db.String(30), nullable=True)
    account_status = db.Column(db.String(20), nullable=False, default='active')  # 'active', 'suspended'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Relationships
    organization = db.relationship('Organization', backref='user', uselist=False, cascade='all, delete-orphan')
    donations = db.relationship('Donation', backref='donor', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='Donation.donor_id')
    requests = db.relationship('DonationRequest', backref='recipient', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='DonationRequest.recipient_id')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan', order_by='Notification.created_at.desc()')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.account_status == 'active'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_donor(self):
        return self.role == 'donor'

    @property
    def is_recipient(self):
        return self.role == 'recipient'

    @property
    def is_verified_recipient(self):
        if not self.is_recipient:
            return False
        return self.organization is not None and self.organization.verification_status == 'verified'

    @property
    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    organization_name = db.Column(db.String(150), nullable=False)
    organization_type = db.Column(db.String(50), nullable=False)  # 'ngo', 'shelter', 'orphanage', 'community_kitchen', 'restaurant', 'hotel', 'college', 'event_organizer', 'other'
    registration_number = db.Column(db.String(80), nullable=True)
    contact_person = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    verification_status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'verified', 'rejected'
    verification_notes = db.Column(db.Text, nullable=True)
    verification_document = db.Column(db.String(255), nullable=True)
    capacity_servings = db.Column(db.Integer, default=100, nullable=False)
    preferred_categories = db.Column(db.String(255), default='Cooked Meals, Raw Produce/Vegetables', nullable=True)
    submitted_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Organization {self.organization_name} ({self.verification_status})>"


class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    donor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)  # 'Cooked Meals', 'Raw Produce/Vegetables', etc.
    dietary_type = db.Column(db.String(30), nullable=False, default='Vegetarian')  # 'Vegetarian', 'Non-Vegetarian', 'Vegan', etc.
    quantity = db.Column(db.Float, nullable=False)
    remaining_quantity = db.Column(db.Float, nullable=False)
    quantity_unit = db.Column(db.String(20), nullable=False, default='kg')  # 'kg', 'servings', 'meals', 'liters', 'packets', 'boxes'
    
    prepared_at = db.Column(db.DateTime, nullable=False)
    pickup_deadline = db.Column(db.DateTime, nullable=False, index=True)
    
    storage_information = db.Column(db.String(100), nullable=False, default='Refrigerated (0-4°C)')
    allergen_information = db.Column(db.String(255), nullable=True, default='None reported')
    packaging_details = db.Column(db.String(255), nullable=True, default='Food-grade sealed containers')
    
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    image_filename = db.Column(db.String(255), nullable=True)
    
    contact_preference = db.Column(db.String(50), nullable=False, default='In-app Messages')
    donor_phone = db.Column(db.String(30), nullable=True)
    
    status = db.Column(db.String(30), nullable=False, default='Available', index=True)
    # Statuses: 'Available', 'Request Pending', 'Accepted', 'Ready for Pickup', 'Collected', 'Completed', 'Cancelled', 'Expired'
    
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    requests = db.relationship('DonationRequest', backref='donation', lazy='dynamic', cascade='all, delete-orphan')
    status_history = db.relationship('DonationStatusHistory', backref='donation', lazy='dynamic', cascade='all, delete-orphan', order_by='DonationStatusHistory.changed_at.desc()')

    @property
    def is_expired(self):
        if self.status == 'Expired':
            return True
        if self.status in ['Available', 'Request Pending'] and self.pickup_deadline < utcnow():
            return True
        return False

    @property
    def hours_remaining(self):
        diff = self.pickup_deadline - utcnow()
        total_seconds = diff.total_seconds()
        if total_seconds <= 0:
            return 0.0
        return round(total_seconds / 3600.0, 1)

    @property
    def urgency_level(self):
        hrs = self.hours_remaining
        if hrs <= 0:
            return 'expired'
        elif hrs <= 2.0:
            return 'critical'
        elif hrs <= 6.0:
            return 'high'
        elif hrs <= 24.0:
            return 'medium'
        return 'normal'

    @property
    def estimated_meals(self):
        """Calculates defensible estimated meals based on quantity unit."""
        unit = (self.quantity_unit or '').lower()
        q = float(self.quantity or 0)
        if unit in ['kg', 'kilograms']:
            return round(q * 2.5)  # 400g per meal
        elif unit in ['servings', 'meals']:
            return round(q)
        elif unit in ['liters', 'l']:
            return round(q * 2.0)
        elif unit in ['packets', 'boxes']:
            return round(q * 1.5)
        return round(q)

    @property
    def estimated_co2_saved(self):
        """Calculates estimated CO2 emissions avoided in kg."""
        unit = (self.quantity_unit or '').lower()
        q = float(self.quantity or 0)
        if unit in ['kg', 'kilograms']:
            kg_food = q
        elif unit in ['servings', 'meals']:
            kg_food = q * 0.4
        elif unit in ['liters', 'l']:
            kg_food = q * 0.8
        else:
            kg_food = q * 0.5
        return round(kg_food * 2.5, 1)

    def __repr__(self):
        return f"<Donation {self.id}: {self.title} ({self.status})>"


class DonationRequest(db.Model):
    __tablename__ = 'donation_requests'

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    requested_quantity = db.Column(db.Float, nullable=False)
    message = db.Column(db.Text, nullable=False)  # Intended distribution and target beneficiaries
    estimated_beneficiaries = db.Column(db.Integer, default=0, nullable=False)
    
    status = db.Column(db.String(30), nullable=False, default='Pending', index=True)
    # Statuses: 'Pending', 'Accepted', 'Rejected', 'Collected', 'Cancelled'
    
    rejection_reason = db.Column(db.Text, nullable=True)
    pickup_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def __repr__(self):
        return f"<DonationRequest #{self.id} for Donation #{self.donation_id} ({self.status})>"


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    notification_type = db.Column(db.String(30), nullable=False, default='system')
    # 'request', 'status_change', 'deadline', 'verification', 'system'
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification {self.id} for User #{self.user_id} - Read: {self.is_read}>"


class DonationStatusHistory(db.Model):
    __tablename__ = 'donation_status_history'

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.Integer, db.ForeignKey('donations.id'), nullable=False, index=True)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    previous_status = db.Column(db.String(30), nullable=False)
    new_status = db.Column(db.String(30), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    changed_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', foreign_keys=[changed_by])

    def __repr__(self):
        return f"<StatusHistory Donation #{self.donation_id}: {self.previous_status} -> {self.new_status}>"
