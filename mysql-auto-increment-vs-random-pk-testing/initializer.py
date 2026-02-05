"""
Data initialization for benchmark tables.
"""
from database import DatabaseConnection
from data_generator import DataGenerator


class DataInitializer:
    """Initialize benchmark tables with data."""
    
    def __init__(self, db_config, bench_config):
        """
        Initialize data loader.
        
        Args:
            db_config: DatabaseConfig instance
            bench_config: BenchmarkConfig instance
        """
        self.db_config = db_config
        self.bench_config = bench_config
    
    def initialize_tables(self):
        """
        Initialize both sequential and UUID tables with initial data.
        
        Returns:
            Tuple of (seq_ids, uuid_ids) sets
        """
        print("Initializing tables with data...")
        
        with DatabaseConnection(self.db_config) as db:
            cursor = db.cur
            
            # Generate data for UUID table (sorted)
            print(f"Generating {self.bench_config.total_records} records...")
            sorted_records = DataGenerator.generate_sorted_pks_with_payload(
                self.bench_config.total_records
            )
            
            # Insert into sequential table
            print(f"Inserting into {self.bench_config.table_seq}...")
            for i in range(0, self.bench_config.total_records, self.bench_config.batch_size):
                batch_size = min(
                    self.bench_config.batch_size,
                    self.bench_config.total_records - i
                )
                payloads = [(DataGenerator.rand_payload(),) for _ in range(batch_size)]
                cursor.executemany(
                    f"INSERT INTO {self.bench_config.table_seq} (payload) VALUES (%s)",
                    payloads
                )
                print(f"  seq inserted {i}")
            
            # Insert into UUID table
            print(f"Inserting into {self.bench_config.table_uuid}...")
            for i in range(0, self.bench_config.total_records, self.bench_config.batch_size):
                end = min(i + self.bench_config.batch_size, self.bench_config.total_records)
                records = sorted_records[i:end]
                cursor.executemany(
                    f"INSERT INTO {self.bench_config.table_uuid} (id, payload) VALUES (%s, %s)",
                    records
                )
                print(f"  uuid inserted {i}")
        
        print("Data initialization complete!")
        return self._load_existing_ids()
    
    def _load_existing_ids(self):
        """
        Load existing IDs from both tables.
        
        Returns:
            Tuple of (seq_ids, uuid_ids) sets
        """
        print("Loading existing IDs...")
        
        with DatabaseConnection(self.db_config) as db:
            cursor = db.cur
            
            # Get UUID table IDs
            cursor.execute(f'SELECT id FROM {self.bench_config.table_uuid}')
            uuid_results = cursor.fetchall()
            uuid_ids = set([row[0] for row in uuid_results])
            
            # Get sequential table IDs
            cursor.execute(f'SELECT id FROM {self.bench_config.table_seq}')
            seq_results = cursor.fetchall()
            seq_ids = set([row[0] for row in seq_results])
        
        print(f"Loaded {len(seq_ids)} seq IDs and {len(uuid_ids)} uuid IDs")
        return seq_ids, uuid_ids
