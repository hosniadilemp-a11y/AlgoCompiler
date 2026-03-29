"""
Admin Blueprint – Teacher Dashboard
Accessible at /admin, protected by session-based login (Teacher1 / teacher).
Completely separate from the main user auth (Flask-Login).
"""
import datetime
import functools
import os
import csv
import io
import json

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from web.models import (
    Chapter, Choice, ChallengeSubmission, CourseChapter, CourseSection, Problem,
    Question, QuizAttempt, TestCase, User, UserBadge, UserProgress, db
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Credentials (override via env vars) ──────────────────────────────────────
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')


def has_env_admin_credentials():
    return bool(ADMIN_USERNAME and ADMIN_PASSWORD)


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.is_json or request.path.startswith('/admin/api/'):
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('admin.login_page'))
        return f(*args, **kwargs)
    return decorated


# ── Auth ─────────────────────────────────────────────────────────────────────
@admin_bp.route('/', methods=['GET'])
@admin_bp.route('/dashboard', methods=['GET'])
def login_page():
    if session.get('admin_logged_in'):
        return render_template('admin.html', view='dashboard')
    return render_template('admin.html', view='login')


@admin_bp.route('/login', methods=['POST'])
def login_api():
    data = request.get_json() or {}
    username_input = str(data.get('username', '')).strip()
    password_input = str(data.get('password', ''))
    
    # Check Database first
    user = User.query.filter_by(name=username_input).first()
    if user and user.password_hash and user.is_admin:
        from werkzeug.security import check_password_hash
        if check_password_hash(user.password_hash, password_input):
            session['admin_logged_in'] = True
            session.permanent = True
            session['admin_user_id'] = user.id
            session['admin_user_name'] = user.name
            session['admin_user_email'] = user.email
            return jsonify({'success': True})

    # Fallback only when env credentials were explicitly configured.
    if has_env_admin_credentials() and username_input == ADMIN_USERNAME and password_input == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
        session.permanent = True
        session['admin_user_id'] = None
        session['admin_user_name'] = username_input
        session['admin_user_email'] = None
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'Identifiants incorrects ou accès non autorisé.'}), 401


@admin_bp.route('/logout')
def do_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user_id', None)
    session.pop('admin_user_name', None)
    session.pop('admin_user_email', None)
    return redirect(url_for('admin.login_page'))


# ── Admin Management Routes ───────────────────────────────────────────────────
@admin_bp.route('/api/admins', methods=['GET'])
@admin_required
def get_admins():
    admins = User.query.filter_by(is_admin=True).all()
    results = [{'id': a.id, 'name': a.name, 'email': a.email} for a in admins]
    return jsonify({'success': True, 'admins': results})

