import os
from flask import Flask, jsonify
import requests
from flask_cors import CORS
from models import db, Team

app = Flask(__name__)
CORS(app) # Allows your React frontend to talk to this backend

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cricket.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# SEED DATA: Automatically adds teams if database is new
def seed_database():
    if Team.query.first() is None:
        teams = [
            {"name": "Mumbai Indians", "logo": "https://upload.wikimedia.org/wikipedia/en/c/cd/Mumbai_Indians_Logo.svg"},
            {"name": "Chennai Super Kings", "logo": "https://upload.wikimedia.org/wikipedia/en/2/2b/Chennai_Super_Kings_Logo.svg"},
            {"name": "RCB", "logo": "https://upload.wikimedia.org/wikipedia/en/2/24/Royal_Challengers_Bangalore_logo.svg"},
            {"name": "Kolkata Knight Riders", "logo": "https://upload.wikimedia.org/wikipedia/en/4/4c/Kolkata_Knight_Riders_Logo.svg"},
            {"name": "Gujarat Titans", "logo": "https://upload.wikimedia.org/wikipedia/en/0/09/Gujarat_Titans_Logo.svg"}
        ]
        for t in teams:
            new_team = Team(name=t["name"], logo_url=t["logo"])
            db.session.add(new_team)
        db.session.commit()
        print("Database Seeded!")

with app.app_context():
    db.create_all()
    seed_database()

@app.route('/api/live-matches', methods=['GET'])
def get_live_matches():
    try:
        # The CricketData API endpoint for current matches
        api_url = "https://api.cricapi.com/v1/currentMatches?apikey=1b3b6e52-10a7-4bb1-94ba-db9800b3ba12&offset=0"
        
        # Fetch the data from the API
        response = requests.get(api_url)
        data = response.json()
        
        # Send the live data directly to your React frontend
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Bind to Render's dynamic port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)