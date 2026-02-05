"""
Database connection management.
"""
import mysql.connector


class DatabaseConnection:
    """Manager for database connections."""
    
    def __init__(self, config):
        """
        Initialize database connection manager.
        
        Args:
            config: DatabaseConfig instance
        """
        self.config = config
        self.conn = None
        self.cur = None
    
    def connect(self):
        """Establish database connection."""
        self.conn = mysql.connector.connect(**self.config.to_dict())
        self.cur = self.conn.cursor()
        return self.cur
    
    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
