import sys
import os
import secrets
import logging
import datetime
import time
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin

APP_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, '..', '..'))

# Load local development secrets from .env first, then legacy env.env if present.
for env_path in (
    os.path.join(PROJECT_ROOT, '.env'),
    os.path.join(PROJECT_ROOT, 'env.env'),
):
    if os.path.exists(env_path):
        load_dotenv(env_path, override=False)

# Add parent directory to path to allow importing 'compiler'
sys.path.append(os.path.abspath(os.path.join(APP_DIR, '..')))

print(">>> [DEBUG] APP STARTING UP...", flush=True)

from flask import Flask, render_template, request, jsonify, Response, session as flask_session, flash, redirect, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import current_user, login_required
import io
import contextlib
from compiler.parser import parser, compile_algo
print(">>> [DEBUG] PARSER IMPORTED", flush=True)

from web.debugger import TraceRunner
from web.models import db, Chapter, Question, Choice, Problem, TestCase, User, QuizAttempt, ChallengeSubmission, ChallengeAttemptSession, UserBadge, CourseChapter, CourseSection
from web.extensions import login_manager, oauth, mail
from web.sandbox.runner import execute_code
print(">>> [DEBUG] MODELS AND EXTENSIONS IMPORTED", flush=True)
from sqlalchemy import func, distinct
from sqlalchemy.orm import joinedload
from sqlalchemy.pool import NullPool
import json
import secrets

# Handle Windows console encoding issues for scientific/accented characters
if sys.platform == 'win32':
    try:
        import io
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import logging
# Aggressively silence all logging to prevent OSError [Errno 22] on Windows console
logging.disable(logging.CRITICAL)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)
# Fix for OAuth redirection if behind a proxy (Render, Heroku, etc.)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

PROBLEM_LEADERBOARD_CACHE_TTL_SECONDS = 60
problem_leaderboard_cache = {}
PROBLEM_DETAIL_CACHE_TTL_SECONDS = 300
problem_detail_cache = {}
problem_navigation_cache = {'expires_at': 0, 'problem_ids': []}
problem_cache_lock = threading.Lock()
USER_LEVEL_CACHE_TTL_SECONDS = 300
user_level_cache = {}
user_level_refresh_futures = {}
user_level_cache_lock = threading.Lock()
background_task_executor = ThreadPoolExecutor(
    max_workers=max(2, int(os.environ.get('BACKGROUND_TASK_WORKERS', '2')))
)

APP_BUILD_ID = (
    os.environ.get('APP_BUILD_ID')
    or os.environ.get('RENDER_GIT_COMMIT')
    or os.environ.get('GIT_COMMIT')
    or 'dev'
)
ASSET_VERSION = os.environ.get('STATIC_ASSET_VERSION') or APP_BUILD_ID[:12]


def is_truthy(value):
    return str(value or '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _is_safe_path(base_dir, requested_path):
    base_dir_abs = os.path.abspath(base_dir)
    requested_abs = os.path.abspath(requested_path)
    try:
        return os.path.commonpath([base_dir_abs, requested_abs]) == base_dir_abs
    except ValueError:
        return False


def _is_safe_redirect_target(target):
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in ('http', 'https') and host_url.netloc == redirect_url.netloc


def generate_csrf_token():
    token = flask_session.get('_csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        flask_session['_csrf_token'] = token
    return token


def get_submitted_csrf_token():
    token = request.headers.get('X-CSRF-Token')
    if token:
        return token
    token = request.form.get('csrf_token')
    if token:
        return token
    data = request.get_json(silent=True) or {}
    return data.get('csrf_token')


def csrf_error_response():
    if request.is_json or request.path.startswith('/api/') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'error': 'Invalid or missing CSRF token'}), 400

    flash('Votre session a expiré. Veuillez réessayer.', 'danger')
    if _is_safe_redirect_target(request.referrer):
        return redirect(request.referrer)
    return redirect(url_for('index'))


@app.before_request
def update_last_seen():
    if current_user.is_authenticated:
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        if current_user.last_seen is None:
            current_user.last_seen = now
            try:
                db.session.commit()
            except:
                db.session.rollback()
        else:
            # We need to make sure last_seen is offset-aware before comparing
            last_seen_utc = current_user.last_seen
            if last_seen_utc.tzinfo is None:
                last_seen_utc = last_seen_utc.replace(tzinfo=datetime.timezone.utc)
            if (now - last_seen_utc).total_seconds() > 3600:
                current_user.last_seen = now
                try:
                    db.session.commit()
                except:
                    db.session.rollback()


@app.before_request
def protect_against_csrf():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None

    expected_token = flask_session.get('_csrf_token')
    submitted_token = get_submitted_csrf_token()
    if not expected_token or not submitted_token or not secrets.compare_digest(expected_token, submitted_token):
        return csrf_error_response()
    return None


@app.teardown_request
def cleanup_db_session(exc):
    if exc is not None:
        db.session.rollback()
    db.session.remove()


# Basic Config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL')
direct_database_url = (
    os.environ.get('SUPABASE_DIRECT_URL')
    or os.environ.get('DIRECT_DATABASE_URL')
)
app_env = (os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV') or '').strip().lower()
is_local_dev = app_env not in {'production', 'prod'}
if direct_database_url and database_url and 'supabase.com:6543' in database_url and is_local_dev:
    database_url = direct_database_url
use_psycopg3 = False
if database_url:
    # Attempt to detect which driver to use
    try:
        import psycopg
        use_psycopg3 = True
    except ImportError:
        pass
    
    if database_url.startswith('postgres://'):
        driver = 'postgresql+psycopg://' if use_psycopg3 else 'postgresql://'
        database_url = database_url.replace('postgres://', driver, 1)
    elif database_url.startswith('postgresql://'):
        if use_psycopg3:
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    
    # Hide password in logs
    safe_log_url = database_url.split('@')[-1] if '@' in database_url else "HIDDEN"
    print(f">>> CONFIGURED DATABASE_URL: {safe_log_url} (Psycopg3: {use_psycopg3})", flush=True)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f"sqlite:///{os.path.join(BASE_DIR, 'algocompiler.db')}"
if not app.config['SQLALCHEMY_DATABASE_URI']:
     # Fail-safe
     app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'algocompiler.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine_options = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
}
if use_psycopg3:
    # Avoid prepared statement conflicts with PgBouncer / pooled connections
    # prepare_threshold=None disables server-side statements in psycopg3
    engine_options['connect_args'] = {
        'prepare_threshold': None,
        'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT_SECONDS', '5'))
    }

if database_url and 'pooler' in database_url:
    # Supabase pooler (PgBouncer) works best without client-side pooling
    engine_options['poolclass'] = NullPool
else:
    engine_options['pool_size'] = 10
    engine_options['max_overflow'] = 20

# Force zero statement cache to prevent DuplicatePreparedStatement errors with psycopg3
# Note: statement_cache_size is not supported with some poolers/dialects in this way
# if use_psycopg3:
#     engine_options['statement_cache_size'] = 0

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

# Production session security
session_cookie_secure = os.environ.get('SESSION_COOKIE_SECURE')
if session_cookie_secure is not None:
    app.config['SESSION_COOKIE_SECURE'] = is_truthy(session_cookie_secure)
elif database_url and not database_url.startswith('sqlite'):
    app.config['SESSION_COOKIE_SECURE'] = not is_local_dev

if database_url and not database_url.startswith('sqlite'):
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    from datetime import timedelta
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

safe_uri = app.config['SQLALCHEMY_DATABASE_URI'].split('@')[-1] if '@' in app.config['SQLALCHEMY_DATABASE_URI'] else "sqlite"
print(f">>> [DEBUG] SQLALCHEMY_DATABASE_URI: {safe_uri}", flush=True)

try:
    print(">>> [DEBUG] INITIALIZING DB...", flush=True)
    db.init_app(app)
    with app.app_context():
        should_auto_create_schema = (
            is_truthy(os.environ.get('AUTO_CREATE_DB_SCHEMA'))
            if os.environ.get('AUTO_CREATE_DB_SCHEMA') is not None
            else not (database_url and not database_url.startswith('sqlite'))
        )
        if should_auto_create_schema:
            print(">>> [DEBUG] ENSURING TABLES EXIST (db.create_all)...", flush=True)
            db.create_all()
            print(">>> [DEBUG] DB TABLES CHECKED/CREATED OK", flush=True)
        else:
            print(">>> [DEBUG] SKIPPING db.create_all() FOR MANAGED REMOTE DATABASE", flush=True)

        try:
            from web.auth import migrate_security_answers_to_hashes
            migrated_security_answers = migrate_security_answers_to_hashes()
            if migrated_security_answers:
                print(f">>> [DEBUG] SECURITY ANSWERS HASHED: {migrated_security_answers}", flush=True)
        except Exception as migrate_err:
            print(f">>> [DEBUG] SECURITY ANSWER MIGRATION FAILED (NON-FATAL): {migrate_err}", flush=True)
        
        # Auto-seed if empty
        if Question.query.count() == 0 and not os.environ.get('SKIP_SEED'):
            print(">>> [DEBUG] DB EMPTY. SEEDING FROM JSON...", flush=True)
            try:
                from web.seed_from_json import seed_from_json
                seed_from_json()
                print(">>> [DEBUG] SEEDING COMPLETED", flush=True)
            except Exception as seed_err:
                print(f">>> [DEBUG] SEEDING FAILED (NON-FATAL): {seed_err}", flush=True)
except Exception as e:
    print(f">>> [CRITICAL] DB SETUP FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

# Mail Config (Resend defaults for easier testing)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.resend.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', 'on', '1']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'resend')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'onboarding@resend.dev')

# OAuth Config Placeholder
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', 'placeholder')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', 'placeholder')
app.config['GITHUB_CLIENT_ID'] = os.environ.get('GITHUB_CLIENT_ID', 'placeholder')
app.config['GITHUB_CLIENT_SECRET'] = os.environ.get('GITHUB_CLIENT_SECRET', 'placeholder')

# Initialize extensions
login_manager.init_app(app)
oauth.init_app(app)
mail.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_supabase_credentials():
    # Inject announcement modified time
    announcement_path = os.path.join(app.root_path, 'templates', 'announcement.html')
    mtime = 0
    if os.path.exists(announcement_path):
        mtime = int(os.path.getmtime(announcement_path))
        
    return {
        'INJECTED_SUPABASE_URL': os.environ.get('SUPABASE_URL', ''),
        'INJECTED_SUPABASE_ANON_KEY': os.environ.get('SUPABASE_ANON_KEY', ''),
        'ANNOUNCEMENT_MTIME': mtime,
        'APP_BUILD_ID': APP_BUILD_ID,
        'ASSET_VERSION': ASSET_VERSION,
        'csrf_token': generate_csrf_token
    }

# Register Auth Blueprint
from web.auth import auth_bp
app.register_blueprint(auth_bp)

# Register Admin Blueprint (Teacher Dashboard at /admin)
from web.admin import admin_bp
app.register_blueprint(admin_bp)

# Correct path to examples and fixtures
EXAMPLES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'examples'))
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'tests', 'fixtures'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/announcement')
def announcement():
    return render_template('announcement.html')

from flask import send_from_directory
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/course')
def course():
    return render_template('course.html')

@app.route('/demo-course/<path:filename>')
@app.route('/demoCourse/<path:filename>')
def demo_course_file(filename):
    full_path = os.path.join(os.path.join(app.root_path, 'DemoCourse'), filename)
    if not _is_safe_path(os.path.join(app.root_path, 'DemoCourse'), full_path):
        return jsonify({'error': 'Invalid filename'}), 400
    return send_from_directory(os.path.join(app.root_path, 'DemoCourse'), filename)

@app.route('/api/course', methods=['GET'])
def get_course():
    chapters = CourseChapter.query.filter_by(is_published=True).order_by(CourseChapter.order_index.asc(), CourseChapter.id.asc()).all()
    items = []
    for c in chapters:
        items.append({
            'id': c.identifier,
            'title': c.title,
            'icon': c.icon,
            'file': f"/api/course/chapters/{c.identifier}",
            'sections': []
        })
    return jsonify({'chapters': items})


@app.route('/api/course/chapters/<string:identifier>', methods=['GET'])
def get_course_chapter(identifier):
    chapter = CourseChapter.query.filter_by(identifier=identifier, is_published=True).first()
    if not chapter:
        return jsonify({'error': 'Not found'}), 404
    sections = CourseSection.query.filter_by(chapter_id=chapter.id).order_by(CourseSection.order_index.asc(), CourseSection.id.asc()).all()
    return jsonify({
        'id': chapter.identifier,
        'title': chapter.title,
        'sections': [
            {'title': s.title, 'content': s.content, 'code': s.code}
            for s in sections
        ]
    })

