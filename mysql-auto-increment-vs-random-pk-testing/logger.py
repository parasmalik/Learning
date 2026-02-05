"""
Logging functionality for benchmark results.
"""
import csv


class BenchmarkLogger:
    """Logger for benchmark results."""
    
    DISK_COLUMNS = ['total_reads', 'disk_reads', 'cache_hits', 'cache_hit_rate', 'pages_from_disk']
    MEM_COLUMNS = ['pages_in_buffer', 'buffer_mb', 'hot_pages']
    TIME_COLUMNS = ['insert_time', 'delete_time']
    BASE_COLUMNS = [
        'table_name', 'data_mb', 'counter', 'op_count', 'pages_merged', 
        'splits', 'estimated_new_pages', 'leaf_index_pages', 'total_index_pages'
    ]
    
    def __init__(self, filename):
        """
        Initialize logger.
        
        Args:
            filename: Output CSV filename
        """
        self.filename = filename
        self.log_file = None
        self.writer = None
        self.logs = []
    
    def open(self):
        """Open log file and write header."""
        self.log_file = open(self.filename, mode='a', newline='')
        self.writer = csv.writer(self.log_file)
        
        # Write header
        columns = (
            self.BASE_COLUMNS + 
            self.TIME_COLUMNS + 
            self.DISK_COLUMNS + 
            [f"i{col}" for col in self.DISK_COLUMNS] +
            [f"d{col}" for col in self.DISK_COLUMNS] +
            self.MEM_COLUMNS
        )
        self.writer.writerow(columns)
    
    def log_event(self, data):
        """
        Log a single event.
        
        Args:
            data: List of data values to log
        """
        self.writer.writerow(data)
        self.log_file.flush()
        self.logs.append(data)
    
    def close(self):
        """Close log file."""
        if self.log_file:
            self.log_file.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
