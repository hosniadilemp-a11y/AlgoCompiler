import sys
import os
sys.path.append(os.path.abspath("src"))

from web.app import app
from web.models import db
from sqlalchemy import text

print(">>> Checking User model and DB connectivity...")

with app.app_context():
    try:
        # Test 1: Raw SQL select stars (to see if existing columns are fine)
        print(">>> Test 1: Raw SQL SELECT * FROM users LIMIT 1")
        res = db.session.execute(text("SELECT * FROM users LIMIT 1")).fetchone()
        print(f"Result: {res}")
        
        # Test 2: SQLAlchemy query (to see if mapping is fine)
        from web.models import User
        print(">>> Test 2: User.query.first()")
        user = User.query.first()
        print(f"User found: {user.name if user else 'None'}")
        
    except Exception as e:
        print(f">>> ERROR: {e}")
        import traceback
        traceback.print_exc()
