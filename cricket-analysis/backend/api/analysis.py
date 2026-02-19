# backend/routes/analysis.py

from flask import Blueprint, request, jsonify
from models import db

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/pitch_map', methods=['POST'])
def pitch_map_data():
    """Get pitch map data for visualization"""
    data = request.json
    conditions = ["pitch_x IS NOT NULL AND pitch_y IS NOT NULL"]
    params = []
    
    if data.get('innings_id'):
        conditions.append("d.innings_id = ?")
        params.append(data['innings_id'])
    if data.get('bowler_id'):
        conditions.append("d.bowler_id = ?")
        params.append(data['bowler_id'])
    if data.get('batsman_id'):
        conditions.append("d.batsman_id = ?")
        params.append(data['batsman_id'])
    if data.get('batting_style'):
        conditions.append("bp.batting_style = ?")
        params.append(data['batting_style'])
    
    where = " AND ".join(conditions)
    
    deliveries = db.fetch_all(f"""
        SELECT d.pitch_x, d.pitch_y, d.line, d.length, d.delivery_type,
               d.runs_scored, d.runs_off_bat, d.is_wicket, d.is_boundary, d.is_six,
               d.is_dot, d.bowling_type, d.movement, d.pace,
               d.over_number, d.ball_number,
               bp.batting_style,
               d.video_timestamp_start
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        WHERE {where}
        ORDER BY d.over_number, d.ball_number
    """, params)
    
    return jsonify(deliveries)

@analysis_bp.route('/wagon_wheel', methods=['POST'])
def wagon_wheel_data():
    """Get wagon wheel data for visualization"""
    data = request.json
    conditions = ["wagon_x IS NOT NULL AND wagon_y IS NOT NULL"]
    params = []
    
    if data.get('innings_id'):
        conditions.append("d.innings_id = ?")
        params.append(data['innings_id'])
    if data.get('batsman_id'):
        conditions.append("d.batsman_id = ?")
        params.append(data['batsman_id'])
    if data.get('bowler_id'):
        conditions.append("d.bowler_id = ?")
        params.append(data['bowler_id'])
    if data.get('shot_type'):
        conditions.append("d.shot_type = ?")
        params.append(data['shot_type'])
    if data.get('runs_min') is not None:
        conditions.append("d.runs_off_bat >= ?")
        params.append(data['runs_min'])
    
    where = " AND ".join(conditions)
    
    deliveries = db.fetch_all(f"""
        SELECT d.wagon_x, d.wagon_y, d.wagon_zone,
               d.runs_off_bat, d.runs_scored, d.is_boundary, d.is_six,
               d.shot_type, d.shot_connection,
               d.over_number, d.ball_number,
               bp.first_name || ' ' || bp.last_name as batsman_name,
               d.video_timestamp_start
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        WHERE {where}
        ORDER BY d.over_number, d.ball_number
    """, params)
    
    return jsonify(deliveries)

@analysis_bp.route('/over_by_over/<int:innings_id>', methods=['GET'])
def over_by_over(innings_id):
    """Over-by-over run progression"""
    overs = db.fetch_all("""
        SELECT 
            over_number,
            SUM(runs_scored) as runs_in_over,
            COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as wickets_in_over,
            COUNT(CASE WHEN is_dot = 1 THEN 1 END) as dots_in_over,
            COUNT(CASE WHEN is_boundary = 1 THEN 1 END) as fours_in_over,
            COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes_in_over,
            COUNT(CASE WHEN extra_type IN ('None', 'Bye', 'Leg Bye') THEN 1 END) as legal_balls
        FROM deliveries
        WHERE innings_id = ?
        GROUP BY over_number
        ORDER BY over_number
    """, (innings_id,))
    
    # Calculate cumulative
    cumulative = 0
    cumulative_wickets = 0
    for over in overs:
        cumulative += over['runs_in_over']
        cumulative_wickets += over['wickets_in_over']
        over['cumulative_runs'] = cumulative
        over['cumulative_wickets'] = cumulative_wickets
        over['run_rate'] = round(cumulative / (over['over_number'] + 1), 2)
    
    return jsonify(overs)

@analysis_bp.route('/batsman_analysis/<int:innings_id>/<int:batsman_id>')
def batsman_analysis(innings_id, batsman_id):
    """Comprehensive batsman analysis"""
    
    # Scoring zones
    zones = db.fetch_all("""
        SELECT wagon_zone,
               SUM(runs_off_bat) as runs,
               COUNT(*) as balls,
               COUNT(CASE WHEN is_boundary = 1 THEN 1 END) as boundaries,
               COUNT(CASE WHEN runs_off_bat = 6 THEN 1 END) as sixes,
               COUNT(CASE WHEN runs_off_bat = 0 THEN 1 END) as dots
        FROM deliveries
        WHERE innings_id = ? AND batsman_id = ?
        GROUP BY wagon_zone
    """, (innings_id, batsman_id))
    
    return jsonify({"zones": zones})
    
    # Against different bowling types
    vs_bowling = db.fetch_all("""
        SELECT bowling_type,
               COUNT(*) as balls,
               SUM(runs_off_bat) as runs,
               COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as dismissals,
               COUNT(CASE WHEN is_dot = 1 THEN 1 END) as dots,
               ROUND(SUM(runs_off_bat) * 100.0 / NULLIF(COUNT(*), 0), 2) as strike_rate
        FROM deliveries
        WHERE innings_id = ? AND batsman_id = ? AND bowling_type IS NOT NULL
        GROUP BY bowling_type
    """, (innings_id, batsman_id))
    
    # Phase-wise
# Phase analysis (Powerplay, Middle, Death)
    phase_stats = db.fetch_all("""
        SELECT phase,
               COUNT(*) as balls,
               SUM(runs_off_bat) as runs,
               COUNT(CASE WHEN is_boundary = 1 THEN 1 END) as boundaries,
               COUNT(CASE WHEN is_six = 1 THEN 1 END) as sixes,
               COUNT(CASE WHEN is_dot = 1 THEN 1 END) as dots,
               ROUND(SUM(runs_off_bat) * 100.0 / COUNT(*), 2) as strike_rate
        FROM deliveries
        WHERE innings_id = ? AND batsman_id = ?
        GROUP BY phase
    """, (innings_id, batsman_id))