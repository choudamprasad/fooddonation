import os
from app import create_app, db
from app.models import User, Organization, Donation, DonationRequest, Notification, DonationStatusHistory

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Organization': Organization,
        'Donation': Donation,
        'DonationRequest': DonationRequest,
        'Notification': Notification,
        'DonationStatusHistory': DonationStatusHistory
    }

@app.cli.command('init-db')
def init_db():
    """Initializes the database schema."""
    with app.app_context():
        db.create_all()
        print("Database schema created successfully.")

@app.cli.command('seed-db')
def seed_db():
    """Seeds the database with realistic demo records."""
    import seed
    with app.app_context():
        seed.run_seed()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
