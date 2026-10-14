from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

def donor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not (current_user.is_donor or current_user.is_admin):
            flash('Access denied: Donor privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def recipient_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not (current_user.is_recipient or current_user.is_admin):
            flash('Access denied: Recipient organization privileges required.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if not current_user.is_admin:
            flash('Access denied: Administrator privileges required.', 'danger')
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
