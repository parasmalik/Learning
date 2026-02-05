"""
Data generation utilities.
"""
import random
import string


class DataGenerator:
    """Utility class for generating random data."""
    
    @staticmethod
    def rand_payload():
        """Generate random 2-character payload."""
        return ''.join(random.choices(string.ascii_letters, k=2))
    
    @staticmethod
    def rand_pk():
        """Generate random primary key value."""
        return random.randint(0, 9_000_000_000_000_000_000)
    
    @staticmethod
    def generate_sorted_pks_with_payload(count):
        """
        Generate sorted list of random PKs with payloads.
        
        Args:
            count: Number of records to generate
            
        Returns:
            List of tuples (pk, payload) sorted by pk
        """
        records = [
            (DataGenerator.rand_pk(), DataGenerator.rand_payload()) 
            for _ in range(count)
        ]
        return sorted(records, key=lambda x: x[0])
