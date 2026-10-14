# FoodBridge – Smart Food Donation Network
> **Reducing Food Waste Through Smart, Explainable Food Sharing & Redistribution**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Flask 3.0](https://img.shields.io/badge/flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hackathon: Ready](https://img.shields.io/badge/Hackathon-Production--Grade-forestgreen.svg)]()

FoodBridge is a full-stack social-impact web application that solves urban food insecurity and commercial food waste by connecting hotels, restaurants, banquets, and university dining services with verified local NGOs, homeless shelters, orphanages, and community kitchens before safe consumption windows expire.

---

## 🌟 Key Innovations & Features

### 1. Explainable Smart Donation Matching Algorithm
Unlike opaque matching, FoodBridge uses a transparent, explainable 4-factor scoring algorithm:
- **Geographic Proximity (35%)**: Great-circle Haversine distance formula with graceful fallback to city/district matching.
- **Deadline Urgency (30%)**: Normalized remaining window prioritizing items within 2–6 hours of expiry.
- **Quantity Compatibility (25%)**: Evaluates donation volume against recipient organization distribution capacity (meals/people served).
- **Category Preferences (10%)**: Direct match with recipient charity dietary and food category specialties.

Every recommendation displays understandable reasoning (e.g., *"Recommended because this donation is 1.2 km away, matches your 100-person capacity, and has an urgent 3.5h collection window"*).

### 2. Reliable Donation Lifecycle State Machine
Guarantees database consistency through server-side state transitions:
`Available` &rarr; `Request Pending` &rarr; `Accepted` &rarr; `Ready for Pickup` &rarr; `Collected` &rarr; `Completed` (or `Cancelled` / `Expired`).
- **Atomic Quantity Decrementing**: Prevents over-allocation when multiple requests compete.
- **Automated Deadline Expiration**: Periodically expires overdue listings and notifies stakeholders.
- **Immutable Audit Trail**: Every status transition logs timestamp, actor, previous state, new state, and notes to `DonationStatusHistory`.

### 3. Food Safety & Temperature Compliance System
- **Mandatory Safe Holding Declarations**: Cold holding (<4°C), Hot holding (>60°C), Deep freeze (<-18°C), Ambient.
- **Allergen Advisories & Packaging Standards**: Mandatory packaging description and allergen disclosures.
- **Interactive Safety Checklist**: Temperature danger zone visualization and regulatory disclaimers.

### 4. Interactive Live Food Map (Leaflet + OpenStreetMap)
- Zero paid API dependencies.
- Custom urgency-coded map pins (Normal, High Urgency <6h, Critical <2h).
- Clickable popup cards with thumbnail, quantity badge, and direct request link.
- Accessible coordinated list view alternative for low-bandwidth clients.

### 5. Impact Analytics (Chart.js)
- Real-time database metrics: total meals supported, CO2e greenhouse emissions prevented (based on EPA WARM landfill diversion formulas: 2.5 kg CO2e / kg food).
- Dynamic Doughnut and Bar charts for food category distribution and lifecycle health.

### 6. Role-Based Portals & Verification
- **Food Donor Dashboard**: Create listings, review incoming NGO requests, accept/reject, coordinate pickups.
- **Recipient NGO Dashboard**: Browse recommendations, request donations, confirm collections, submit verification credentials.
- **Administrator Portal**: Review NGO registration documents, approve/reject partners, suspend abusive accounts, moderate listings, inspect audit logs.

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Pip

### 1. Clone & Enter Directory
```bash
cd fooddonation
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Seed Realistic Demo Data
```bash
python seed.py
```
*This initializes the SQLite database schema and seeds multiple restaurants, hotels, colleges, verified NGOs, active requests, notifications, and status history logs.*

### 4. Run Application
```bash
python run.py
```
Visit **`http://localhost:5000`** in your browser.

---

## 🔑 Demo Accounts for Presentation

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@foodbridge.org` | `admin123` | Full admin moderation & NGO verification |
| **Food Donor** | `donor@grandhotel.com` | `password123` | Grand Plaza Hotel & Culinary Kitchen |
| **Recipient NGO** | `info@hopeorphanage.org` | `password123` | Hope Children's Home (Verified Partner) |
| **Recipient NGO (Pending)** | `outreach@compassion.org` | `password123` | Compassion Outreach (Pending Verification) |

*Tip: The login page includes quick **1-click Fill** buttons for hackathon demonstration.*

---

## 🧪 Running Automated Tests

Run the full pytest suite:
```bash
python -m pytest -v
```

The test suite covers:
- User registration, duplicate email rejection, session authentication, and account suspension.
- Role-based access control (`@donor_required`, `@recipient_required`, `@admin_required`).
- Safe pickup deadline validation (rejects expired or negative dates).
- Quantity validation and over-allocation limits.
- Duplicate request prevention for identical organizations.
- Atomic state transitions, status history logging, and auto-expiration.
- Explainable matching algorithm math and distance calculations.
- Administrator verification approvals, moderation, and user toggling.

---

## 📂 Project Directory Structure

```text
fooddonation/
│
├── app/
│   ├── __init__.py              # Application factory & Jinja filters
│   ├── models.py                # SQLAlchemy ORM models & relationships
│   ├── forms.py                 # Flask-WTF validation forms
│   │
│   ├── routes/
│   │   ├── auth.py              # Login, register, logout, profile
│   │   ├── donor.py             # Donor dashboard, create, manage listings
│   │   ├── recipient.py         # NGO dashboard, browse, request, verify
│   │   ├── donations.py         # Detail view, interactive map view
│   │   ├── admin.py             # Admin portal, verifications, moderation
│   │   ├── main.py              # Landing page, impact analytics, safety guide
│   │   ├── api.py               # Map GeoJSON, async notifications API
│   │   └── decorators.py        # Role-based route decorators
│   │
│   ├── services/
│   │   ├── matching.py          # 4-factor explainable matching algorithm
│   │   ├── lifecycle.py         # Atomic state machine & safe transitions
│   │   └── notifications.py     # In-app notification dispatcher
│   │
│   ├── templates/               # Responsive Jinja2 HTML5 templates
│   │   ├── base.html            # Core layout, navbar, footer, modals
│   │   ├── index.html           # Landing page with real-time stats
│   │   ├── auth/                # Login & register pages
│   │   ├── donor/               # Donor dashboard & listing creation
│   │   ├── recipient/           # NGO dashboard, browse & my requests
│   │   ├── donations/           # Donation detail & Leaflet map view
│   │   ├── admin/               # Admin dashboard, audit logs, verifications
│   │   ├── analytics/           # Impact charts (Chart.js)
│   │   ├── safety/              # Food safety checklist & temperature zones
│   │   ├── profile/             # Profile settings
│   │   └── errors/              # 403, 404, 500 custom error pages
│   │
│   └── static/
│       ├── css/style.css        # Clean forest-green design system
│       ├── js/main.js           # Toasts, modals, countdown timers, notifications
│       └── js/map.js            # Leaflet + OpenStreetMap interactive pins
│
├── tests/                       # Automated pytest suite
│   ├── conftest.py              # Pytest fixtures & in-memory test DB
│   ├── test_auth.py             # Authentication & role authorization tests
│   ├── test_donations.py        # Donation creation & validation tests
│   ├── test_requests.py         # Donation requests & quantity limits
│   ├── test_lifecycle.py        # State transitions & auto-expiration tests
│   ├── test_matching.py         # Multi-factor matching scoring tests
│   └── test_admin.py            # Admin verifications & moderation tests
│
├── config.py                    # Dev, testing, and prod configurations
├── seed.py                      # Realistic demonstration data generator
├── run.py                       # Application execution entry point
├── requirements.txt             # Project dependencies
└── README.md                    # Project documentation
```

---

## 🛡️ Food Safety & Legal Framework
FoodBridge is built around Good Samaritan principles and food hygiene standards:
1. **Mandatory Disclosures**: Preparation time, allergen warnings, holding temperatures.
2. **Strict Expiry Automation**: Expired donations are locked and removed from public discovery.
3. **Verified Organizations**: Sensitive high-volume donations require verified non-profit credentials.
4. **Transparent Estimates**: Environmental and nutritional stats are labeled as defensible scientific estimates.

---

## 👥 Hackathon Team & Presentation Notes
- **Problem Category**: Food Waste Reduction, Zero Hunger (UN SDG 2 & 12).
- **Target Audience**: Restaurants, banquet venues, university dining halls, community shelters, soup kitchens.
- **Tech Stack Choices**: Selected for maximum reliability, speed, zero paid API costs, and cross-platform compatibility.
