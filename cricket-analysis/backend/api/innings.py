# backend/routes/innings.py

from flask import Blueprint, request, jsonify
from models import db

innings_bp = Blueprint('innings', __name__)

@innings_bp.route('/match/<int:match_id>', methods=['GET'])
def get_innings_for_match(match_id):
    innings = db.fetch_all("""
        SELECT i.*, bt.name as batting_team_name, bt.short_name as batting_short,
               bwt.name as bowling_team_name, bwt.short_name as bowling_short
        FROM innings i
        LEFT JOIN teams bt ON i.batting_team_id = bt.id
        LEFT JOIN teams bwt ON i.bowling_team_id = bwt.id
        WHERE i.match_id = ?
        ORDER BY i.innings_number
    """, (match_id,))
    return jsonify(innings)

@innings_bp.route('/<int:innings_id>', methods=['GET'])
def get_innings(innings_id):
    innings = db.fetch_one("""
        SELECT i.*, bt.name as batting_team_name, bwt.name as bowling_team_name
        FROM innings i
        LEFT JOIN teams bt ON i.batting_team_id = bt.id
        LEFT JOIN teams bwt ON i.bowling_team_id = bwt.id
        WHERE i.id = ?
    """, (innings_id,))
    return jsonify(innings)

@innings_bp.route('/<int:innings_id>/scorecard', methods=['GET'])
def get_scorecard(innings_id):
    # Batting scorecard
    batting = db.fetch_all("""
        SELECT 
            p.id, p.first_name, p.last_name,
            COUNT(CASE WHEN d.extra_type IN ('None', 'No Ball') THEN 1 END) as balls_faced,
            SUM(d.runs_off_bat) as runs,
            COUNT(CASE WHEN d.is_boundary = 1 THEN 1 END) as fours,
            COUNT(CASE WHEN d.is_six = 1 THEN 1 END) as sixes,
            COUNT(CASE WHEN d.is_dot = 1 THEN 1 END) as dots,
            ROUND(SUM(d.runs_off_bat) * 100.0 / NULLIF(COUNT(CASE WHEN d.extra_type IN ('None', 'No Ball') THEN 1 END), 0), 2) as strike_rate
        FROM deliveries d
        JOIN players p ON d.batsman_id = p.id
        WHERE d.innings_id = ?
        GROUP BY d.batsman_id
        ORDER BY MIN(d.id)
    """, (innings_id,))
    
    # Add dismissal info
    for bat in batting:
        dismissal = db.fetch_one("""
            SELECT wicket_type, 
                   (SELECT first_name || ' ' || last_name FROM players WHERE id = d.bowler_id) as bowler_name,
                   (SELECT first_name || ' ' || last_name FROM players WHERE id = d.fielder_id) as fielder_name
            FROM deliveries d
            WHERE d.innings_id = ? AND d.dismissed_batsman_id = ? AND d.is_wicket = 1
        """, (innings_id, bat['id']))
        bat['dismissal'] = dismissal
    
    # Bowling scorecard
    bowling = db.fetch_all("""
        SELECT 
            p.id, p.first_name, p.last_name,
            COUNT(CASE WHEN d.extra_type IN ('None', 'Bye', 'Leg Bye') THEN 1 END) as balls,
            SUM(d.runs_scored) as runs_conceded,
            COUNT(CASE WHEN d.is_wicket = 1 AND d.wicket_type NOT IN ('Run Out') THEN 1 END) as wickets,
            COUNT(CASE WHEN d.extra_type = 'Wide' THEN 1 END) as wides,
            COUNT(CASE WHEN d.extra_type = 'No Ball' THEN 1 END) as no_balls,
            COUNT(CASE WHEN d.is_dot = 1 THEN 1 END) as dots,
            COUNT(CASE WHEN d.is_boundary = 1 OR d.is_six = 1 THEN 1 END) as boundaries_conceded
        FROM deliveries d
        JOIN players p ON d.bowler_id = p.id
        WHERE d.innings_id = ?
        GROUP BY d.bowler_id
        ORDER BY MIN(d.over_number)
    """, (innings_id,))
    
    # Calculate overs properly
    for b in bowling:
        complete_overs = b['balls'] // 6
        remaining = b['balls'] % 6
        b['overs'] = f"{complete_overs}.{remaining}"
        if b['balls'] > 0:
            b['economy'] = round(b['runs_conceded'] * 6.0 / b['balls'], 2)
        else:
            b['economy'] = 0
    
    # Fall of wickets
    fow = db.fetch_all("""
        SELECT d.over_number, d.ball_number, d.runs_scored,
               p.first_name || ' ' || p.last_name as batsman_name,
               (SELECT SUM(d2.runs_scored) FROM deliveries d2 
                WHERE d2.innings_id = d.innings_id AND d2.id <= d.id) as team_score,
               (SELECT COUNT(*) FROM deliveries d2 
                WHERE d2.innings_id = d.innings_id AND d2.is_wicket = 1 AND d2.id <= d.id) as wicket_number
        FROM deliveries d
        JOIN players p ON d.dismissed_batsman_id = p.id
        WHERE d.innings_id = ? AND d.is_wicket = 1
        ORDER BY d.id
    """, (innings_id,))
    
    return jsonify({
        'batting': batting,
        'bowling': bowling,
        'fall_of_wickets': fow
    })

@innings_bp.route('/<int:innings_id>/update_totals', methods=['POST'])
def update_innings_totals(innings_id):
    """Recalculate innings totals from deliveries"""
    totals = db.fetch_one("""
        SELECT 
            COALESCE(SUM(runs_scored), 0) as total_runs,
            COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as total_wickets,
            COALESCE(SUM(CASE WHEN extra_type = 'Wide' THEN extras ELSE 0 END), 0) as extras_wides,
            COALESCE(SUM(CASE WHEN extra_type = 'No Ball' THEN extras ELSE 0 END), 0) as extras_noballs,
            COALESCE(SUM(CASE WHEN extra_type = 'Bye' THEN extras ELSE 0 END), 0) as extras_byes,
            COALESCE(SUM(CASE WHEN extra_type = 'Leg Bye' THEN extras ELSE 0 END), 0) as extras_legbyes,
            COALESCE(SUM(extras), 0) as extras_total,
            MAX(over_number) as last_over,
            MAX(CASE WHEN extra_type IN ('None', 'Bye', 'Leg Bye') THEN ball_number ELSE 0 END) as last_ball
        FROM deliveries WHERE innings_id = ?
    """, (innings_id,))
    
    if totals:
        legal_balls = db.fetch_one("""
            SELECT COUNT(*) as cnt FROM deliveries 
            WHERE innings_id = ? AND extra_type IN ('None', 'Bye', 'Leg Bye')
        """, (innings_id,))
        
        overs = legal_balls['cnt'] // 6
        balls = legal_balls['cnt'] % 6
        total_overs = float(f"{overs}.{balls}")
        
        db.execute("""
            UPDATE innings SET total_runs=?, total_wickets=?, total_overs=?,
                extras_total=?, extras_wides=?, extras_noballs=?,
                extras_byes=?, extras_legbyes=?
            WHERE id=?
        """, (
            totals['total_runs'], totals['total_wickets'], total_overs,
            totals['extras_total'], totals['extras_wides'], totals['extras_noballs'],
            totals['extras_byes'], totals['extras_legbyes'], innings_id
        ))
    
    return jsonify({'message': 'Totals updated', 'totals': totals})