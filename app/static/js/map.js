/**
 * FoodBridge - Interactive Map System with Leaflet & OpenStreetMap
 */

let donationMap = null;
let markersLayer = null;
let userMarker = null;

document.addEventListener('DOMContentLoaded', () => {
  const mapElement = document.getElementById('map');
  if (mapElement) {
    initDonationMap();
  }
});

async function initDonationMap() {
  // Default coordinate center (fallback: Central / City center)
  const defaultLat = 40.7128;
  const defaultLng = -74.0060;
  const defaultZoom = 12;

  // Initialize Leaflet map
  donationMap = L.map('map').setView([defaultLat, defaultLng], defaultZoom);

  // Add OpenStreetMap tile layer (Free, no API key required)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(donationMap);

  markersLayer = L.layerGroup().addTo(donationMap);

  // Request browser location if permitted
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const userLat = pos.coords.latitude;
        const userLng = pos.coords.longitude;

        // User location marker
        const userIcon = L.divIcon({
          className: 'user-location-marker',
          html: `<div style="background-color:#2563eb; width:16px; height:16px; border-radius:50%; border:3px solid white; box-shadow:0 0 10px rgba(37,99,235,0.6);"></div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });

        userMarker = L.marker([userLat, userLng], { icon: userIcon })
          .addTo(donationMap)
          .bindPopup('<b>Your Current Location</b>');

        donationMap.setView([userLat, userLng], 13);
      },
      (err) => {
        console.log('Location permission denied or unavailable. Using default map viewpoint.');
      }
    );
  }

  // Load donation markers from API
  await loadDonationMarkers();

  // Bind filter inputs
  const citySelect = document.getElementById('mapCityFilter');
  const catSelect = document.getElementById('mapCategoryFilter');

  if (citySelect) {
    citySelect.addEventListener('change', () => loadDonationMarkers());
  }
  if (catSelect) {
    catSelect.addEventListener('change', () => loadDonationMarkers());
  }
}

async function loadDonationMarkers() {
  if (!markersLayer) return;
  markersLayer.clearLayers();

  const cityFilter = document.getElementById('mapCityFilter')?.value || '';
  const categoryFilter = document.getElementById('mapCategoryFilter')?.value || 'all';

  try {
    const res = await fetch('/api/donations-map');
    if (!res.ok) throw new Error('Failed to fetch map data');
    const data = await res.json();
    let donations = data.donations || [];

    // Filter client-side if needed
    if (cityFilter && cityFilter !== 'all') {
      donations = donations.filter(d => d.city && d.city.toLowerCase().includes(cityFilter.toLowerCase()));
    }
    if (categoryFilter && categoryFilter !== 'all') {
      donations = donations.filter(d => d.category === categoryFilter);
    }

    if (donations.length === 0) {
      return;
    }

    const bounds = [];

    donations.forEach(d => {
      if (d.lat && d.lng) {
        bounds.push([d.lat, d.lng]);

        // Marker color based on urgency
        let markerColor = '#2d6a4f'; // standard forest green
        if (d.urgency === 'critical') markerColor = '#dc2626';
        else if (d.urgency === 'high') markerColor = '#ea580c';

        const customMarkerIcon = L.divIcon({
          className: 'custom-map-pin',
          html: `
            <div style="background-color: ${markerColor}; color: white; width: 34px; height: 34px; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 2px solid white;">
              <i class="fa-solid fa-utensils" style="transform: rotate(45deg); font-size: 14px;"></i>
            </div>
          `,
          iconSize: [34, 34],
          iconAnchor: [17, 34],
          popupAnchor: [0, -30]
        });

        const popupContent = `
          <div class="map-popup-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
              <span class="badge ${d.dietary_type === 'Vegetarian' ? 'badge-success' : 'badge-warning'}">${d.dietary_type}</span>
              <span class="badge urgency-${d.urgency}">${d.hours_remaining}h left</span>
            </div>
            <h4>${escapeHtml(d.title)}</h4>
            <div class="map-popup-meta">
              <strong>${d.quantity} ${d.unit}</strong> • ${d.category}<br>
              <i class="fa-solid fa-location-dot" style="color:var(--primary-600); margin-right:4px;"></i>${escapeHtml(d.address)}, ${escapeHtml(d.city)}
            </div>
            <a href="${d.detail_url}" class="btn btn-primary btn-sm" style="width:100%; text-align:center;">
              View & Request
            </a>
          </div>
        `;

        const marker = L.marker([d.lat, d.lng], { icon: customMarkerIcon })
          .bindPopup(popupContent);

        markersLayer.addLayer(marker);
      }
    });

    // Fit map bounds to encompass all visible markers
    if (bounds.length > 0 && donationMap) {
      donationMap.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  } catch (err) {
    console.error('Error rendering donation map markers:', err);
  }
}
