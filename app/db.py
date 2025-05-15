import sqlite3
import os
import threading
from contextlib import contextmanager

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()
        self._lock = threading.RLock()
    
    @contextmanager
    def connection(self):
        """Get a thread-local database connection"""
        with self._lock:
            if not hasattr(self._local, 'connection'):
                self._local.connection = sqlite3.connect(self.db_path)
                self._local.connection.row_factory = sqlite3.Row
            
            try:
                yield self._local.connection
            except Exception as e:
                self._local.connection.rollback()
                raise e
    
    def initialize(self):
        """Initialize the database with required tables"""
        with self.connection() as conn:
            cursor = conn.cursor()
            
            # App settings table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value BLOB
            )
            ''')
            
            # Widget settings table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS widget_settings (
                widget_id TEXT,
                key TEXT,
                value BLOB,
                PRIMARY KEY (widget_id, key)
            )
            ''')
            
            # Data cache table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_cache (
                source_id TEXT PRIMARY KEY,
                data BLOB,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
    
    def execute(self, query, params=()):
        """Execute a query and commit changes"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
    
    def executemany(self, query, params_list):
        """Execute a query with multiple parameter sets and commit changes"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.lastrowid
    
    def query(self, query, params=()):
        """Execute a query and return all results"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def query_one(self, query, params=()):
        """Execute a query and return the first result"""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def get_widget_setting(self, widget_id, key, default=None):
        """Get a setting for a specific widget"""
        row = self.query_one(
            "SELECT value FROM widget_settings WHERE widget_id = ? AND key = ?",
            (widget_id, key)
        )
        return row[0] if row else default
    
    def set_widget_setting(self, widget_id, key, value):
        """Set a setting for a specific widget"""
        self.execute(
            "INSERT OR REPLACE INTO widget_settings (widget_id, key, value) VALUES (?, ?, ?)",
            (widget_id, key, value)
        )
    
    def get_cached_data(self, source_id):
        """Get cached data for a specific source"""
        row = self.query_one(
            "SELECT data, last_updated FROM data_cache WHERE source_id = ?",
            (source_id,)
        )
        return row if row else (None, None)
    
    def set_cached_data(self, source_id, data):
        """Set cached data for a specific source"""
        self.execute(
            "INSERT OR REPLACE INTO data_cache (source_id, data, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (source_id, data)
        )