"""
Q&A Blueprint — /qa
Authenticated-only StackOverflow-like module with question/answer/vote support.
"""
from datetime import datetime
from markupsafe import Markup
from flask import Blueprint, abort, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import update as sa_update

from web.models import QAAnswer, QAQuestion, QAVote, db, User


# ── Input sanitiser ───────────────────────────────────────────────────────────
import re

def _strip_html(value: str) -> str:
    """Remove all HTML/script tags and dangerous sequences from user input."""
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]+>', '', value)
    return cleaned


qa_bp = Blueprint("qa", __name__, url_prefix="/qa")

# ── CSRF guard for all state-changing requests (VULN-008) ────────────────────
@qa_bp.before_request
def _csrf_protect():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        token = request.headers.get("X-CSRFToken") or request.headers.get("X-Csrf-Token")
        session_token = session.get("_csrf_token")
        if not token or not session_token or token != session_token:
            return jsonify({"success": False, "error": "CSRF token manquant ou invalide."}), 403

# Allowed sort keys (VULN-011)
_ALLOWED_QA_SORTS = frozenset({"date", "votes"})
_MAX_BODY = 20_000   # chars
_MAX_CODE = 10_000   # chars


# ── Helpers ───────────────────────────────────────────────────────────────────

def _question_json(q, user_vote=None):
    return {
        "id":          q.id,
        "title":       q.title,
        "body":        q.body,
        "code":        q.code or "",
        "vote_score":  q.vote_score,
        "answer_count": len(q.answers),
        "author":      q.author.name,
        "created_at":  q.created_at.isoformat(),
        "user_vote":   user_vote,
    }


def _answer_json(a, user_vote=None):
    return {
        "id":         a.id,
        "body":       a.body,
        "code":       a.code or "",
        "vote_score": a.vote_score,
        "author":     a.author.name,
        "created_at": a.created_at.isoformat(),
        "user_vote":  user_vote,
    }


def _get_user_vote(target_type, target_id):
    if not current_user.is_authenticated:
        return None
    v = QAVote.query.filter_by(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id
    ).first()
    return v.value if v else None


# ── Routes ────────────────────────────────────────────────────────────────────

@qa_bp.route("/", methods=["GET"])
@login_required
def index():
    """Return the main Q&A page (SPA-like, data loaded via JS)."""
    return render_template("qa.html")


@qa_bp.route("/api/questions", methods=["GET"])
@login_required
def api_list_questions():
    """Return paginated questions as JSON. sort=date|votes"""
    sort  = request.args.get("sort", "date")
    if sort not in _ALLOWED_QA_SORTS:  # VULN-011: allowlist
        sort = "date"
    page  = request.args.get("page", 1, type=int)
    limit = min(50, max(1, request.args.get("limit", 20, type=int)))  # cap at 50

    q = QAQuestion.query
    if sort == "votes":
        q = q.order_by(QAQuestion.vote_score.desc(), QAQuestion.created_at.desc())
    else:
        q = q.order_by(QAQuestion.created_at.desc())

    pagination = q.paginate(page=page, per_page=limit, error_out=False)

    # Fetch user's own votes for displayed questions in one query
    q_ids = [item.id for item in pagination.items]
    user_votes = {}
    if q_ids:
        votes = QAVote.query.filter(
            QAVote.user_id == current_user.id,
            QAVote.target_type == "question",
            QAVote.target_id.in_(q_ids)
        ).all()
        user_votes = {v.target_id: v.value for v in votes}

    return jsonify({
        "success":    True,
        "questions":  [_question_json(item, user_votes.get(item.id)) for item in pagination.items],
        "total":      pagination.total,
        "page":       page,
        "pages":      pagination.pages,
    })


@qa_bp.route("/api/questions", methods=["POST"])
@login_required
def api_ask_question():
    """Create a new question."""
    data  = request.get_json(force=True) or {}
    title = _strip_html(str(data.get("title", "")).strip())
    body  = _strip_html(str(data.get("body",  "")).strip())
    code  = _strip_html(str(data.get("code",  "")).strip()) or None

    if not title or not body:
        return jsonify({"success": False, "error": "Titre et description requis."}), 400
    if len(title) > 255:
        return jsonify({"success": False, "error": "Titre trop long (max 255 caractères)."}), 400
    if len(body) > _MAX_BODY:
        return jsonify({"success": False, "error": f"Description trop longue (max {_MAX_BODY} caractères)."}), 400
    if code and len(code) > _MAX_CODE:
        return jsonify({"success": False, "error": f"Code trop long (max {_MAX_CODE} caractères)."}), 400

    q = QAQuestion(user_id=current_user.id, title=title, body=body, code=code)
    db.session.add(q)
    db.session.commit()
    return jsonify({"success": True, "id": q.id}), 201


