import sys
import os
sys.path.append(os.path.abspath("src"))
from web.app import app

with app.app_context():
    for rule in app.url_map.iter_rules():
        if 'leaderboard' in rule.rule:
            print(f"Route: {rule.rule} -> {rule.endpoint}")
