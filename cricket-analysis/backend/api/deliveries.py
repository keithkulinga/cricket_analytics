# backend/routes/deliveries.py

from flask import Blueprint, request, jsonify
from models import db
import json

deliveries_bp = Blueprint('deliveries', __name__)

@deliveries_bp.route('/innings/<int:innings_id>', methods=['GET'])
def get_deliveries(innings_id):
    deliveries = db.fetch_all("""
        SELECT d.*,
            bp.first_name || ' ' || bp.last_name as batsman_name,
            bp.batting_style,
            nsp.first_name || ' ' || nsp.last_name as non_striker_name,
            bwp.first_name || ' ' || bwp.last_name as bowler_name,
            fp.first_name || ' ' || fp.last_name as fielder_name,
            dp.first_name || ' ' || dp.last_name as dismissed_name
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        LEFT JOIN players nsp ON d.non_striker_id = nsp.id
        LEFT JOIN players bwp ON d.bowler_id = bwp.id
        LEFT JOIN players fp ON d.fielder_id = fp.id
        LEFT JOIN players dp ON d.dismissed_batsman_id = dp.id
        WHERE d.innings_id = ?
        ORDER BY d.over_number, d.ball_number, d.id
    """, (innings_id,))
    return jsonify(deliveries)

@deliveries_bp.route('/<int:delivery_id>', methods=['GET'])
def get_delivery(delivery_id):
    delivery = db.fetch_one("""
        SELECT d.*,
            bp.first_name || ' ' || bp.last_name as batsman_name,
            bwp.first_name || ' ' || bwp.last_name as bowler_name
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        LEFT JOIN players bwp ON d.bowler_id = bwp.id
        WHERE d.id = ?
    """, (delivery_id,))
    return jsonify(delivery)

@deliveries_bp.route('/', methods=['POST'])
def create_delivery():
    data = request.json
    
    # Determine legal ball number
    legal_ball = None
    if data.get('extra_type') in (None, 'None', 'Bye', 'Leg Bye'):
        # Count existing legal balls in this over
        count = db.fetch_one("""
            SELECT COUNT(*) as cnt FROM deliveries 
            WHERE innings_id = ? AND over_number = ? 
            AND extra_type IN ('None', 'Bye', 'Leg Bye')
        """, (data['innings_id'], data['over_number']))
        legal_ball = (count['cnt'] if count else 0) + 1
    
    # Determine if dot ball
    is_dot = 1 if data.get('runs_scored', 0) == 0 and data.get('extra_type', 'None') == 'None' else 0
    
    # Determine is_scoring_shot
    is_scoring = 1 if data.get('runs_off_bat', 0) > 0 else 0
    
    # Determine phase
    over_num = data.get('over_number', 0)
    match = db.fetch_one("""
        SELECT m.match_format FROM matches m
        JOIN innings i ON i.match_id = m.id
        WHERE i.id = ?
    """, (data['innings_id'],))
    
    phase = 'Middle'
    if match:
        fmt = match.get('match_format', 'T20')
        if fmt == 'T20':
            if over_num < 6:
                phase = 'Powerplay'
            elif over_num >= 16:
                phase = 'Death'
            else:
                phase = 'Middle'
        elif fmt in ('ODI', 'Other'):
            if over_num < 10:
                phase = 'Powerplay'
            elif over_num >= 40:
                phase = 'Death'
            else:
                phase = 'Middle'
    
    powerplay = 1 if phase == 'Powerplay' else 0
    
    tags = json.dumps(data.get('tags', [])) if data.get('tags') else None
    
    delivery_id = db.insert("""
        INSERT INTO deliveries (
            innings_id, match_id, over_number, ball_number, legal_ball_number,
            batsman_id, non_striker_id, bowler_id,
            video_timestamp_start, video_timestamp_end, video_bookmark,
            bowling_type, delivery_type, line, length,
            pitch_x, pitch_y, movement, pace,
            shot_type, shot_connection,
            wagon_x, wagon_y, wagon_zone,
            runs_scored, runs_off_bat, extras, extra_type,
            is_boundary, is_six, is_dot,
            is_wicket, wicket_type, fielder_id, dismissed_batsman_id,
            appeal, drs_review, drs_outcome,
            control_percentage, is_scoring_shot, is_false_shot,
            is_beaten, is_play_and_miss,
            tags, notes, highlight, powerplay, phase
        ) VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?, ?, ?
        )
    """, (
        data['innings_id'], data['match_id'], data['over_number'], data['ball_number'], legal_ball,
        data['batsman_id'], data.get('non_striker_id'), data['bowler_id'],
        data.get('video_timestamp_start'), data.get('video_timestamp_end'), data.get('video_bookmark'),
        data.get('bowling_type'), data.get('delivery_type'), data.get('line'), data.get('length'),
        data.get('pitch_x'), data.get('pitch_y'), data.get('movement'), data.get('pace'),
        data.get('shot_type'), data.get('shot_connection'),
        data.get('wagon_x'), data.get('wagon_y'), data.get('wagon_zone'),
        data.get('runs_scored', 0), data.get('runs_off_bat', 0),
        data.get('extras', 0), data.get('extra_type', 'None'),
        data.get('is_boundary', 0), data.get('is_six', 0), is_dot,
        data.get('is_wicket', 0), data.get('wicket_type'),
        data.get('fielder_id'), data.get('dismissed_batsman_id'),
        data.get('appeal', 0), data.get('drs_review', 0), data.get('drs_outcome'),
        data.get('control_percentage'), is_scoring, data.get('is_false_shot', 0),
        data.get('is_beaten', 0), data.get('is_play_and_miss', 0),
        tags, data.get('notes'), data.get('highlight', 0), powerplay, phase
    ))
    
    # Update innings totals
    _update_innings_totals(data['innings_id'])
    
    return jsonify({'id': delivery_id, 'message': 'Delivery recorded'}), 201

