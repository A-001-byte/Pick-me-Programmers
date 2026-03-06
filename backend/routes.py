import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Blueprint, request, jsonify, current_app, Response
from backend.database import get_db_connection, add_alert, add_incident
from core.stream_manager import stream_manager
import time
from werkzeug.security import check_password_hash, generate_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
api_bp = Blueprint('api', __name__)

MAX_LIMIT = 100


def token_required(roles=None, optional=False):
    """
    Decorator to protect endpoints with PyJWT authentication.
    Optionally enforces role-based access control.
    Roles: admin, security, operator, viewer
    If optional=True, allows unauthenticated access but still validates tokens if present.
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
                if optional:
                    # Allow unauthenticated access
                    return f(*args, **kwargs)
                return jsonify({'error': 'Token is missing'}), 401

            try:
                # Decode the token
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                current_user_role = data.get('role')

                # Verify role
                if roles and current_user_role not in roles:
                    return jsonify({'error': 'Permission denied. Invalid role.'}), 403

            except jwt.ExpiredSignatureError:
                # If optional and NO token was provided, allow anonymous access
                # But if a token WAS provided (even if invalid/expired), reject
                if optional and not token:
                    return f(*args, **kwargs)
                return jsonify({'error': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                # If optional and NO token was provided, allow anonymous access
                # But if a token WAS provided (even if invalid), reject
                if optional and not token:
                    return f(*args, **kwargs)
                return jsonify({'error': 'Invalid token'}), 401

            return f(*args, **kwargs)
        return decorated
    return decorator


@api_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
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
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm="HS256")

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'role': user['role']
        }), 200

    return jsonify({'error': 'Invalid username or password'}), 401


@api_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not data:
        return jsonify({'message': 'Missing request body'}), 400

    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return jsonify({'message': 'Username already exists'}), 409

        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash, role, status, last_active) VALUES (?, ?, ?, ?, ?)',
            (username, generate_password_hash(password), 'operator', 'Active', 'Just now')
        )
        conn.commit()
    finally:
        conn.close()

    # Email is accepted for API parity but not stored in current schema.
    return jsonify({'message': 'Registration successful', 'username': username}), 201


@api_bp.route('/me', methods=['GET'])
@token_required()
def get_me():
    """Return the current user's profile from their JWT."""
    token = None
    if 'Authorization' in request.headers:
        parts = request.headers['Authorization'].split()
        if len(parts) == 2 and parts[0] == 'Bearer':
            token = parts[1]
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'username': data.get('username'), 'role': data.get('role')}), 200
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

@api_bp.route('/alerts', methods=['GET'])
@token_required(roles=['admin', 'security', 'operator', 'viewer'], optional=True)
def get_alerts():
    limit = request.args.get('limit', 50, type=int)
    limit = max(1, min(limit, MAX_LIMIT))

    conn = get_db_connection()
    alerts = conn.execute('SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?', (limit,)).fetchall()
    conn.close()

    return jsonify([dict(row) for row in alerts]), 200


