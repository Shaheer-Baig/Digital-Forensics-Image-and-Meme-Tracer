class Analyzer:
    @staticmethod
    def compare_hashes(hash1, hash2, threshold=10):
        """
        Compares two pHashes. Returns True if they are similar.
        Threshold: Hamming distance tolerance (lower = stricter).
        """
        if hash1 is None or hash2 is None:
            return False
        return (hash1 - hash2) <= threshold

    @staticmethod
    def find_earliest_match(matches):
        """
        Sorts a list of match dictionaries by 'date'.
        Expected format: [{'url': ..., 'date': datetime_obj, ...}, ...]
        """
        # Filter out items with no date
        valid_matches = [m for m in matches if m.get('date')]
        
        # Sort by date (ascending = oldest first)
        sorted_matches = sorted(valid_matches, key=lambda x: x['date'])
        
        return sorted_matches
