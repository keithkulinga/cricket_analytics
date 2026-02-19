import os
from flask import Flask, jsonify
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

@app.route('/api/teams', methods=['GET'])
def get_teams():
    teams = Team.query.all()
    return jsonify([team.to_dict() for team in teams])

if __name__ == '__main__':
    # Bind to Render's dynamic port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)