@deliveries_bp.route('/<int:delivery_id>', methods=['PUT'])
def update_delivery(delivery_id):
    data = request.json
    
    # Build dynamic update query
    fields = []
    values = []
    
    updatable_fields = [
        'video_timestamp_start', 'video_timestamp_end', 'video_bookmark',
        'bowling_type', 'delivery_type', 'line', 'length',
        'pitch_x', 'pitch_y', 'movement', 'pace',
        'shot_type', 'shot_connection',
        'wagon_x', 'wagon_y', 'wagon_zone',
        'runs_scored', 'runs_off_bat', 'extras', 'extra_type',
        'is_boundary', 'is_six', 'is_dot',
        'is_wicket', 'wicket_type', 'fielder_id', 'dismissed_batsman_id',
        'appeal', 'drs_review', 'drs_outcome',
        'control_percentage', 'is_scoring_shot', 'is_false_shot',
        'is_beaten', 'is_play_and_miss',
        'notes', 'highlight', 'tags'
    ]
    
    for field in updatable_fields:
        if field in data:
            fields.append(f"{field} = ?")
            val = data[field]
            if field == 'tags' and isinstance(val, list):
                val = json.dumps(val)
            values.append(val)
    
    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(delivery_id)
        db.execute(
            f"UPDATE deliveries SET {', '.join(fields)} WHERE id = ?",
            values
        )
    
    # Update innings totals
    delivery = db.fetch_one("SELECT innings_id FROM deliveries WHERE id=?", (delivery_id,))
    if delivery:
        _update_innings_totals(delivery['innings_id'])
    
    return jsonify({'message': 'Delivery updated'})

@deliveries_bp.route('/<int:delivery_id>', methods=['DELETE'])
def delete_delivery(delivery_id):
    delivery = db.fetch_one("SELECT innings_id FROM deliveries WHERE id=?", (delivery_id,))
    db.execute("DELETE FROM deliveries WHERE id=?", (delivery_id,))
    if delivery:
        _update_innings_totals(delivery['innings_id'])
    return jsonify({'message': 'Delivery deleted'})

@deliveries_bp.route('/last/<int:innings_id>', methods=['GET'])
def get_last_delivery(innings_id):
    """Get the last delivery in an innings"""
    delivery = db.fetch_one("""
        SELECT d.*, 
            bp.first_name || ' ' || bp.last_name as batsman_name,
            bwp.first_name || ' ' || bwp.last_name as bowler_name
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        LEFT JOIN players bwp ON d.bowler_id = bwp.id
        WHERE d.innings_id = ?
        ORDER BY d.id DESC LIMIT 1
    """, (innings_id,))
    return jsonify(delivery)

