import json
import os
import glob
import psycopg

DB_URL = 'postgresql://postgres.yrzorrfeddgmkowvgdaa:bdur6fScarWhn6KI@aws-1-eu-west-1.pooler.supabase.com:5432/postgres'
QUIZZES_DIR = os.path.join(os.path.dirname(__file__), 'quizzes')


def ultra_fast_sync():
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

    # 1. Collect all questions
    question_payloads = []

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

            choices = q.get('choices', [])
            answer = q.get('answer')

            question_payloads.append({
                'chapter_id': chapter_id,
                'text': q_text,
                'type': q_type,
                'explanation': explanation,
                'concept': concept,
                'difficulty': difficulty,
                'raw_choices': choices,
                'answer': answer
            })

    print(f">>> Inserting {len(question_payloads)} questions into Supabase...")

    # Insert questions & retrieve IDs
    choice_rows = []
    for q_data in question_payloads:
        cur.execute("""
            INSERT INTO question (chapter_id, text, type, explanation, concept, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
        """, (q_data['chapter_id'], q_data['text'], q_data['type'], q_data['explanation'], q_data['concept'], q_data['difficulty']))
        
        q_id = cur.fetchone()[0]

        for c in q_data['raw_choices']:
            if isinstance(c, dict):
                c_text = str(c.get('text', '')).strip()
                is_correct = bool(c.get('is_correct', False))
            else:
                c_text = str(c).strip()
                is_correct = (c_text == str(q_data['answer']).strip())
            choice_rows.append((q_id, c_text, is_correct))

    print(f">>> Inserting {len(choice_rows)} choices in bulk...")
    
    # Bulk insert all 1480+ choices in batches of 500
    batch_size = 500
    for i in range(0, len(choice_rows), batch_size):
        batch = choice_rows[i:i + batch_size]
        cur.executemany("INSERT INTO choice (question_id, text, is_correct) VALUES (%s, %s, %s);", batch)
        conn.commit()
        print(f" -> Committed choices batch {i // batch_size + 1}/{len(choice_rows) // batch_size + 1}")

    conn.commit()
    conn.close()

    print(f"\n✅ ULTRA FAST SYNC COMPLETE:")
    print(f" - Questions: {len(question_payloads)}")
    print(f" - Choices  : {len(choice_rows)}")


if __name__ == '__main__':
    ultra_fast_sync()
