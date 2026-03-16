import argparse
import json
import os
import sys
from pathlib import Path

from flask import Flask

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from web.models import CourseChapter, CourseSection, db

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / 'static'
COURSE_INDEX = STATIC_DIR / 'algo-course.json'


def create_app():
    app = Flask(__name__)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or f"sqlite:///{BASE_DIR / 'algocompiler.db'}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app


def load_course_files():
    if not COURSE_INDEX.exists():
        raise FileNotFoundError(f"Course index not found: {COURSE_INDEX}")
    with open(COURSE_INDEX, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('chapters', [])


def resolve_chapter_path(file_field: str) -> Path:
    if not file_field:
        return None
    cleaned = file_field.lstrip('/')
    if cleaned.startswith('static/'):
        cleaned = cleaned[len('static/'):]
    return STATIC_DIR / cleaned


def import_course(reset=True):
    chapters = load_course_files()
    app = create_app()
    with app.app_context():
        db.create_all()

        if reset:
            CourseSection.query.delete()
            CourseChapter.query.delete()
            db.session.commit()

        for idx, ch in enumerate(chapters, start=1):
            identifier = ch.get('id')
            title = ch.get('title')
            icon = ch.get('icon') or 'fas fa-book'
            if not identifier or not title:
                continue
            chapter = CourseChapter(identifier=identifier, title=title, icon=icon, order_index=idx, is_published=True)
            db.session.add(chapter)
            db.session.flush()

            chapter_path = resolve_chapter_path(ch.get('file', ''))
            if chapter_path and chapter_path.exists():
                with open(chapter_path, 'r', encoding='utf-8') as f:
                    chapter_payload = json.load(f)
                sections = chapter_payload.get('sections', [])
                for s_idx, s in enumerate(sections, start=1):
                    db.session.add(CourseSection(
                        chapter_id=chapter.id,
                        title=s.get('title'),
                        content=s.get('content'),
                        code=s.get('code'),
                        order_index=s_idx
                    ))

        db.session.commit()
        print(f"Imported {len(chapters)} course chapters")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import course content from static JSON into DB')
    parser.add_argument('--no-reset', action='store_true', help='Do not delete existing course content')
    args = parser.parse_args()
    import_course(reset=not args.no_reset)
