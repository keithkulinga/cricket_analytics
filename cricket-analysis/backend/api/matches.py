# backend/routes/matches.py

from flask import Blueprint, request, jsonify
from models import db

matches_bp = Blueprint('matches', __name__)

@matches_bp.route('/', methods=['GET'])
def get_matches():
    matches = db.fetch_all("""
        SELECT m.*, 
            th.name as home_team_name, th.short_name as home_short,
            ta.name as away_team_name, ta.short_name as away_short
        FROM matches m
        LEFT JOIN teams th ON m.team_home_id = th.id
        LEFT JOIN teams ta ON m.team_away_id = ta.id
        ORDER BY m.created_at DESC
    """)
    return jsonify(matches)

@matches_bp.route('/<int:match_id>', methods=['GET'])
def get_match(match_id):
    match = db.fetch_one("""
        SELECT m.*, 
            th.name as home_team_name, th.short_name as home_short,
            ta.name as away_team_name, ta.short_name as away_short
        FROM matches m
        LEFT JOIN teams th ON m.team_home_id = th.id
        LEFT JOIN teams ta ON m.team_away_id = ta.id
        WHERE m.id = ?
    """, (match_id,))
    
    if not match:
        return jsonify({'error': 'Match not found'}), 404
    
    # Get innings
    innings = db.fetch_all("""
        SELECT i.*, bt.name as batting_team_name, bwt.name as bowling_team_name
        FROM innings i
        LEFT JOIN teams bt ON i.batting_team_id = bt.id
        LEFT JOIN teams bwt ON i.bowling_team_id = bwt.id
        WHERE i.match_id = ?
        ORDER BY i.innings_number
    """, (match_id,))
    
    match['innings'] = innings
    return jsonify(match)

@matches_bp.route('/', methods=['POST'])
def create_match():
    data = request.json
    match_id = db.insert("""
        INSERT INTO matches (match_title, match_format, team_home_id, team_away_id, 
                           venue, match_date, toss_winner_id, toss_decision, video_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('match_title'),
        data.get('match_format', 'T20'),
        data.get('team_home_id'),
        data.get('team_away_id'),
        data.get('venue'),
        data.get('match_date'),
        data.get('toss_winner_id'),
        data.get('toss_decision'),
        data.get('video_path'),
        data.get('notes')
    ))
    
    # Auto-create innings
    if data.get('team_home_id') and data.get('team_away_id'):
        batting_first = data.get('team_home_id')
        bowling_first = data.get('team_away_id')
        
        if data.get('toss_winner_id') and data.get('toss_decision'):
            if data['toss_decision'] == 'Bat':
                batting_first = data['toss_winner_id']
                bowling_first = data['team_home_id'] if data['toss_winner_id'] == data['team_away_id'] else data['team_away_id']
            else:
                bowling_first = data['toss_winner_id']
                batting_first = data['team_home_id'] if data['toss_winner_id'] == data['team_away_id'] else data['team_away_id']
        
        db.insert("""
            INSERT INTO innings (match_id, innings_number, batting_team_id, bowling_team_id)
            VALUES (?, 1, ?, ?)
        """, (match_id, batting_first, bowling_first))
        
        db.insert("""
            INSERT INTO innings (match_id, innings_number, batting_team_id, bowling_team_id)
            VALUES (?, 2, ?, ?)
        """, (match_id, bowling_first, batting_first))
    
    return jsonify({'id': match_id, 'message': 'Match created successfully'}), 201

@matches_bp.route('/<int:match_id>', methods=['PUT'])
def update_match(match_id):
    data = request.json
    db.execute("""
        UPDATE matches SET match_title=?, match_format=?, venue=?, match_date=?,
            status=?, match_result=?, winner_id=?, notes=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (
        data.get('match_title'), data.get('match_format'),
        data.get('venue'), data.get('match_date'),
        data.get('status'), data.get('match_result'),
        data.get('winner_id'), data.get('notes'), match_id
    ))
    return jsonify({'message': 'Match updated'})

@matches_bp.route('/<int:match_id>', methods=['DELETE'])
def delete_match(match_id):
    db.execute("DELETE FROM deliveries WHERE match_id=?", (match_id,))
    db.execute("DELETE FROM innings WHERE match_id=?", (match_id,))
    db.execute("DELETE FROM video_clips WHERE match_id=?", (match_id,))
    db.execute("DELETE FROM matches WHERE id=?", (match_id,))
    return jsonify({'message': 'Match deleted'})

# Teams endpoints
@matches_bp.route('/teams', methods=['GET'])
def get_teams():
    teams = db.fetch_all("SELECT * FROM teams ORDER BY name")
    return jsonify(teams)

@matches_bp.route('/teams', methods=['POST'])
def create_team():
    data = request.json
    team_id = db.insert(
        "INSERT INTO teams (name, short_name) VALUES (?, ?)",
        (data['name'], data.get('short_name'))
    )
    return jsonify({'id': team_id}), 201