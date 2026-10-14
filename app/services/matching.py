import math
from app.models import Donation, Organization, utcnow

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates great-circle distance between two points in kilometers
    using the Haversine formula.
    """
    if None in (lat1, lon1, lat2, lon2):
        return None

    # Radius of earth in kilometers
    R = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c
    return round(distance, 1)

def calculate_proximity_score(donation, recipient_org):
    """
    Calculates normalized proximity score (0 to 1.0) and distance details.
    Weight: 35%
    """
    if recipient_org and recipient_org.latitude and recipient_org.longitude and donation.latitude and donation.longitude:
        dist_km = haversine_distance(
            recipient_org.latitude, recipient_org.longitude,
            donation.latitude, donation.longitude
        )
        if dist_km is not None:
            # Score formula: 1.0 at 0km, decreasing to 0.5 at 10km, 0.2 at 25km, min 0.05
            if dist_km <= 2.0:
                score = 1.0
            elif dist_km <= 10.0:
                score = 1.0 - ((dist_km - 2.0) / 8.0) * 0.4  # 1.0 down to 0.6
            elif dist_km <= 25.0:
                score = 0.6 - ((dist_km - 10.0) / 15.0) * 0.4  # 0.6 down to 0.2
            else:
                score = max(0.05, 0.2 - ((dist_km - 25.0) / 25.0) * 0.15)
            
            return score, f"{dist_km} km away", dist_km

    # Fallback to city matching when coordinates unavailable
    if recipient_org and recipient_org.city and donation.city:
        if recipient_org.city.strip().lower() == donation.city.strip().lower():
            return 0.75, f"Same city ({donation.city})", None
        else:
            return 0.25, f"Different city ({donation.city})", None

    return 0.4, "Location approximate", None

def calculate_deadline_urgency_score(donation):
    """
    Calculates deadline urgency score (0 to 1.0) based on remaining hours.
    Weight: 30%
    High urgency (2-6 hours remaining) receives highest score to prevent waste,
    while safe pickup window remains valid.
    """
    hrs = donation.hours_remaining
    if hrs <= 0:
        return 0.0, "Expired"

    if hrs <= 2.0:
        return 1.0, f"Critical urgency ({hrs}h left)"
    elif hrs <= 6.0:
        return 0.90, f"High urgency ({hrs}h left)"
    elif hrs <= 12.0:
        return 0.75, f"Moderate window ({hrs}h left)"
    elif hrs <= 24.0:
        return 0.55, f"Ample time ({hrs}h left)"
    else:
        days = round(hrs / 24.0, 1)
        return 0.35, f"Extended window ({days} days left)"

def calculate_quantity_compatibility_score(donation, recipient_org):
    """
    Calculates quantity compatibility score (0 to 1.0).
    Weight: 25%
    Matches donation quantity against recipient organization distribution capacity.
    """
    target_capacity = recipient_org.capacity_servings if recipient_org and recipient_org.capacity_servings else 100
    
    # Estimate donation portions/servings
    donation_servings = donation.estimated_meals
    if donation_servings <= 0:
        return 0.2, "Unknown volume"

    ratio = donation_servings / float(target_capacity)
    
    # Ideal range: 0.5 to 1.2 times org capacity
    if 0.5 <= ratio <= 1.2:
        score = 1.0
        reason = f"Ideal fit for your ~{target_capacity} distribution capacity ({donation_servings} meals)"
    elif 0.25 <= ratio < 0.5:
        score = 0.75
        reason = f"Good smaller batch ({donation_servings} meals vs {target_capacity} capacity)"
    elif 1.2 < ratio <= 2.5:
        score = 0.80
        reason = f"Large batch ({donation_servings} meals) - partial request possible"
    else:
        score = 0.50
        reason = f"Capacity mismatch ({donation_servings} meals vs {target_capacity} capacity)"

    return score, reason

def calculate_category_score(donation, recipient_org):
    """
    Calculates category preference score (0 to 1.0).
    Weight: 10%
    """
    if not recipient_org or not recipient_org.preferred_categories:
        return 0.7, "Standard category match"

    prefs = [c.strip().lower() for c in recipient_org.preferred_categories.split(',')]
    cat_lower = donation.category.strip().lower()

    if any(p in cat_lower or cat_lower in p for p in prefs if p):
        return 1.0, f"Matches your preferred food type ({donation.category})"
    else:
        return 0.35, f"Category: {donation.category}"

def rank_donations_for_recipient(recipient_user, limit=20, category_filter=None, dietary_filter=None, city_filter=None):
    """
    Executes explainable multi-factor ranking for an organization user.
    Weights:
      - Proximity: 35%
      - Urgency: 30%
      - Quantity: 25%
      - Category: 10%
    """
    org = recipient_user.organization if recipient_user else None
    
    query = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.remaining_quantity > 0,
        Donation.pickup_deadline > utcnow()
    )

    if category_filter and category_filter != 'all':
        query = query.filter(Donation.category == category_filter)

    if dietary_filter and dietary_filter != 'all':
        query = query.filter(Donation.dietary_type == dietary_filter)

    if city_filter and city_filter != 'all':
        query = query.filter(Donation.city.ilike(f"%{city_filter}%"))

    candidates = query.all()
    ranked_results = []

    for donation in candidates:
        prox_score, prox_label, dist_km = calculate_proximity_score(donation, org)
        urg_score, urg_label = calculate_deadline_urgency_score(donation)
        quant_score, quant_label = calculate_quantity_compatibility_score(donation, org)
        cat_score, cat_label = calculate_category_score(donation, org)

        # Weighted calculation
        total_score = (
            (0.35 * prox_score) +
            (0.30 * urg_score) +
            (0.25 * quant_score) +
            (0.10 * cat_score)
        )
        match_percentage = round(total_score * 100)

        # Human-readable explanation summary
        explanations = []
        if urg_score >= 0.75:
            explanations.append(urg_label)
        if prox_score >= 0.6:
            explanations.append(prox_label)
        if quant_score >= 0.75:
            explanations.append(quant_label)
        if cat_score >= 0.9:
            explanations.append(cat_label)

        if not explanations:
            explanations.append("Meets standard availability criteria")

        ranked_results.append({
            'donation': donation,
            'match_score': match_percentage,
            'explanations': explanations,
            'distance_label': prox_label,
            'distance_km': dist_km,
            'urgency_label': urg_label
        })

    # Sort descending by match_score
    ranked_results.sort(key=lambda x: x['match_score'], reverse=True)

    if limit:
        return ranked_results[:limit]
    return ranked_results