@deliveries_bp.route('/over/<int:innings_id>/<int:over_number>', methods=['GET'])
def get_over(innings_id, over_number):
    """Get all deliveries in a specific over"""
    deliveries = db.fetch_all("""
        SELECT d.*,
            bp.first_name || ' ' || bp.last_name as batsman_name,
            bwp.first_name || ' ' || bwp.last_name as bowler_name
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        LEFT JOIN players bwp ON d.bowler_id = bwp.id
        WHERE d.innings_id = ? AND d.over_number = ?
        ORDER BY d.ball_number, d.id
    """, (innings_id, over_number))
    return jsonify(deliveries)

@deliveries_bp.route('/filter', methods=['POST'])
def filter_deliveries():
    """Advanced filtering for deliveries"""
    data = request.json
    
    conditions = ["1=1"]
    params = []
    
    if data.get('innings_id'):
        conditions.append("d.innings_id = ?")
        params.append(data['innings_id'])
    
    if data.get('match_id'):
        conditions.append("d.match_id = ?")
        params.append(data['match_id'])
    
    if data.get('batsman_id'):
        conditions.append("d.batsman_id = ?")
        params.append(data['batsman_id'])
    
    if data.get('bowler_id'):
        conditions.append("d.bowler_id = ?")
        params.append(data['bowler_id'])
    
    if data.get('bowling_type'):
        conditions.append("d.bowling_type = ?")
        params.append(data['bowling_type'])
    
    if data.get('shot_type'):
        conditions.append("d.shot_type = ?")
        params.append(data['shot_type'])
    
    if data.get('line'):
        conditions.append("d.line = ?")
        params.append(data['line'])
    
    if data.get('length'):
        conditions.append("d.length = ?")
        params.append(data['length'])
    
    if data.get('is_wicket'):
        conditions.append("d.is_wicket = 1")
    
    if data.get('is_boundary'):
        conditions.append("(d.is_boundary = 1 OR d.is_six = 1)")
    
    if data.get('is_dot'):
        conditions.append("d.is_dot = 1")
    
    if data.get('phase'):
        conditions.append("d.phase = ?")
        params.append(data['phase'])
    
    if data.get('over_from') is not None:
        conditions.append("d.over_number >= ?")
        params.append(data['over_from'])
    
    if data.get('over_to') is not None:
        conditions.append("d.over_number <= ?")
        params.append(data['over_to'])
    
    if data.get('wagon_zone'):
        conditions.append("d.wagon_zone = ?")
        params.append(data['wagon_zone'])
    
    if data.get('runs_min') is not None:
        conditions.append("d.runs_scored >= ?")
        params.append(data['runs_min'])
    
    if data.get('highlight'):
        conditions.append("d.highlight = 1")
    
    where_clause = " AND ".join(conditions)
    
    deliveries = db.fetch_all(f"""
        SELECT d.*,
            bp.first_name || ' ' || bp.last_name as batsman_name,
            bwp.first_name || ' ' || bwp.last_name as bowler_name,
            bp.batting_style
        FROM deliveries d
        LEFT JOIN players bp ON d.batsman_id = bp.id
        LEFT JOIN players bwp ON d.bowler_id = bwp.id
        WHERE {where_clause}
        ORDER BY d.over_number, d.ball_number, d.id
    """, params)
    
    return jsonify(deliveries)


def _update_innings_totals(innings_id):
    """Helper to recalculate innings totals"""
    totals = db.fetch_one("""
        SELECT 
            COALESCE(SUM(runs_scored), 0) as total_runs,
            COUNT(CASE WHEN is_wicket = 1 THEN 1 END) as total_wickets,
            COALESCE(SUM(CASE WHEN extra_type = 'Wide' THEN extras ELSE 0 END), 0) as extras_wides,
            COALESCE(SUM(CASE WHEN extra_type = 'No Ball' THEN extras ELSE 0 END), 0) as extras_noballs,
            COALESCE(SUM(CASE WHEN extra_type = 'Bye' THEN extras ELSE 0 END), 0) as extras_byes,
            COALESCE(SUM(CASE WHEN extra_type = 'Leg Bye' THEN extras ELSE 0 END), 0) as extras_legbyes,
            COALESCE(SUM(extras), 0) as extras_total
        FROM deliveries WHERE innings_id = ?
    """, (innings_id,))
    
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