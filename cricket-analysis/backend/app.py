from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_FILE = 'cricket_league.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize DB and perform upgrades if needed."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create Tables
    c.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT,
            team TEXT,
            image_url TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS match_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            runs INTEGER DEFAULT 0,
            balls INTEGER DEFAULT 0,
            fours INTEGER DEFAULT 0,
            sixes INTEGER DEFAULT 0,
            wickets INTEGER DEFAULT 0,
            overs REAL DEFAULT 0,
            runs_conceded INTEGER DEFAULT 0,
            catches INTEGER DEFAULT 0,
            stumpings INTEGER DEFAULT 0,
            run_outs INTEGER DEFAULT 0,
            match_date TEXT,
            opposition TEXT,
            venue TEXT,
            match_result TEXT DEFAULT 'Won',
            FOREIGN KEY (player_id) REFERENCES players (id)
        )
    ''')
    
    # --- MIGRATION CHECK ---
    # Check if 'image_url' exists in players table (for older users)
    c.execute("PRAGMA table_info(players)")
    columns = [info[1] for info in c.fetchall()]
    if 'image_url' not in columns:
        print("Migrating Database: Adding image_url column...")
        c.execute("ALTER TABLE players ADD COLUMN image_url TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- API ROUTES ---

@app.route('/api/players', methods=['GET'])
def get_players():
    conn = get_db_connection()
    players = conn.execute('SELECT * FROM players').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in players])

@app.route('/api/players', methods=['POST'])
def add_player():
    new_player = request.json
    conn = get_db_connection()
    c = conn.cursor()
    # Default image if none provided
    img = new_player.get('image_url', '')
    if not img: img = "https://cdn-icons-png.flaticon.com/512/3237/3237472.png" # Default Avatar

    c.execute("INSERT INTO players (first_name, last_name, role, team, image_url) VALUES (?, ?, ?, ?, ?)",
              (new_player['first_name'], new_player['last_name'], new_player['role'], new_player['team'], img))
    conn.commit()
    conn.close()
    return jsonify(new_player), 201

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    stats = conn.execute('SELECT * FROM match_stats').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in stats])

@app.route('/api/stats', methods=['POST'])
def add_stats():
    s = request.json
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO match_stats 
        (player_id, runs, balls, fours, sixes, wickets, overs, runs_conceded, catches, stumpings, run_outs, match_date, opposition, venue, match_result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (s['player_id'], s['runs'], s['balls'], s['fours'], s['sixes'], 
          s['wickets'], s['overs'], s['runs_conceded'], 
          s['catches'], s['stumpings'], s['run_outs'],
          s['match_date'], s['opposition'], s['venue'], s['match_result']))
    conn.commit()
    conn.close()
    return jsonify(s), 201

@app.route('/api/stats/<int:id>', methods=['DELETE'])
def delete_stat(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM match_stats WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Deleted'}), 200

@app.route('/api/reset', methods=['POST'])
def reset_db():
    conn = get_db_connection()
    conn.execute('DELETE FROM match_stats')
    conn.execute('DELETE FROM players')
    conn.commit()
    conn.close()
    return jsonify({'message': 'Database Wiped'}), 200

if __name__ == '__main__':
    # Render assigns a PORT environment variable. We use 5000 as a fallback for local testing.
    port = int(os.environ.get("PORT", 5000))
    # 0.0.0.0 tells Flask to listen on all public IPs so Render can route traffic to it.
    app.run(host='0.0.0.0', port=port)