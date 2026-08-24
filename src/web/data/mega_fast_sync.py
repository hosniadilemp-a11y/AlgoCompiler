import json
import os
import glob
import psycopg

DB_URL = 'postgresql://postgres.yrzorrfeddgmkowvgdaa:bdur6fScarWhn6KI@aws-1-eu-west-1.pooler.supabase.com:5432/postgres'
QUIZZES_DIR = os.path.join(os.path.dirname(__file__), 'quizzes')


def mega_fast_sync():
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    print(">>> Connecting to Supabase PostgreSQL...")
    cur.execute("SELECT id, identifier FROM chapter;")
    db_chapters = {row[1]: row[0] for row in cur.fetchall()}

    json_files = sorted(glob.glob(os.path.join(QUIZZES_DIR, '*.json')))

    file_to_identifier = {
        'actions.json': 'actions',
        'allocation.json': 'allocation',
        'chaines.json': 'chaines',
        'enregistrements.json': 'enregistrements',
        'fichiers.json': 'fichiers',
        'files.json': 'files',
        'intro.json': 'intro',
        'listes_chainees.json': 'listes_chainees',
        'piles.json': 'piles',
        'tableaux.json': 'tableaux'
    }

    chapter_ids = list(db_chapters.values())
    if chapter_ids:
        cur.execute("DELETE FROM choice WHERE question_id IN (SELECT id FROM question WHERE chapter_id = ANY(%s));", (chapter_ids,))
        cur.execute("DELETE FROM question WHERE chapter_id = ANY(%s);", (chapter_ids,))
        conn.commit()
        print(">>> Cleared existing questions and choices.")

    # Get max IDs to avoid sequence conflicts
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM question;")
    start_q_id = cur.fetchone()[0] + 1

    cur.execute("SELECT COALESCE(MAX(id), 0) FROM choice;")
    start_c_id = cur.fetchone()[0] + 1

    q_tuples = []
    c_tuples = []

    curr_q_id = start_q_id
    curr_c_id = start_c_id

    for json_path in json_files:
        basename = os.path.basename(json_path)
        identifier = file_to_identifier.get(basename)
        if not identifier or identifier not in db_chapters:
            continue

        chapter_id = db_chapters[identifier]

        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        questions = data if isinstance(data, list) else data.get('questions', [])

        for q in questions:
            q_text = (q.get('question') or q.get('text') or '').strip()
            explanation = (q.get('explanation') or 'Explication fournie.').strip()
            concept = (q.get('concept') or 'Général').strip()
            difficulty = (q.get('difficulty') or 'Medium').strip()
            q_type = (q.get('type') or 'MCQ').strip()

            q_tuples.append((curr_q_id, chapter_id, q_text, q_type, explanation, concept, difficulty))

            choices = q.get('choices', [])
            answer = q.get('answer')

            for c in choices:
                if isinstance(c, dict):
                    c_text = str(c.get('text', '')).strip()
                    is_correct = bool(c.get('is_correct', False))
                else:
                    c_text = str(c).strip()
                    is_correct = (c_text == str(answer).strip())

                c_tuples.append((curr_c_id, curr_q_id, c_text, is_correct))
                curr_c_id += 1

            curr_q_id += 1

    print(f">>> Executing batch insert of {len(q_tuples)} questions...")
    cur.executemany("""
        INSERT INTO question (id, chapter_id, text, type, explanation, concept, difficulty)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, q_tuples)

    print(f">>> Executing batch insert of {len(c_tuples)} choices...")
    cur.executemany("""
        INSERT INTO choice (id, question_id, text, is_correct)
        VALUES (%s, %s, %s, %s);
    """, c_tuples)

    # Sync sequence counters
    cur.execute("SELECT setval(pg_get_serial_sequence('question', 'id'), COALESCE(MAX(id), 1)) FROM question;")
    cur.execute("SELECT setval(pg_get_serial_sequence('choice', 'id'), COALESCE(MAX(id), 1)) FROM choice;")

    conn.commit()
    conn.close()

    print(f"\n✅ MEGA FAST SYNC COMPLETED SUCCESSFULLY:")
    print(f" - Questions Inserted: {len(q_tuples)}")
    print(f" - Choices Inserted  : {len(c_tuples)}")


if __name__ == '__main__':
    mega_fast_sync()
