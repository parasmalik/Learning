"""
Database statistics collection.
"""


class DatabaseStats:
    """Collect database statistics and metrics."""
    
    def __init__(self, cursor, config):
        """
        Initialize stats collector.
        
        Args:
            cursor: Database cursor
            config: BenchmarkConfig instance
        """
        self.cursor = cursor
        self.config = config
    
    def get_buffer_stats(self):
        """
        Get InnoDB buffer pool statistics.
        
        Returns:
            Dictionary with buffer stats
        """
        query = """
            SELECT 
                VARIABLE_NAME, 
                VARIABLE_VALUE 
            FROM performance_schema.global_status 
            WHERE VARIABLE_NAME IN (
                'Innodb_buffer_pool_reads',
                'Innodb_buffer_pool_read_requests',
                'Innodb_pages_read'
            )
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        stats = {row[0]: int(row[1]) for row in results}
        
        total_reads = stats.get('Innodb_buffer_pool_read_requests', 0)
        disk_reads = stats.get('Innodb_buffer_pool_reads', 0)
        cache_hits = total_reads - disk_reads
        cache_hit_rate = (cache_hits / total_reads * 100) if total_reads > 0 else 0
        pages_from_disk = stats.get('Innodb_pages_read', 0)
        
        return {
            'total_reads': total_reads,
            'disk_reads': disk_reads,
            'cache_hits': cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'pages_from_disk': pages_from_disk
        }
    
    @staticmethod
    def get_buffer_stats_diff(before, after):
        """
        Calculate difference in buffer stats.
        
        Args:
            before: Stats dictionary before operation
            after: Stats dictionary after operation
            
        Returns:
            Dictionary with stat differences
        """
        diff = {}
        for key in before.keys():
            if key == 'cache_hit_rate':
                # Recalculate cache hit rate
                total = after['total_reads'] - before['total_reads']
                disk = after['disk_reads'] - before['disk_reads']
                hits = total - disk
                diff[key] = (hits / total * 100) if total > 0 else 0
            else:
                diff[key] = after[key] - before[key]
        return diff
    
    def splits(self):
        """
        Get number of B-tree splits.
        
        Returns:
            Number of splits
        """
        query = """
            SELECT count 
            FROM information_schema.innodb_metrics 
            WHERE name = 'index_page_splits'
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def index_stats(self, table_name):
        """
        Get index statistics for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with index stats
        """
        query = f"""
            SELECT 
                stat_name, 
                stat_value 
            FROM mysql.innodb_index_stats 
            WHERE table_name = '{table_name}' 
                AND index_name = 'PRIMARY'
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        stats = {row[0]: row[1] for row in results}
        
        return {
            'n_leaf_pages': stats.get('n_leaf_pages', 0),
            'size': stats.get('size', 0)
        }
    
    def get_page_buffer(self, table_name):
        """
        Get buffer pool page information for a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with page buffer info
        """
        query = f"""
            SELECT 
                COUNT(*) as pages_in_buffer,
                SUM(data_size)/1024/1024 as buffer_mb,
                SUM(CASE WHEN access_time > 0 THEN 1 ELSE 0 END) as hot_pages
            FROM information_schema.innodb_buffer_page
            WHERE table_name = '{table_name}'
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        
        if result:
            return {
                'pages_in_buffer': result[0] or 0,
                'buffer_mb': float(result[1] or 0),
                'hot_pages': result[2] or 0
            }
        return {'pages_in_buffer': 0, 'buffer_mb': 0.0, 'hot_pages': 0}
    
    def get_table_info(self, table_name):
        """
        Get table information including size.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table info
        """
        # First analyze the table
        self.cursor.execute(f'ANALYZE TABLE {table_name}')
        self.cursor.fetchall()
        
        # Get table size
        query = f"""
            SELECT 
                table_name, 
                data_length / 1024 / 1024 AS data_mb, 
                index_length / 1024 / 1024 AS index_mb 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
                AND table_name = '{table_name}'
        """
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        
        # Get row count
        self.cursor.execute(f"SELECT COUNT(1) FROM {table_name}")
        count = self.cursor.fetchone()[0]
        
        # Get merged pages
        query = """
            SELECT count 
            FROM information_schema.innodb_metrics 
            WHERE name LIKE '%index_page_merge_successful%'
        """
        self.cursor.execute(query)
        merged_pages = self.cursor.fetchone()[0]
        
        return {
            'data_mb': float(result[1]) if result else 0,
            'count': count,
            'merged_pages': merged_pages
        }
