# backend/routes/players.py

from flask import Blueprint, request, jsonify
from models import db

players_bp = Blueprint('players', __name__)

@players_bp.route('/', methods=['GET'])
def get_players():
    team_id = request.args.get('team_id')
    if team_id:
        players = db.fetch_all("""
            SELECT p.*, t.name as team_name, t.short_name as team_short
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE p.team_id = ?
            ORDER BY p.first_name
        """, (team_id,))
    else:
        players = db.fetch_all("""
            SELECT p.*, t.name as team_name, t.short_name as team_short
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            ORDER BY t.name, p.first_name
        """)
    return jsonify(players)

@players_bp.route('/<int:player_id>', methods=['GET'])
def get_player(player_id):
    player = db.fetch_one("SELECT * FROM players WHERE id=?", (player_id,))
    return jsonify(player)

@players_bp.route('/', methods=['POST'])
def create_player():
    data = request.json
    player_id = db.insert("""
        INSERT INTO players (first_name, last_name, team_id, batting_style, bowling_style, player_role, jersey_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data['first_name'], data['last_name'], data.get('team_id'),
        data.get('batting_style'), data.get('bowling_style'),
        data.get('player_role'), data.get('jersey_number')
    ))
    return jsonify({'id': player_id}), 201

@players_bp.route('/<int:player_id>', methods=['PUT'])
def update_player(player_id):
    data = request.json
    db.execute("""
        UPDATE players SET first_name=?, last_name=?, team_id=?, 
            batting_style=?, bowling_style=?, player_role=?, jersey_number=?
        WHERE id=?
    """, (
        data['first_name'], data['last_name'], data.get('team_id'),
        data.get('batting_style'), data.get('bowling_style'),
        data.get('player_role'), data.get('jersey_number'), player_id
    ))
    return jsonify({'message': 'Player updated'})

@players_bp.route('/<int:player_id>/stats', methods=['GET'])
def get_player_stats(player_id):
    """Get comprehensive player statistics"""
    match_id = request.args.get('match_id')
    innings_id = request.args.get('innings_id')
    
    condition = ""
    params = [player_id]
    
    if innings_id:
        condition = " AND d.innings_id = ?"
        params.append(innings_id)
    elif match_id:
        condition = " AND d.match_id = ?"
        params.append(match_id)
    
    # Batting stats
    batting = db.fetch_one(f"""
        SELECT 
            COUNT(*) as innings_balls,
            SUM(runs_off_bat) as total_runs,
            COUNT(CASE WHEN is_boundary = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN is_dot = 1 THEN 1 END) as dots,
            COUNT(CASE WHEN runs_off_bat = 1 THEN 1 END) as singles,
            COUNT(CASE WHEN runs_off_bat = 2 THEN 1 END) as twos,
            COUNT(CASE WHEN runs_off_bat = 3 THEN 1 END) as threes,
            ROUND(SUM(runs_off_bat) * 100.0 / NULLIF(COUNT(CASE WHEN extra_type IN ('None', 'No Ball') THEN 1 END), 0), 2) as strike_rate,
            COUNT(CASE WHEN is_false_shot = 1 THEN 1 END) as false_shots,
            COUNT(CASE WHEN is_beaten = 1 THEN 1 END) as beaten,
            AVG(control_percentage) as avg_control
        FROM deliveries d
        WHERE d.batsman_id = ? {condition}
    """, params)
    
    # Bowling stats
    params2 = [player_id]
    if innings_id:
        params2.append(innings_id)
    elif match_id:
        params2.append(match_id)
    
    bowling = db.fetch_one(f"""
        SELECT 
            COUNT(CASE WHEN extra_type IN ('None', 'Bye', 'Leg Bye') THEN 1 END) as legal_balls,
            SUM(runs_scored) as runs_conceded,
            COUNT(CASE WHEN is_wicket = 1 AND wicket_type NOT IN ('Run Out') THEN 1 END) as wickets,
            COUNT(CASE WHEN is_dot = 1 THEN 1 END) as dots,
            COUNT(CASE WHEN is_boundary = 1 THEN 1 END) as fours_conceded,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes_conceded,
            COUNT(CASE WHEN extra_type = 'Wide' THEN 1 END) as wides,
            COUNT(CASE WHEN extra_type = 'No Ball' THEN 1 END) as no_balls
        FROM deliveries d
        WHERE d.bowler_id = ? {condition}
    """, params2)
    
    return jsonify({
        'batting': batting,
        'bowling': bowling
    })