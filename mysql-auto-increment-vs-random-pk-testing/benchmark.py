"""
Main benchmark runner.
"""
import time
import mysql.connector
from database import DatabaseConnection
from operations import DatabaseOperations
from stats import DatabaseStats
from logger import BenchmarkLogger


class BenchmarkRunner:
    """Run database benchmarks."""
    
    def __init__(self, db_config, bench_config, logger):
        """
        Initialize benchmark runner.
        
        Args:
            db_config: DatabaseConfig instance
            bench_config: BenchmarkConfig instance
            logger: BenchmarkLogger instance
        """
        self.db_config = db_config
        self.bench_config = bench_config
        self.logger = logger
    
    def log_metrics(self, table_name, initial_merged_pages, initial_splits, 
                   initial_disk_stats, insert_disk_stats, delete_disk_stats, times):
        """
        Log metrics for a benchmark run.
        
        Args:
            table_name: Name of the table
            initial_merged_pages: Initial merged pages count
            initial_splits: Initial splits count
            initial_disk_stats: Initial disk statistics
            insert_disk_stats: Disk stats during insert
            delete_disk_stats: Disk stats during delete
            times: Tuple of (op_count, insert_time, delete_time)
        """
        # Create new connection for stats collection
        conn = mysql.connector.connect(**self.db_config.to_dict())
        cursor = conn.cursor()
        
        try:
            stats = DatabaseStats(cursor, self.bench_config)
            
            # Get current table info
            table_info = stats.get_table_info(table_name)
            
            # Get current splits and index stats
            current_splits = stats.splits()
            index_info = stats.index_stats(table_name)
            
            # Get buffer stats
            current_disk_stats = stats.get_buffer_stats()
            disk_stats_diff = DatabaseStats.get_buffer_stats_diff(initial_disk_stats, current_disk_stats)
            page_buffer = stats.get_page_buffer(table_name)
            
            # Calculate estimated new pages
            estimated_new_pages = int(
                (times[0] - self.bench_config.total_records) / 
                self.bench_config.number_of_records_per_page
            )
            
            # Build row data
            row = [
                table_name,
                table_info['data_mb'],
                table_info['count'],
                times[0],
                table_info['merged_pages'] - initial_merged_pages,
                current_splits - initial_splits,
                estimated_new_pages,
                index_info['n_leaf_pages'],
                index_info['size'],
                times[1],
                times[2]
            ]
            
            # Add disk statistics
            row.extend([disk_stats_diff[col] for col in BenchmarkLogger.DISK_COLUMNS])
            row.extend([insert_disk_stats[col] for col in BenchmarkLogger.DISK_COLUMNS])
            row.extend([delete_disk_stats[col] for col in BenchmarkLogger.DISK_COLUMNS])
            row.extend([page_buffer[col] for col in BenchmarkLogger.MEM_COLUMNS])
            
            self.logger.log_event(row)
            
        finally:
            cursor.close()
            conn.close()
    
    def run_table_benchmark(self, table_name, values, is_uuid=False):
        """
        Run benchmark for a specific table.
        
        Args:
            table_name: Name of the table to benchmark
            values: Set of IDs in the table
            is_uuid: Whether this is a UUID table
        """
        print(f"\nRunning benchmark for {table_name}")
        
        with DatabaseConnection(self.db_config) as db:
            cursor = db.cur
            stats = DatabaseStats(cursor, self.bench_config)
            ops = DatabaseOperations(cursor, self.bench_config)
            
            # Get initial metrics
            initial_table_info = stats.get_table_info(table_name)
            initial_merged_pages = initial_table_info['merged_pages']
            initial_splits = stats.splits()
            initial_disk_stats = stats.get_buffer_stats()
            
            counter = self.bench_config.total_records + 1
            op_count = counter
            
            # Run benchmark loop
            iterations = 1000  # Number of insert/delete cycles
            for i in range(iterations):
                # Measure insert
                insert_start_disk = stats.get_buffer_stats()
                insert_start = time.perf_counter()
                
                if is_uuid:
                    ops.insert_uuid(values)
                else:
                    counter = ops.insert_seq(values, counter)
                
                insert_time = time.perf_counter() - insert_start
                insert_disk_stats = DatabaseStats.get_buffer_stats_diff(
                    insert_start_disk, stats.get_buffer_stats()
                )
                
                # Measure delete
                delete_start_disk = stats.get_buffer_stats()
                delete_start = time.perf_counter()
                
                if is_uuid:
                    ops.delete_uuid(values)
                else:
                    ops.delete_seq(values)
                
                delete_time = time.perf_counter() - delete_start
                delete_disk_stats = DatabaseStats.get_buffer_stats_diff(
                    delete_start_disk, stats.get_buffer_stats()
                )
                
                op_count += self.bench_config.operation_batch
                
                # Log every iteration
                if (i + 1) % 1 == 0:
                    times = (op_count, insert_time, delete_time)
                    self.log_metrics(
                        table_name, initial_merged_pages, initial_splits,
                        initial_disk_stats, insert_disk_stats, delete_disk_stats, times
                    )
                    
                    if (i + 1) % 100 == 0:
                        print(f"{table_name}: {i + 1}/{iterations} iterations completed")
                        print(f"  Data size: {initial_table_info['data_mb']:.2f} MB")
                        print(f"  Record count: {initial_table_info['count']}")
                        print(f"  Ops: {op_count}")
                        print(f"  Insert time: {insert_time:.4f}s, Delete time: {delete_time:.4f}s")
        
        print(f"\nCompleted benchmark for {table_name}")
    
    def run(self, seq_values, uuid_values):
        """
        Run benchmarks for both tables.
        
        Args:
            seq_values: Set of IDs in sequential table
            uuid_values: Set of IDs in UUID table
        """
        print("Starting benchmarks...")
        
        # Run sequential table benchmark
        self.run_table_benchmark(self.bench_config.table_seq, seq_values, is_uuid=False)
        
        # Run UUID table benchmark
        self.run_table_benchmark(self.bench_config.table_uuid, uuid_values, is_uuid=True)
        
        print("\nBenchmarks completed!")
        print(f"Results logged to: {self.logger.filename}")
        print(f"Total log entries: {len(self.logger.logs)}")
