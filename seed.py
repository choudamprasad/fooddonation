import os
from datetime import timedelta
from app import create_app, db
from app.models import (
    User, Organization, Donation, DonationRequest,
    Notification, DonationStatusHistory, utcnow
)

def run_seed():
    print("Clearing existing database tables...")
    db.drop_all()
    db.create_all()

    now = utcnow()

    print("Creating user accounts...")
    # 1. Admin
    admin = User(
        name="Platform Administrator",
        email="admin@foodbridge.org",
        role="admin",
        phone="+1 (555) 010-0001",
        account_status="active",
        created_at=now - timedelta(days=30)
    )
    admin.set_password("admin123")
    db.session.add(admin)

    # 2. Donors
    donor1 = User(
        name="Chef Marcus Vance",
        email="donor@grandhotel.com",
        role="donor",
        phone="+1 (555) 012-3456",
        account_status="active",
        created_at=now - timedelta(days=20)
    )
    donor1.set_password("password123")
    db.session.add(donor1)

    donor2 = User(
        name="Elena Rostova",
        email="dining@campus.edu",
        role="donor",
        phone="+1 (555) 014-7890",
        account_status="active",
        created_at=now - timedelta(days=15)
    )
    donor2.set_password("password123")
    db.session.add(donor2)

    donor3 = User(
        name="David Miller",
        email="bakery@greenharvest.com",
        role="donor",
        phone="+1 (555) 016-1122",
        account_status="active",
        created_at=now - timedelta(days=10)
    )
    donor3.set_password("password123")
    db.session.add(donor3)

    donor4 = User(
        name="Angela Davis",
        email="events@sunsethall.com",
        role="donor",
        phone="+1 (555) 018-9988",
        account_status="active",
        created_at=now - timedelta(days=8)
    )
    donor4.set_password("password123")
    db.session.add(donor4)

    # 3. Recipients (NGOs & Shelters)
    recip1 = User(
        name="Sister Mary Catherine",
        email="info@hopeorphanage.org",
        role="recipient",
        phone="+1 (555) 021-4321",
        account_status="active",
        created_at=now - timedelta(days=25)
    )
    recip1.set_password("password123")
    db.session.add(recip1)

    recip2 = User(
        name="Robert Thorne",
        email="contact@citykitchen.org",
        role="recipient",
        phone="+1 (555) 023-8765",
        account_status="active",
        created_at=now - timedelta(days=18)
    )
    recip2.set_password("password123")
    db.session.add(recip2)

    recip3 = User(
        name="Pastor Thomas Lee",
        email="shelter@stjudes.org",
        role="recipient",
        phone="+1 (555) 025-5544",
        account_status="active",
        created_at=now - timedelta(days=12)
    )
    recip3.set_password("password123")
    db.session.add(recip3)

    recip4 = User(
        name="Kavita Sharma",
        email="outreach@compassion.org",
        role="recipient",
        phone="+1 (555) 027-3322",
        account_status="active",
        created_at=now - timedelta(days=3)
    )
    recip4.set_password("password123")
    db.session.add(recip4)

    db.session.flush()

    print("Creating organizations...")
    # Donor Organizations
    org_d1 = Organization(
        user_id=donor1.id,
        organization_name="Grand Plaza Hotel & Culinary Arts",
        organization_type="hotel",
        registration_number="HOTEL-NYC-9482",
        contact_person="Chef Marcus Vance",
        address="100 Broadway, 4th Floor Kitchen",
        city="Downtown",
        state="NY",
        postal_code="10005",
        latitude=40.7115,
        longitude=-74.0080,
        verification_status="verified",
        submitted_at=now - timedelta(days=20),
        verified_at=now - timedelta(days=19)
    )
    db.session.add(org_d1)

    org_d2 = Organization(
        user_id=donor2.id,
        organization_name="Metropolitan University Campus Dining",
        organization_type="college",
        registration_number="EDU-NY-5521",
        contact_person="Elena Rostova",
        address="70 Washington Square South",
        city="Midtown",
        state="NY",
        postal_code="10012",
        latitude=40.7295,
        longitude=-73.9965,
        verification_status="verified",
        submitted_at=now - timedelta(days=15),
        verified_at=now - timedelta(days=14)
    )
    db.session.add(org_d2)

    org_d3 = Organization(
        user_id=donor3.id,
        organization_name="Green Harvest Artisan Bakery",
        organization_type="restaurant",
        registration_number="BAKE-NY-7729",
        contact_person="David Miller",
        address="320 Columbus Avenue",
        city="Uptown",
        state="NY",
        postal_code="10023",
        latitude=40.7790,
        longitude=-73.9780,
        verification_status="verified",
        submitted_at=now - timedelta(days=10),
        verified_at=now - timedelta(days=9)
    )
    db.session.add(org_d3)

    org_d4 = Organization(
        user_id=donor4.id,
        organization_name="Sunset Banquet & Event Hall",
        organization_type="event_organizer",
        registration_number="EVT-NY-1104",
        contact_person="Angela Davis",
        address="450 West 33rd Street",
        city="Westside",
        state="NY",
        postal_code="10001",
        latitude=40.7535,
        longitude=-74.0005,
        verification_status="verified",
        submitted_at=now - timedelta(days=8),
        verified_at=now - timedelta(days=7)
    )
    db.session.add(org_d4)

    # Recipient Organizations
    org_r1 = Organization(
        user_id=recip1.id,
        organization_name="Hope Children's Home & Community Kitchen",
        organization_type="orphanage",
        registration_number="NGO-501C3-99410",
        contact_person="Sister Mary Catherine",
        address="250 Mulberry Street",
        city="Downtown",
        state="NY",
        postal_code="10012",
        latitude=40.7220,
        longitude=-73.9960,
        capacity_servings=120,
        preferred_categories="Cooked Meals, Bakery & Bread, Dairy Products",
        verification_status="verified",
        submitted_at=now - timedelta(days=25),
        verified_at=now - timedelta(days=24)
    )
    db.session.add(org_r1)

    org_r2 = Organization(
        user_id=recip2.id,
        organization_name="City Center Community Soup Kitchen",
        organization_type="community_kitchen",
        registration_number="NGO-501C3-88123",
        contact_person="Robert Thorne",
        address="510 8th Avenue",
        city="Westside",
        state="NY",
        postal_code="10018",
        latitude=40.7520,
        longitude=-73.9925,
        capacity_servings=250,
        preferred_categories="Cooked Meals, Raw Produce/Vegetables",
        verification_status="verified",
        submitted_at=now - timedelta(days=18),
        verified_at=now - timedelta(days=17)
    )
    db.session.add(org_r2)

    org_r3 = Organization(
        user_id=recip3.id,
        organization_name="St. Jude Emergency Shelter",
        organization_type="shelter",
        registration_number="NGO-501C3-44190",
        contact_person="Pastor Thomas Lee",
        address="140 East 45th Street",
        city="Midtown",
        state="NY",
        postal_code="10017",
        latitude=40.7530,
        longitude=-73.9740,
        capacity_servings=80,
        preferred_categories="Cooked Meals, Packaged/Canned Foods",
        verification_status="verified",
        submitted_at=now - timedelta(days=12),
        verified_at=now - timedelta(days=11)
    )
    db.session.add(org_r3)

    org_r4 = Organization(
        user_id=recip4.id,
        organization_name="Compassion Grassroots Community Outreach",
        organization_type="ngo",
        registration_number="REG-PENDING-2025",
        contact_person="Kavita Sharma",
        address="88 Rivington Street",
        city="Downtown",
        state="NY",
        postal_code="10002",
        latitude=40.7200,
        longitude=-73.9880,
        capacity_servings=60,
        preferred_categories="Cooked Meals, Raw Produce/Vegetables",
        verification_status="pending",
        verification_notes="Grassroots relief program feeding homeless youth. Official state certificate attached.",
        submitted_at=now - timedelta(days=3)
    )
    db.session.add(org_r4)

    db.session.flush()

    print("Creating food donations across lifecycle stages...")
    # Donation 1: Available, High Urgency (< 4 hours)
    don1 = Donation(
        donor_id=donor1.id,
        title="45 Fresh Gourmet Lunch Bento Trays",
        category="Cooked Meals",
        dietary_type="Vegetarian",
        quantity=25.0,
        remaining_quantity=25.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=1, minutes=30),
        pickup_deadline=now + timedelta(hours=3, minutes=30),
        storage_information="Hot Holding (>60°C)",
        allergen_information="Contains Dairy (Paneer/Cheese). No Nuts.",
        packaging_details="Individual food-grade sealed thermal boxes",
        description="Freshly cooked executive buffet lunches: basmati saffron rice, paneer butter masala, mixed steamed vegetables, and soft whole wheat rotis. Kept strictly above 65°C in Cambro food warmers.",
        address="100 Broadway, Loading Bay C",
        city="Downtown",
        latitude=40.7115,
        longitude=-74.0080,
        contact_preference="Phone Call",
        donor_phone="+1 (555) 012-3456",
        status="Available",
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1)
    )
    db.session.add(don1)

    # Donation 2: Available, Moderate Urgency (~8 hours)
    don2 = Donation(
        donor_id=donor3.id,
        title="Fresh Artisan Sourdough Breads & Pastries",
        category="Bakery & Bread",
        dietary_type="Vegetarian",
        quantity=18.0,
        remaining_quantity=18.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=3),
        pickup_deadline=now + timedelta(hours=8),
        storage_information="Room Temperature",
        allergen_information="Contains Gluten/Wheat. Traces of Sesame.",
        packaging_details="Food-grade parchment lined clean delivery crates",
        description="Daily morning surplus of whole-wheat sourdough loaves, multigrain baguettes, and assorted croissants. Baked this morning in our certified kitchen.",
        address="320 Columbus Avenue",
        city="Uptown",
        latitude=40.7790,
        longitude=-73.9780,
        contact_preference="In-app Messages",
        status="Available",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2)
    )
    db.session.add(don2)

    # Donation 3: Available, Fresh Produce (~20 hours)
    don3 = Donation(
        donor_id=donor2.id,
        title="60 kg Organic Farm Produce (Carrots, Squash, Apples)",
        category="Raw Produce/Vegetables",
        dietary_type="Vegan",
        quantity=60.0,
        remaining_quantity=60.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=4),
        pickup_deadline=now + timedelta(hours=20),
        storage_information="Refrigerated (0-4°C)",
        allergen_information="None reported",
        packaging_details="Clean ventilated produce crates",
        description="Surplus crisp farm-fresh organic carrots, butternut squash, bell peppers, and eating apples from university dining inventory. Ideal for soup kitchens.",
        address="70 Washington Square South",
        city="Midtown",
        latitude=40.7295,
        longitude=-73.9965,
        contact_preference="In-app Messages",
        status="Available",
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(hours=3)
    )
    db.session.add(don3)

    # Donation 4: Request Pending (Hope Orphanage has requested)
    don4 = Donation(
        donor_id=donor1.id,
        title="40 kg Campus Dining Pasta & Hearty Vegetable Soup",
        category="Cooked Meals",
        dietary_type="Vegetarian",
        quantity=40.0,
        remaining_quantity=40.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=2),
        pickup_deadline=now + timedelta(hours=4),
        storage_information="Hot Holding (>60°C)",
        allergen_information="Contains Gluten, Dairy. Nut-free.",
        packaging_details="Stainless steel thermal transport urns (loaned)",
        description="Penne pasta with marinara vegetable sauce and hearty minestrone soup. Prepared in university central kitchen.",
        address="100 Broadway, Loading Dock B",
        city="Downtown",
        latitude=40.7120,
        longitude=-74.0075,
        contact_preference="Phone Call",
        donor_phone="+1 (555) 012-3456",
        status="Request Pending",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(minutes=45)
    )
    db.session.add(don4)

    # Donation 5: Accepted & Ready for Pickup
    don5 = Donation(
        donor_id=donor4.id,
        title="Banquet Roasted Herb Chicken & Steamed Potatoes",
        category="Cooked Meals",
        dietary_type="Non-Vegetarian",
        quantity=35.0,
        remaining_quantity=0.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=3),
        pickup_deadline=now + timedelta(hours=3),
        storage_information="Refrigerated (0-4°C)",
        allergen_information="None reported. Halal certified chicken.",
        packaging_details="Heavy-duty foil pans with crimped lids",
        description="Freshly prepared catered banquet dinner: roasted rosemary chicken breasts, rosemary garlic potatoes, and steamed green beans. Rapidly chilled in blast chiller.",
        address="450 West 33rd Street, Dock #2",
        city="Westside",
        latitude=40.7535,
        longitude=-74.0005,
        contact_preference="Phone Call",
        donor_phone="+1 (555) 018-9988",
        status="Ready for Pickup",
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(minutes=20)
    )
    db.session.add(don5)

    # Donation 6: Completed (Impact recorded!)
    don6 = Donation(
        donor_id=donor4.id,
        title="120 Plates Wedding Feast & Vegetable Biryani",
        category="Cooked Meals",
        dietary_type="Vegetarian",
        quantity=50.0,
        remaining_quantity=0.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(days=2, hours=4),
        pickup_deadline=now - timedelta(days=2),
        storage_information="Hot Holding (>60°C)",
        allergen_information="Contains Cashews and Dairy",
        packaging_details="Sealed heavy-duty food foil containers",
        description="Surplus royal vegetable biryani, spiced lentils, and cucumber raita from evening wedding reception.",
        address="450 West 33rd Street",
        city="Westside",
        latitude=40.7535,
        longitude=-74.0005,
        status="Completed",
        created_at=now - timedelta(days=2, hours=5),
        updated_at=now - timedelta(days=2)
    )
    db.session.add(don6)

    # Donation 7: Completed (Impact recorded!)
    don7 = Donation(
        donor_id=donor3.id,
        title="30 kg Sandwiches & Fresh Fruit Cups",
        category="Cooked Meals",
        dietary_type="Vegetarian",
        quantity=30.0,
        remaining_quantity=0.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(days=4),
        pickup_deadline=now - timedelta(days=4, hours=-4),
        storage_information="Refrigerated (0-4°C)",
        allergen_information="Contains Dairy, Wheat",
        packaging_details="Individually wrapped eco-boxes",
        description="Catered corporate seminar lunch boxes: mozzarella pesto paninis and fresh seasonal fruit cups.",
        address="320 Columbus Avenue",
        city="Uptown",
        latitude=40.7790,
        longitude=-73.9780,
        status="Completed",
        created_at=now - timedelta(days=4, hours=2),
        updated_at=now - timedelta(days=4)
    )
    db.session.add(don7)

    # Donation 8: Expired (Past safe deadline)
    don8 = Donation(
        donor_id=donor2.id,
        title="Cream of Mushroom Soup & Baguettes",
        category="Cooked Meals",
        dietary_type="Vegetarian",
        quantity=15.0,
        remaining_quantity=15.0,
        quantity_unit="kg",
        prepared_at=now - timedelta(hours=14),
        pickup_deadline=now - timedelta(hours=2),  # Expired 2 hours ago
        storage_information="Hot Holding (>60°C)",
        allergen_information="Contains Dairy, Gluten",
        packaging_details="Covered metal stockpots",
        description="Mushroom soup prepared yesterday evening.",
        address="70 Washington Square South",
        city="Midtown",
        latitude=40.7295,
        longitude=-73.9965,
        status="Expired",
        created_at=now - timedelta(hours=14),
        updated_at=now - timedelta(hours=2)
    )
    db.session.add(don8)

    db.session.flush()

    print("Creating requests...")
    # Request on Donation 4: Pending from Hope Orphanage
    req1 = DonationRequest(
        donation_id=don4.id,
        recipient_id=recip1.id,
        requested_quantity=30.0,
        estimated_beneficiaries=80,
        message="We will collect this in our insulated van at 3:30 PM to serve 80 children and youth at Hope Center dinner program.",
        status="Pending",
        created_at=now - timedelta(minutes=45),
        updated_at=now - timedelta(minutes=45)
    )
    db.session.add(req1)

    # Request on Donation 5: Accepted by City Center Kitchen
    req2 = DonationRequest(
        donation_id=don5.id,
        recipient_id=recip2.id,
        requested_quantity=35.0,
        estimated_beneficiaries=90,
        message="City Kitchen van will arrive with thermal Cambros for rapid pickup. Will be served to evening homeless community.",
        status="Accepted",
        pickup_notes="Please use Dock #2 and ring buzzer labeled Kitchen Handoff.",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(minutes=30)
    )
    db.session.add(req2)

    # Request on Donation 6: Completed by St. Jude Shelter
    req3 = DonationRequest(
        donation_id=don6.id,
        recipient_id=recip3.id,
        requested_quantity=50.0,
        estimated_beneficiaries=125,
        message="Collected and served 125 warm dinners to emergency shelter residents. Zero food wasted!",
        status="Completed",
        created_at=now - timedelta(days=2, hours=3),
        updated_at=now - timedelta(days=2)
    )
    db.session.add(req3)

    # Request on Donation 7: Completed by Hope Orphanage
    req4 = DonationRequest(
        donation_id=don7.id,
        recipient_id=recip1.id,
        requested_quantity=30.0,
        estimated_beneficiaries=75,
        message="Distributed to children after-school program with fresh fruit cups.",
        status="Completed",
        created_at=now - timedelta(days=4, hours=1),
        updated_at=now - timedelta(days=4)
    )
    db.session.add(req4)

    db.session.flush()

    print("Creating status history audit trail...")
    # History for Completed Donation 6
    db.session.add(DonationStatusHistory(
        donation_id=don6.id,
        changed_by=donor4.id,
        previous_status="Draft",
        new_status="Available",
        notes="Published surplus wedding banquet.",
        changed_at=now - timedelta(days=2, hours=5)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don6.id,
        changed_by=donor4.id,
        previous_status="Available",
        new_status="Accepted",
        notes="Accepted collection request from St. Jude Shelter.",
        changed_at=now - timedelta(days=2, hours=2, minutes=30)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don6.id,
        changed_by=donor4.id,
        previous_status="Accepted",
        new_status="Ready for Pickup",
        notes="Food sealed in thermal containers.",
        changed_at=now - timedelta(days=2, hours=1, minutes=45)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don6.id,
        changed_by=recip3.id,
        previous_status="Ready for Pickup",
        new_status="Collected",
        notes="Van arrived; handoff verified.",
        changed_at=now - timedelta(days=2, hours=1)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don6.id,
        changed_by=recip3.id,
        previous_status="Collected",
        new_status="Completed",
        notes="Dinners distributed to 125 people. Impact logged.",
        changed_at=now - timedelta(days=2)
    ))

    # History for Donation 5
    db.session.add(DonationStatusHistory(
        donation_id=don5.id,
        changed_by=donor4.id,
        previous_status="Draft",
        new_status="Available",
        notes="Listing published.",
        changed_at=now - timedelta(hours=3)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don5.id,
        changed_by=donor4.id,
        previous_status="Available",
        new_status="Accepted",
        notes="Accepted request from City Center Soup Kitchen.",
        changed_at=now - timedelta(minutes=30)
    ))
    db.session.add(DonationStatusHistory(
        donation_id=don5.id,
        changed_by=donor4.id,
        previous_status="Accepted",
        new_status="Ready for Pickup",
        notes="Packed in insulated Cambros.",
        changed_at=now - timedelta(minutes=20)
    ))

    print("Creating in-app notifications...")
    # Notifications for donor1
    db.session.add(Notification(
        user_id=donor1.id,
        title="New Request: 40 kg Campus Dining Pasta",
        message="Hope Children's Home has requested 30.0 kg of '40 kg Campus Dining Pasta'. Target: 80 beneficiaries.",
        link="/donor/manage-donations#donation-4",
        notification_type="request",
        is_read=False,
        created_at=now - timedelta(minutes=45)
    ))
    db.session.add(Notification(
        user_id=donor1.id,
        title="Welcome to FoodBridge!",
        message="Thank you for partnering to reduce food waste and feed local communities.",
        link="/donor/dashboard",
        notification_type="system",
        is_read=True,
        created_at=now - timedelta(days=20)
    ))

    # Notifications for recip1 (Hope Orphanage)
    db.session.add(Notification(
        user_id=recip1.id,
        title="Organization Verified!",
        message="Congratulations! Your organization 'Hope Children's Home & Community Kitchen' has been officially verified on FoodBridge.",
        link="/recipient/available-donations",
        notification_type="verification",
        is_read=True,
        created_at=now - timedelta(days=24)
    ))
    db.session.add(Notification(
        user_id=recip1.id,
        title="New Urgent Food Listing Nearby",
        message="Grand Plaza Hotel has listed 25 kg of Vegetarian Cooked Meals only 0.8 km from your kitchen.",
        link="/donations/1",
        notification_type="status_change",
        is_read=False,
        created_at=now - timedelta(hours=1)
    ))

    # Notifications for recip2 (City Center Kitchen)
    db.session.add(Notification(
        user_id=recip2.id,
        title="Request Accepted: Banquet Roasted Herb Chicken",
        message="Great news! Your request for 35.0 kg of 'Banquet Roasted Herb Chicken' was accepted. Pickup address: 450 West 33rd Street, Dock #2.",
        link="/recipient/my-requests",
        notification_type="status_change",
        is_read=False,
        created_at=now - timedelta(minutes=30)
    ))

    # Notifications for admin
    db.session.add(Notification(
        user_id=admin.id,
        title="New NGO Verification Request",
        message="Compassion Grassroots Community Outreach has submitted registration documents for administrator review.",
        link="/admin/verifications",
        notification_type="verification",
        is_read=False,
        created_at=now - timedelta(days=3)
    ))

    db.session.commit()
    print("Database seeding completed successfully!")
    print("\n---------------- DEMO CREDENTIALS ----------------")
    print("Administrator: admin@foodbridge.org        / admin123")
    print("Food Donor:    donor@grandhotel.com        / password123")
    print("Recipient NGO: info@hopeorphanage.org      / password123")
    print("---------------------------------------------------\n")

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        run_seed()
