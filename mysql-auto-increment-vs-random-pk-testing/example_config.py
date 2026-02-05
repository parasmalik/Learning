"""
Example configuration file showing how to customize the benchmark.

Copy this file and modify as needed, then import in your own script.
"""
from config import DatabaseConfig, BenchmarkConfig
from initializer import DataInitializer
from benchmark import BenchmarkRunner
from logger import BenchmarkLogger


# Custom database configuration
db_config = DatabaseConfig(
    host='localhost',
    user='your_username',
    password='your_password',
    database='your_database'
)

# Custom benchmark configuration
bench_config = BenchmarkConfig(
    batch_size=50_000,          # Smaller batches for limited memory
    total_records=500_000,      # Fewer initial records for faster setup
    operation_batch=500,        # Smaller operation batches
    table_seq='my_seq_table',
    table_uuid='my_uuid_table'
)

# Run the benchmark
if __name__ == '__main__':
    # Initialize data
    initializer = DataInitializer(db_config, bench_config)
    seq_ids, uuid_ids = initializer.initialize_tables()
    
    # Run benchmark
    with BenchmarkLogger('custom_results.csv') as logger:
        runner = BenchmarkRunner(db_config, bench_config, logger)
        runner.run(seq_ids, uuid_ids)
