"""
Database configuration module.
"""


class DatabaseConfig:
    """Configuration for database connection."""
    
    def __init__(self, host="localhost", user="paras.mal", password="password", database="test"):
        """
        Initialize database configuration.
        
        Args:
            host: Database host
            user: Database user
            password: Database password
            database: Database name
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.autocommit = True
    
    def to_dict(self):
        """Convert configuration to dictionary for mysql.connector."""
        return {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "autocommit": self.autocommit
        }


class BenchmarkConfig:
    """Configuration for benchmark parameters."""
    
    def __init__(self, batch_size=100_000, total_records=1_000_000, 
                 operation_batch=1000, table_seq='seq_pk7', table_uuid='uuid_pk7'):
        """
        Initialize benchmark configuration.
        
        Args:
            batch_size: Batch size for bulk operations
            total_records: Total number of records to insert initially
            operation_batch: Batch size for insert/delete operations during benchmark
            table_seq: Name of sequential PK table
            table_uuid: Name of UUID PK table
        """
        self.batch_size = batch_size
        self.total_records = total_records
        self.operation_batch = operation_batch
        self.table_seq = table_seq
        self.table_uuid = table_uuid
        self.number_of_records_per_page = 430