@app.route('/progress')
@login_required
def progress_page():
    initial_progress = None
    try:
        progress_response = get_user_progress()
        if isinstance(progress_response, tuple):
            progress_response = progress_response[0]
        if hasattr(progress_response, 'get_json'):
            initial_progress = progress_response.get_json(silent=True)
    except Exception:
        initial_progress = None
    return render_template('progress.html', initial_progress=initial_progress)

@app.route('/problems')
def problems_page():
    return render_template('problems.html')

@app.route('/challenge/<int:problem_id>')
def challenge_page(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return render_template('errors.html'), 404
    if not problem.is_published:
        return render_template('errors.html'), 403
    if current_user.is_authenticated:
        get_or_create_active_attempt_session(current_user.id, problem_id)
    return render_template('challenge.html', problem_id=problem_id)

def utcnow():
    return datetime.datetime.utcnow()

def decimal_to_float(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def safe_metric_sort_value(value):
    converted = decimal_to_float(value)
    return converted if converted is not None else float('inf')

def average_metric_from_json(metrics_json, key):
    if not isinstance(metrics_json, list):
        return None
    values = []
    for item in metrics_json:
        if not isinstance(item, dict):
            continue
        numeric_value = decimal_to_float(item.get(key))
        if numeric_value is not None:
            values.append(numeric_value)
    if not values:
        return None
    return round(sum(values) / len(values), 3)

def build_test_case_metrics(results):
    return [
        {
            'test_case_id': result.get('test_case_id'),
            'passed': bool(result.get('passed')),
            'execution_time_ms': round(float(result.get('execution_time_ms') or 0.0), 3),
            'memory_usage_kb': int(result.get('memory_usage_kb') or 0),
            'error': result.get('error')
        }
        for result in results
    ]

def get_or_create_active_attempt_session(user_id, problem_id):
    session = (
        ChallengeAttemptSession.query
        .filter_by(user_id=user_id, problem_id=problem_id, completed_at=None)
        .order_by(ChallengeAttemptSession.started_at.desc())
        .first()
    )
    if session:
        return session

    session = ChallengeAttemptSession(
        user_id=user_id,
        problem_id=problem_id,
        started_at=utcnow(),
        created_at=utcnow()
    )
    db.session.add(session)
    db.session.commit()
    return session

def invalidate_problem_leaderboard_cache(problem_id=None):
    if problem_id is None:
        problem_leaderboard_cache.clear()
        return
    problem_leaderboard_cache.pop(int(problem_id), None)


def invalidate_problem_detail_cache(problem_id=None):
    with problem_cache_lock:
        if problem_id is None:
            problem_detail_cache.clear()
            problem_navigation_cache['expires_at'] = 0
            problem_navigation_cache['problem_ids'] = []
            return

        problem_detail_cache.pop(int(problem_id), None)
        problem_navigation_cache['expires_at'] = 0
        problem_navigation_cache['problem_ids'] = []


def get_cached_problem_payload(problem_id):
    now_ts = time.time()
    cache_key = int(problem_id)
    with problem_cache_lock:
        cached_entry = problem_detail_cache.get(cache_key)
        if cached_entry and cached_entry['expires_at'] > now_ts:
            return cached_entry['payload']

    problem = (
        Problem.query
        .options(joinedload(Problem.test_cases))
        .filter(Problem.id == cache_key)
        .first()
    )
    if not problem:
        return None

    payload = {
        'id': problem.id,
        'title': problem.title,
        'description': problem.description,
        'topic': problem.topic,
        'difficulty': problem.difficulty,
        'template_code': problem.template_code,
        'is_published': bool(problem.is_published),
        'test_cases': [
            {
                'id': tc.id,
                'input': tc.input_data,
                'expected_output': tc.expected_output
            }
            for tc in problem.test_cases if tc.is_public
        ]
    }
    with problem_cache_lock:
        problem_detail_cache[cache_key] = {
            'expires_at': now_ts + PROBLEM_DETAIL_CACHE_TTL_SECONDS,
            'payload': payload
        }
    return payload


def get_cached_navigation_problem_ids():
    now_ts = time.time()
    with problem_cache_lock:
        if problem_navigation_cache['expires_at'] > now_ts:
            return list(problem_navigation_cache['problem_ids'])

    problem_ids = [
        row[0]
        for row in db.session.query(Problem.id)
        .filter(Problem.is_published.is_(True))
        .order_by(Problem.id.asc())
        .all()
    ]
    with problem_cache_lock:
        problem_navigation_cache['expires_at'] = now_ts + PROBLEM_DETAIL_CACHE_TTL_SECONDS
        problem_navigation_cache['problem_ids'] = list(problem_ids)
    return problem_ids


def invalidate_user_level_cache(user_id=None):
    with user_level_cache_lock:
        if user_id is None:
            user_level_cache.clear()
            user_level_refresh_futures.clear()
            return
        user_level_cache.pop(int(user_id), None)
        user_level_refresh_futures.pop(int(user_id), None)


def build_user_level_snapshot(user_id):
    xp_total, _, level_dict, xp_to_next = compute_xp_and_level(user_id)
    return {
        'xp_total': xp_total,
        'level': level_dict,
        'xp_to_next': xp_to_next,
        'computed_at': utcnow().isoformat()
    }


def get_cached_user_level_snapshot(user_id, force_refresh=False):
    user_id = int(user_id)
    now_ts = time.time()
    with user_level_cache_lock:
        cached_entry = user_level_cache.get(user_id)
        if cached_entry and not force_refresh and cached_entry['expires_at'] > now_ts:
            return cached_entry['payload']

    payload = build_user_level_snapshot(user_id)
    with user_level_cache_lock:
        user_level_cache[user_id] = {
            'expires_at': now_ts + USER_LEVEL_CACHE_TTL_SECONDS,
            'payload': payload
        }
    return payload


def refresh_user_level_snapshot(user_id):
    user_id = int(user_id)
    try:
        with app.app_context():
            payload = build_user_level_snapshot(user_id)
    except Exception as exc:
        print(f">>> [WARN] USER LEVEL REFRESH FAILED FOR {user_id}: {exc}", flush=True)
        raise
    finally:
        with user_level_cache_lock:
            future = user_level_refresh_futures.get(user_id)
            if future is not None and future.done():
                user_level_refresh_futures.pop(user_id, None)

    with user_level_cache_lock:
        user_level_cache[user_id] = {
            'expires_at': time.time() + USER_LEVEL_CACHE_TTL_SECONDS,
            'payload': payload
        }
        user_level_refresh_futures.pop(user_id, None)
    return payload


def schedule_user_level_refresh(user_id):
    user_id = int(user_id)
    with user_level_cache_lock:
        future = user_level_refresh_futures.get(user_id)
        if future and not future.done():
            return future
        future = background_task_executor.submit(refresh_user_level_snapshot, user_id)
        user_level_refresh_futures[user_id] = future
        return future

def get_problem_leaderboard_base(problem_id):
    now_ts = time.time()
    cache_key = int(problem_id)
    cached = problem_leaderboard_cache.get(cache_key)
    if cached and cached['expires_at'] > now_ts:
        return cached['payload']
    if cached:
        problem_leaderboard_cache.pop(cache_key, None)

    problem = db.session.get(Problem, problem_id)
    if not problem:
        return None

    stats_by_user = get_bulk_users_stats()
    submissions = (
        ChallengeSubmission.query
        .options(joinedload(ChallengeSubmission.user))
        .filter(
            ChallengeSubmission.problem_id == problem_id,
            ChallengeSubmission.passed == True
        )
        .all()
    )

    selected_rows = {}
    available_years = set()
    for submission in submissions:
        if not submission.user:
            continue

        joined_year = submission.user.created_at.year if submission.user.created_at else None
        if joined_year is not None:
            available_years.add(joined_year)

        current_level = stats_by_user.get(submission.user_id, {}).get('level') or {
            'num': 1,
            'name': 'Débutant',
            'icon': '🌟',
            'color': '#6c757d',
            'glow': 'rgba(108,117,125,0.5)'
        }

        row = {
            'submission_id': submission.id,
            'user_id': submission.user_id,
            'name': submission.user.name or f'User {submission.user_id}',
            'joined_year': joined_year,
            'level': current_level,
            'time_taken_seconds': int(submission.time_taken_seconds or 0),
            'avg_execution_time_ms': (
                decimal_to_float(submission.avg_execution_time_ms)
                if decimal_to_float(submission.avg_execution_time_ms) is not None
                else average_metric_from_json(submission.test_case_metrics_json, 'execution_time_ms')
            ),
            'avg_memory_kb': (
                decimal_to_float(submission.avg_memory_kb)
                if decimal_to_float(submission.avg_memory_kb) is not None
                else average_metric_from_json(submission.test_case_metrics_json, 'memory_usage_kb')
            ),
            'timestamp': submission.timestamp,
            'test_cases_total': int(submission.test_cases_total or 0),
            'test_cases_passed': int(submission.test_cases_passed or 0),
            '_selection_key': (
                safe_metric_sort_value(submission.avg_execution_time_ms),
                safe_metric_sort_value(submission.avg_memory_kb),
                int(submission.time_taken_seconds or 0),
                submission.timestamp or datetime.datetime.max,
                submission.id
            )
        }

        existing = selected_rows.get(submission.user_id)
        if existing is None or row['_selection_key'] < existing['_selection_key']:
            selected_rows[submission.user_id] = row

    rows = []
    for row in selected_rows.values():
        row.pop('_selection_key', None)
        rows.append(row)

    payload = {
        'problem': {
            'id': problem.id,
            'title': problem.title,
            'difficulty': problem.difficulty
        },
        'rows': rows,
        'available_years': sorted(available_years, reverse=True)
    }
    problem_leaderboard_cache[cache_key] = {
        'expires_at': now_ts + PROBLEM_LEADERBOARD_CACHE_TTL_SECONDS,
        'payload': payload
    }
    return payload

def compute_participation_aware_score(value, values, missing_score=0.0, baseline_score=6.0):
    numeric_values = [decimal_to_float(v) for v in values if decimal_to_float(v) is not None]
    numeric_value = decimal_to_float(value)
    if numeric_value is None:
        return round(missing_score, 3)

    if not numeric_values:
        return 10.0

    best = min(numeric_values)
    worst = max(numeric_values)
    if best == worst:
        return 10.0

    relative_score = (worst - numeric_value) / (worst - best)
    raw_score = 2.0 + 8.0 * relative_score
    participant_count = len(numeric_values)
    confidence = min(1.0, max(0.0, (participant_count - 1) / 4.0))
    adjusted_score = baseline_score + confidence * (raw_score - baseline_score)
    return round(max(missing_score, min(10.0, adjusted_score)), 3)

def compute_problem_placement_counts(passed_submissions):
    best_submissions_by_problem = defaultdict(dict)
    for sub in passed_submissions:
        selected_for_problem = best_submissions_by_problem[sub.problem_id]
        avg_exec = (
            decimal_to_float(sub.avg_execution_time_ms)
            if decimal_to_float(sub.avg_execution_time_ms) is not None
            else average_metric_from_json(sub.test_case_metrics_json, 'execution_time_ms')
        )
        avg_memory = (
            decimal_to_float(sub.avg_memory_kb)
            if decimal_to_float(sub.avg_memory_kb) is not None
            else average_metric_from_json(sub.test_case_metrics_json, 'memory_usage_kb')
        )
        candidate = {
            'user_id': sub.user_id,
            'time_taken_seconds': int(sub.time_taken_seconds or 0),
            'avg_execution_time_ms': avg_exec,
            'avg_memory_kb': avg_memory,
            'timestamp': sub.timestamp,
            '_selection_key': (
                safe_metric_sort_value(avg_exec),
                safe_metric_sort_value(avg_memory),
                int(sub.time_taken_seconds or 0),
                sub.timestamp or datetime.datetime.max,
                sub.id
            )
        }
        existing = selected_for_problem.get(sub.user_id)
        if existing is None or candidate['_selection_key'] < existing['_selection_key']:
            selected_for_problem[sub.user_id] = candidate

    placement_counts = defaultdict(lambda: {'top1': 0, 'top3': 0, 'top10': 0})
    for problem_rows in best_submissions_by_problem.values():
        rows = list(problem_rows.values())
        solve_values = [row.get('time_taken_seconds') for row in rows if row.get('time_taken_seconds') is not None]
        exec_values = [row.get('avg_execution_time_ms') for row in rows if row.get('avg_execution_time_ms') is not None]
        memory_values = [row.get('avg_memory_kb') for row in rows if row.get('avg_memory_kb') is not None]

        ranked_rows = []
        for row in rows:
            tests_score = 10.0
            solve_time_score = compute_participation_aware_score(row.get('time_taken_seconds'), solve_values)
            execution_score = compute_participation_aware_score(
                row.get('avg_execution_time_ms'),
                exec_values,
                missing_score=2.0
            )
            memory_score = compute_participation_aware_score(
                row.get('avg_memory_kb'),
                memory_values,
                missing_score=2.0
            )
            final_score = round(
                tests_score + solve_time_score + execution_score + memory_score,
                3
            )
            ranked_rows.append({
                'user_id': row['user_id'],
                'final_score': final_score,
                'time_taken_seconds': int(row.get('time_taken_seconds') or 0),
                'avg_execution_time_ms': row.get('avg_execution_time_ms'),
                'avg_memory_kb': row.get('avg_memory_kb'),
                'timestamp': row.get('timestamp') or datetime.datetime.max
            })

        ranked_rows.sort(
            key=lambda row: (
                -row['final_score'],
                row['time_taken_seconds'],
                safe_metric_sort_value(row.get('avg_execution_time_ms')),
                safe_metric_sort_value(row.get('avg_memory_kb')),
                row['timestamp'],
                row['user_id']
            )
        )

        for rank, row in enumerate(ranked_rows, start=1):
            counters = placement_counts[row['user_id']]
            if rank == 1:
                counters['top1'] += 1
            if rank <= 3:
                counters['top3'] += 1
            if rank <= 10:
                counters['top10'] += 1

    return placement_counts

def build_problem_leaderboard_rows(problem_id, year=None):
    base_payload = get_problem_leaderboard_base(problem_id)
    if base_payload is None:
        return None

    rows = list(base_payload['rows'])
    if year is not None:
        rows = [row for row in rows if row.get('joined_year') == year]

    solve_values = [row.get('time_taken_seconds') for row in rows if row.get('time_taken_seconds') is not None]
    exec_values = [row.get('avg_execution_time_ms') for row in rows if row.get('avg_execution_time_ms') is not None]
    memory_values = [row.get('avg_memory_kb') for row in rows if row.get('avg_memory_kb') is not None]

    scored_rows = []
    for row in rows:
        scored_row = dict(row)
        scored_row['tests_score'] = 10.0
        scored_row['solve_time_score'] = compute_participation_aware_score(
            row.get('time_taken_seconds'),
            solve_values
        )
        scored_row['execution_score'] = compute_participation_aware_score(
            row.get('avg_execution_time_ms'),
            exec_values,
            missing_score=2.0
        )
        scored_row['memory_score'] = compute_participation_aware_score(
            row.get('avg_memory_kb'),
            memory_values,
            missing_score=2.0
        )
        scored_row['final_score'] = round(
            scored_row['tests_score']
            + scored_row['solve_time_score']
            + scored_row['execution_score']
            + scored_row['memory_score'],
            3
        )
        scored_rows.append(scored_row)

    ranked_rows = sorted(
        scored_rows,
        key=lambda row: (
            -row['final_score'],
            int(row.get('time_taken_seconds') or 0),
            safe_metric_sort_value(row.get('avg_execution_time_ms')),
            safe_metric_sort_value(row.get('avg_memory_kb')),
            row.get('timestamp') or datetime.datetime.max,
            row.get('user_id') or 0
        )
    )

    for index, row in enumerate(ranked_rows, start=1):
        row['rank'] = index
        row['badge_label'] = 'Top 1' if index == 1 else ('Top 10' if index <= 10 else None)

    return {
        'problem': base_payload['problem'],
        'available_years': base_payload['available_years'],
        'rows': ranked_rows
    }

def sort_problem_leaderboard_rows(rows, sort_key, order):
    if sort_key == 'final_score':
        ranked_rows = sorted(
            rows,
            key=lambda row: (
                row['rank'],
                int(row.get('time_taken_seconds') or 0),
                safe_metric_sort_value(row.get('avg_execution_time_ms')),
                safe_metric_sort_value(row.get('avg_memory_kb')),
                row.get('timestamp') or datetime.datetime.max,
                row.get('user_id') or 0
            )
        )
        return list(reversed(ranked_rows)) if order == 'asc' else ranked_rows

    def metric_key(row):
        metric_value = decimal_to_float(row.get(sort_key))
        is_missing = metric_value is None
        sortable_value = metric_value if metric_value is not None else 0.0
        if order == 'desc':
            sortable_value *= -1
        return (is_missing, sortable_value, row['rank'])

    return sorted(rows, key=metric_key)

def serialize_leaderboard_row(row):
    return {
        'rank': row['rank'],
        'user_id': row['user_id'],
        'name': row['name'],
        'level': row['level'],
        'joined_year': row.get('joined_year'),
        'time_taken_seconds': int(row.get('time_taken_seconds') or 0),
        'avg_execution_time_ms': decimal_to_float(row.get('avg_execution_time_ms')),
        'avg_memory_kb': decimal_to_float(row.get('avg_memory_kb')),
        'tests_score': round(float(row.get('tests_score') or 0.0), 3),
        'solve_time_score': round(float(row.get('solve_time_score') or 0.0), 3),
        'execution_score': round(float(row.get('execution_score') or 0.0), 3),
        'memory_score': round(float(row.get('memory_score') or 0.0), 3),
        'final_score': round(float(row.get('final_score') or 0.0), 3),
        'badge_label': row.get('badge_label')
    }

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    r.headers['X-App-Build'] = APP_BUILD_ID
    return r

@app.route('/examples')
def list_examples():
    try:
        categories = {
            "Basics": [],
            "Arrays": [],
            "Strings": [],
            "Functions": [],
            "Pointers": [],
            "Dynamic_Allocation": [],
            "Enregistrements": [],
            "Listes_Chainees": [],
            "Piles": [],
            "Files": []
        }

        # Helper to categorize based on filename
        def categorize(filepath, is_fixture=False):
            if is_fixture:
                return "Fixtures"
            
            dirname = os.path.dirname(filepath).replace('\\', '/')
            if dirname:
                cat = dirname.replace('Allocation', ' Allocation').replace('_', ' ').replace('  ', ' ')
                # normalize common case
                if "dynamic" in cat.lower() and "alloc" in cat.lower():
                    cat = "Dynamic Allocation"
                if "enregistr" in cat.lower():
                    return "Enregistrements"
                if "pile" in cat.lower() or "stack" in cat.lower():
                    return "Piles"
                if "file" in cat.lower() or "queue" in cat.lower():
                    return "Files"
                if "liste" in cat.lower() or "chain" in cat.lower():
                    return "Listes_Chainees"
                return cat

            name = filepath.lower()
            if "dynamic" in name or "alloc" in name:
                return "Dynamic Allocation"
            if name.startswith("str_") or "string" in name or "chaine" in name:
                return "Strings"
            if "ptr" in name or "pointer" in name:
                return "Pointers"
            if "liste" in name or "chain" in name or "linked" in name:
                return "Listes_Chainees"
            if "pile" in name or "stack" in name:
                return "Piles"
            if "file" in name or "queue" in name:
                return "Files"
            if "record" in name or "enregistr" in name:
                return "Enregistrements"
            if "func" in name or "fonction" in name or "proc" in name:
                return "Functions"
            if "array" in name or "tableau" in name:
                return "Arrays"
            if name.startswith("test_"):
                return "Tests"
            return "Basics"

        # Main examples
        if os.path.exists(EXAMPLES_DIR):
            for root, dirs, files in os.walk(EXAMPLES_DIR):
                for f in files:
                    if f.endswith('.algo'):
                        # Get relative path for grouping
                        rel_path = os.path.relpath(os.path.join(root, f), EXAMPLES_DIR)
                        cat = categorize(rel_path)
                        # Ensure forward slashes for URLs
                        filepath_url = rel_path.replace('\\\\', '/')
                        if cat not in ["Tests", "Fixtures"]:
                            if cat not in categories:
                                categories[cat] = []
                            categories[cat].append({'name': f, 'path': filepath_url})
        
        # Sort each category: 00_Tutoriel first, then alphabetically
        for cat in categories:
            categories[cat].sort(key=lambda x: (
                0 if x['name'].startswith('00_Tutoriel') else 1,
                x['name'].lower()
            ))

        # Remove empty categories
        filtered_categories = {k: v for k, v in categories.items() if v and k not in ["Tests", "Fixtures"]}
        return jsonify(filtered_categories)
    except Exception as e:
        print(f"DEBUG: Exception in list_examples: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({})

@app.route('/example/<path:filename>')
def get_example(filename):
    try:
        # Determine path
        if filename.startswith('fixtures/'):
            real_filename = filename.split('/', 1)[1]
            filepath = os.path.join(FIXTURES_DIR, real_filename)
            base_dir = FIXTURES_DIR
        else:
            filepath = os.path.join(EXAMPLES_DIR, filename)
            base_dir = EXAMPLES_DIR

        if not _is_safe_path(base_dir, filepath):
             return jsonify({'error': "Invalid filename"}), 400

        if not os.path.exists(filepath):
            return jsonify({'error': "File not found"}), 404
            
        with open(filepath, 'r', encoding='utf-8') as f:
            code_content = f.read()
            
        # Check for associated .input file
        input_content = ""
        # Handle input file path logic based on directory
        base_path = os.path.splitext(filepath)[0]
        input_filepath = base_path + ".input"
        
        if os.path.exists(input_filepath):
             with open(input_filepath, 'r', encoding='utf-8') as f:
                 input_content = f.read()

        return jsonify({
            'code': code_content,
            'input': input_content
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate_algo', methods=['POST'])
def validate_algo():
    """Validate a course snippet against the current compiler without executing it."""
    try:
        data = request.get_json(silent=True) or {}
        code = data.get('code', '')
        if isinstance(code, dict):
            code = json.dumps(code)
        code = str(code)

        if not code.strip():
            return jsonify({'ok': False, 'errors': [{'message': 'Code vide'}]}), 200

        result = compile_algo(code)

        # Modern parser returns (python_code, errors)
        if isinstance(result, tuple):
            python_code, errors = result
            if errors:
                return jsonify({'ok': False, 'errors': errors}), 200
                
            return jsonify({'ok': bool(python_code), 'errors': []}), 200

        # Backward compatibility
        return jsonify({'ok': bool(result), 'errors': [] if result else [{'message': 'Compilation failed'}]}), 200
    except Exception as e:
        return jsonify({'ok': False, 'errors': [{'message': str(e)}]}), 200

# --- QUIZ API ENDPOINTS ---

import random

@app.route('/api/quiz/<chapter_identifier>')
def get_quiz(chapter_identifier):
    try:
        chapter = Chapter.query.filter_by(identifier=chapter_identifier).first()
        if not chapter:
            return jsonify({'error': 'Chapter not found in database'}), 404

        # Requirements: 6 Easy, 8 Medium, 6 Hard (Total 20)
        # If not enough, get as many as possible
        easy_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Easy').all()
        medium_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Medium').all()
        hard_q = Question.query.filter_by(chapter_id=chapter.id, difficulty='Hard').all()

        selected_questions = (
            random.sample(easy_q, min(6, len(easy_q))) +
            random.sample(medium_q, min(8, len(medium_q))) +
            random.sample(hard_q, min(6, len(hard_q)))
        )
        random.shuffle(selected_questions)

        quiz_data = []
        for q in selected_questions:
            choices = Choice.query.filter_by(question_id=q.id).all()
            
            # Get the correct choice and up to 3 random incorrect choices
            correct_choice = next((c for c in choices if c.is_correct), None)
            incorrect_choices = [c for c in choices if not c.is_correct]
            selected_incorrect = random.sample(incorrect_choices, min(3, len(incorrect_choices)))
            
            final_choices = [correct_choice] + selected_incorrect if correct_choice else selected_incorrect
            random.shuffle(final_choices)

            quiz_data.append({
                'id': q.id,
                'type': q.type,
                'difficulty': q.difficulty,
                'concept': q.concept,
                'text': q.text,
                'explanation': q.explanation,
                'choices': [{'id': c.id, 'text': c.text, 'is_correct': c.is_correct} for c in final_choices]
            })

        return jsonify({'questions': quiz_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/save_progress', methods=['POST'])
def save_quiz_progress():
    try:
        data = request.json
        chapter_identifier = data.get('chapter_identifier')
        score = data.get('score')
        total = data.get('total')
        details = data.get('details', '{}') 

        chapter = Chapter.query.filter_by(identifier=chapter_identifier).first()
        if not chapter:
            return jsonify({'error': 'Chapter not found'}), 404

        if current_user.is_authenticated:
            # Check interpretation
            all_correct = (score == total)
            none_correct = (score == 0)

            # Capture level before save
            old_xp, _, old_level, _ = compute_xp_and_level(current_user.id)

            attempt = QuizAttempt(
                user_id=current_user.id,
                chapter_id=chapter.id,
                score=score,
                total_questions=total,
                all_correct=all_correct,
                none_correct=none_correct,
                details=json.dumps(details)
            )
            db.session.add(attempt)
            db.session.commit()

            # Percentile calculation
            # Calculate how many unique users have a score lower than this one
            all_scores = db.session.query(
                func.max(QuizAttempt.score)
            ).filter(
                QuizAttempt.chapter_id == chapter.id
            ).group_by(QuizAttempt.user_id).all()
            
            all_scores_list = [s[0] for s in all_scores if s[0] is not None]
            total_participants = len(all_scores_list)
            
            percentile = 0
            if total_participants > 1:
                # Count scores strictly lower
                lower_scores = sum(1 for s in all_scores_list if s < score)
                percentile = (lower_scores / (total_participants - 1)) * 100
            elif total_participants == 1:
                percentile = 100

            # Capture level after save
            new_xp, _, new_level, new_xp_to_next = compute_xp_and_level(current_user.id)
            level_up = new_level['num'] > old_level['num']
            with user_level_cache_lock:
                user_level_cache[current_user.id] = {
                    'expires_at': time.time() + USER_LEVEL_CACHE_TTL_SECONDS,
                    'payload': {
                        'xp_total': new_xp,
                        'level': new_level,
                        'xp_to_next': new_xp_to_next,
                        'computed_at': utcnow().isoformat()
                    }
                }

            return jsonify({
                'success': True,
                'saved': True,
                'percentile': round(percentile, 1),
                'xp_earned': new_xp - old_xp,
                'xp_total': new_xp,
                'level': new_level,
                'level_up': level_up,
                'xp_to_next': new_xp_to_next
            })

        return jsonify({'success': True, 'saved': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

import queue
import uuid

_ORIGINAL_STDOUT = sys.stdout
_ORIGINAL_STDERR = sys.stderr
_execution_io_local = threading.local()


class ThreadBoundTextProxy:
    def __init__(self, fallback, attr_name):
        self.fallback = fallback
        self.attr_name = attr_name

    def _target(self):
        return getattr(_execution_io_local, self.attr_name, None) or self.fallback

    def write(self, text):
        return self._target().write(text)

    def flush(self):
        target = self._target()
        if hasattr(target, 'flush'):
            return target.flush()
        return None

    def isatty(self):
        target = self._target()
        return target.isatty() if hasattr(target, 'isatty') else False

    def fileno(self):
        target = self._target()
        if hasattr(target, 'fileno'):
            return target.fileno()
        raise io.UnsupportedOperation("fileno")

    def __getattr__(self, name):
        return getattr(self._target(), name)


EXECUTION_STDOUT_PROXY = ThreadBoundTextProxy(_ORIGINAL_STDOUT, 'stdout')
EXECUTION_STDERR_PROXY = ThreadBoundTextProxy(_ORIGINAL_STDERR, 'stderr')

# Global Session State
class GlobalSession:
    def __init__(self, owner_id=None, run_id=None):
        self.owner_id = owner_id
        self.run_id = run_id
        self.input_queue = queue.Queue(maxsize=1000) # Limit size to prevent memory issues
        self.output_queue = queue.Queue(maxsize=10000) # Limit output buffer
        self.is_running = False
        self.current_thread = None
        self.current_ctx = None
        self.created_at = time.time()
        self.updated_at = self.created_at

    def reset(self):
        self.input_queue = queue.Queue(maxsize=1000)
        self.output_queue = queue.Queue(maxsize=10000)
        self.is_running = False
        self.current_thread = None
        self.current_ctx = None
        self.touch()

    def touch(self):
        self.updated_at = time.time()


class ExecutionManager:
    def __init__(self, ttl_seconds=3600, max_active_runs_per_owner=3):
        self.ttl_seconds = ttl_seconds
        self.max_active_runs_per_owner = max_active_runs_per_owner
        self.runs = {}
        self.lock = threading.Lock()

    def _cleanup_locked(self):
        now = time.time()
        stale_run_ids = [
            run_id for run_id, state in self.runs.items()
            if not state.is_running and (now - state.updated_at) > self.ttl_seconds
        ]
        for run_id in stale_run_ids:
            self.runs.pop(run_id, None)

    def create_run(self, owner_id):
        with self.lock:
            self._cleanup_locked()
            active_runs = sum(
                1 for state in self.runs.values()
                if state.owner_id == owner_id and state.is_running
            )
            if active_runs >= self.max_active_runs_per_owner:
                return None

            run_id = uuid.uuid4().hex
            state = GlobalSession(owner_id=owner_id, run_id=run_id)
            self.runs[run_id] = state
            return state

    def get_run(self, owner_id, run_id):
        if not run_id:
            return None

        with self.lock:
            self._cleanup_locked()
            state = self.runs.get(run_id)
            if not state or state.owner_id != owner_id:
                return None
            state.touch()
            return state

    def remove_run(self, run_id):
        with self.lock:
            self.runs.pop(run_id, None)


execution_manager = ExecutionManager()


def get_execution_owner_id():
    owner_id = flask_session.get('_execution_owner_id')
    if not owner_id:
        owner_id = secrets.token_urlsafe(24)
        flask_session['_execution_owner_id'] = owner_id
        flask_session.modified = True
    return owner_id


def get_requested_run_id():
    if request.method == 'GET':
        return request.args.get('run_id', '').strip()

    data = request.get_json(silent=True) or {}
    return str(data.get('run_id') or request.form.get('run_id') or '').strip()

import ctypes

def terminate_thread(thread):
    """Terminates a python thread from another thread.
    :param thread: a threading.Thread instance
    """
    if not thread or not thread.is_alive():
        return

    exc = ctypes.py_object(SystemExit)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), exc)
    if res == 0:
        # Thread might be dead already
        pass
    elif res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(thread.ident), None)
        raise SystemError("PyThreadState_SetAsyncExc failed")

@app.route('/stop_execution', methods=['POST'])
def stop_execution_route():
    owner_id = get_execution_owner_id()
    run_state = execution_manager.get_run(owner_id, get_requested_run_id())
    if run_state and run_state.is_running:
        run_state.is_running = False
        run_state.touch()
        if hasattr(run_state, 'current_ctx') and run_state.current_ctx:
            run_state.current_ctx.is_running = False
        
        # Force kill the thread
        if run_state.current_thread:
             try:
                 terminate_thread(run_state.current_thread)
             except Exception as e:
                 print(f"Error terminating thread: {e}")

        # Unblock any waiting input
        try:
             # Drain input queue to ensure put doesn't block if full
             while not run_state.input_queue.empty():
                 try: run_state.input_queue.get_nowait()
                 except: break
             run_state.input_queue.put(None) 
        except:
             pass
        
        # Clear queues
        try:
            with run_state.input_queue.mutex:
                run_state.input_queue.queue.clear()
            with run_state.output_queue.mutex:
                run_state.output_queue.queue.clear()
        except Exception:
            # In case mutex is locked or other issues
            pass
            
        # session.output_queue.put({'type': 'finished', 'data': 'Execution stopped by user.'})
        # We rely on the thread catching SystemExit and sending 'stopped'
        
        return jsonify({'success': True})
    if not run_state:
        return jsonify({'success': False, 'error': 'Execution not found'}), 404
    return jsonify({'success': False, 'error': 'Not running'}), 409

@app.route('/doc/errors')
def doc_errors():
    return render_template('errors.html')

@app.route('/start_execution', methods=['POST'])
def start_execution():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    if isinstance(code, dict):
        # Fallback if frontend accidentally sends an object or object payload was double-nested
        import json
        code = json.dumps(code)
    code = str(code)

    try:
        owner_id = get_execution_owner_id()
        run_state = execution_manager.create_run(owner_id)
        if run_state is None:
            return jsonify({
                'success': False,
                'error': 'Too many active executions for this browser session. Stop one before starting another.'
            }), 429

        # Transpile to Python
        # Use compile_algo to ensure indent_level is reset
        result = compile_algo(code)
        
        # Handle tuple return (code, errors)
        if isinstance(result, tuple):
            python_code, errors = result
            if errors:
                execution_manager.remove_run(run_state.run_id)
                # Return structured errors
                return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
        else:
             python_code = result # Fallback for backward compatibility if parser didn't update (shouldn't happen)

        if not python_code:
            execution_manager.remove_run(run_state.run_id)
            return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})

        if os.environ.get('LOG_COMPILED_CODE', '').lower() in ('1', 'true', 'yes', 'on'):
            print(f"\n--- DEBUG: GENERATED PYTHON CODE (LIVE EXECUTION) ---\n{python_code}\n-----------------------------------------------------\n")

        # Save to file only when explicitly enabled
        if os.environ.get('WRITE_COMPILED_OUTPUT', '').lower() in ('1', 'true', 'yes', 'on'):
            with open(f'output_{run_state.run_id}.py', 'w', encoding='utf-8') as f:
                f.write(python_code)

        # Reset Session
        run_state.reset()
        run_state.is_running = True
        run_state.touch()
        
        class RunContext:
            def __init__(self, in_q, out_q):
                self.is_running = True
                self.input_queue = in_q
                self.output_queue = out_q
                
        ctx = RunContext(run_state.input_queue, run_state.output_queue)
        run_state.current_ctx = ctx
        
        # Check for pre-loaded input file
        input_file_content = data.get('inputFileContent', '')
        if input_file_content:
             # Split by lines and put into input queue
             lines = input_file_content.split('\n')
             for line in lines:
                 run_state.input_queue.put(line.strip())

        # Thread Target
        def run_script():
            try:
                # Mock Input
                def mock_input(prompt=''):
                    if prompt:
                        ctx.output_queue.put({'type': 'stdout', 'data': prompt})
                    
                    # Check if we have pre-loaded input in queue
                    if not ctx.input_queue.empty():
                         return ctx.input_queue.get()

                    # Request Input from Frontend
                    # print("DEBUG: Sending input_request to frontend")
                    ctx.output_queue.put({'type': 'input_request'})
                    
                    # Block wait for input
                    # print("DEBUG: Waiting for input from session.input_queue")
                    user_input = ctx.input_queue.get()
                    if user_input is None: # Signal to stop
                        raise EOFError("Execution Terminated")
                    return user_input

                # Mock Print? 
                # We need to capture stdout.
                # TraceRunner captures it, but we also want real-time streaming.
                # Let's create a stream-like object that puts to queue.
                class StreamToQueue:
                    def __init__(self):
                        import io
                        self.buffer = io.StringIO()
                    def write(self, text):
                        if text:
                            self.buffer.write(text)
                            try:
                                # Use timeout to allow checking if session is still running
                                # This prevents deadlock if queue is full and stop is requested
                                while ctx.is_running:
                                    try:
                                        ctx.output_queue.put({'type': 'stdout', 'data': text}, timeout=0.5)
                                        break
                                    except queue.Full:
                                        if not ctx.is_running: break
                                        continue
                            except Exception:
                                pass
                    def flush(self):
                        pass

                    def isatty(self):
                        return False

                    def getvalue(self):
                        return self.buffer.getvalue()

                    def fileno(self):
                        import io
                        raise io.UnsupportedOperation("fileno")
                
                stream = StreamToQueue()
                _execution_io_local.stdout = stream
                _execution_io_local.stderr = stream
                
                # Redirect through thread-aware proxies so one execution cannot capture another thread's logs.
                with contextlib.redirect_stdout(EXECUTION_STDOUT_PROXY), contextlib.redirect_stderr(EXECUTION_STDERR_PROXY):

                    # Prepare builtins
                    # Custom print to ensure capture
                    def custom_print(*args, **kwargs):
                        sep = kwargs.get('sep', ' ')
                        end = kwargs.get('end', '\n')
                        file = kwargs.get('file', None)
                        if file is None:
                            text = sep.join(map(str, args)) + end
                            stream.write(text)
                        else:
                            try:
                                file.write(sep.join(map(str, args)) + end)
                            except:
                                pass

                    # Helper to convert Algo types (like char lists) to string for display
                    def _algo_to_string(val):
                        if isinstance(val, bool): return "Vrai" if val else "Faux"
                        if isinstance(val, list):
                            res = ""
                            for char in val:
                                if char is None or char == "\0": break
                                res += str(char)
                            return res
                        return str(val)

                    def _algo_longueur(val):
                        """Calculate length of a string (stops at null terminator for fixed strings)"""
                        if isinstance(val, list):
                            return len(_algo_to_string(val))
                        return len(str(val))
                
                    def _algo_concat(val1, val2):
                        """Concatenate two strings, handling fixed-size string arrays"""
                        # Convert both values to strings
                        s1 = _algo_to_string(val1) if isinstance(val1, list) else str(val1)
                        s2 = _algo_to_string(val2) if isinstance(val2, list) else str(val2)
                        return s1 + s2
                        
                    def _algo_assign_fixed_string(target_list, source_val):
                        # Update target_list in-place to match source_val (string or list)
                        if not isinstance(target_list, list): return target_list
                        limit = len(target_list)
                        s_val = ''
                        if hasattr(source_val, '_get_target_container'):
                            targ = source_val._get_target_container()
                            while hasattr(targ, '_get_target_container'): 
                                targ = targ._get_target_container()
                            if isinstance(targ, list):
                                s_val = _algo_to_string(targ[source_val.index:])
                            else:
                                s_val = str(source_val._get_string() if hasattr(source_val, '_get_string') else source_val._get())
                        elif isinstance(source_val, list):
                             s_val = _algo_to_string(source_val)
                        else:
                             s_val = str(source_val)
                        
                        if limit > 0:
                            s_val = s_val[:limit-1]
                            for i in range(len(s_val)):
                                target_list[i] = s_val[i]
                            target_list[len(s_val)] = '\0'
                            for i in range(len(s_val)+1, limit):
                                target_list[i] = None
                        return target_list

                    # Mock input for LIRE if needed
                    def _algo_read_typed(current_val, raw_val, target_type_name='CHAINE'):
                        type_to_check = target_type_name.upper()
                        if 'CHAINE' in type_to_check:
                            if isinstance(current_val, list):
                                 _algo_assign_fixed_string(current_val, raw_val)
                                 return current_val
                            return str(raw_val)
                        if 'BOOLEEN' in type_to_check or isinstance(current_val, bool):
                            val_str = str(raw_val).lower()
                            if val_str in ['vrai', 'true', '1']: return True
                            if val_str in ['faux', 'false', '0']: return False
                            raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Booléen valide.")
                        if 'ENTIER' in type_to_check or isinstance(current_val, int):
                            try: return int(raw_val)
                            except: raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Entier valide.")
                        if 'REEL' in type_to_check or isinstance(current_val, float):
                            try: return float(raw_val)
                            except: raise ValueError(f"Type mismatch: '{raw_val}' n'est pas un Reel valide.")
                        if isinstance(current_val, list): return raw_val 
                        return str(raw_val)

                    def _algo_set_char(target_list, index, char_val):
                        if not isinstance(target_list, list): return target_list
                        idx = int(index)
                        if 0 <= idx < len(target_list):
                            c = str(char_val)[0] if char_val else "\0"
                            target_list[idx] = c
                        return target_list

                    def _algo_get_char(target_list, index):
                        if isinstance(target_list, list):
                            idx = int(index)
                            if 0 <= idx < len(target_list):
                                c = target_list[idx]
                                return c if c is not None and c != "\0" else ""
                            return ""
                        s = str(target_list)
                        idx = int(index)
                        return s[idx] if 0 <= idx < len(s) else ""

                    # Prepare builtins
                    safe_builtins = {}
                    if isinstance(__builtins__, dict):
                        safe_builtins = __builtins__.copy()
                    else:
                        safe_builtins = __builtins__.__dict__.copy()
                    safe_builtins['print'] = custom_print
                    safe_builtins['input'] = mock_input

                    exec_globals = {
                        '_algo_to_string': _algo_to_string,
                        '_algo_longueur': _algo_longueur,
                        '_algo_concat': _algo_concat,
                        '_algo_assign_fixed_string': _algo_assign_fixed_string,
                        '_algo_set_char': _algo_set_char,
                        '_algo_get_char': _algo_get_char,
                        'print': custom_print,
                        'input': mock_input, 
                        '__builtins__': safe_builtins
                    }

                    tracer = TraceRunner()
                    
                    def on_log_step(step):
                         if not ctx.is_running:
                             raise SystemExit("Execution stopped by user")
                         try:
                             while ctx.is_running:
                                 try:
                                     ctx.output_queue.put({'type': 'trace', 'data': step}, timeout=0.1)
                                     break
                                 except queue.Full:
                                     if not ctx.is_running: break
                                     continue
                         except:
                             pass
                    
                    # Run execution
                    tracer.run(python_code, exec_globals, stdout_capture=stream, on_step=on_log_step)


            except SystemExit:
                 ctx.output_queue.put({'type': 'stopped', 'data': 'Exécution interrompue.'})
            except Exception as e:
                # Translate Python errors to friendly Algo errors
                err_msg = str(e)
                error_type = type(e).__name__
                
                if "not supported between instances of 'str' and 'int'" in err_msg:
                    err_msg = "Impossible de comparer une Chaîne et un Entier."
                elif "not supported between instances of 'int' and 'str'" in err_msg:
                    err_msg = "Impossible de comparer un Entier et une Chaîne."
                elif "unsupported operand type(s)" in err_msg:
                    err_msg = f"Opération impossible entre ces types: {err_msg}"
                elif "name" in err_msg and "is not defined" in err_msg:
                    # Extract variable name
                    import re
                    match = re.search(r"name '(\w+)' is not defined", err_msg)
                    if match:
                        err_msg = f"Variable non déclarée ou inconnue: '{match.group(1)}'"
                    else:
                        err_msg = "Variable non déclarée."
                elif "division by zero" in err_msg:
                    err_msg = "[E4.5] Division par zéro impossible."
                elif "list index out of range" in err_msg:
                    err_msg = "[E4.4] Accès au tableau expiré ou hors limites."
                elif isinstance(e, TimeoutError):
                    err_msg = "[E4.1] Boucle infinie détectée (Temps/Instructions dépassés)."
                elif isinstance(e, RecursionError):
                    err_msg = "[E4.2] Erreur de récursion infinie (Trop d'appels de sous-programmes)."
                elif isinstance(e, MemoryError):
                    err_msg = "[E4.3] Dépassement de capacité mémoire (Trop d'allocations)."
                    
                run_state.output_queue.put({'type': 'error', 'data': f"Erreur d'exécution ({error_type}): {err_msg}"})
            finally:
                for attr_name in ('stdout', 'stderr'):
                    if hasattr(_execution_io_local, attr_name):
                        delattr(_execution_io_local, attr_name)
                # If we stopped manually, we might have already sent 'stopped'
                # But to be safe, let's mark finished if we were running
                if run_state.is_running:
                     run_state.output_queue.put({'type': 'finished'})
                     run_state.is_running = False
                run_state.touch()

        # Start Thread
        t = threading.Thread(target=run_script)
        t.daemon = True # Kill thread if main process ends
        run_state.current_thread = t
        t.start()

        return jsonify({'success': True, 'run_id': run_state.run_id})

    except Exception as e:
        if 'run_state' in locals() and run_state and not run_state.is_running:
            execution_manager.remove_run(run_state.run_id)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stream')
def stream():
    owner_id = get_execution_owner_id()
    run_state = execution_manager.get_run(owner_id, get_requested_run_id())
    if not run_state:
        return jsonify({'error': 'Execution not found'}), 404

    def event_stream():
        try:
            while True:
                try:
                    # Get message from queue, wait up to 1s
                    msg = run_state.output_queue.get(timeout=1.0)
                    run_state.touch()
                    yield f"data: {json.dumps(msg)}\n\n"
                    if msg['type'] in ('finished', 'stopped'):
                        break
                except queue.Empty:
                    if not run_state.is_running and run_state.output_queue.empty():
                        break
                    # Send heartbeat
                    yield ": keepalive\n\n"
        finally:
            if not run_state.is_running and run_state.output_queue.empty():
                execution_manager.remove_run(run_state.run_id)
    
    return Response(event_stream(), mimetype="text/event-stream")

@app.route('/send_input', methods=['POST'])
def send_input():
    owner_id = get_execution_owner_id()
    data = request.get_json(silent=True) or {}
    run_state = execution_manager.get_run(owner_id, str(data.get('run_id', '')).strip())
    if not run_state:
         return jsonify({'success': False, 'error': 'Execution not found'}), 404
    if not run_state.is_running:
         return jsonify({'success': False, 'error': 'Not running'}), 409
         
    user_input = data.get('input')
    # print(f"DEBUG: Received input from frontend: '{user_input}'")
    run_state.input_queue.put(user_input)
    run_state.touch()
    return jsonify({'success': True})


@app.route('/api/problems', methods=['GET'])
def get_problems():
    topics = request.args.getlist('topic')
    difficulties = request.args.getlist('difficulty')
    
    query = Problem.query.filter(Problem.is_published.is_(True))
    if topics:
        query = query.filter(Problem.topic.in_(topics))
    if difficulties:
        query = query.filter(Problem.difficulty.in_(difficulties))
    
    problems = query.all()
    
    # Get solved problems for the current user if authenticated
    solved_ids = set()
    if current_user.is_authenticated:
        solved_submissions = ChallengeSubmission.query.filter_by(user_id=current_user.id, passed=True).all()
        solved_ids = {s.problem_id for s in solved_submissions}

    # Count distinct users who attempted each problem
    attempt_counts = (
        db.session.query(
            ChallengeSubmission.problem_id,
            func.count(distinct(ChallengeSubmission.user_id))
        )
        .group_by(ChallengeSubmission.problem_id)
        .all()
    )
    attempt_map = {prob_id: count for prob_id, count in attempt_counts}

    # Count distinct users who solved each problem
    solver_counts = (
        db.session.query(
            ChallengeSubmission.problem_id,
            func.count(distinct(ChallengeSubmission.user_id))
        )
        .filter(ChallengeSubmission.passed == True)
        .group_by(ChallengeSubmission.problem_id)
        .all()
    )
    solver_map = {prob_id: count for prob_id, count in solver_counts}
    
    return jsonify({
        'success': True,
        'problems': [
            {
                'id': p.id,
                'title': p.title,
                'topic': p.topic,
                'difficulty': p.difficulty,
                'solved': p.id in solved_ids if current_user.is_authenticated else None,
                'attempted_users': attempt_map.get(p.id, 0),
                'solvers': solver_map.get(p.id, 0),
                'success_rate': round((solver_map.get(p.id, 0) / attempt_map.get(p.id, 1)) * 100, 1) if attempt_map.get(p.id, 0) else 0,
                'description': p.description[:150] + '...' if p.description and len(p.description) > 150 else p.description
            }
            for p in problems
        ]
    })

@app.route('/api/problems/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    problem_payload = get_cached_problem_payload(problem_id)
    if not problem_payload:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404
    if not problem_payload.get('is_published'):
        return jsonify({'success': False, 'error': 'Problem not published'}), 403

    return jsonify({
        'success': True,
        'problem': {k: v for k, v in problem_payload.items() if k != 'is_published'}
    })


@app.route('/api/problems/navigation', methods=['GET'])
def get_problem_navigation():
    return jsonify({
        'success': True,
        'problem_ids': get_cached_navigation_problem_ids()
    })

@app.route('/problems/<int:problem_id>/leaderboard')
def problem_leaderboard_page(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return render_template('errors.html'), 404
    if not problem.is_published:
        return render_template('errors.html'), 403
    return render_template('problem_leaderboard.html', problem=problem)

@app.route('/api/problems/<int:problem_id>/leaderboard', methods=['GET'])
def get_problem_leaderboard(problem_id):
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404
    if not problem.is_published:
        return jsonify({'success': False, 'error': 'Problem not published'}), 403

    year_param = (request.args.get('year') or '').strip()
    year = None
    if year_param:
        try:
            year = int(year_param)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid year filter'}), 400

    sort_key = (request.args.get('sort') or 'final_score').strip()
    allowed_sorts = {'final_score', 'time_taken_seconds', 'avg_execution_time_ms', 'avg_memory_kb'}
    if sort_key not in allowed_sorts:
        sort_key = 'final_score'

    order = (request.args.get('order') or ('desc' if sort_key == 'final_score' else 'asc')).strip().lower()
    if order not in {'asc', 'desc'}:
        order = 'desc' if sort_key == 'final_score' else 'asc'

    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    try:
        page_size = min(100, max(1, int(request.args.get('page_size', 10))))
    except ValueError:
        page_size = 10

    payload = build_problem_leaderboard_rows(problem_id, year=year)
    if payload is None:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404

    ranked_rows = payload['rows']
    sorted_rows = sort_problem_leaderboard_rows(ranked_rows, sort_key, order)
    total_items = len(sorted_rows)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    if page > total_pages:
        page = total_pages

    start = (page - 1) * page_size
    end = start + page_size
    paged_rows = sorted_rows[start:end]

    return jsonify({
        'success': True,
        'problem': payload['problem'],
        'available_years': payload['available_years'],
        'top_users': [serialize_leaderboard_row(row) for row in ranked_rows[:3]],
        'leaderboard': [serialize_leaderboard_row(row) for row in paged_rows],
        'sort': sort_key,
        'order': order,
        'filters': {'year': year},
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages
        }
    })

@app.route('/submission_results')
def submission_results():
    return render_template('submission_results.html')

from web.sandbox.runner import execute_code
# Assuming compiler is available in the same scope as before for `run` endpoint
import ast

@app.route('/api/submissions/custom', methods=['POST'])
def submit_custom_code():
    data = request.get_json()
    code = data.get('code')
    custom_input = data.get('input', '')
    
    # 1. Compile Algo code to Python
    result = compile_algo(code)
    
    # Handle tuple return (code, errors)
    if isinstance(result, tuple):
        python_code, errors = result
        if errors:
            return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
    else:
        python_code = result
        
    if not python_code:
        return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})
        
        
    tc_data = [{
        'id': 'custom',
        'input': custom_input,
        'expected_output': ''
    }]
    
    
    results = execute_code(python_code, tc_data)
    avg_execution_time_ms = round(
        sum(float(r.get('execution_time_ms') or 0.0) for r in results) / len(results),
        3
    ) if results else None
    avg_memory_kb = round(
        sum(float(r.get('memory_usage_kb') or 0.0) for r in results) / len(results),
        2
    ) if results else None
    
    return jsonify({
        'success': True,
        'all_passed': results[0]['passed'],
        'results': results,
        'avg_execution_time_ms': avg_execution_time_ms,
        'avg_memory_kb': avg_memory_kb,
        'metrics_summary': {
            'time_taken_seconds': 0,
            'test_cases_total': len(results),
            'test_cases_passed': sum(1 for r in results if r.get('passed')),
            'avg_execution_time_ms': avg_execution_time_ms,
            'avg_memory_kb': avg_memory_kb
        }
    })

@app.route('/api/submissions', methods=['POST'])
def submit_code():
    data = request.get_json()
    problem_id = data.get('problem_id')
    code = data.get('code')
    execute_all = data.get('execute_all', False)
    requested_time_taken_seconds = data.get('time_taken_seconds', 0)
    
    problem = db.session.get(Problem, problem_id)
    if not problem:
        return jsonify({'success': False, 'error': 'Problem not found'}), 404
    
    # 1. Compile Algo code to Python
    result = compile_algo(code)
    
    # Handle tuple return (code, errors)
    if isinstance(result, tuple):
        python_code, errors = result
        if errors:
            # Return structured errors exactly as expected by frontend mapping
            return jsonify({'success': False, 'error': 'Compilation failed', 'details': errors})
    else:
        python_code = result
        
    if not python_code:
        return jsonify({'success': False, 'error': 'Compilation failed (Syntax Error)'})
    
    
    # 2. Select test cases
    if execute_all:
        test_cases = problem.test_cases
    else:
        test_cases = [tc for tc in problem.test_cases if tc.is_public]
        
    # 3. Format test case data for sandbox
    tc_data = [{
        'id': tc.id,
        'input': tc.input_data,
        'expected_output': tc.expected_output
    } for tc in test_cases]
    
    # 4. Execute in sandbox
    raw_results = execute_code(python_code, tc_data)

    # Merge original tc_data with execution results
    results = []
    for i, raw_res in enumerate(raw_results):
        tc_info = tc_data[i]
        results.append({
            'test_case_id': tc_info['id'],
            'input': tc_info['input'],
            'expected_output': tc_info['expected_output'],
            'actual_output': raw_res['actual_output'],
            'passed': raw_res['passed'],
            'error': raw_res['error'],
            'execution_time_ms': round(float(raw_res.get('execution_time_ms') or 0.0), 3),
            'memory_usage_kb': int(raw_res.get('memory_usage_kb') or 0)
        })

    # Calculate all_passed
    all_passed = all(r['passed'] for r in results) if results else False
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    avg_execution_time_ms = round(
        sum(float(r.get('execution_time_ms') or 0.0) for r in results) / total_count,
        3
    ) if total_count else None
    avg_memory_kb = round(
        sum(float(r.get('memory_usage_kb') or 0.0) for r in results) / total_count,
        2
    ) if total_count else None
    submission_timestamp = utcnow()
    effective_time_taken_seconds = int(requested_time_taken_seconds or 0)
    attempt_session = None
    if current_user.is_authenticated and execute_all:
        attempt_session = get_or_create_active_attempt_session(current_user.id, problem.id)
        if attempt_session and attempt_session.started_at:
            effective_time_taken_seconds = max(
                0,
                int((submission_timestamp - attempt_session.started_at).total_seconds())
            )
    metrics_summary = {
        'time_taken_seconds': effective_time_taken_seconds,
        'test_cases_total': total_count,
        'test_cases_passed': passed_count,
        'avg_execution_time_ms': avg_execution_time_ms,
        'avg_memory_kb': avg_memory_kb
    }

    # Save submission if user is logged in and it's a full submission
    level_refresh_scheduled = False
    if current_user.is_authenticated and execute_all:
        score_percent = passed_count / total_count * 100 if total_count else 0

        submission = ChallengeSubmission(
            user_id=current_user.id,
            problem_id=problem.id,
            score=score_percent,
            code=code,
            passed=all_passed,
            time_taken_seconds=effective_time_taken_seconds,
            test_cases_total=total_count,
            test_cases_passed=passed_count,
            avg_execution_time_ms=avg_execution_time_ms,
            avg_memory_kb=avg_memory_kb,
            test_case_metrics_json=build_test_case_metrics(results),
            attempt_session_id=attempt_session.id if attempt_session else None,
            timestamp=submission_timestamp
        )
        if all_passed and attempt_session and attempt_session.completed_at is None:
            attempt_session.completed_at = submission_timestamp
        db.session.add(submission)
        db.session.commit()
        invalidate_problem_leaderboard_cache(problem.id)
        invalidate_user_level_cache(current_user.id)
        schedule_user_level_refresh(current_user.id)
        level_refresh_scheduled = True

    return jsonify({
        'success': True,
        'all_passed': all_passed,
        'results': results,
        'time_taken_seconds': effective_time_taken_seconds,
        'avg_execution_time_ms': avg_execution_time_ms,
        'avg_memory_kb': avg_memory_kb,
        'metrics_summary': metrics_summary,
        'leaderboard_url': url_for('problem_leaderboard_page', problem_id=problem.id),
        'problem_title': problem.title,
        'level_refresh_scheduled': level_refresh_scheduled
    })


# ─────────────────────────────────────────────────────────────────────────────
# XP POINTS & LEVEL SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
LEVEL_DEFS = [
    # (min_xp, level_num, name_fr, color, glow, icon, special_requirement_key)
    (0,    1, "Débutant",    "#6c757d", "rgba(108,117,125,0.5)", "🌟", None),
    (50,   2, "Amateur",     "#0dcaf0", "rgba(13,202,240,0.5)",  "⚡", None),
    (200,  3, "Bosseur",     "#fd7e14", "rgba(253,126,20,0.5)",  "🔥", None),
    (500,  4, "Expert",      "#0d6efd", "rgba(13,110,253,0.5)",  "⚙️", None),
    (1200, 5, "Master",      "#ffc107", "rgba(255,193,7,0.5)",   "🏆", None),
    (3000, 6, "Légende",     "#a855f7", "rgba(168,85,247,0.5)",  "👑", "master_criteria"),
]

def compute_xp_and_level(user_id):
    """Return (xp_total, xp_breakdown, level_dict, xp_to_next) for a user."""
    from web.models import QuizAttempt, ChallengeSubmission, UserBadge, Chapter

    quiz_attempts = QuizAttempt.query.filter_by(user_id=user_id).all()
    submissions   = ChallengeSubmission.query.filter_by(user_id=user_id, passed=True).all()
    badges        = UserBadge.query.filter_by(user_id=user_id).all()

    chapters = {c.id: c.identifier for c in Chapter.query.all()}

    breakdown = []
    xp = 0

    # Quiz XP — per chapter, count the BEST attempt (if score >= 80%) → +10 XP
    chapter_best = {}
    for qa in quiz_attempts:
        pct = qa.score / qa.total_questions if qa.total_questions else 0
        if pct >= 0.8:
            prev = chapter_best.get(qa.chapter_id, 0)
            chapter_best[qa.chapter_id] = max(prev, qa.score)
    for cid, best_score in chapter_best.items():
        ident = chapters.get(cid, f"Chap {cid}")
        breakdown.append({"label": f"Quiz — {ident.capitalize()}", "xp": 10, "icon": "📚"})
        xp += 10

    # Challenge XP — per unique passed problem → scaled by difficulty
    passed_pids = set()
    for sub in submissions:
        if sub.problem_id not in passed_pids:
            passed_pids.add(sub.problem_id)
    
    if passed_pids:
        passed_problems = Problem.query.filter(Problem.id.in_(passed_pids)).all()
        for p in passed_problems:
            if p.difficulty == 'Easy':
                val = 10
                icon = "🌱"
            elif p.difficulty == 'Medium':
                val = 20
                icon = "⚡"
            elif p.difficulty == 'Hard':
                val = 50
                icon = "🔥"
            else:
                val = 25
                icon = "⚔️"
            breakdown.append({"label": f"Défi #{p.id} ({p.difficulty})", "xp": val, "icon": icon})
            xp += val

    # Badge XP — per badge → +50 XP
    from web.models import UserBadge as UB
    badge_map = {
        "streak_3": "Séquence 3 Jours", "streak_7": "Séquence 7 Jours",
        "course_1": "Premier Pas", "course_3": "Étudiant Assidu",
        "course_7": "Érudit", "course_10_master": "Algo Master",
        "chall_1": "Développeur", "chall_5": "Codeur",
        "chall_10_beg": "Débutant Challenges", "chall_20_int": "Intermédiaire Challenges",
        "chall_50_adv": "Avancé Challenges", "chall_100_mast": "Maître des Défis",
        "hacker_bronze": "Hacker Bronze", "hacker_gold": "Hacker Or",
        "hacker_platinum": "Hacker Platine", "hacker_diamond": "Hacker Diamant",
        "hacker_master": "Maître Hacker", "hacker_grandmaster": "Grand Maître Hacker",
    }
    for ub in badges:
        label = badge_map.get(ub.badge_id, ub.badge_id)
        breakdown.append({"label": f"Badge : {label}", "xp": 50, "icon": "🏅"})
        xp += 50

    # Determine level
    # Check master criteria for level 6
    total_challenges = len(passed_pids)
    all_quiz_pct = 0
    if quiz_attempts:
        # average of best % per chapter
        chapter_pct = {}
        for qa in quiz_attempts:
            p = qa.score / qa.total_questions * 100 if qa.total_questions else 0
            chapter_pct[qa.chapter_id] = max(chapter_pct.get(qa.chapter_id, 0), p)
        all_quiz_pct = sum(chapter_pct.values()) / len(chapter_pct) if chapter_pct else 0

    master_ok = (xp >= 3000 and all_quiz_pct >= 95 and total_challenges >= 50)
    
    current_level = LEVEL_DEFS[0]
    for lvl in LEVEL_DEFS:
        min_xp, lnum, name, color, glow, icon, special = lvl
        if special == "master_criteria":
            if master_ok:
                current_level = lvl
        elif xp >= min_xp:
            current_level = lvl

    # XP to next level
    next_xp = None
    for lvl in LEVEL_DEFS:
        if lvl[0] > xp:
            next_xp = lvl[0]
            break
    # If we're level 6 (max) and criteria met, no next level
    if current_level[1] == 6:
        xp_to_next = 0
        next_level_name = None
    elif next_xp is not None:
        xp_to_next = next_xp - xp
        next_level_name = [l[2] for l in LEVEL_DEFS if l[0] == next_xp][0]
    else:
        xp_to_next = 0
        next_level_name = None

    level_dict = {
        "num": current_level[1],
        "name": current_level[2],
        "color": current_level[3],
        "glow": current_level[4],
        "icon": current_level[5],
        "min_xp": current_level[0],
        "next_xp": next_xp,
        "next_level_name": next_level_name,
    }
    return xp, breakdown, level_dict, xp_to_next

def get_bulk_users_stats():
    """Return a dictionary mapping user_id to their stats (xp, level, counts) computed in bulk."""
    all_users = User.query.all()
    if not all_users:
        return {}

    # 1. Bulk Fetch all data
    quiz_attempts = QuizAttempt.query.all()
    submissions = ChallengeSubmission.query.filter_by(passed=True).all()
    user_badges = UserBadge.query.all()
    chapters = {c.id: c.identifier for c in Chapter.query.all()}
    problems = {p.id: p.difficulty for p in Problem.query.all()}

    # 2. Group data by user_id
    qa_by_user = {}
    for qa in quiz_attempts:
        if qa.user_id not in qa_by_user: qa_by_user[qa.user_id] = []
        qa_by_user[qa.user_id].append(qa)

    sub_by_user = {}
    for sub in submissions:
        if sub.user_id not in sub_by_user: sub_by_user[sub.user_id] = []
        sub_by_user[sub.user_id].append(sub)

    badges_by_user = {}
    for ub in user_badges:
        if ub.user_id not in badges_by_user: badges_by_user[ub.user_id] = []
        badges_by_user[ub.user_id].append(ub)

    # 2b. Compute per-problem placements in memory so the global leaderboard
    # can expose Top 1 / Top 3 / Top 10 without issuing one query per problem.
    placement_counts = compute_problem_placement_counts(submissions)

    # 3. Compute for each user
    results = {}
    for user in all_users:
        uid = user.id
        u_qas = qa_by_user.get(uid, [])
        u_subs = sub_by_user.get(uid, [])
        u_badges = badges_by_user.get(uid, [])

        xp = 0
        
        # Quiz XP
        chapter_best = {}
        chapter_pct = {}
        q_count = 0
        for qa in u_qas:
            pct = qa.score / qa.total_questions if qa.total_questions else 0
            chapter_pct[qa.chapter_id] = max(chapter_pct.get(qa.chapter_id, 0), pct * 100)
            if pct >= 0.8:
                prev = chapter_best.get(qa.chapter_id, 0)
                if prev == 0: q_count += 1
                chapter_best[qa.chapter_id] = max(prev, qa.score)
        
        for _ in chapter_best:
            xp += 10

        # Challenge XP
        passed_pids = set()
        for sub in u_subs:
            if sub.problem_id not in passed_pids:
                passed_pids.add(sub.problem_id)
        
        for pid in passed_pids:
            diff = problems.get(pid, 'Easy')
            if diff == 'Easy': val = 10
            elif diff == 'Medium': val = 20
            elif diff == 'Hard': val = 50
            else: val = 25
            xp += val

        # Badge XP
        for _ in u_badges:
            xp += 50

        # Level detection
        total_challenges = len(passed_pids)
        all_quiz_pct = sum(chapter_pct.values()) / len(chapter_pct) if chapter_pct else 0
        master_ok = (xp >= 3000 and all_quiz_pct >= 95 and total_challenges >= 50)
        
        current_level = LEVEL_DEFS[0]
        for lvl in LEVEL_DEFS:
            min_xp, lnum, name, color, glow, icon, special = lvl
            if special == "master_criteria":
                if master_ok: current_level = lvl
            elif xp >= min_xp:
                current_level = lvl

        results[uid] = {
            'name': user.name,
            'score': xp,
            'level': {
                'num': current_level[1],
                'name': current_level[2],
                'icon': current_level[5],
                'color': current_level[3],
                'glow': current_level[4]
            },
            'quizzes': q_count,
            'challenges': total_challenges,
            'badges': len(u_badges),
            'year_created': user.created_at.year if user.created_at else None,
            'top1': placement_counts[uid]['top1'],
            'top3': placement_counts[uid]['top3'],
            'top10': placement_counts[uid]['top10']
        }

    return results

def compute_user_leaderboard_bucket(stats_by_user, user_id):
    if not stats_by_user or user_id not in stats_by_user:
        return {
            'rank': None,
            'total_users': 0,
            'top_percent': 100.0,
            'bucket_percent': 100,
            'bucket_label': 'Top 100%'
        }

    ranked_users = sorted(
        stats_by_user.items(),
        key=lambda item: (
            -item[1].get('score', 0),
            -item[1].get('challenges', 0),
            -item[1].get('quizzes', 0),
            str(item[1].get('name', '')).lower(),
            item[0]
        )
    )

    total_users = len(ranked_users)
    user_rank = next((index for index, (uid, _) in enumerate(ranked_users, start=1) if uid == user_id), None)
    if user_rank is None:
        return {
            'rank': None,
            'total_users': total_users,
            'top_percent': 100.0,
            'bucket_percent': 100,
            'bucket_label': 'Top 100%'
        }

    if total_users <= 1:
        top_percent = 1.0
    else:
        top_percent = round((user_rank / total_users) * 100, 1)

    thresholds = [1, 5, 10, 20, 50, 70]
    bucket_percent = next((threshold for threshold in thresholds if top_percent <= threshold), 100)

    return {
        'rank': user_rank,
        'total_users': total_users,
        'top_percent': top_percent,
        'bucket_percent': bucket_percent,
        'bucket_label': f'Top {bucket_percent}%'
    }

@app.route('/api/user/progress', methods=['GET'])
def get_user_progress():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    # Aggregate data
    quiz_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.timestamp.desc()).all()
    submissions = ChallengeSubmission.query.filter_by(user_id=current_user.id).order_by(ChallengeSubmission.timestamp.desc()).all()
    
    chapter_stats = {}
    for qa in quiz_attempts:
        chap_id = qa.chapter_id
        is_completed = (qa.score / qa.total_questions) >= 0.8 if qa.total_questions > 0 else False
        score_perc = (qa.score / qa.total_questions * 100) if qa.total_questions > 0 else 0
        
        if chap_id not in chapter_stats:
            chapter_stats[chap_id] = {
                'all_correct': is_completed, 
                'taken': True, 
                'score': qa.score, 
                'total': qa.total_questions,
                'attempts_count': 1,
                'total_perc': score_perc
            }
        else:
            chapter_stats[chap_id]['attempts_count'] += 1
            chapter_stats[chap_id]['total_perc'] += score_perc
            if is_completed:
                chapter_stats[chap_id]['all_correct'] = True
            if qa.score > chapter_stats[chap_id]['score']:
                chapter_stats[chap_id]['score'] = qa.score
                chapter_stats[chap_id]['total'] = qa.total_questions

    # Finalize average calculation
    for chap_id in chapter_stats:
        stats = chapter_stats[chap_id]
        stats['avg_score'] = round(stats['total_perc'] / stats['attempts_count'], 1)
            
    # Map chapter IDs to their identifiers to send back to frontend
    chapters = Chapter.query.all()
    chapter_map = {c.id: c.identifier for c in chapters}
    
    frontend_chapter_stats = {}
    for cid, stats in chapter_stats.items():
        if cid in chapter_map:
            frontend_chapter_stats[chapter_map[cid]] = stats

    challenge_stats = {}
    for sub in submissions:
        pid = sub.problem_id
        if pid not in challenge_stats:
            challenge_stats[pid] = {'passed': False, 'best_score': 0}
        if sub.passed:
            challenge_stats[pid]['passed'] = True
        if sub.score > challenge_stats[pid]['best_score']:
             challenge_stats[pid]['best_score'] = sub.score

    total_quizzes = len(quiz_attempts)
    perfect_quizzes = sum(1 for q in quiz_attempts if q.all_correct)
    unique_perfect_chapters = sum(1 for cid in frontend_chapter_stats if frontend_chapter_stats[cid].get('all_correct'))
    
    total_challenges_attempted = len(set(sub.problem_id for sub in submissions))
    total_available_challenges = Problem.query.filter_by(is_published=True).count()
    if total_available_challenges == 0:
        total_available_challenges = Problem.query.count()
    passed_challenges = sum(1 for pid in challenge_stats if challenge_stats[pid]['passed'])
    global_user_stats = get_bulk_users_stats()
    current_global_stats = global_user_stats.get(current_user.id, {})
    current_user_placements = {
        'top1': current_global_stats.get('top1', 0),
        'top3': current_global_stats.get('top3', 0),
        'top10': current_global_stats.get('top10', 0)
    }
    top1_percentage = round((current_user_placements['top1'] / total_available_challenges) * 100, 1) if total_available_challenges else 0.0
    top3_percentage = round((current_user_placements['top3'] / total_available_challenges) * 100, 1) if total_available_challenges else 0.0
    top10_percentage = round((current_user_placements['top10'] / total_available_challenges) * 100, 1) if total_available_challenges else 0.0
    leaderboard_bucket = compute_user_leaderboard_bucket(global_user_stats, current_user.id)

    # Normalize challenge topics for badge logic / stats
    def normalize_topic(value):
        t = str(value or '').strip().lower()
        if 'pile' in t or 'stack' in t:
            return 'Piles'
        if 'liste' in t or 'chain' in t or 'linked' in t:
            return 'Listes_Chainees'
        if 'file' in t or 'queue' in t:
            return 'Files'
        if 'array' in t or 'tableau' in t:
            return 'Arrays'
        if 'string' in t or 'chaine' in t:
            return 'Strings'
        if 'enregistr' in t or 'record' in t:
            return 'Enregistrements'
        return str(value or '').strip()

    passed_problem_rows = ChallengeSubmission.query.join(Problem).filter(
        ChallengeSubmission.user_id == current_user.id,
        ChallengeSubmission.passed == True
    ).with_entities(Problem.id, Problem.topic).distinct().all()
    topic_counts_norm = {}
    for _, topic in passed_problem_rows:
        canon = normalize_topic(topic)
        topic_counts_norm[canon] = topic_counts_norm.get(canon, 0) + 1
    
    # --- NEW ADVANCED STATISTICS (Phase 6) ---
    # 1. Challenge Distributions
    challenge_topic_dist = {}
    challenge_diff_dist = {'Easy': 0, 'Medium': 0, 'Hard': 0}
    
    # We only count UNIQUE passed problems for distribution
    passed_pids = [pid for pid, s in challenge_stats.items() if s['passed']]
    if passed_pids:
        passed_problems = Problem.query.filter(Problem.id.in_(passed_pids)).all()
        for p in passed_problems:
            challenge_topic_dist[p.topic] = challenge_topic_dist.get(p.topic, 0) + 1
            challenge_diff_dist[p.difficulty] = challenge_diff_dist.get(p.difficulty, 0) + 1

    # 2. Temporal Quiz Data (Daily Averages)
    daily_stats = {}
    for qa in quiz_attempts:
        day = qa.timestamp.date().isoformat()
        if day not in daily_stats:
            daily_stats[day] = {'total_score': 0, 'count': 0}
        daily_stats[day]['total_score'] += (qa.score / qa.total_questions) * 100
        daily_stats[day]['count'] += 1
    
    daily_avg_quiz_score = [
        {'day': d, 'avg': round(s['total_score'] / s['count'], 1)} 
        for d, s in sorted(daily_stats.items())
    ]

    # 3. Per-Chapter Score Evolution
    # Format: { 'chap_identifier': [ {timestamp, score_perc} ] }
    quiz_evolution_per_chapter = {}
    # Process in chronological order for the chart
    for qa in sorted(quiz_attempts, key=lambda x: x.timestamp):
        ident = chapter_map.get(qa.chapter_id)
        if not ident: continue
        if ident not in quiz_evolution_per_chapter:
            quiz_evolution_per_chapter[ident] = []
        quiz_evolution_per_chapter[ident].append({
            'ts': qa.timestamp.isoformat(),
            'score': round((qa.score / qa.total_questions) * 100, 1)
        })

    # --- END ADVANCED STATISTICS ---

    # --- NEW BADGES LOGIC based on Badges.txt ---
    # Streaks calculation (simplified for now to days active based on timestamps)
    # Course completion stats
    courses_completed = sum(1 for cid in frontend_chapter_stats if frontend_chapter_stats[cid].get('all_correct'))
    
    # Challenge Stats
    challenges_completed = passed_challenges
    
    # Mastery / Hacker Stats
    # Assuming "hard" challenges are those marked difficulty='Hard'
    hard_problems_passed = ChallengeSubmission.query.join(Problem).filter(
        ChallengeSubmission.user_id == current_user.id,
        ChallengeSubmission.passed == True,
        Problem.difficulty == 'Hard'
    ).with_entities(Problem.id).distinct().count()

    total_course_score = sum(stats['score']/stats['total'] for stats in chapter_stats.values()) if chapter_stats else 0
    num_courses_taken = len(chapter_stats) if chapter_stats else 1
    avg_course_score = (total_course_score / num_courses_taken) * 100
    
    # Calculate badges to award
    badges_to_award = []
    
    # 1. Streaks (Require complex date parsing - simplified placeholder for demo or basic activity)
    # We will award 3 day streak if they have submissions/quizzes on 3 distinct days
    import datetime
    distinct_active_days = set([d.timestamp.date() for d in submissions] + [d.timestamp.date() for d in quiz_attempts])
    active_days = len(distinct_active_days)
    
    if active_days >= 3: badges_to_award.append("streak_3")
    if active_days >= 7: badges_to_award.append("streak_7")
    if active_days >= 14: badges_to_award.append("streak_14")
    if active_days >= 30: badges_to_award.append("streak_30")
    if active_days >= 60: badges_to_award.append("streak_60")
    if active_days >= 90: badges_to_award.append("streak_90")
    if active_days >= 180: badges_to_award.append("streak_180")
    if active_days >= 365: badges_to_award.append("streak_365")
    
    # 2. Courses
    if courses_completed >= 1: badges_to_award.append("course_1")
    if courses_completed >= 3: badges_to_award.append("course_3")
    if courses_completed >= 7: badges_to_award.append("course_7")
    if courses_completed >= 10: badges_to_award.append("course_10_master")
    
    # 3. Challenges 
    if challenges_completed >= 1: badges_to_award.append("chall_1")
    if challenges_completed >= 5: badges_to_award.append("chall_5")
    if challenges_completed >= 10: badges_to_award.append("chall_10_beg")
    if challenges_completed >= 20: badges_to_award.append("chall_20_int")
    if challenges_completed >= 50: badges_to_award.append("chall_50_adv")
    if challenges_completed >= 100: badges_to_award.append("chall_100_mast")
        
    # 4. Mastery Hacker
    all_courses_finished = courses_completed >= 10
    if all_courses_finished and avg_course_score > 70 and challenges_completed >= 10 and hard_problems_passed >= 2:
        badges_to_award.append("hacker_bronze")
    if all_courses_finished and avg_course_score > 80 and challenges_completed >= 15 and hard_problems_passed >= 3:
        badges_to_award.append("hacker_gold")
    if all_courses_finished and avg_course_score > 90 and challenges_completed >= 20 and hard_problems_passed >= 4:
        badges_to_award.append("hacker_platinum")
    if all_courses_finished and avg_course_score > 92 and challenges_completed >= 30 and hard_problems_passed >= 6:
        badges_to_award.append("hacker_diamond")
    if all_courses_finished and avg_course_score > 95 and challenges_completed >= 40 and hard_problems_passed >= 8:
        badges_to_award.append("hacker_master")
    if all_courses_finished and avg_course_score > 99 and challenges_completed >= 50 and hard_problems_passed >= 10:
        badges_to_award.append("hacker_grandmaster")
        
    # 5. Maitre Badges (Assuming specific topic problem counts)
    def chapter_prob_passed(topic):
        return topic_counts_norm.get(topic, 0)
        
    if chapter_prob_passed("Arrays") >= 20: badges_to_award.append("maitre_tableaux")
    if chapter_prob_passed("Strings") >= 20: badges_to_award.append("maitre_chaines")
    if chapter_prob_passed("Enregistrements") >= 20: badges_to_award.append("maitre_enregistrements")
    if chapter_prob_passed("Listes_Chainees") >= 20: badges_to_award.append("maitre_listes")
    if chapter_prob_passed("Files") >= 20: badges_to_award.append("maitre_files")
    if chapter_prob_passed("Piles") >= 20: badges_to_award.append("maitre_piles")

    # Query existing badges to see what's new
    existing_badges = {ub.badge_id: ub for ub in UserBadge.query.filter_by(user_id=current_user.id).all()}
    
    new_badges_awarded = []
    for bid in badges_to_award:
        if bid not in existing_badges:
            ub = UserBadge(user_id=current_user.id, badge_id=bid, seen=False)
            db.session.add(ub)
            new_badges_awarded.append(bid)
            existing_badges[bid] = ub
            
    if new_badges_awarded:
        db.session.commit()

    # Define metadata for frontend delivery
    badge_defs = {
        "streak_3": {"name": "Séquence 3 Jours", "desc": "Actif pendant 3 jours distincts", "icon": "fas fa-fire", "category": "streak"},
        "streak_7": {"name": "Séquence 7 Jours", "desc": "Actif pendant 7 jours distincts", "icon": "fas fa-fire-alt", "category": "streak"},
        "streak_14": {"name": "Séquence 14 Jours", "desc": "Actif pendant 14 jours distincts", "icon": "fas fa-burn", "category": "streak"},
        "streak_30": {"name": "Séquence Mensuelle", "desc": "Actif pendant 30 jours", "icon": "fas fa-calendar-check", "category": "streak"},
        
        "course_1": {"name": "Premier Pas", "desc": "1 cours terminé", "icon": "fas fa-book-open", "category": "course"},
        "course_3": {"name": "Étudiant Assidu", "desc": "3 cours terminés", "icon": "fas fa-book-reader", "category": "course"},
        "course_7": {"name": "Érudit", "desc": "7 cours terminés", "icon": "fas fa-graduation-cap", "category": "course"},
        "course_10_master": {"name": "Algo Master", "desc": "10 cours terminés", "icon": "fas fa-university", "category": "course"},
        
        "chall_1": {"name": "Développeur", "desc": "1 défi terminé", "icon": "fas fa-keyboard", "category": "challenges"},
        "chall_5": {"name": "Codeur", "desc": "5 défis terminés", "icon": "fas fa-laptop-code", "category": "challenges"},
        "chall_10_beg": {"name": "Débutant", "desc": "10 défis terminés", "icon": "fas fa-medal", "category": "challenges"},
        "chall_20_int": {"name": "Intermédiaire", "desc": "20 défis terminés", "icon": "fas fa-award", "category": "challenges"},
        "chall_50_adv": {"name": "Avancé", "desc": "50 défis terminés", "icon": "fas fa-trophy", "category": "challenges"},
        "chall_100_mast": {"name": "Maître des Défis", "desc": "100 défis terminés", "icon": "fas fa-crown", "category": "challenges"},
        
        "hacker_bronze": {"name": "Hacker Bronze", "desc": "Tous cours, avg > 70%, 10 défis dont 2 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_gold": {"name": "Hacker Or", "desc": "Tous cours, avg > 80%, 15 défis dont 3 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_platinum": {"name": "Hacker Platine", "desc": "Tous cours, avg > 90%, 20 défis dont 4 difficiles", "icon": "fas fa-user-ninja", "category": "mastery"},
        "hacker_diamond": {"name": "Hacker Diamant", "desc": "Tous cours, avg > 92%, 30 défis dont 6 difficiles", "icon": "fas fa-user-astronaut", "category": "mastery"},
        "hacker_master": {"name": "Maître Hacker", "desc": "Tous cours, avg > 95%, 40 défis dont 8 difficiles", "icon": "fas fa-user-secret", "category": "mastery"},
        "hacker_grandmaster": {"name": "Grand Maître Hacker", "desc": "Tous cours, avg > 99%, 50 défis dont 10 difficiles", "icon": "fas fa-user-secret", "category": "mastery"},
        
        "maitre_tableaux": {"name": "Maitre des Tableaux", "desc": "20 problèmes sur Arrays", "icon": "fas fa-table", "category": "maitre"},
        "maitre_chaines": {"name": "Maitre des Chaines", "desc": "20 problèmes sur Strings", "icon": "fas fa-font", "category": "maitre"},
        "maitre_enregistrements": {"name": "Maitre des Enregistrements", "desc": "20 problèmes d'Enregistrements", "icon": "fas fa-address-card", "category": "maitre"},
        "maitre_listes": {"name": "Maitre des Listes Chainees", "desc": "20 problèmes sur LinkedList", "icon": "fas fa-link", "category": "maitre"},
        "maitre_files": {"name": "Maitre des Files", "desc": "20 problèmes sur Files", "icon": "fas fa-layer-group", "category": "maitre"},
        "maitre_piles": {"name": "Maitre des Piles", "desc": "20 problèmes sur Piles", "icon": "fas fa-bars", "category": "maitre"},
    }
    
    # Send up all definitions, marking which ones the user earned vs locked
    badges_response = []
    for bid, meta in badge_defs.items():
        badges_response.append({
            "id": bid,
            "name": meta["name"],
            "description": meta["desc"],
            "icon": meta["icon"],
            "category": meta["category"],
            "earned": bid in existing_badges,
            "seen": existing_badges[bid].seen if bid in existing_badges else True
        })

    # Topic counts for "Maitre" badges
    topics = ["Arrays", "Strings", "Enregistrements", "Listes_Chainees", "Files", "Piles"]
    topic_counts = {t: chapter_prob_passed(t) for t in topics}

    # Activity Heatmap Data (last 365 days)
    activity_map = {}
    today = datetime.date.today()
    one_year_ago = today - datetime.timedelta(days=365)
    for sub in submissions:
        d = sub.timestamp.date()
        if d >= one_year_ago:
            key = d.isoformat()
            activity_map[key] = activity_map.get(key, 0) + 1
    for qa in quiz_attempts:
        d = qa.timestamp.date()
        if d >= one_year_ago:
            key = d.isoformat()
            activity_map[key] = activity_map.get(key, 0) + 1

    # XP and Level computation
    xp_total, xp_breakdown, level_dict, xp_to_next = compute_xp_and_level(current_user.id)

    return jsonify({
        'success': True,
        'progress': {
            'chapter_stats': frontend_chapter_stats,
            'challenge_stats': challenge_stats,
            'total_quizzes_taken': total_quizzes,
            'total_challenges_attempted': total_challenges_attempted,
            'total_available_challenges': total_available_challenges,
            'challenges_completed': passed_challenges,
            'top1_finishes': current_user_placements['top1'],
            'top1_percentage': top1_percentage,
            'top3_finishes': current_user_placements['top3'],
            'top3_percentage': top3_percentage,
            'top10_finishes': current_user_placements['top10'],
            'top10_percentage': top10_percentage,
            'leaderboard_bucket': leaderboard_bucket,
            'active_days': active_days,
            'courses_completed': courses_completed,
            'hard_challenges_completed': hard_problems_passed,
            'avg_course_score': avg_course_score,
            'topic_counts': topic_counts,
            'badges': badges_response,
            'activity_map': activity_map,
            'xp_total': xp_total,
            'xp_breakdown': xp_breakdown,
            'level': level_dict,
            'xp_to_next': xp_to_next,
            'advanced_stats': {
                'challenge_topic_dist': challenge_topic_dist,
                'challenge_diff_dist': challenge_diff_dist,
                'daily_avg_quiz_score': daily_avg_quiz_score,
                'quiz_evolution_per_chapter': quiz_evolution_per_chapter
            }
        }
    })


@app.route('/api/user/level', methods=['GET'])
def get_user_level():
    if not current_user.is_authenticated:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    snapshot = get_cached_user_level_snapshot(current_user.id)
    return jsonify({
        'success': True,
        'xp_total': snapshot['xp_total'],
        'level': snapshot['level'],
        'xp_to_next': snapshot['xp_to_next'],
        'computed_at': snapshot['computed_at']
    })

@app.route('/leaderboard')
@app.route('/leaderboards')
def leaderboard_page():
    return render_template('leaderboard.html')

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        stats = get_bulk_users_stats()
        leaderboard = list(stats.values())
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/badges')
@login_required
def badges_page():
    return render_template('badges.html')

@app.route('/api/user/badges/seen', methods=['POST'])
@login_required
def mark_badges_seen():
    try:
        data = request.json or {}
        badge_ids = data.get('badge_ids', [])
        
        if badge_ids:
            # Mark specific badges
            UserBadge.query.filter(
                UserBadge.user_id == current_user.id,
                UserBadge.badge_id.in_(badge_ids)
            ).update({"seen": True}, synchronize_session=False)
        else:
            # Mark all as seen
            UserBadge.query.filter_by(
                user_id=current_user.id, 
                seen=False
            ).update({"seen": True}, synchronize_session=False)
            
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    name = data.get('name')
    dob_str = data.get('date_of_birth')
    study_year = data.get('study_year')
    
    if not name:
        return jsonify({'success': False, 'error': 'Le pseudo est requis'}), 400
        
    current_user.name = name
    current_user.study_year = study_year
    
    if dob_str:
        try:
            from datetime import datetime
            current_user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            pass # Ignore invalid date format
            
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Profil mis à jour avec succès'
    })

@app.route('/api/challenge/<int:problem_id>/live')
def live_contest(problem_id):
    from web.models import ChallengeSubmission
    import datetime
    
    # Simplified real-time tracking: only consider submissions from the last 24 hours
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    from sqlalchemy.orm import joinedload
    submissions = ChallengeSubmission.query.options(joinedload(ChallengeSubmission.user)).filter(
        ChallengeSubmission.problem_id == problem_id,
        ChallengeSubmission.timestamp >= cutoff
    ).all()
    
    user_map = {}
    for s in submissions:
        uid = s.user_id
        if uid not in user_map:
            user_map[uid] = {
                'user': s.user,
                'attempts': 0,
                'best_score': 0,
                'passed': False,
                'best_time': 999999
            }
        
        entry = user_map[uid]
        entry['attempts'] += 1
        
        if s.score > entry['best_score']:
            entry['best_score'] = s.score
            entry['best_time'] = s.time_taken_seconds
            entry['passed'] = s.passed
        elif s.score == entry['best_score'] and s.time_taken_seconds < entry['best_time']:
            entry['best_time'] = s.time_taken_seconds

    results = []
    for uid, data in user_map.items():
        status = 'Échoué'
        if data['passed']:
            status = 'Réussi'
        elif data['best_score'] > 0:
            status = 'Partiel'
            
        results.append({
            'user_id': uid,
            'name': data['user'].name if data['user'] else f"User {uid}",
            'score': round(data['best_score'], 1),
            'time_taken': data['best_time'] if data['best_time'] != 999999 else 0,
            'attempts': data['attempts'],
            'status': status,
            'passed': data['passed']
        })
        
    results.sort(key=lambda x: (-x['score'], x['time_taken']))
    
    return jsonify({'success': True, 'leaderboard': results})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    debug_enabled = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes', 'on')
    app.run(debug=debug_enabled, host='0.0.0.0', port=port, use_reloader=debug_enabled)