@qa_bp.route("/api/questions/<int:qid>", methods=["GET"])
@login_required
def api_get_question(qid):
    """Return a single question with all its answers."""
    q = db.session.get(QAQuestion, qid)
    if not q:
        return jsonify({"success": False, "error": "Question introuvable."}), 404

    q_vote = _get_user_vote("question", qid)

    # Fetch answer votes in one query
    a_ids = [a.id for a in q.answers]
    a_votes = {}
    if a_ids:
        votes = QAVote.query.filter(
            QAVote.user_id == current_user.id,
            QAVote.target_type == "answer",
            QAVote.target_id.in_(a_ids)
        ).all()
        a_votes = {v.target_id: v.value for v in votes}

    return jsonify({
        "success":  True,
        "question": _question_json(q, q_vote),
        "answers":  [_answer_json(a, a_votes.get(a.id)) for a in q.answers],
    })


@qa_bp.route("/api/questions/<int:qid>/answers", methods=["POST"])
@login_required
def api_post_answer(qid):
    """Submit an answer to a question."""
    q = db.session.get(QAQuestion, qid)
    if not q:
        return jsonify({"success": False, "error": "Question introuvable."}), 404

    data = request.get_json(force=True) or {}
    body = _strip_html(str(data.get("body", "")).strip())
    code = _strip_html(str(data.get("code", "")).strip()) or None

    if not body:
        return jsonify({"success": False, "error": "La réponse ne peut pas être vide."}), 400

    a = QAAnswer(question_id=qid, user_id=current_user.id, body=body, code=code)
    db.session.add(a)
    db.session.commit()
    return jsonify({"success": True, "answer": _answer_json(a, None)}), 201


@qa_bp.route("/api/vote", methods=["POST"])
@login_required
def api_vote():
    """Toggle or change a +1/-1 vote on a question or answer."""
    data        = request.get_json(force=True) or {}
    target_type = str(data.get("target_type", ""))
    target_id   = int(data.get("target_id", 0))
    value       = int(data.get("value", 1))

    if target_type not in ("question", "answer") or value not in (1, -1) or target_id <= 0:
        return jsonify({"success": False, "error": "Paramètres invalides."}), 400

    # Resolve the target object with row-level lock to prevent race conditions
    if target_type == "question":
        target = db.session.get(QAQuestion, target_id, with_for_update=True)
    else:
        target = db.session.get(QAAnswer, target_id, with_for_update=True)

    if not target:
        return jsonify({"success": False, "error": "Cible introuvable."}), 404

    existing = QAVote.query.filter_by(
        user_id=current_user.id,
        target_type=target_type,
        target_id=target_id
    ).with_for_update().first()

    if existing:
        if existing.value == value:
            # Toggle off (remove vote) — atomic decrement
            if target_type == "question":
                db.session.execute(
                    sa_update(QAQuestion).where(QAQuestion.id == target_id)
                    .values(vote_score=QAQuestion.vote_score - existing.value)
                )
                db.session.refresh(target)
            else:
                db.session.execute(
                    sa_update(QAAnswer).where(QAAnswer.id == target_id)
                    .values(vote_score=QAAnswer.vote_score - existing.value)
                )
                db.session.refresh(target)
            db.session.delete(existing)
            new_vote = None
        else:
            # Change direction — atomic swap
            delta = value - existing.value
            if target_type == "question":
                db.session.execute(
                    sa_update(QAQuestion).where(QAQuestion.id == target_id)
                    .values(vote_score=QAQuestion.vote_score + delta)
                )
                db.session.refresh(target)
            else:
                db.session.execute(
                    sa_update(QAAnswer).where(QAAnswer.id == target_id)
                    .values(vote_score=QAAnswer.vote_score + delta)
                )
                db.session.refresh(target)
            existing.value = value
            new_vote = value
    else:
        # New vote — atomic increment
        vote = QAVote(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
            value=value
        )
        db.session.add(vote)
        if target_type == "question":
            db.session.execute(
                sa_update(QAQuestion).where(QAQuestion.id == target_id)
                .values(vote_score=QAQuestion.vote_score + value)
            )
            db.session.refresh(target)
        else:
            db.session.execute(
                sa_update(QAAnswer).where(QAAnswer.id == target_id)
                .values(vote_score=QAAnswer.vote_score + value)
            )
            db.session.refresh(target)
        new_vote = value

    db.session.commit()
    return jsonify({"success": True, "new_score": target.vote_score, "user_vote": new_vote})



@qa_bp.route("/api/questions/<int:qid>", methods=["DELETE"])
@login_required
def api_delete_question(qid):
    """Delete a question (owner or admin only)."""
    q = db.session.get(QAQuestion, qid)
    if not q:
        return jsonify({"success": False, "error": "Question introuvable."}), 404
    if q.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Interdit."}), 403
    db.session.delete(q)
    db.session.commit()
    return jsonify({"success": True})


@qa_bp.route("/api/answers/<int:aid>", methods=["DELETE"])
@login_required
def api_delete_answer(aid):
    """Delete an answer (owner or admin only)."""
    a = db.session.get(QAAnswer, aid)
    if not a:
        return jsonify({"success": False, "error": "Réponse introuvable."}), 404
    if a.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"success": False, "error": "Interdit."}), 403
    db.session.delete(a)
    db.session.commit()
    return jsonify({"success": True})
