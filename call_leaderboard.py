import sys
import os
sys.path.append(os.path.abspath("src"))
from web.app import app, get_leaderboard

with app.app_context():
    # Calling the internal leaderboard function
    response = get_leaderboard()
    data = response.get_json()
    
    if data and 'leaderboard' in data:
        leaderboard = data['leaderboard']
        print(f"Number of users in leaderboard: {len(leaderboard)}")
        
        # Why might it be less? (Usually unverified, no progress, or admin)
        for u in leaderboard[:5]:
            print(f"User: {u.get('name')} | XP: {u.get('total_xp')} | Level: {u.get('level')}")
            
    else:
        print("No leaderboard data found or error")
