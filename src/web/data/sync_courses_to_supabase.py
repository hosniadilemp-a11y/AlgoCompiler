import json
import os
from pathlib import Path
import psycopg

DB_URL = 'postgresql://postgres.yrzorrfeddgmkowvgdaa:bdur6fScarWhn6KI@aws-1-eu-west-1.pooler.supabase.com:5432/postgres'
STATIC_DIR = Path(__file__).resolve().parents[1] / 'static'
COURSE_INDEX = STATIC_DIR / 'algo-course.json'


def sync_courses():
    if not COURSE_INDEX.exists():
        print(f"Error: {COURSE_INDEX} does not exist.")
        return

    with open(COURSE_INDEX, 'r', encoding='utf-8') as f:
        course_index_data = json.load(f)

    chapters = course_index_data.get('chapters', [])
    print(f">>> Found {len(chapters)} course chapters in {COURSE_INDEX.name}")

    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    total_chapters = 0
    total_sections = 0

    for idx, ch in enumerate(chapters, start=1):
        identifier = ch.get('id')
        title = ch.get('title')
        icon = ch.get('icon') or 'fas fa-book'
        file_path_str = ch.get('file', '')

        if not identifier or not title:
            continue

        # Check or insert CourseChapter
        cur.execute("SELECT id FROM course_chapters WHERE identifier = %s;", (identifier,))
        row = cur.fetchone()

        if row:
            chapter_id = row[0]
            cur.execute("""
                UPDATE course_chapters
                SET title = %s, icon = %s, order_index = %s, is_published = true
                WHERE id = %s;
            """, (title, icon, idx, chapter_id))
        else:
            cur.execute("""
                INSERT INTO course_chapters (identifier, title, icon, order_index, is_published)
                VALUES (%s, %s, %s, %s, true) RETURNING id;
            """, (identifier, title, icon, idx))
            chapter_id = cur.fetchone()[0]

        total_chapters += 1

        # Clear existing sections for this chapter
        cur.execute("DELETE FROM course_sections WHERE chapter_id = %s;", (chapter_id,))

        # Resolve section JSON file path
        cleaned = file_path_str.lstrip('/')
        if cleaned.startswith('static/'):
            cleaned = cleaned[len('static/'):]
        json_path = STATIC_DIR / cleaned

        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                ch_data = json.load(f)

            sections = ch_data.get('sections', [])
            section_rows = []
            for s_idx, s in enumerate(sections, start=1):
                s_title = (s.get('title') or f"Section {s_idx}").strip()
                s_content = (s.get('content') or '').strip()
                s_code = s.get('code')

                section_rows.append((chapter_id, s_title, s_content, s_code, s_idx))

            if section_rows:
                cur.executemany("""
                    INSERT INTO course_sections (chapter_id, title, content, code, order_index)
                    VALUES (%s, %s, %s, %s, %s);
                """, section_rows)
                total_sections += len(section_rows)

            print(f" -> [{identifier:20s}] Updated {len(section_rows):2d} sections")

    conn.commit()
    conn.close()

    print(f"\n✅ SUCCESSFULLY SYNCED ALL COURSE CHAPTERS & SECTIONS TO SUPABASE POSTGRESQL:")
    print(f" - Course Chapters Updated: {total_chapters}")
    print(f" - Course Sections Updated: {total_sections}")


if __name__ == '__main__':
    sync_courses()
