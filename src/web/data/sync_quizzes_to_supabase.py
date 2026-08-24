import json
import os
import glob
import psycopg

DB_URL = 'postgresql://postgres.yrzorrfeddgmkowvgdaa:bdur6fScarWhn6KI@aws-1-eu-west-1.pooler.supabase.com:5432/postgres'
QUIZZES_DIR = os.path.join(os.path.dirname(__file__), 'quizzes')


def sync_quizzes_to_supabase():
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

    total_questions = 0
    total_choices = 0

    for json_path in json_files:
        basename = os.path.basename(json_path)
        identifier = file_to_identifier.get(basename)
        if not identifier or identifier not in db_chapters:
            continue

        chapter_id = db_chapters[identifier]

        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)

        questions = data if isinstance(data, list) else data.get('questions', [])
        ch_q_count = 0

        for q in questions:
            q_text = (q.get('question') or q.get('text') or '').strip()
            explanation = (q.get('explanation') or 'Explication fournie.').strip()
            concept = (q.get('concept') or 'Général').strip()
            difficulty = (q.get('difficulty') or 'Medium').strip()
            q_type = (q.get('type') or 'MCQ').strip()

            cur.execute("""
                INSERT INTO question (chapter_id, text, type, explanation, concept, difficulty)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
            """, (chapter_id, q_text, q_type, explanation, concept, difficulty))

            question_id = cur.fetchone()[0]
            total_questions += 1
            ch_q_count += 1

            choices = q.get('choices', [])
            answer = q.get('answer')

            choice_rows = []
            for c in choices:
                if isinstance(c, dict):
                    c_text = str(c.get('text', '')).strip()
                    is_correct = bool(c.get('is_correct', False))
                else:
                    c_text = str(c).strip()
                    is_correct = (c_text == str(answer).strip())

                choice_rows.append((question_id, c_text, is_correct))

            if choice_rows:
                cur.executemany("INSERT INTO choice (question_id, text, is_correct) VALUES (%s, %s, %s);", choice_rows)
                total_choices += len(choice_rows)

        conn.commit()
        print(f" -> [{identifier}] Inserted {ch_q_count} questions")

    conn.close()

    print(f"\n✅ SUCCESSFULLY SYNCED ALL QUIZZES TO SUPABASE POSTGRESQL:")
    print(f" - Total Questions Inserted: {total_questions}")
    print(f" - Total Choices Inserted  : {total_choices}")


if __name__ == '__main__':
    sync_quizzes_to_supabase()
