from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app.models import Donation, Notification, utcnow
from app.services.notifications import mark_notification_as_read, mark_all_notifications_read

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/donations-map')
def donations_map():
    """Returns active donations with coordinates for Leaflet map markers."""
    donations = Donation.query.filter(
        Donation.status.in_(['Available', 'Request Pending']),
        Donation.remaining_quantity > 0,
        Donation.pickup_deadline > utcnow()
    ).all()

    markers = []
    for d in donations:
        # If explicit coordinates are present, use them; otherwise provide a default cluster offset for known cities
        lat = d.latitude
        lng = d.longitude

        # Fallback coordinates for demo cities if not explicitly set
        if lat is None or lng is None:
            city_coords = {
                'New York': (40.7128, -74.0060),
                'San Francisco': (37.7749, -122.4194),
                'Chicago': (41.8781, -87.6298),
                'Seattle': (47.6062, -122.3321),
                'Boston': (42.3601, -71.0589),
                'Austin': (30.2672, -97.7431),
                'Mumbai': (19.0760, 72.8777),
                'Delhi': (28.6139, 77.2090),
                'Bangalore': (12.9716, 77.5946),
                'London': (51.5074, -0.1278)
            }
            city_norm = d.city.strip().title() if d.city else ''
            if city_norm in city_coords:
                base_lat, base_lng = city_coords[city_norm]
                # small jitter for multiple donations in same city
                jitter = (d.id % 7 - 3) * 0.008
                lat = base_lat + jitter
                lng = base_lng + jitter

        if lat is not None and lng is not None:
            markers.append({
                'id': d.id,
                'title': d.title,
                'category': d.category,
                'dietary_type': d.dietary_type,
                'quantity': d.remaining_quantity,
                'unit': d.quantity_unit,
                'address': d.address,
                'city': d.city,
                'lat': lat,
                'lng': lng,
                'hours_remaining': d.hours_remaining,
                'urgency': d.urgency_level,
                'detail_url': f"/donations/{d.id}",
                'image_url': f"/static/uploads/{d.image_filename}" if d.image_filename else None
            })

    return jsonify({'donations': markers, 'count': len(markers)})

@api_bp.route('/notifications/unread-count')
@login_required
def unread_notifications_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})

@api_bp.route('/notifications/mark-read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    success = mark_notification_as_read(notif_id, current_user.id)
    return jsonify({'success': success})

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    mark_all_notifications_read(current_user.id)
    return jsonify({'success': True})

@api_bp.route('/notifications')
@login_required
def get_notifications():
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'type': n.notification_type,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%b %d, %H:%M')
    } for n in notifs]
    return jsonify({'notifications': data})
