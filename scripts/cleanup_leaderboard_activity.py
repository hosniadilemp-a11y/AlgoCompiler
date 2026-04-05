import argparse
import json
import os
import sys


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from web.app import (  # noqa: E402
    app,
    invalidate_global_user_stats_cache,
    invalidate_user_level_cache,
    invalidate_user_progress_cache,
)
from web.models import (  # noqa: E402
    db,
    ChallengeAttemptSession,
    ChallengeSubmission,
    QuizAttempt,
    UserBadge,
)


DEFAULT_USER_IDS = [3, 4, 5]


def count_activity_rows(user_ids):
    return {
        'quiz_attempts': QuizAttempt.query.filter(QuizAttempt.user_id.in_(user_ids)).count(),
        'challenge_submissions': ChallengeSubmission.query.filter(
            ChallengeSubmission.user_id.in_(user_ids)
        ).count(),
        'challenge_attempt_sessions': ChallengeAttemptSession.query.filter(
            ChallengeAttemptSession.user_id.in_(user_ids)
        ).count(),
        'user_badges': UserBadge.query.filter(UserBadge.user_id.in_(user_ids)).count(),
    }


def delete_activity_rows(user_ids):
    deleted = {}
    deleted['challenge_submissions'] = ChallengeSubmission.query.filter(
        ChallengeSubmission.user_id.in_(user_ids)
    ).delete(synchronize_session=False)
    deleted['challenge_attempt_sessions'] = ChallengeAttemptSession.query.filter(
        ChallengeAttemptSession.user_id.in_(user_ids)
    ).delete(synchronize_session=False)
    deleted['quiz_attempts'] = QuizAttempt.query.filter(
        QuizAttempt.user_id.in_(user_ids)
    ).delete(synchronize_session=False)
    deleted['user_badges'] = UserBadge.query.filter(
        UserBadge.user_id.in_(user_ids)
    ).delete(synchronize_session=False)
    return deleted


def parse_args():
    parser = argparse.ArgumentParser(
        description='Delete leaderboard-related activity for specific user IDs.'
    )
    parser.add_argument(
        '--user-id',
        dest='user_ids',
        action='append',
        type=int,
        help='Target user ID. Can be provided multiple times.',
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Only show counts without deleting rows.',
    )
    return parser.parse_args()


def main():
    args = parse_args()
    user_ids = sorted(set(args.user_ids or DEFAULT_USER_IDS))

    with app.app_context():
        before_counts = count_activity_rows(user_ids)
        print(json.dumps({
            'user_ids': user_ids,
            'before_counts': before_counts,
            'dry_run': args.dry_run,
        }, indent=2))

        if args.dry_run:
            return 0

        try:
            deleted_counts = delete_activity_rows(user_ids)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        invalidate_global_user_stats_cache()
        for user_id in user_ids:
            invalidate_user_level_cache(user_id)
            invalidate_user_progress_cache(user_id)

        after_counts = count_activity_rows(user_ids)
        print(json.dumps({
            'user_ids': user_ids,
            'deleted_counts': deleted_counts,
            'after_counts': after_counts,
        }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
