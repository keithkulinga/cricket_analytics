# backend/routes/video.py

from flask import Blueprint, request, jsonify, send_file
from models import db
from config import Config
import os
import subprocess
import json

video_bp = Blueprint('video', __name__)

@video_bp.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file'}), 400
    
    file = request.files['video']
    match_id = request.form.get('match_id')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in Config.ALLOWED_VIDEO_EXTENSIONS:
        return jsonify({'error': 'Invalid file format'}), 400
    
    filename = f"match_{match_id}_{file.filename}"
    filepath = os.path.join(Config.VIDEO_UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    # Get video duration
    duration = get_video_duration(filepath)
    
    # Update match with video path
    if match_id:
        db.execute(
            "UPDATE matches SET video_path=?, video_duration=? WHERE id=?",
            (filename, duration, match_id)
        )
    
    return jsonify({
        'filename': filename,
        'duration': duration,
        'message': 'Video uploaded successfully'
    })

@video_bp.route('/clip', methods=['POST'])
def create_clip():
    """Extract a video clip"""
    data = request.json
    match_id = data['match_id']
    start_time = data['start_time']
    end_time = data['end_time']
    title = data.get('title', f'Clip_{start_time}_{end_time}')
    
    match = db.fetch_one("SELECT video_path FROM matches WHERE id=?", (match_id,))
    if not match or not match['video_path']:
        return jsonify({'error': 'No video found'}), 404
    
    source = os.path.join(Config.VIDEO_UPLOAD_FOLDER, match['video_path'])
    clip_filename = f"clip_{match_id}_{int(start_time)}_{int(end_time)}.mp4"
    output = os.path.join(Config.VIDEO_UPLOAD_FOLDER, 'clips', clip_filename)
    os.makedirs(os.path.dirname(output), exist_ok=True)
    
    # Use FFmpeg to extract clip
    try:
        cmd = [
            Config.FFMPEG_PATH, '-y',
            '-i', source,
            '-ss', str(start_time),
            '-to', str(end_time),
            '-c', 'copy',
            output
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    except Exception as e:
        return jsonify({'error': f'FFmpeg error: {str(e)}'}), 500
    
    # Save clip metadata
    clip_id = db.insert("""
        INSERT INTO video_clips (match_id, title, start_time, end_time, clip_type, tags, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        match_id, title, start_time, end_time,
        data.get('clip_type', 'Custom'),
        json.dumps(data.get('tags', [])),
        data.get('description')
    ))
    
    return jsonify({
        'id': clip_id,
        'filename': clip_filename,
        'message': 'Clip created'
    })

@video_bp.route('/clips/<int:match_id>', methods=['GET'])
def get_clips(match_id):
    clips = db.fetch_all("""
        SELECT * FROM video_clips WHERE match_id = ? ORDER BY start_time
    """, (match_id,))
    return jsonify(clips)

@video_bp.route('/playlists', methods=['GET'])
def get_playlists():
    match_id = request.args.get('match_id')
    if match_id:
        playlists = db.fetch_all(
            "SELECT * FROM playlists WHERE match_id=? ORDER BY created_at", (match_id,)
        )
    else:
        playlists = db.fetch_all("SELECT * FROM playlists ORDER BY created_at")
    return jsonify(playlists)

@video_bp.route('/playlists', methods=['POST'])
def create_playlist():
    data = request.json
    playlist_id = db.insert("""
        INSERT INTO playlists (name, description, match_id, created_by)
        VALUES (?, ?, ?, ?)
    """, (data['name'], data.get('description'), data.get('match_id'), data.get('created_by')))
    return jsonify({'id': playlist_id}), 201

@video_bp.route('/playlists/<int:playlist_id>/add', methods=['POST'])
def add_to_playlist(playlist_id):
    data = request.json
    db.execute(
        "UPDATE video_clips SET playlist_id=?, sort_order=? WHERE id=?",
        (playlist_id, data.get('sort_order', 0), data['clip_id'])
    )
    return jsonify({'message': 'Added to playlist'})

@video_bp.route('/tag_delivery', methods=['POST'])
def tag_delivery_video():
    """Tag a delivery with video timestamps"""
    data = request.json
    db.execute("""
        UPDATE deliveries SET video_timestamp_start=?, video_timestamp_end=?, video_bookmark=?
        WHERE id=?
    """, (data['start_time'], data['end_time'], data.get('bookmark'), data['delivery_id']))
    return jsonify({'message': 'Video tagged'})

@video_bp.route('/auto_clips/<int:innings_id>', methods=['POST'])
def auto_generate_clips(innings_id):
    """Auto-generate clips for wickets, boundaries, etc."""
    clip_type = request.json.get('type', 'all')
    buffer_before = request.json.get('buffer_before', 3)
    buffer_after = request.json.get('buffer_after', 5)
    
    conditions = []
    if clip_type in ('wickets', 'all'):
        conditions.append(('is_wicket = 1', 'Wicket'))
    if clip_type in ('boundaries', 'all'):
        conditions.append(('(is_boundary = 1 OR is_six = 1)', 'Boundary'))
    if clip_type in ('highlights', 'all'):
        conditions.append(('highlight = 1', 'Highlight'))
    
    innings = db.fetch_one("""
        SELECT i.match_id FROM innings i WHERE i.id = ?
    """, (innings_id,))
    
    clips_created = 0
    for condition, clip_type_name in conditions:
        deliveries = db.fetch_all(f"""
            SELECT d.*, p.first_name || ' ' || p.last_name as batsman_name,
                   b.first_name || ' ' || b.last_name as bowler_name
            FROM deliveries d
            LEFT JOIN players p ON d.batsman_id = p.id
            LEFT JOIN players b ON d.bowler_id = b.id
            WHERE d.innings_id = ? AND {condition}
            AND d.video_timestamp_start IS NOT NULL
        """, (innings_id,))
        
        for d in deliveries:
            start = max(0, d['video_timestamp_start'] - buffer_before)
            end = d['video_timestamp_end'] + buffer_after if d['video_timestamp_end'] else d['video_timestamp_start'] + buffer_after
            
            title = f"{clip_type_name}: {d.get('batsman_name', 'Unknown')} - Over {d['over_number']}.{d['ball_number']}"
            
            db.insert("""
                INSERT INTO video_clips (match_id, title, start_time, end_time, clip_type)
                VALUES (?, ?, ?, ?, ?)
            """, (innings['match_id'], title, start, end, clip_type_name))
            clips_created += 1
    
    return jsonify({'message': f'{clips_created} clips created'})


def get_video_duration(filepath):
    """Get video duration using ffprobe"""
    try:
        cmd = [
            Config.FFPROBE_PATH, '-v', 'quiet',
            '-print_format', 'json',
            '-show_format', filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        return float(info['format']['duration'])
    except Exception:
        return 0