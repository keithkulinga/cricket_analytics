# backend/models.py

import sqlite3
import json
from config import Config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_PATH
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    
    def init_db(self):
        """Initialize database from schema file"""
        import os
        schema_path = os.path.join(os.path.dirname(self.db_path), 'schema.sql')
        conn = self.get_connection()
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
    
    def execute(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def fetch_one(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def fetch_all(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def insert(self, query, params=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

db = Database()