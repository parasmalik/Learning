"""
Main entry point for MySQL Primary Key Benchmark.

This script benchmarks the performance difference between sequential and UUID primary keys
in MySQL InnoDB tables under concurrent insert/delete workloads.
"""
import argparse
from config import DatabaseConfig, BenchmarkConfig
from initializer import DataInitializer
from benchmark import BenchmarkRunner
from logger import BenchmarkLogger


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Benchmark MySQL sequential vs UUID primary key performance'
    )
    
    # Database connection arguments
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--user', default='paras.mal', help='Database user')
    parser.add_argument('--password', default='password', help='Database password')
    parser.add_argument('--database', default='test', help='Database name')
    
    # Benchmark configuration
    parser.add_argument('--batch-size', type=int, default=100_000,
                       help='Batch size for initial load')
    parser.add_argument('--total-records', type=int, default=1_000_000,
                       help='Total records to insert initially')
    parser.add_argument('--operation-batch', type=int, default=1000,
                       help='Batch size for insert/delete operations')
    parser.add_argument('--table-seq', default='seq_pk7',
                       help='Name of sequential PK table')
    parser.add_argument('--table-uuid', default='uuid_pk7',
                       help='Name of UUID PK table')
    
    # Output configuration
    parser.add_argument('--output', default='benchmark_results.csv',
                       help='Output CSV filename')
    
    # Execution mode
    parser.add_argument('--skip-init', action='store_true',
                       help='Skip data initialization (use existing data)')
    parser.add_argument('--init-only', action='store_true',
                       help='Only initialize data, do not run benchmark')
    
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    
    # Create configurations
    db_config = DatabaseConfig(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database
    )
    
    bench_config = BenchmarkConfig(
        batch_size=args.batch_size,
        total_records=args.total_records,
        operation_batch=args.operation_batch,
        table_seq=args.table_seq,
        table_uuid=args.table_uuid
    )
    
    # Initialize data or load existing
    initializer = DataInitializer(db_config, bench_config)
    
    if args.skip_init:
        print("Skipping data initialization, loading existing IDs...")
        seq_ids, uuid_ids = initializer._load_existing_ids()
    else:
        seq_ids, uuid_ids = initializer.initialize_tables()
    
    if args.init_only:
        print("Initialization complete. Exiting (--init-only specified).")
        return
    
    # Run benchmark
    with BenchmarkLogger(args.output) as logger:
        runner = BenchmarkRunner(db_config, bench_config, logger)
        runner.run(seq_ids, uuid_ids)


if __name__ == '__main__':
    main()
