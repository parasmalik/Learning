"""
Database operations for insert/delete.
"""
import json
import random
import threading
from data_generator import DataGenerator


class DatabaseOperations:
    """Handle database insert and delete operations."""
    
    def __init__(self, cursor, config):
        """
        Initialize database operations.
        
        Args:
            cursor: Database cursor
            config: BenchmarkConfig instance
        """
        self.cursor = cursor
        self.config = config
        self.counter_lock = threading.Lock()
    
    def insert_seq(self, values, counter):
        """
        Insert records into sequential PK table.
        
        Args:
            values: Set to track inserted IDs
            counter: Current counter value
            
        Returns:
            Updated counter value
        """
        batch_size = self.config.operation_batch
        payloads = [(DataGenerator.rand_payload(),) for _ in range(batch_size)]
        
        self.cursor.executemany(
            f"INSERT INTO {self.config.table_seq} (payload) VALUES (%s)",
            payloads
        )
        
        values.update([counter + i for i in range(batch_size)])
        return counter + batch_size
    
    def insert_uuid(self, values):
        """
        Insert records into UUID PK table.
        
        Args:
            values: Set to track inserted IDs
        """
        batch_size = self.config.operation_batch
        records = [
            {'id': DataGenerator.rand_pk(), 'p': DataGenerator.rand_payload()} 
            for _ in range(batch_size)
        ]
        
        self.cursor.callproc("insert_rows_json2", [self.config.table_uuid, json.dumps(records)])
        values.update([rec['id'] for rec in records])
    
    def delete_seq(self, values):
        """
        Delete records from sequential PK table.
        
        Args:
            values: Set of IDs to delete from
        """
        batch_size = self.config.operation_batch
        
        with self.counter_lock:
            records = random.sample(values, batch_size)
            values.difference_update(records)
        
        records = sorted(records)
        self.cursor.callproc("delete_by_ids_json", [self.config.table_seq, json.dumps(records)])
    
    def delete_uuid(self, values):
        """
        Delete records from UUID PK table.
        
        Args:
            values: Set of IDs to delete from
        """
        batch_size = self.config.operation_batch
        
        with self.counter_lock:
            records = random.sample(values, batch_size)
            values.difference_update(records)
        
        records = sorted(records)
        self.cursor.callproc("delete_by_ids_json", [self.config.table_uuid, json.dumps(records)])
