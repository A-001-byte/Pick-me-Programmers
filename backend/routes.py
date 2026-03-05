import jwt
import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from backend.database import get_db_connection
from werkzeug.security import check_password_hash

api_bp = Blueprint('api', __name__)

MAX_LIMIT = 100


def token_required(roles=None):
    """
    Decorator to protect endpoints with PyJWT authentication.
    Optionally enforces role-based access control.
    Roles: admin, security, operator, viewer
    """
    if roles is None:
        roles = ['admin', 'security', 'operator', 'viewer']

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None

            # Check for token in headers
            if 'Authorization' in request.headers:
                parts = request.headers['Authorization'].split()
                if len(parts) == 2 and parts[0] == 'Bearer':
                    token = parts[1]

            if not token:
                return jsonify({'error': 'Token is missing'}), 401

            try:
                # Decode the token
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user_role = data.get('role')

                # Verify role
                if roles and current_user_role not in roles:
                    return jsonify({'error': 'Permission denied. Invalid role.'}), 403

            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

            return f(*args, **kwargs)
        return decorated
    return decorator


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        # Generate PyJWT token
        token = jwt.encode({
            'username': user['username'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'role': user['role']
        }), 200

    return jsonify({'error': 'Invalid username or password'}), 401


@api_bp.route('/alerts', methods=['GET'])
@token_required(roles=['admin', 'security', 'operator', 'viewer'])
def get_alerts():
    limit = request.args.get('limit', 50, type=int)
    limit = max(1, min(limit, MAX_LIMIT))

    conn = get_db_connection()
    alerts = conn.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in alerts]), 200


@api_bp.route('/incidents', methods=['GET'])
@token_required(roles=['admin', 'security', 'operator', 'viewer'])
def get_incidents():
    status = request.args.get('status')
    limit = request.args.get('limit', 100, type=int)
    limit = max(1, min(limit, 1000))

    conn = get_db_connection()
    if status:
        incidents = conn.execute('SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC LIMIT ?', (status, limit)).fetchall()
    else:
        incidents = conn.execute('SELECT * FROM incidents ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in incidents]), 200


@api_bp.route('/stats', methods=['GET'])
@token_required()
def get_stats():
    conn = get_db_connection()

    total_alerts = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    total_incidents = conn.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
    active_incidents = conn.execute('SELECT COUNT(*) FROM incidents WHERE status = ?', ('open',)).fetchone()[0]

    # recent high risk alerts
    high_risk_alerts = conn.execute('SELECT COUNT(*) FROM alerts WHERE risk_score >= 0.8').fetchone()[0]

    conn.close()

    return jsonify({
        'total_alerts': total_alerts,
        'total_incidents': total_incidents,
        'active_incidents': active_incidents,
        'high_risk_alerts': high_risk_alerts
    }), 200


@api_bp.route('/users', methods=['GET'])
@token_required(roles=['admin'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role, status, last_active FROM users ORDER BY id').fetchall()
    conn.close()

    return jsonify([dict(row) for row in users]), 200
