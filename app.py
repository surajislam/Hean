#!/usr/bin/env python3
"""
Telegram Username Search Web App
Web-based interface for Telegram username search with hash code authentication
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import time
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from admin_data import admin_db
from searched_usernames import searched_username_manager

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'super-secret-key-change-this')

# Session and CSRF
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    PERMANENT_SESSION_LIFETIME=1800
)
csrf = CSRFProtect(app)
CORS(app, resources={r'/*': {'origins': '*'}})

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Admin credentials
ADMIN_CREDENTIALS = {
    'rxprime': os.environ.get('ADMIN_PASSWORD_HASH_1', generate_password_hash('rxprime'))
}

class TelegramUserSearch:
    def __init__(self):
        self.demo_usernames = admin_db.get_usernames()

    def search_public_info(self, username):
        if username.startswith('@'):
            username = username[1:]
        username_lower = username.lower()
        for user_data in self.demo_usernames:
            if user_data['active'] and user_data['username'].lower() == username_lower:
                return {
                    'success': True,
                    'user_data': {
                        'username': user_data['username'],
                        'mobile_number': user_data['mobile_number'],
                        'mobile_details': user_data['mobile_details']
                    }
                }
        return {'success': False, 'error': 'No details available in the database'}

searcher = TelegramUserSearch()

@app.route('/')
def home():
    if not session.get('authenticated'):
        return redirect(url_for('login_page'))
    return redirect(url_for('dashboard'))

@app.route('/login')
def login_page():
    if session.get('authenticated'):
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
@csrf.exempt
def signup():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name or len(name) < 2:
        return jsonify({'success': False, 'error': 'Please enter a valid name (min 2 chars)'}), 400
    new_user = admin_db.create_user(name)
    return jsonify({'success': True, 'hash_code': new_user['hash_code'], 'name': new_user['name']})

@app.route('/login', methods=['POST'])
@csrf.exempt
def login():
    data = request.get_json()
    hash_code = data.get('hash_code', '').strip()
    if not hash_code:
        return jsonify({'success': False, 'error': 'Enter your hash code'}), 400
    user = admin_db.get_user_by_hash(hash_code)
    if user:
        session['authenticated'] = True
        session['user_hash'] = hash_code
        session['user_name'] = user['name']
        session['user_balance'] = user['balance']
        return jsonify({'success': True, 'message': f'Welcome back, {user["name"]}!'}), 200
    return jsonify({'success': False, 'error': 'Invalid hash code'}), 401

@app.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login_page'))
    user_hash = session.get('user_hash')
    user = admin_db.get_user_by_hash(user_hash)
    balance = user['balance'] if user else 0
    return render_template('index.html', balance=balance, user_name=session.get('user_name'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/search', methods=['POST'])
@csrf.exempt
def search():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401
    data = request.get_json()
    username = data.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'error': 'Enter username'}), 400
    user_hash = session.get('user_hash')
    user = admin_db.get_user_by_hash(user_hash)
    # Free search, no balance deduction
    time.sleep(2)  # simulate delay
    result = searcher.search_public_info(username)
    if not result.get('success'):
        searched_username_manager.add_searched_username(username, user_hash)
        result['error'] = admin_db.get_custom_message()
    return jsonify(result)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'app': 'Telegram Username Search', 'version': '2.0'})

# ----- ADMIN PANEL -----
@app.route('/admin/login')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
@csrf.exempt
def admin_login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if username in ADMIN_CREDENTIALS and check_password_hash(ADMIN_CREDENTIALS[username], password):
        session['admin_authenticated'] = True
        session['admin_username'] = username
        return jsonify({'success': True, 'message': 'Admin access granted'})
    return jsonify({'success': False, 'error': 'Invalid admin credentials'}), 401

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login_page'))
    from flask_wtf.csrf import generate_csrf
    return render_template('admin_dashboard.html', csrf_token=generate_csrf)

@app.route('/admin/api/users')
def admin_get_users():
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(admin_db.get_users())

@app.route('/admin/api/users/<int:user_id>/add-balance', methods=['POST'])
@csrf.exempt
def admin_add_user_balance(user_id):
    if not session.get('admin_authenticated'):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    amount = data.get('amount', 0)
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Amount must be > 0'})
    users = admin_db.get_users()
    user_found = next((u for u in users if u['id'] == user_id), None)
    if not user_found:
        return jsonify({'success': False, 'error': 'User not found'})
    new_balance = user_found['balance'] + amount
    admin_db.update_user_balance(user_found['hash_code'], new_balance)
    return jsonify({'success': True, 'new_balance': new_balance})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)