from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    SelectField, TextAreaField, FloatField, IntegerField, DateTimeLocalField, HiddenField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, NumberRange, ValidationError, Optional
)
from datetime import datetime, timezone
from app.models import User, utcnow

FOOD_CATEGORIES = [
    ('Cooked Meals', 'Cooked Meals (Ready to Eat)'),
    ('Raw Produce/Vegetables', 'Raw Produce & Fresh Vegetables/Fruits'),
    ('Bakery & Bread', 'Bakery Items, Breads & Pastries'),
    ('Packaged/Canned Foods', 'Packaged & Canned Goods (Sealed)'),
    ('Dairy Products', 'Dairy Products (Milk, Cheese, Yogurt)'),
    ('Beverages', 'Non-Alcoholic Beverages & Juices'),
    ('Other', 'Other Food Items')
]

DIETARY_TYPES = [
    ('Vegetarian', 'Vegetarian (No meat/fish)'),
    ('Non-Vegetarian', 'Non-Vegetarian (Contains meat/poultry)'),
    ('Vegan', 'Vegan (Strictly plant-based)'),
    ('Jain', 'Jain (No root vegetables, purely veg)'),
    ('Halal', 'Halal Certified/Compliant')
]

QUANTITY_UNITS = [
    ('kg', 'Kilograms (kg)'),
    ('servings', 'Servings / Portions'),
    ('meals', 'Prepared Meals / Plates'),
    ('liters', 'Liters (L)'),
    ('packets', 'Packets / Cartons'),
    ('boxes', 'Standard Food Boxes')
]

STORAGE_OPTIONS = [
    ('Refrigerated (0-4°C)', 'Refrigerated Cold Holding (0°C – 4°C)'),
    ('Hot Holding (>60°C)', 'Insulated Hot Holding (>60°C)'),
    ('Room Temperature', 'Dry / Ambient Room Temperature (Clean & Dry)'),
    ('Frozen (< -18°C)', 'Deep Freeze (< -18°C)')
]

CONTACT_PREFERENCES = [
    ('In-app Messages', 'In-App Secure Notes only'),
    ('Phone Call', 'Phone Call from Verified Recipient'),
    ('Email', 'Email notification')
]

ORG_TYPES = [
    ('ngo', 'Registered NGO / Non-Profit'),
    ('shelter', 'Homeless / Community Shelter'),
    ('orphanage', 'Children’s Home / Orphanage'),
    ('community_kitchen', 'Community Kitchen / Langar / Soup Kitchen'),
    ('restaurant', 'Restaurant / Food Outlet (Donor)'),
    ('hotel', 'Hotel / Hospitality (Donor)'),
    ('college', 'College / University / Campus (Donor)'),
    ('event_organizer', 'Event & Banquet Hall (Donor)'),
    ('other', 'Other Community Initiative')
]

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me signed in')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    name = StringField('Full Name or Contact Person', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    role = SelectField('Register As', choices=[
        ('donor', 'Food Donor (Restaurant, Hotel, Caterer, Event, College, Individual)'),
        ('recipient', 'Recipient Organization (NGO, Shelter, Orphanage, Community Kitchen)')
    ], validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=7, max=25)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    
    # Organization profile fields
    organization_name = StringField('Organization / Business Name', validators=[DataRequired(), Length(max=150)])
    organization_type = SelectField('Entity Type', choices=ORG_TYPES, validators=[DataRequired()])
    address = StringField('Street Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City / Town', validators=[DataRequired(), Length(max=100)])
    state = StringField('State / Province', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal / ZIP Code', validators=[Optional(), Length(max=20)])
    
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError('An account with this email address already exists.')

class DonationForm(FlaskForm):
    title = StringField('Donation Title', validators=[
        DataRequired(),
        Length(min=3, max=150, message='Title must be between 3 and 150 characters.')
    ])
    category = SelectField('Food Category', choices=FOOD_CATEGORIES, validators=[DataRequired()])
    dietary_type = SelectField('Dietary Classification', choices=DIETARY_TYPES, validators=[DataRequired()])
    quantity = FloatField('Available Quantity', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Quantity must be greater than 0.')
    ])
    quantity_unit = SelectField('Unit of Measure', choices=QUANTITY_UNITS, validators=[DataRequired()])
    
    prepared_at = DateTimeLocalField('Preparation / Cooking Date & Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    pickup_deadline = DateTimeLocalField('Safe Pickup Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    
    storage_information = SelectField('Storage & Holding Conditions', choices=STORAGE_OPTIONS, validators=[DataRequired()])
    allergen_information = StringField('Allergen Advisory (e.g. Nuts, Dairy, Gluten, Shellfish, None)', validators=[Optional(), Length(max=255)])
    packaging_details = StringField('Packaging Description (e.g. Clean food-grade containers, Sealed trays)', validators=[DataRequired(), Length(max=255)])
    
    description = TextAreaField('Description & Handling Notes', validators=[
        DataRequired(),
        Length(min=10, max=1000, message='Please provide an accurate description (10-1000 chars).')
    ])
    
    address = StringField('Pickup Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City / Area', validators=[DataRequired(), Length(max=100)])
    latitude = FloatField('Latitude (Optional or Auto-fill)', validators=[Optional()])
    longitude = FloatField('Longitude (Optional or Auto-fill)', validators=[Optional()])
    
    image = FileField('Food Photo (Optional, max 5MB)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (.jpg, .jpeg, .png, .webp)!')
    ])
    
    contact_preference = SelectField('Preferred Contact Method', choices=CONTACT_PREFERENCES, validators=[DataRequired()])
    donor_phone = StringField('Pickup Contact Phone', validators=[Optional(), Length(max=30)])
    
    # Food Safety Confirmation Checkbox
    safety_pledge = BooleanField('I certify that this food was handled under hygienic conditions, is safe for human consumption, and is stored as specified.', validators=[DataRequired(message='You must confirm the food safety pledge.')])
    
    submit = SubmitField('Publish Food Donation')

    def validate_pickup_deadline(self, field):
        if field.data:
            # Check deadline is in the future
            if field.data <= utcnow():
                raise ValidationError('Safe pickup deadline must be in the future.')
            
            # Check deadline is after preparation time
            if self.prepared_at.data and field.data < self.prepared_at.data:
                raise ValidationError('Safe pickup deadline cannot be earlier than preparation date and time.')

