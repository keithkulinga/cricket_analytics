# backend/config.py

import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, '..', 'database', 'cricket_analysis.db')
    VIDEO_UPLOAD_FOLDER = os.path.join(BASE_DIR, '..', 'videos')
    EXPORT_FOLDER = os.path.join(BASE_DIR, '..', 'exports')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max upload
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv'}
    SECRET_KEY = os.environ.get('SECRET_KEY', 'cricket-analysis-secret-key-2024')
    
    # FFmpeg path (adjust for your system)
    FFMPEG_PATH = os.environ.get('FFMPEG_PATH', 'ffmpeg')
    FFPROBE_PATH = os.environ.get('FFPROBE_PATH', 'ffprobe')