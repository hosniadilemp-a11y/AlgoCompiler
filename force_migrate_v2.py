import sys
import os
import time
sys.path.append(os.path.abspath("src"))

from web.app import app
from web.models import db
from sqlalchemy import text

retry_sql = """
DO $$
DECLARE
    i int := 0;
BEGIN
    FOR i IN 1..100 LOOP
        BEGIN
            -- Try to get a lock for 2 seconds
            SET lock_timeout = '2s';
            
            -- Add the column
            ALTER TABLE users ADD COLUMN IF NOT EXISTS force_password_change BOOLEAN DEFAULT FALSE;
            
            -- Success!
            RETURN;
        EXCEPTION WHEN lock_not_available THEN
            -- Table is busy, wait 0.2s and try again
            PERFORM pg_sleep(0.2);
        END;
    END LOOP;
END;
$$;
"""

with app.app_context():
    print(">>> Connecting to Database...")
    try:
        # 1. Disable session-level timeout so we don't get canceled by Supabase
        db.session.execute(text("SET statement_timeout = 0"))
        
        print(">>> Attempting self-retrying migration (sniping a gap in traffic)...")
        db.session.execute(text(retry_sql))
        db.session.commit()
        
        # 4. Verify
        result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'force_password_change'")).fetchone()
        if result:
            print(">>> SUCCESS: force_password_change column added successfully.")
        else:
            print(">>> ERROR: Migration finished but column not found.")
            
    except Exception as e:
        db.session.rollback()
        print(f">>> CRITICAL ERROR: {e}")