@api_bp.route('/alerts', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def create_alert():
    """Create a new alert (primarily for testing and manual insertion)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    # Required fields
    event_type = data.get('event_type')
    risk_score = data.get('risk_score')
    
    if not event_type or risk_score is None:
        return jsonify({'error': 'Missing required fields: event_type, risk_score'}), 400

    # Optional fields with defaults
    person_id = data.get('person_id', 'UNKNOWN')
    risk_level = data.get('risk_level', 'low')
    camera_id = data.get('camera_id', 'CAM-01')
    location = data.get('location', 'Main Entrance')
    status = data.get('status', 'Active')

    # Validate risk_score before calling add_alert
    try:
        risk_score_float = float(risk_score)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid risk_score: must be a number'}), 400

    try:
        alert_id = add_alert(
            person_id=person_id,
            event_type=event_type,
            risk_score=risk_score_float,
            risk_level=risk_level,
            camera_id=camera_id,
            location=location,
            status=status
        )
        return jsonify({'message': 'Alert created', 'id': alert_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.exception("Failed to create alert")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/incidents', methods=['GET'])
@token_required(roles=['admin', 'security', 'operator', 'viewer'], optional=True)
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


@api_bp.route('/incidents', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def create_incident():
    """Create a new incident (primarily for testing and manual insertion)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    # Required fields
    title = data.get('title')
    if not title:
        return jsonify({'error': 'Missing required field: title'}), 400

    # Optional fields with defaults
    description = data.get('description', '')
    event_type = data.get('event_type', 'Manual Entry')
    location = data.get('location', 'Main Entrance')
    risk_level = data.get('risk_level', 'low')
    status = data.get('status', 'open')

    try:
        incident_id = add_incident(
            title=title,
            description=description,
            event_type=event_type,
            location=location,
            risk_level=risk_level,
            status=status
        )
        return jsonify({'message': 'Incident created', 'id': incident_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.exception("Failed to create incident")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/stats', methods=['GET'])
@token_required(optional=True)
def get_stats():
    conn = get_db_connection()

    total_alerts = conn.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    total_incidents = conn.execute('SELECT COUNT(*) FROM incidents').fetchone()[0]
    active_incidents = conn.execute("SELECT COUNT(*) FROM incidents WHERE status NOT IN ('Resolved', 'False Alarm')").fetchone()[0]

    # recent high risk alerts
    high_risk_alerts = conn.execute('SELECT COUNT(*) FROM alerts WHERE risk_score >= 0.8').fetchone()[0]

    # active tracks: count distinct persons with active (non-resolved/dismissed) alerts
    active_tracks = conn.execute(
        "SELECT COUNT(DISTINCT person_id) FROM alerts WHERE status NOT IN ('Resolved', 'Dismissed')"
    ).fetchone()[0]

    conn.close()

    # Pipeline metrics from stream_manager
    health = stream_manager.health()
    fps = health.get('fps')
    pipeline_running = health.get('last_frame_ts') is not None
    last_frame_age = None
    if health.get('last_frame_ts'):
        last_frame_age = round(time.time() - health['last_frame_ts'], 1)

    return jsonify({
        'total_alerts': total_alerts,
        'total_incidents': total_incidents,
        'active_incidents': active_incidents,
        'high_risk_alerts': high_risk_alerts,
        'active_tracks': active_tracks,
        'pipeline_fps': round(fps, 1) if fps else None,
        'pipeline_running': pipeline_running,
        'pipeline_frames': health.get('frames', 0),
        'last_frame_age_s': last_frame_age,
    }), 200


@api_bp.route('/users', methods=['GET'])
@token_required(roles=['admin'])
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, username, role, status, last_active FROM users ORDER BY id').fetchall()
    conn.close()

    return jsonify([dict(row) for row in users]), 200


@api_bp.route('/video_feed')
def video_feed():
    """Video streaming route. Returns MJPEG stream.
    
    Supports authentication via:
    - Authorization header (Bearer token)
    - Query parameter (?token=xxx) for use with img/video tags
    If no token is provided, stream is still allowed (dev-friendly).
    """
    # Check for token in header or query param
    token = None
    if 'Authorization' in request.headers:
        parts = request.headers['Authorization'].split()
        if len(parts) == 2 and parts[0] == 'Bearer':
            token = parts[1]
    
    # Fallback to query parameter for img/video tag support
    if not token:
        token = request.args.get('token')
    
    if token:
        try:
            jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

    def generate():
        while True:
            frame_bytes = stream_manager.get_frame_bytes()
            if frame_bytes is None:
                time.sleep(0.05)  # wait for first frame
                continue
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.016)  # ~60 FPS streaming rate (browser will throttle if needed)

    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@api_bp.route('/frame')
def single_frame():
    """Return the latest frame as a single JPEG for fallback polling."""
    token = None
    if 'Authorization' in request.headers:
        parts = request.headers['Authorization'].split()
        if len(parts) == 2 and parts[0] == 'Bearer':
            token = parts[1]
    if not token:
        token = request.args.get('token')
    if token:
        try:
            jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

    frame_bytes = stream_manager.get_frame_bytes()
    if frame_bytes is None:
        return jsonify({'error': 'No frame available'}), 503
    return Response(frame_bytes, mimetype='image/jpeg')


@api_bp.route('/system_status', methods=['GET'])
def system_status():
    """Lightweight health probe for dashboard auto-start logic."""
    health = stream_manager.health()
    now = time.time()
    last_ts = health.get("last_frame_ts") or 0
    pipeline_running = (now - last_ts) < 5
    camera_connected = pipeline_running
    fps = health.get("fps") or 0
    return jsonify({
        "pipeline_running": bool(pipeline_running),
        "camera_connected": bool(camera_connected),
        "fps": round(fps, 1) if fps else 0,
        "last_frame_ts": last_ts,
    }), 200


# ==================== ALERT ACTIONS ====================

@api_bp.route('/alerts/<int:alert_id>/dismiss', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def dismiss_alert(alert_id):
    """Dismiss an alert - removes it from active alerts."""
    conn = get_db_connection()
    result = conn.execute('UPDATE alerts SET status = ? WHERE id = ?', ('Dismissed', alert_id))
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify({'message': 'Alert dismissed', 'id': alert_id}), 200


@api_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert - marks it as under review."""
    conn = get_db_connection()
    result = conn.execute('UPDATE alerts SET status = ? WHERE id = ?', ('Under Review', alert_id))
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify({'message': 'Alert acknowledged', 'id': alert_id}), 200


@api_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def resolve_alert(alert_id):
    """Resolve an alert - marks it as resolved."""
    conn = get_db_connection()
    result = conn.execute('UPDATE alerts SET status = ? WHERE id = ?', ('Resolved', alert_id))
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify({'message': 'Alert resolved', 'id': alert_id}), 200


@api_bp.route('/alerts/bulk-dismiss', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def bulk_dismiss_alerts():
    """Dismiss all resolved alerts in a single operation."""
    conn = get_db_connection()
    result = conn.execute(
        "UPDATE alerts SET status = 'Dismissed' WHERE status IN ('Resolved', 'Active')"
    )
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    return jsonify({'message': f'{rows_affected} alerts dismissed', 'count': rows_affected}), 200

# ==================== INCIDENT ACTIONS ====================

@api_bp.route('/incidents/<int:incident_id>/resolve', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def resolve_incident(incident_id):
    """Resolve an incident - marks it as resolved with timestamp."""
    conn = get_db_connection()
    result = conn.execute(
        'UPDATE incidents SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?',
        ('Resolved', incident_id)
    )
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify({'message': 'Incident resolved', 'id': incident_id}), 200


@api_bp.route('/incidents/<int:incident_id>/escalate', methods=['POST'])
@token_required(roles=['admin', 'security', 'operator'])
def escalate_incident(incident_id):
    """Escalate an incident - raises its priority."""
    conn = get_db_connection()
    # Also upgrade risk_level to high if not already
    result = conn.execute(
        "UPDATE incidents SET status = ?, risk_level = CASE WHEN risk_level = 'low' THEN 'medium' WHEN risk_level = 'medium' THEN 'high' ELSE risk_level END WHERE id = ?",
        ('Escalated', incident_id)
    )
    conn.commit()
    rows_affected = result.rowcount
    conn.close()
    
    if rows_affected == 0:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify({'message': 'Incident escalated', 'id': incident_id}), 200


@api_bp.route('/incidents/<int:incident_id>', methods=['GET'])
@token_required(roles=['admin', 'security', 'operator', 'viewer'], optional=True)
def get_incident(incident_id):
    """Get a single incident by ID."""
    conn = get_db_connection()
    incident = conn.execute('SELECT * FROM incidents WHERE id = ?', (incident_id,)).fetchone()
    conn.close()
    
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify(dict(incident)), 200


# ==================== USER MANAGEMENT ====================

@api_bp.route('/users', methods=['POST'])
@token_required(roles=['admin'])
def create_user():
    """Create a new user."""
    from werkzeug.security import generate_password_hash
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400
    
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'viewer')
    
    if not username or not password:
        return jsonify({'error': 'Missing required fields: username, password'}), 400
    
    if role not in ['admin', 'operator', 'viewer', 'security']:
        return jsonify({'error': 'Invalid role. Must be: admin, operator, viewer, security'}), 400
    
    conn = get_db_connection()
    
    # Check if username already exists
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'error': 'Username already exists'}), 409
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash, role, status, last_active) VALUES (?, ?, ?, ?, ?)',
            (username, generate_password_hash(password), role, 'Active', 'Just now')
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return jsonify({'message': 'User created', 'id': user_id}), 201
    except Exception as e:
        conn.close()
        current_app.logger.exception("Failed to create user")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required(roles=['admin'])
def update_user(user_id):
    """Update an existing user."""
    from werkzeug.security import generate_password_hash
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400
    
    conn = get_db_connection()
    
    # Check if user exists
    existing = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Build update query dynamically
    updates = []
    values = []
    
    if 'username' in data:
        # Check if new username is taken by another user
        other = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?', (data['username'], user_id)).fetchone()
        if other:
            conn.close()
            return jsonify({'error': 'Username already taken'}), 409
        updates.append('username = ?')
        values.append(data['username'])
    
    if 'password' in data and data['password']:
        updates.append('password_hash = ?')
        values.append(generate_password_hash(data['password']))
    
    if 'role' in data:
        if data['role'] not in ['admin', 'operator', 'viewer', 'security']:
            conn.close()
            return jsonify({'error': 'Invalid role'}), 400
        updates.append('role = ?')
        values.append(data['role'])
    
    if 'status' in data:
        allowed_statuses = {'active', 'inactive', 'suspended'}
        status_val = str(data['status']).strip().lower()
        if status_val not in allowed_statuses:
            conn.close()
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(allowed_statuses)}'}), 400
        updates.append('status = ?')
        values.append(data['status'].strip().title())  # Normalize to Title Case
    
    if not updates:
        conn.close()
        return jsonify({'error': 'No fields to update'}), 400
    
    values.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    
    try:
        conn.execute(query, values)
        conn.commit()
        conn.close()
        return jsonify({'message': 'User updated', 'id': user_id}), 200
    except Exception as e:
        conn.close()
        current_app.logger.exception("Failed to update user")
        return jsonify({'error': 'Internal server error'}), 500


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required(roles=['admin'])
def delete_user(user_id):
    """Deactivate a user (soft delete)."""
    conn = get_db_connection()
    
    # Check if user exists
    existing = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not existing:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    # Soft delete - set status to Inactive
    conn.execute('UPDATE users SET status = ? WHERE id = ?', ('Inactive', user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'User deactivated', 'id': user_id}), 200