@admin_bp.route('/api/admins', methods=['POST'])
@admin_required
def add_admin():
    data = request.get_json() or {}
    name = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not name or not email or not password:
        return jsonify({'success': False, 'error': 'Tous les champs sont requis.'}), 400
        
    # Check if user already exists
    user = User.query.filter((User.name == name) | (User.email == email)).first()
    
    if user:
        if user.is_admin:
            return jsonify({'success': False, 'error': 'Cet utilisateur est déjà administrateur.'}), 400
        # Promote existing user
        user.is_admin = True
        if password: # Optionally update missing password hash
            user.password_hash = generate_password_hash(password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Utilisateur existant promu administrateur.'})
        
    # Create new explicit admin user
    new_user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        is_admin=True,
        email_verified=True # Automatically verified since created by admin
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Nouvel administrateur créé.'})

@admin_bp.route('/api/admins/remove', methods=['POST'])
@admin_required
def remove_admin():
    data = request.get_json() or {}
    admin_id = data.get('admin_id')
    user = db.session.get(User, admin_id)
    if not user:
        return jsonify({'success': False, 'error': 'Utilisateur introuvable.'}), 404
    
    user.is_admin = False
    db.session.commit()
    return jsonify({'success': True, 'message': 'Droits administrateurs révoqués.'})
    
# ── Problem Editor Pages ──────────────────────────────────────────────────────
@admin_bp.route('/problems/new')
@admin_required
def problem_new():
    return render_template('admin_problem_editor.html', problem=None, problem_id=None)


@admin_bp.route('/problems/<int:pid>/edit')
@admin_required
def problem_edit(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return redirect(url_for('admin.login_page'))
    return render_template('admin_problem_editor.html', problem=_prob_json(p), problem_id=pid)


@admin_bp.route('/courses/editor')
@admin_required
def admin_course_editor_page():
    return render_template('admin_course_editor.html')


# ── Analytics: Overview ───────────────────────────────────────────────────────
@admin_bp.route('/api/stats/overview')
@admin_required
def stats_overview():
    return jsonify({
        'total_users': User.query.count(),
        'total_problems': Problem.query.count(),
        'total_chapters': Chapter.query.count(),
        'total_quiz_attempts': QuizAttempt.query.count(),
        'total_submissions': ChallengeSubmission.query.count(),
        'passed_submissions': ChallengeSubmission.query.filter_by(passed=True).count(),
        'total_badges_awarded': UserBadge.query.count(),
    })


# ── Analytics: Activity ───────────────────────────────────────────────────────
@admin_bp.route('/api/stats/activity')
@admin_required
def stats_activity():
    days = int(request.args.get('days', 30))
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)

    activity = {(start + datetime.timedelta(days=i)).isoformat(): 0 for i in range(days)}

    for row in (
        db.session.query(func.date(QuizAttempt.timestamp).label('d'), func.count(QuizAttempt.id).label('c'))
        .filter(QuizAttempt.timestamp >= start)
        .group_by(func.date(QuizAttempt.timestamp)).all()
    ):
        if row.d in activity:
            activity[row.d] += row.c

    for row in (
        db.session.query(func.date(ChallengeSubmission.timestamp).label('d'), func.count(ChallengeSubmission.id).label('c'))
        .filter(ChallengeSubmission.timestamp >= start)
        .group_by(func.date(ChallengeSubmission.timestamp)).all()
    ):
        if row.d in activity:
            activity[row.d] += row.c

    return jsonify({'labels': list(activity.keys()), 'values': list(activity.values())})


@admin_bp.route('/api/stats/insights')
@admin_required
def stats_insights():
    now = datetime.datetime.utcnow()
    online_cutoff = now - datetime.timedelta(minutes=5)
    d1 = now - datetime.timedelta(days=1)
    d7 = now - datetime.timedelta(days=7)

    users = User.query.all()
    user_ids = [u.id for u in users]
    user_map = {u.id: u for u in users}

    quiz_rows = (
        db.session.query(
            QuizAttempt.user_id,
            func.count(QuizAttempt.id).label('quiz_count'),
            func.avg((QuizAttempt.score * 100.0) / func.nullif(QuizAttempt.total_questions, 0)).label('avg_quiz_score'),
            func.max(QuizAttempt.timestamp).label('last_quiz_at')
        )
        .group_by(QuizAttempt.user_id)
        .all()
    )
    quiz_map = {r.user_id: r for r in quiz_rows}

    sub_rows = (
        db.session.query(
            ChallengeSubmission.user_id,
            func.count(ChallengeSubmission.id).label('sub_count'),
            func.sum(case((ChallengeSubmission.passed == True, 1), else_=0)).label('passed_count'),
            func.avg(ChallengeSubmission.time_taken_seconds).label('avg_sub_time'),
            func.max(ChallengeSubmission.timestamp).label('last_sub_at')
        )
        .group_by(ChallengeSubmission.user_id)
        .all()
    )
    sub_map = {r.user_id: r for r in sub_rows}

    # Distinct challenge engagement (avoids inflated scores from repeated submissions)
    challenge_distinct_rows = (
        db.session.query(
            ChallengeSubmission.user_id,
            func.count(func.distinct(ChallengeSubmission.problem_id)).label('distinct_challenges'),
            func.count(func.distinct(case((ChallengeSubmission.passed == True, ChallengeSubmission.problem_id), else_=None))).label('distinct_solved')
        )
        .group_by(ChallengeSubmission.user_id)
        .all()
    )
    challenge_distinct_map = {r.user_id: r for r in challenge_distinct_rows}

    # Distinct quiz chapter coverage
    quiz_chapter_rows = (
        db.session.query(
            QuizAttempt.user_id,
            func.count(func.distinct(QuizAttempt.chapter_id)).label('quiz_chapters')
        )
        .group_by(QuizAttempt.user_id)
        .all()
    )
    quiz_chapter_map = {r.user_id: int(r.quiz_chapters or 0) for r in quiz_chapter_rows}

    # Recent activity intensity (24h / 7d)
    recent_r24 = db.session.query(
        ChallengeSubmission.user_id, func.count(ChallengeSubmission.id).label('cnt')
    ).filter(ChallengeSubmission.timestamp >= d1).group_by(ChallengeSubmission.user_id).all()
    recent_q24 = db.session.query(
        QuizAttempt.user_id, func.count(QuizAttempt.id).label('cnt')
    ).filter(QuizAttempt.timestamp >= d1).group_by(QuizAttempt.user_id).all()
    
    recent_r7 = db.session.query(
        ChallengeSubmission.user_id, func.count(ChallengeSubmission.id).label('cnt')
    ).filter(ChallengeSubmission.timestamp >= d7).group_by(ChallengeSubmission.user_id).all()
    recent_q7 = db.session.query(
        QuizAttempt.user_id, func.count(QuizAttempt.id).label('cnt')
    ).filter(QuizAttempt.timestamp >= d7).group_by(QuizAttempt.user_id).all()

    r24_map = {}
    r7_map = {}
    for r in recent_r24: r24_map[r.user_id] = r24_map.get(r.user_id, 0) + r.cnt
    for r in recent_q24: r24_map[r.user_id] = r24_map.get(r.user_id, 0) + r.cnt
    for r in recent_r7: r7_map[r.user_id] = r7_map.get(r.user_id, 0) + r.cnt
    for r in recent_q7: r7_map[r.user_id] = r7_map.get(r.user_id, 0) + r.cnt

    badge_rows = (
        db.session.query(UserBadge.user_id, func.count(UserBadge.id).label('badge_count'))
        .group_by(UserBadge.user_id)
        .all()
    )
    badge_map = {r.user_id: int(r.badge_count or 0) for r in badge_rows}

    # Fetch all users once with only needed columns
    users_basic = db.session.query(User.id, User.name, User.email, User.last_seen).all()
    user_ids = [u.id for u in users_basic]

    ranked = []
    # Use the same XP source as profile/leaderboard to keep scores consistent.
    bulk_stats = {}
    try:
        # Avoid redundant User.query.all() inside get_bulk_users_stats by manually doing it or passing IDs
        from web.app import get_bulk_users_stats
        bulk_stats = get_bulk_users_stats()
    except Exception:
        pass

    online_now = 0
    active_24h = 0
    for u in users_basic:
        uid = u.id
        q = quiz_map.get(uid)
        s = sub_map.get(uid)
        ds = challenge_distinct_map.get(uid)
        quiz_count = int(getattr(q, 'quiz_count', 0) or 0)
        sub_count = int(getattr(ds, 'distinct_challenges', 0) or 0)
        passed_count = int(getattr(ds, 'distinct_solved', 0) or 0)
        badge_count = int(badge_map.get(uid, 0))
        quiz_chapters = int(quiz_chapter_map.get(uid, 0))
        recent_24h_actions = int(r24_map.get(uid, 0))
        recent_7d_actions = int(r7_map.get(uid, 0))
        avg_quiz_score = float(getattr(q, 'avg_quiz_score', 0) or 0)

        last_quiz_at = getattr(q, 'last_quiz_at', None)
        last_sub_at = getattr(s, 'last_sub_at', None)
        last_seen_at = getattr(u, 'last_seen', None)
        dates = [d for d in [last_quiz_at, last_sub_at, last_seen_at] if d]
        last_activity = max(dates) if dates else None

        if last_activity and last_activity >= online_cutoff:
            online_now += 1
        if last_activity and last_activity >= d1:
            active_24h += 1

        total_actions = quiz_chapters + sub_count
        success_rate = round((passed_count / sub_count * 100), 1) if sub_count else 0
        
        # Main displayed score now follows profile/leaderboard XP exactly.
        xp_total = bulk_stats.get(uid, {}).get('score', 0)
        activity_score = int(xp_total)

        # Main displayed score now follows profile/leaderboard XP exactly.
        activity_score = int(xp_total or 0)

        ranked.append({
            'id': uid,
            'name': u.name,
            'email': u.email,
            'quiz_count': quiz_count,
            'quiz_chapters': quiz_chapters,
            'challenge_count': sub_count,
            'passed_count': passed_count,
            'badge_count': badge_count,
            'avg_quiz_score': round(avg_quiz_score, 1),
            'success_rate': success_rate,
            'total_actions': total_actions,
            'recent_24h_actions': recent_24h_actions,
            'recent_7d_actions': recent_7d_actions,
            'activity_score': activity_score,
            'xp_total': activity_score,
            'last_activity': last_activity.isoformat() if last_activity else None,
        })

    top_active_users = sorted(
        ranked,
        key=lambda x: (x['activity_score'], x['recent_24h_actions'], x['recent_7d_actions'], x['last_activity'] or ''),
        reverse=True
    )[:10]
    ranked_users = sorted(
        ranked,
        key=lambda x: (x['success_rate'], x['avg_quiz_score'], x['total_actions']),
        reverse=True
    )[:10]

    for i, item in enumerate(top_active_users, start=1):
        item['rank'] = i
    for i, item in enumerate(ranked_users, start=1):
        item['rank'] = i

    new_users_7d = User.query.filter(User.created_at >= d7).count()
    submissions_24h = ChallengeSubmission.query.filter(ChallengeSubmission.timestamp >= d1).count()

    # 7d Analytics via SQL
    summ_sub_7d = db.session.query(
        func.count(ChallengeSubmission.id).label('total'),
        func.sum(case((ChallengeSubmission.passed == True, 1), else_=0)).label('passed'),
        func.sum(func.coalesce(ChallengeSubmission.time_taken_seconds, 0)).label('sum_time')
    ).filter(ChallengeSubmission.timestamp >= d7).first()
    
    pass_rate_7d = round((summ_sub_7d.passed / summ_sub_7d.total * 100), 1) if summ_sub_7d and summ_sub_7d.total else 0
    avg_sub_time_7d = round(float(summ_sub_7d.sum_time or 0) / summ_sub_7d.total, 1) if summ_sub_7d and summ_sub_7d.total else 0

    summ_quiz_7d = db.session.query(
        func.count(QuizAttempt.id).label('total'),
        func.avg(QuizAttempt.score * 100.0 / func.nullif(QuizAttempt.total_questions, 0)).label('avg_score')
    ).filter(QuizAttempt.timestamp >= d7).first()
    avg_quiz_score_7d = round(float(summ_quiz_7d.avg_score or 0), 1) if summ_quiz_7d else 0

    total_questions = Question.query.count()
    total_test_cases = TestCase.query.count()
    public_test_cases = TestCase.query.filter_by(is_public=True).count()
    hidden_test_cases = total_test_cases - public_test_cases

    # Problems without hidden tests (efficient via subquery)
    problems_with_hidden = db.session.query(TestCase.problem_id).filter(TestCase.is_public == False).distinct().subquery()
    problems_without_hidden_tests = db.session.query(func.count(Problem.id)).filter(Problem.id.not_in(problems_with_hidden)).scalar() or 0

    # Problem Spotlight (efficient aggregation)
    spotlight_stats = db.session.query(
        Problem.title,
        func.count(ChallengeSubmission.id).label('attempts'),
        func.sum(case((ChallengeSubmission.passed == True, 1), else_=0)).label('passed')
    ).join(ChallengeSubmission, ChallengeSubmission.problem_id == Problem.id).group_by(Problem.id, Problem.title).all()
    
    per_problem = []
    for s in spotlight_stats:
        p_rate = round((s.passed / s.attempts * 100), 1) if s.attempts else 0
        per_problem.append({'title': s.title, 'attempts': s.attempts, 'pass_rate': p_rate})

    attempted = [x for x in per_problem if x['attempts'] > 0]
    hardest = min(attempted, key=lambda x: x['pass_rate']) if attempted else None
    easiest = max(attempted, key=lambda x: x['pass_rate']) if attempted else None

    return jsonify({
        'summary': {
            'online_now': online_now,
            'active_24h': active_24h,
            'new_users_7d': new_users_7d,
            'submissions_24h': submissions_24h,
            'pass_rate_7d': pass_rate_7d,
            'avg_submission_time_7d': avg_sub_time_7d,
            'avg_quiz_score_7d': avg_quiz_score_7d,
            'total_questions': total_questions,
            'total_test_cases': total_test_cases,
            'public_test_cases': public_test_cases,
            'hidden_test_cases': hidden_test_cases,
            'problems_without_hidden_tests': problems_without_hidden_tests,
        },
        'top_active_users': top_active_users,
        'ranked_users': ranked_users,
        'problem_spotlight': {
            'hardest': hardest,
            'easiest': easiest,
        }
    })


# ── Analytics: Users list ─────────────────────────────────────────────────────
@admin_bp.route('/api/stats/users')
@admin_required
def stats_users():
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Bulk fetch counts and last activity
    from sqlalchemy import distinct
    
    quiz_stats = db.session.query(
        QuizAttempt.user_id,
        func.count(QuizAttempt.id).label('count'),
        func.avg(QuizAttempt.score * 100.0 / func.nullif(QuizAttempt.total_questions, 0)).label('avg_score'),
        func.max(QuizAttempt.timestamp).label('last_ts')
    ).group_by(QuizAttempt.user_id).all()
    quiz_map = {r.user_id: r for r in quiz_stats}
    
    chall_stats = db.session.query(
        ChallengeSubmission.user_id,
        func.count(distinct(ChallengeSubmission.problem_id)).label('total'),
        func.max(ChallengeSubmission.timestamp).label('last_ts')
    ).group_by(ChallengeSubmission.user_id).all()
    chall_map = {r.user_id: r for r in chall_stats}
    
    passed_stats = db.session.query(
        ChallengeSubmission.user_id,
        func.count(distinct(ChallengeSubmission.problem_id)).label('passed')
    ).filter(ChallengeSubmission.passed == True).group_by(ChallengeSubmission.user_id).all()
    passed_map = {r.user_id: r.passed for r in passed_stats}
    
    badge_counts = db.session.query(
        UserBadge.user_id,
        func.count(UserBadge.id).label('count')
    ).group_by(UserBadge.user_id).all()
    badge_map = {r.user_id: r.count for r in badge_counts}
    
    result = []
    for u in users:
        q = quiz_map.get(u.id)
        c = chall_map.get(u.id)
        
        last_q = q.last_ts if q else None
        last_c = c.last_ts if c else None
        dates = [d for d in [last_q, last_c] if d]
        last_activity = max(dates).isoformat() if dates else None

        result.append({
            'id': u.id, 
            'name': u.name,
            'email': u.email,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_activity': last_activity,
            'quiz_count': q.count if q else 0,
            'avg_quiz_score': round(float(q.avg_score or 0), 1) if q else 0,
            'challenge_total': c.total if c else 0,
            'challenge_passed': passed_map.get(u.id, 0),
            'badge_count': badge_map.get(u.id, 0),
        })
    return jsonify({'users': result})


# ── Analytics: User detail ────────────────────────────────────────────────────
@admin_bp.route('/api/stats/users/<int:user_id>')
@admin_required
def stats_user_detail(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'error': 'Not found'}), 404

    chapter_map = {c.id: c.title for c in Chapter.query.all()}
    problem_map = {p.id: p.title for p in Problem.query.all()}
    quizzes = QuizAttempt.query.filter_by(user_id=u.id).order_by(QuizAttempt.timestamp.desc()).all()
    subs = ChallengeSubmission.query.filter_by(user_id=u.id).order_by(ChallengeSubmission.timestamp.desc()).all()

    return jsonify({
        'user': {
            'id': u.id, 'name': u.name,
            'email': u.email, 'study_year': u.study_year,
            'created_at': u.created_at.isoformat() if u.created_at else None,
        },
        'quizzes': [{
            'chapter': chapter_map.get(q.chapter_id, f'#{q.chapter_id}'),
            'score': q.score, 'total': q.total_questions,
            'pct': round(q.score / q.total_questions * 100, 1) if q.total_questions else 0,
            'timestamp': q.timestamp.isoformat(),
        } for q in quizzes],
        'submissions': [{
            'problem': problem_map.get(s.problem_id, f'#{s.problem_id}'),
            'score': round(s.score, 1), 'passed': s.passed,
            'time_taken': s.time_taken_seconds,
            'timestamp': s.timestamp.isoformat(),
        } for s in subs],
    })


