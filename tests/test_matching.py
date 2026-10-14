from datetime import timedelta
from app.models import User, Donation, utcnow
from app.services.matching import (
    haversine_distance, calculate_proximity_score, calculate_deadline_urgency_score,
    calculate_quantity_compatibility_score, calculate_category_score, rank_donations_for_recipient
)

def test_haversine_distance():
    """Test distance formula between two known points in NYC."""
    # Distance between Downtown (40.7128, -74.0060) and Midtown (40.7580, -73.9855) ~ 5.3 km
    dist = haversine_distance(40.7128, -74.0060, 40.7580, -73.9855)
    assert dist is not None
    assert 4.5 < dist < 6.0

def test_deadline_urgency_scoring(app, test_donor):
    """Test that closer deadlines produce higher urgency scores."""
    with app.app_context():
        now = utcnow()
        urgent_donation = Donation(
            donor_id=test_donor,
            title="Urgent Meals",
            category="Cooked Meals",
            quantity=10.0,
            remaining_quantity=10.0,
            quantity_unit="kg",
            prepared_at=now - timedelta(hours=1),
            pickup_deadline=now + timedelta(hours=1.5),  # 1.5h left -> critical
            address="100 Main St",
            city="Downtown"
        )
        relaxed_donation = Donation(
            donor_id=test_donor,
            title="Relaxed Produce",
            category="Raw Produce/Vegetables",
            quantity=10.0,
            remaining_quantity=10.0,
            quantity_unit="kg",
            prepared_at=now,
            pickup_deadline=now + timedelta(hours=30),  # 30h left -> relaxed
            address="100 Main St",
            city="Downtown"
        )

        score_urgent, label_urgent = calculate_deadline_urgency_score(urgent_donation)
        score_relaxed, label_relaxed = calculate_deadline_urgency_score(relaxed_donation)

        assert score_urgent > score_relaxed
        assert score_urgent == 1.0
        assert "Critical" in label_urgent

def test_rank_donations_for_recipient(app, test_recipient, test_donation):
    """Test ranking returns explainable reasons and percentage scores."""
    with app.app_context():
        user = User.query.get(test_recipient)
        ranked = rank_donations_for_recipient(user)

        assert len(ranked) >= 1
        top_match = ranked[0]
        assert 'match_score' in top_match
        assert 0 <= top_match['match_score'] <= 100
        assert 'explanations' in top_match
        assert len(top_match['explanations']) > 0
        assert 'distance_label' in top_match