class DonationRequestForm(FlaskForm):
    requested_quantity = FloatField('Quantity to Collect', validators=[
        DataRequired(),
        NumberRange(min=0.1, message='Requested quantity must be at least 0.1.')
    ])
    estimated_beneficiaries = IntegerField('Estimated People / Beneficiaries to Feed', validators=[
        DataRequired(),
        NumberRange(min=1, message='Please specify at least 1 beneficiary.')
    ])
    message = TextAreaField('Distribution Plan & Safe Transport', validators=[
        DataRequired(),
        Length(min=15, max=1000, message='Please explain where and how the food will be distributed and safely transported (min 15 chars).')
    ])
    safety_commitment = BooleanField('Our organization confirms adequate temperature-controlled transport and prompt hygienic distribution to intended recipients.', validators=[DataRequired(message='Safety and distribution confirmation is required.')])
    submit = SubmitField('Submit Donation Request')

class OrganizationVerificationForm(FlaskForm):
    organization_name = StringField('Official Organization Name', validators=[DataRequired(), Length(max=150)])
    organization_type = SelectField('Type of Entity', choices=ORG_TYPES, validators=[DataRequired()])
    registration_number = StringField('Government Registration / Tax Exemption / NGO ID', validators=[DataRequired(), Length(max=80)])
    contact_person = StringField('Authorized Representative Name', validators=[DataRequired(), Length(max=120)])
    address = StringField('Physical Registered Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City / District', validators=[DataRequired(), Length(max=100)])
    state = StringField('State / Province', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    capacity_servings = IntegerField('Average Meal Distribution Capacity (People/Day)', validators=[
        DataRequired(),
        NumberRange(min=5, max=50000, message='Enter a realistic capacity (5 to 50,000).')
    ])
    preferred_categories = StringField('Preferred Food Categories (comma-separated)', validators=[Optional(), Length(max=255)])
    verification_document = FileField('Registration Certificate / Letter (PDF/JPG/PNG, Max 5MB)', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Allowed file types: PDF, JPG, PNG!')
    ])
    verification_notes = TextAreaField('Additional Verification Details / Website / Social Media Links', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Submit for Official Verification')

class ProfileForm(FlaskForm):
    name = StringField('Contact Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Profile Changes')

class RejectRequestForm(FlaskForm):
    reason = TextAreaField('Reason for Declining', validators=[DataRequired(), Length(min=5, max=300)])
    submit = SubmitField('Confirm Decline')

class CancelDonationForm(FlaskForm):
    reason = TextAreaField('Reason for Cancellation', validators=[DataRequired(), Length(min=5, max=300)])
    submit = SubmitField('Confirm Cancellation')