# ── Analytics: Problem stats ──────────────────────────────────────────────────
@admin_bp.route('/api/stats/problems')
@admin_required
def stats_problems():
    problems = Problem.query.order_by(Problem.id.asc()).all()
    
    from sqlalchemy import distinct
    sub_stats = db.session.query(
        ChallengeSubmission.problem_id,
        func.count(ChallengeSubmission.id).label('total'),
        func.sum(case((ChallengeSubmission.passed == True, 1), else_=0)).label('passed'),
        func.count(distinct(case((ChallengeSubmission.passed == True, ChallengeSubmission.user_id), else_=None))).label('unique_solvers'),
        func.sum(ChallengeSubmission.score).label('sum_score'),
        func.sum(ChallengeSubmission.time_taken_seconds).label('sum_time')
    ).group_by(ChallengeSubmission.problem_id).all()
    
    stats_map = {r.problem_id: r for r in sub_stats}
    
    result = []
    for p in problems:
        s = stats_map.get(p.id)
        total = s.total if s else 0
        passed = s.passed if s else 0
        result.append({
            'id': p.id, 'title': p.title, 'topic': p.topic, 'difficulty': p.difficulty,
            'total_attempts': total, 'total_passed': passed,
            'unique_solvers': s.unique_solvers if s else 0,
            'avg_score': round(float(s.sum_score or 0) / total, 1) if total else 0,
            'avg_time_seconds': round(float(s.sum_time or 0) / total, 1) if total else 0,
            'pass_rate': round(passed / total * 100, 1) if total else 0,
        })
    return jsonify({'problems': result})


# ── Analytics: Quiz stats ───────────────────────────────────────────────────
@admin_bp.route('/api/stats/quizzes')
@admin_required
def stats_quizzes():
    chapters = Chapter.query.order_by(Chapter.id.asc()).all()
    
    from sqlalchemy import distinct
    quiz_stats = db.session.query(
        QuizAttempt.chapter_id,
        func.count(distinct(QuizAttempt.user_id)).label('participants'),
        func.avg(QuizAttempt.score * 100.0 / func.nullif(QuizAttempt.total_questions, 0)).label('avg_score')
    ).group_by(QuizAttempt.chapter_id).all()
    
    stats_map = {r.chapter_id: r for r in quiz_stats}
    
    result = []
    for c in chapters:
        s = stats_map.get(c.id)
        result.append({
            'id': c.id,
            'title': c.title,
            'participants': s.participants if s else 0,
            'avg_score': round(float(s.avg_score or 0), 1) if s else 0
        })
    return jsonify({'chapters': result})


@admin_bp.route('/api/stats/quizzes/<int:cid>/questions')
@admin_required
def stats_quiz_questions(cid):
    questions = Question.query.filter_by(chapter_id=cid).order_by(Question.id.asc()).all()
    attempts = QuizAttempt.query.filter_by(chapter_id=cid).all()
    
    import json
    q_stats = {}
    for a in attempts:
        if a.details:
            try:
                details = json.loads(a.details)
                # New structure has questionResults
                q_res = details.get('questionResults', {})
                for qid_str, is_correct in q_res.items():
                    qid = int(qid_str)
                    if qid not in q_stats:
                        q_stats[qid] = {'total': 0, 'correct': 0}
                    q_stats[qid]['total'] += 1
                    if is_correct:
                        q_stats[qid]['correct'] += 1
            except Exception:
                pass
                
    result = []
    for q in questions:
        stats = q_stats.get(q.id, {'total': 0, 'correct': 0})
        success_rate = round(stats['correct'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        result.append({
            'id': q.id,
            'text': q.text,
            'concept': q.concept,
            'difficulty': q.difficulty,
            'total_answers': stats['total'],
            'success_rate': success_rate
        })
    return jsonify({'questions': result})


# ── User management ───────────────────────────────────────────────────────────
@admin_bp.route('/api/users/<int:user_id>/reset_password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    u = db.session.get(User, user_id)
    if not u:
        return jsonify({'error': 'Not found'}), 404
    pwd = str((request.get_json() or {}).get('password', '')).strip()
    if len(pwd) < 4:
        return jsonify({'error': 'Password must be at least 4 characters'}), 400
    u.password_hash = generate_password_hash(pwd)
    db.session.commit()
    return jsonify({'success': True})


# ── Problems CRUD ─────────────────────────────────────────────────────────────
def _prob_json(p):
    return {
        'id': p.id, 'title': p.title, 'description': p.description,
        'topic': p.topic, 'difficulty': p.difficulty, 'template_code': p.template_code,
        'is_published': bool(p.is_published),
        'test_cases': [
            {'id': tc.id, 'input': tc.input_data, 'expected_output': tc.expected_output, 'is_public': bool(tc.is_public)}
            for tc in sorted(p.test_cases, key=lambda x: x.id)
        ],
    }


def _normalize_prob(payload):
    for f in ['title', 'description', 'topic', 'difficulty']:
        if not str(payload.get(f, '')).strip():
            raise ValueError(f"'{f}' is required")
    tcs = payload.get('test_cases', [])
    if not isinstance(tcs, list):
        raise ValueError("'test_cases' must be a list")
    data = {
        'title': str(payload['title']).strip(), 'description': str(payload['description']),
        'topic': str(payload['topic']).strip(), 'difficulty': str(payload['difficulty']).strip(),
        'template_code': str(payload.get('template_code', '')),
        'test_cases': [{'input': str(t.get('input', '')), 'expected_output': str(t.get('expected_output', '')), 'is_public': bool(t.get('is_public', False))} for t in tcs],
    }
    if 'is_published' in payload:
        data['is_published'] = bool(payload.get('is_published'))
    return data


@admin_bp.route('/api/problems', methods=['GET'])
@admin_required
def admin_list_problems():
    from sqlalchemy.orm import joinedload
    problems = Problem.query.options(joinedload(Problem.test_cases)).order_by(Problem.id).all()
    return jsonify({'items': [_prob_json(p) for p in problems]})


@admin_bp.route('/api/problems/topics', methods=['GET'])
@admin_required
def admin_list_problem_topics():
    rows = (
        db.session.query(Problem.topic)
        .filter(Problem.topic.isnot(None))
        .distinct()
        .order_by(Problem.topic.asc())
        .all()
    )
    items = [str(row[0]).strip() for row in rows if str(row[0]).strip()]
    return jsonify({'items': items})


@admin_bp.route('/api/problems/<int:pid>', methods=['GET'])
@admin_required
def admin_get_problem(pid):
    p = db.session.get(Problem, pid)
    return jsonify(_prob_json(p)) if p else (jsonify({'error': 'Not found'}), 404)


@admin_bp.route('/api/problems', methods=['POST'])
@admin_required
def admin_create_problem():
    try:
        data = _normalize_prob(request.get_json(force=True))
        p = Problem(title=data['title'], description=data['description'], topic=data['topic'],
                    difficulty=data['difficulty'], template_code=data['template_code'],
                    is_published=bool(data.get('is_published', False)))
        db.session.add(p)
        db.session.flush()
        for tc in data['test_cases']:
            db.session.add(TestCase(problem_id=p.id, input_data=tc['input'], expected_output=tc['expected_output'], is_public=tc['is_public']))
        db.session.commit()
        return jsonify(_prob_json(p)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/problems/<int:pid>', methods=['PUT'])
@admin_required
def admin_update_problem(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    try:
        data = _normalize_prob(request.get_json(force=True))
        p.title = data['title']; p.description = data['description']
        p.topic = data['topic']; p.difficulty = data['difficulty']
        p.template_code = data['template_code']
        if 'is_published' in data:
            p.is_published = bool(data.get('is_published'))
        TestCase.query.filter_by(problem_id=p.id).delete()
        db.session.flush()
        for tc in data['test_cases']:
            db.session.add(TestCase(problem_id=p.id, input_data=tc['input'], expected_output=tc['expected_output'], is_public=tc['is_public']))
        db.session.commit()
        return jsonify(_prob_json(p))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/problems/<int:pid>', methods=['DELETE'])
@admin_required
def admin_delete_problem(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    ChallengeSubmission.query.filter_by(problem_id=p.id).delete()
    db.session.delete(p); db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/api/problems/<int:pid>/publish', methods=['POST'])
@admin_required
def admin_publish_problem(pid):
    p = db.session.get(Problem, pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True) or {}
    if 'is_published' not in data:
        return jsonify({'error': 'is_published required'}), 400
    p.is_published = bool(data.get('is_published'))
    db.session.commit()
    return jsonify(_prob_json(p))


@admin_bp.route('/api/problems/import_json', methods=['POST'])
@admin_required
def admin_import_problems_json():
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No files uploaded'}), 400

    required = ['title', 'topic', 'difficulty', 'description', 'template_code', 'test_cases']
    inserted = 0
    errors = []

    for f in files:
        try:
            payload = json.load(f)
            missing = [k for k in required if k not in payload]
            if missing:
                raise ValueError(f"Missing fields: {', '.join(missing)}")
            if not isinstance(payload.get('test_cases'), list):
                raise ValueError("'test_cases' must be a list")
            if not str(payload.get('title', '')).strip():
                raise ValueError("'title' is required")
            if not str(payload.get('topic', '')).strip():
                raise ValueError("'topic' is required")
            if not str(payload.get('difficulty', '')).strip():
                raise ValueError("'difficulty' is required")
            if not str(payload.get('description', '')).strip():
                raise ValueError("'description' is required")

            p = Problem(
                title=str(payload['title']).strip(),
                description=str(payload['description']),
                topic=str(payload['topic']).strip(),
                difficulty=str(payload['difficulty']).strip(),
                template_code=str(payload.get('template_code', '')),
                is_published=False,
            )
            db.session.add(p)
            db.session.flush()

            for tc in payload['test_cases']:
                db.session.add(TestCase(
                    problem_id=p.id,
                    input_data=str(tc.get('input', '')),
                    expected_output=str(tc.get('expected_output', '')),
                    is_public=bool(tc.get('is_public', False)),
                ))

            db.session.commit()
            inserted += 1
        except IntegrityError:
            db.session.rollback()
            errors.append({'file': getattr(f, 'filename', 'unknown'), 'error': 'Title already exists'})
        except Exception as e:
            db.session.rollback()
            errors.append({'file': getattr(f, 'filename', 'unknown'), 'error': str(e)})

    return jsonify({'inserted': inserted, 'errors': errors})


# ── Chapters CRUD ─────────────────────────────────────────────────────────────
@admin_bp.route('/api/chapters', methods=['GET'])
@admin_required
def admin_list_chapters():
    return jsonify({'items': [
        {'id': c.id, 'identifier': c.identifier, 'title': c.title,
         'question_count': Question.query.filter_by(chapter_id=c.id).count()}
        for c in Chapter.query.order_by(Chapter.id).all()
    ]})


@admin_bp.route('/api/chapters', methods=['POST'])
@admin_required
def admin_create_chapter():
    data = request.get_json(force=True) or {}
    title = str(data.get('title', '')).strip()
    identifier = str(data.get('identifier', '')).strip()
    if not title or not identifier:
        return jsonify({'error': 'title and identifier required'}), 400
    c = Chapter(title=title, identifier=identifier)
    db.session.add(c)
    try:
        db.session.commit()
        return jsonify({'id': c.id, 'title': c.title, 'identifier': c.identifier}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/chapters/<int:cid>', methods=['PUT'])
@admin_required
def admin_update_chapter(cid):
    c = db.session.get(Chapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True) or {}
    c.title = str(data.get('title', c.title)).strip() or c.title
    c.identifier = str(data.get('identifier', c.identifier)).strip() or c.identifier
    try:
        db.session.commit(); return jsonify({'ok': True})
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/chapters/<int:cid>', methods=['DELETE'])
@admin_required
def admin_delete_chapter(cid):
    c = db.session.get(Chapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    q_ids = [q.id for q in Question.query.filter_by(chapter_id=c.id).all()]
    if q_ids:
        Choice.query.filter(Choice.question_id.in_(q_ids)).delete(synchronize_session=False)
        Question.query.filter_by(chapter_id=c.id).delete(synchronize_session=False)
    UserProgress.query.filter_by(chapter_id=c.id).delete(synchronize_session=False)
    db.session.delete(c); db.session.commit()
    return jsonify({'ok': True})


# ── Questions CRUD ────────────────────────────────────────────────────────────
def _q_json(q):
    return {
        'id': q.id, 'chapter_id': q.chapter_id, 'type': q.type,
        'difficulty': q.difficulty, 'concept': q.concept,
        'text': q.text, 'explanation': q.explanation,
        'choices': [{'id': c.id, 'text': c.text, 'is_correct': bool(c.is_correct)} for c in sorted(q.choices, key=lambda x: x.id)],
    }


def _normalize_q(payload):
    for f in ['type', 'difficulty', 'concept', 'text', 'explanation']:
        if not str(payload.get(f, '')).strip():
            raise ValueError(f"'{f}' is required")
    try:
        chapter_id = int(payload['chapter_id'])
    except Exception:
        raise ValueError("'chapter_id' must be an integer")
    choices = payload.get('choices', [])
    if not isinstance(choices, list) or len(choices) < 2:
        raise ValueError("Need at least 2 choices")
    normalized = [{'text': str(c.get('text', '')).strip(), 'is_correct': bool(c.get('is_correct', False))} for c in choices]
    if not any(c['is_correct'] for c in normalized):
        raise ValueError("At least one choice must be correct")
    return {'chapter_id': chapter_id, 'type': str(payload.get('type', 'MCQ')).strip(),
            'difficulty': str(payload.get('difficulty', 'Medium')).strip(),
            'concept': str(payload['concept']).strip(), 'text': str(payload['text']),
            'explanation': str(payload['explanation']), 'choices': normalized}


@admin_bp.route('/api/questions', methods=['GET'])
@admin_required
def admin_list_questions():
    chapter_id = request.args.get('chapter_id', type=int)
    query = Question.query
    if chapter_id:
        query = query.filter_by(chapter_id=chapter_id)
    return jsonify({'items': [_q_json(q) for q in query.order_by(Question.id).all()]})


@admin_bp.route('/api/questions/<int:qid>', methods=['GET'])
@admin_required
def admin_get_question(qid):
    q = db.session.get(Question, qid)
    return jsonify(_q_json(q)) if q else (jsonify({'error': 'Not found'}), 404)


@admin_bp.route('/api/questions', methods=['POST'])
@admin_required
def admin_create_question():
    try:
        data = _normalize_q(request.get_json(force=True))
        q = Question(chapter_id=data['chapter_id'], type=data['type'], difficulty=data['difficulty'],
                     concept=data['concept'], text=data['text'], explanation=data['explanation'])
        db.session.add(q); db.session.flush()
        for c in data['choices']:
            db.session.add(Choice(question_id=q.id, text=c['text'], is_correct=c['is_correct']))
        db.session.commit()
        return jsonify(_q_json(q)), 201
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/questions/<int:qid>', methods=['PUT'])
@admin_required
def admin_update_question(qid):
    q = db.session.get(Question, qid)
    if not q:
        return jsonify({'error': 'Not found'}), 404
    try:
        data = _normalize_q(request.get_json(force=True))
        q.chapter_id = data['chapter_id']; q.type = data['type']
        q.difficulty = data['difficulty']; q.concept = data['concept']
        q.text = data['text']; q.explanation = data['explanation']
        Choice.query.filter_by(question_id=q.id).delete(); db.session.flush()
        for c in data['choices']:
            db.session.add(Choice(question_id=q.id, text=c['text'], is_correct=c['is_correct']))
        db.session.commit()
        return jsonify(_q_json(q))
    except Exception as e:
        db.session.rollback(); return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/questions/<int:qid>', methods=['DELETE'])
@admin_required
def admin_delete_question(qid):
    q = db.session.get(Question, qid)
    if not q:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(q); db.session.commit()
    return jsonify({'ok': True})


def _parse_choice_indices(raw_value):
    if raw_value is None:
        return []
    parts = str(raw_value).replace(',', '|').split('|')
    result = []
    for part in parts:
        item = part.strip()
        if not item:
            continue
        try:
            idx = int(item)
        except Exception:
            continue
        if idx > 0:
            result.append(idx)
    return result


@admin_bp.route('/api/questions/export_csv', methods=['GET'])
@admin_required
def admin_export_questions_csv():
    chapter_id = request.args.get('chapter_id', type=int)
    if not chapter_id:
        return jsonify({'error': 'chapter_id is required'}), 400

    chapter = db.session.get(Chapter, chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    questions = Question.query.filter_by(chapter_id=chapter_id).order_by(Question.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['chapter_id', 'concept', 'type', 'difficulty', 'text', 'explanation', 'choices', 'correct_indices'])

    for q in questions:
        sorted_choices = sorted(q.choices, key=lambda c: c.id)
        choices = [c.text for c in sorted_choices]
        correct_indices = [str(i + 1) for i, c in enumerate(sorted_choices) if c.is_correct]
        writer.writerow([
            q.chapter_id,
            q.concept,
            q.type,
            q.difficulty,
            q.text,
            q.explanation,
            '||'.join(choices),
            '|'.join(correct_indices),
        ])

    csv_bytes = output.getvalue()
    output.close()

    filename = f"chapter_{chapter_id}_questions.csv"
    return Response(
        csv_bytes,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename=\"{filename}\"'}
    )


@admin_bp.route('/api/questions/export_json', methods=['GET'])
@admin_required
def admin_export_questions_json():
    chapter_id = request.args.get('chapter_id', type=int)
    if not chapter_id:
        return jsonify({'error': 'chapter_id is required'}), 400

    chapter = db.session.get(Chapter, chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    questions = Question.query.filter_by(chapter_id=chapter_id).order_by(Question.id.asc()).all()
    payload = {
        'chapter_id': chapter_id,
        'chapter_title': chapter.title,
        'questions': [_q_json(q) for q in questions],
    }
    filename = f"chapter_{chapter_id}_questions.json"
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename=\"{filename}\"'}
    )


@admin_bp.route('/api/questions/import_csv', methods=['POST'])
@admin_required
def admin_import_questions_csv():
    try:
        chapter_id = int(request.form.get('chapter_id', '0'))
    except Exception:
        return jsonify({'error': 'chapter_id is required'}), 400

    chapter = db.session.get(Chapter, chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'CSV file is required'}), 400

    replace_existing = str(request.form.get('replace', 'false')).lower() in ('1', 'true', 'yes', 'on')

    try:
        raw = uploaded.read().decode('utf-8-sig')
    except Exception:
        return jsonify({'error': 'Unable to read CSV file (utf-8 expected)'}), 400

    try:
        reader = csv.DictReader(io.StringIO(raw))
        required = {'concept', 'type', 'difficulty', 'text', 'explanation', 'choices', 'correct_indices'}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            return jsonify({'error': 'Invalid CSV columns. Required: concept,type,difficulty,text,explanation,choices,correct_indices'}), 400

        rows = list(reader)
        if not rows:
            return jsonify({'error': 'CSV is empty'}), 400

        if replace_existing:
            q_ids = [q.id for q in Question.query.filter_by(chapter_id=chapter_id).all()]
            if q_ids:
                Choice.query.filter(Choice.question_id.in_(q_ids)).delete(synchronize_session=False)
                Question.query.filter_by(chapter_id=chapter_id).delete(synchronize_session=False)
                db.session.flush()

        inserted = 0
        for i, row in enumerate(rows, start=2):
            concept = str(row.get('concept', '')).strip()
            q_type = str(row.get('type', 'MCQ')).strip() or 'MCQ'
            difficulty = str(row.get('difficulty', 'Medium')).strip() or 'Medium'
            text = str(row.get('text', ''))
            explanation = str(row.get('explanation', ''))
            raw_choices = str(row.get('choices', ''))
            choices = [c.strip() for c in raw_choices.split('||') if c.strip()]
            correct_indices = _parse_choice_indices(row.get('correct_indices', ''))

            if not concept or not text.strip() or not explanation.strip():
                raise ValueError(f'Line {i}: concept, text and explanation are required')
            if len(choices) < 2:
                raise ValueError(f'Line {i}: at least 2 choices are required (separate with ||)')
            if not correct_indices:
                raise ValueError(f'Line {i}: correct_indices is required (example: 1 or 1|3)')
            if any(idx < 1 or idx > len(choices) for idx in correct_indices):
                raise ValueError(f'Line {i}: correct_indices out of range')

            q = Question(
                chapter_id=chapter_id,
                type=q_type,
                difficulty=difficulty,
                concept=concept,
                text=text,
                explanation=explanation
            )
            db.session.add(q)
            db.session.flush()

            correct_set = set(correct_indices)
            for idx, choice_text in enumerate(choices, start=1):
                db.session.add(Choice(
                    question_id=q.id,
                    text=choice_text,
                    is_correct=(idx in correct_set)
                ))
            inserted += 1

        db.session.commit()
        return jsonify({'ok': True, 'inserted': inserted, 'chapter_id': chapter_id, 'replace': replace_existing})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/questions/import_json', methods=['POST'])
@admin_required
def admin_import_questions_json():
    try:
        chapter_id = int(request.form.get('chapter_id', '0'))
    except Exception:
        return jsonify({'error': 'chapter_id is required'}), 400

    chapter = db.session.get(Chapter, chapter_id)
    if not chapter:
        return jsonify({'error': 'Chapter not found'}), 404

    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'JSON file is required'}), 400

    replace_existing = str(request.form.get('replace', 'false')).lower() in ('1', 'true', 'yes', 'on')

    try:
        payload = json.load(uploaded)
    except Exception:
        return jsonify({'error': 'Invalid JSON file'}), 400

    questions = payload.get('questions') if isinstance(payload, dict) else payload
    if not isinstance(questions, list):
        return jsonify({'error': 'JSON must be an array of questions or {questions: [...]}'}), 400

    try:
        if replace_existing:
            q_ids = [q.id for q in Question.query.filter_by(chapter_id=chapter_id).all()]
            if q_ids:
                Choice.query.filter(Choice.question_id.in_(q_ids)).delete(synchronize_session=False)
                Question.query.filter_by(chapter_id=chapter_id).delete(synchronize_session=False)
                db.session.flush()

        inserted = 0
        for q in questions:
            q_payload = {
                'chapter_id': chapter_id,
                'type': q.get('type', 'MCQ'),
                'difficulty': q.get('difficulty', 'Medium'),
                'concept': q.get('concept', ''),
                'text': q.get('text', ''),
                'explanation': q.get('explanation', ''),
                'choices': q.get('choices', []),
            }
            data = _normalize_q(q_payload)
            nq = Question(chapter_id=data['chapter_id'], type=data['type'], difficulty=data['difficulty'],
                          concept=data['concept'], text=data['text'], explanation=data['explanation'])
            db.session.add(nq); db.session.flush()
            for c in data['choices']:
                db.session.add(Choice(question_id=nq.id, text=c['text'], is_correct=c['is_correct']))
            inserted += 1

        db.session.commit()
        return jsonify({'inserted': inserted})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ── Course Chapters / Sections ───────────────────────────────────────────────
def _course_chapter_json(c):
    return {
        'id': c.id,
        'identifier': c.identifier,
        'title': c.title,
        'icon': c.icon,
        'order_index': c.order_index,
        'is_published': bool(c.is_published),
    }


def _course_section_json(s):
    return {
        'id': s.id,
        'chapter_id': s.chapter_id,
        'title': s.title,
        'content': s.content,
        'code': s.code,
        'order_index': s.order_index,
    }


@admin_bp.route('/api/course/chapters', methods=['GET'])
@admin_required
def admin_list_course_chapters():
    chapters = CourseChapter.query.order_by(CourseChapter.order_index.asc(), CourseChapter.id.asc()).all()
    return jsonify({'items': [_course_chapter_json(c) for c in chapters]})


@admin_bp.route('/api/course/chapters', methods=['POST'])
@admin_required
def admin_create_course_chapter():
    data = request.get_json(force=True) or {}
    identifier = str(data.get('identifier', '')).strip()
    title = str(data.get('title', '')).strip()
    if not identifier or not title:
        return jsonify({'error': 'identifier and title required'}), 400
    icon = str(data.get('icon', '')).strip() or 'fas fa-book'
    order_index = int(data.get('order_index', 0) or 0)
    is_published = bool(data.get('is_published', True))
    c = CourseChapter(identifier=identifier, title=title, icon=icon, order_index=order_index, is_published=is_published)
    db.session.add(c)
    try:
        db.session.commit()
        return jsonify(_course_chapter_json(c)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/course/chapters/<int:cid>', methods=['PUT'])
@admin_required
def admin_update_course_chapter(cid):
    c = db.session.get(CourseChapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True) or {}
    if 'identifier' in data:
        ident = str(data.get('identifier', '')).strip()
        if not ident:
            return jsonify({'error': 'identifier required'}), 400
        c.identifier = ident
    if 'title' in data:
        title = str(data.get('title', '')).strip()
        if not title:
            return jsonify({'error': 'title required'}), 400
        c.title = title
    if 'icon' in data:
        c.icon = str(data.get('icon', '')).strip() or 'fas fa-book'
    if 'order_index' in data:
        c.order_index = int(data.get('order_index', 0) or 0)
    if 'is_published' in data:
        c.is_published = bool(data.get('is_published'))
    try:
        db.session.commit()
        return jsonify(_course_chapter_json(c))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/course/chapters/<int:cid>', methods=['DELETE'])
@admin_required
def admin_delete_course_chapter(cid):
    c = db.session.get(CourseChapter, cid)
    if not c:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/api/course/chapters/<int:cid>/sections', methods=['GET'])
@admin_required
def admin_list_course_sections(cid):
    c = db.session.get(CourseChapter, cid)
    if not c:
        return jsonify({'error': 'Chapter not found'}), 404
    sections = CourseSection.query.filter_by(chapter_id=cid).order_by(CourseSection.order_index.asc(), CourseSection.id.asc()).all()
    return jsonify({'items': [_course_section_json(s) for s in sections]})


@admin_bp.route('/api/course/chapters/<int:cid>/sections', methods=['POST'])
@admin_required
def admin_create_course_section(cid):
    c = db.session.get(CourseChapter, cid)
    if not c:
        return jsonify({'error': 'Chapter not found'}), 404
    data = request.get_json(force=True) or {}
    title = str(data.get('title', '')).strip() or None
    content = str(data.get('content', '') or '')
    code = str(data.get('code', '') or '')
    order_index = int(data.get('order_index', 0) or 0)
    s = CourseSection(chapter_id=cid, title=title, content=content, code=code, order_index=order_index)
    db.session.add(s)
    db.session.commit()
    return jsonify(_course_section_json(s)), 201


@admin_bp.route('/api/course/sections/<int:sid>', methods=['PUT'])
@admin_required
def admin_update_course_section(sid):
    s = db.session.get(CourseSection, sid)
    if not s:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(force=True) or {}
    if 'title' in data:
        s.title = str(data.get('title', '')).strip() or None
    if 'content' in data:
        s.content = str(data.get('content', '') or '')
    if 'code' in data:
        s.code = str(data.get('code', '') or '')
    if 'order_index' in data:
        s.order_index = int(data.get('order_index', 0) or 0)
    db.session.commit()
    return jsonify(_course_section_json(s))


@admin_bp.route('/api/course/sections/<int:sid>', methods=['DELETE'])
@admin_required
def admin_delete_course_section(sid):
    s = db.session.get(CourseSection, sid)
    if not s:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})


@admin_bp.route('/api/course/export_json', methods=['GET'])
@admin_required
def admin_export_course_json():
    chapters = CourseChapter.query.order_by(CourseChapter.order_index.asc(), CourseChapter.id.asc()).all()
    payload = {
        'chapters': [
            {
                'id': c.identifier,
                'title': c.title,
                'icon': c.icon,
                'order_index': c.order_index,
                'is_published': bool(c.is_published),
                'sections': [
                    {
                        'title': s.title,
                        'content': s.content,
                        'code': s.code,
                        'order_index': s.order_index
                    }
                    for s in CourseSection.query.filter_by(chapter_id=c.id).order_by(CourseSection.order_index.asc(), CourseSection.id.asc()).all()
                ]
            }
            for c in chapters
        ]
    }
    return Response(
        json.dumps(payload, ensure_ascii=False, indent=2),
        mimetype='application/json; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="course_full.json"'}
    )


@admin_bp.route('/api/course/import_json', methods=['POST'])
@admin_required
def admin_import_course_json():
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'JSON file is required'}), 400
    try:
        payload = json.load(uploaded)
    except Exception:
        return jsonify({'error': 'Invalid JSON file'}), 400

    chapters = payload.get('chapters') if isinstance(payload, dict) else None
    if not isinstance(chapters, list):
        return jsonify({'error': 'JSON must be {chapters: [...]}'}), 400

    try:
        CourseSection.query.delete()
        CourseChapter.query.delete()
        db.session.flush()

        for idx, ch in enumerate(chapters, start=1):
            identifier = str(ch.get('id', '')).strip()
            title = str(ch.get('title', '')).strip()
            if not identifier or not title:
                raise ValueError('chapter id/title required')
            icon = str(ch.get('icon', '')).strip() or 'fas fa-book'
            order_index = int(ch.get('order_index', idx) or idx)
            is_published = bool(ch.get('is_published', True))
            c = CourseChapter(identifier=identifier, title=title, icon=icon, order_index=order_index, is_published=is_published)
            db.session.add(c)
            db.session.flush()

            sections = ch.get('sections', [])
            if sections and not isinstance(sections, list):
                raise ValueError('sections must be a list')
            for sidx, s in enumerate(sections or [], start=1):
                db.session.add(CourseSection(
                    chapter_id=c.id,
                    title=str(s.get('title', '')).strip() or None,
                    content=str(s.get('content', '') or ''),
                    code=str(s.get('code', '') or ''),
                    order_index=int(s.get('order_index', sidx) or sidx)
                ))

        db.session.commit()
        return jsonify({'ok': True, 'chapters': len(chapters)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/api/course/chapters/import_json', methods=['POST'])
@admin_required
def admin_import_course_chapter_json():
    uploaded = request.files.get('file')
    if not uploaded:
        return jsonify({'error': 'JSON file is required'}), 400
    try:
        payload = json.load(uploaded)
    except Exception:
        return jsonify({'error': 'Invalid JSON file'}), 400

    chapter_payload = payload.get('chapter') if isinstance(payload, dict) and 'chapter' in payload else payload
    if not isinstance(chapter_payload, dict):
        return jsonify({'error': 'JSON must be a single chapter object'}), 400

    identifier = str(chapter_payload.get('id') or chapter_payload.get('identifier') or '').strip()
    title = str(chapter_payload.get('title') or '').strip()
    if not identifier or not title:
        return jsonify({'error': 'chapter id/title required'}), 400
    icon = str(chapter_payload.get('icon', '')).strip() or 'fas fa-book'
    is_published = bool(chapter_payload.get('is_published', True))
    order_index_raw = chapter_payload.get('order_index', None)

    sections = chapter_payload.get('sections', [])
    if sections and not isinstance(sections, list):
        return jsonify({'error': 'sections must be a list'}), 400

    try:
        existing = CourseChapter.query.filter_by(identifier=identifier).first()
        created = False
        if existing:
            existing.title = title
            existing.icon = icon
            existing.is_published = is_published
            if order_index_raw is not None:
                existing.order_index = int(order_index_raw or 0)
            CourseSection.query.filter_by(chapter_id=existing.id).delete()
            chapter = existing
        else:
            if order_index_raw is None:
                max_order = db.session.query(func.max(CourseChapter.order_index)).scalar() or 0
                order_index = max_order + 1
            else:
                order_index = int(order_index_raw or 0)
            chapter = CourseChapter(
                identifier=identifier,
                title=title,
                icon=icon,
                order_index=order_index,
                is_published=is_published
            )
            db.session.add(chapter)
            db.session.flush()
            created = True

        for sidx, s in enumerate(sections or [], start=1):
            db.session.add(CourseSection(
                chapter_id=chapter.id,
                title=str(s.get('title', '')).strip() or None,
                content=str(s.get('content', '') or ''),
                code=str(s.get('code', '') or ''),
                order_index=int(s.get('order_index', sidx) or sidx)
            ))

        db.session.commit()
        return jsonify({'ok': True, 'created': created, 'chapter_id': chapter.id, 'sections': len(sections or [])})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

