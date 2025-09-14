class DistanceTable:

    # allow empty construction so main.py can do DistanceTable()
    def __init__(self, addresses=None, distance_matrix=None):

        # list of address strings
        self.addresses = addresses or []

        # 2D matrix of distances (list of lists)
        self.distance_matrix = distance_matrix or []
    
    # simple load helper used by main.py
    def load(self, addresses, distance_matrix):

        # store addresses and matrix with correct attribute names
        self.addresses = addresses
        self.distance_matrix = distance_matrix
    
    # instance method to get distance between two addresses (robust-ish)
    def get_distance(self, address1, address2):

        # small normalizer for address strings
        def norm(s):
            if s is None:
                return ""

            # more aggressive normalization to handle format differences
            s = str(s).lower().strip().replace('"', "").replace("\n", " ")

            # remove extra whitespace
            s = ' '.join(s.split())

            return s
        
        def extract_street_address(addr):
            """extract just the street address part from full address"""

            normalized = norm(addr)

            # look for street address patterns like "4580 s 2300 e"

            parts = normalized.split()
            street_parts = []
            for part in parts:

                # keep parts that look like addresses (numbers, directions, street types)
                if any(char.isdigit() for char in part) or part in ['s', 'n', 'e', 'w', 'south', 'north', 'east', 'west', 'st', 'ave', 'blvd', 'rd', 'station', 'loop']:
                    street_parts.append(part)

            return ' '.join(street_parts)
        
        a1 = norm(address1)
        a2 = norm(address2)
        a1_street = extract_street_address(address1)
        a2_street = extract_street_address(address2)
        
        # try exact matches first
        i = j = None

        for idx, a in enumerate(self.addresses):
            if norm(a) == a1:
                i = idx
                break
        for idx, a in enumerate(self.addresses):
            if norm(a) == a2:
                j = idx
                break
        
        # fallback: try street address matching
        if i is None and a1_street:
            for idx, a in enumerate(self.addresses):

                addr_street = extract_street_address(a)
                if addr_street and a1_street in addr_street:
                    i = idx

                    break
        
        if j is None and a2_street:
            for idx, a in enumerate(self.addresses):

                addr_street = extract_street_address(a)

                if addr_street and a2_street in addr_street:
                    j = idx
                    break
        
        # final fallback: substring matching
        if i is None:
            for idx, a in enumerate(self.addresses):
                na = norm(a)
                if a1 and (a1 in na or na in a1):
                    i = idx
                    break
        
        if j is None:
            for idx, a in enumerate(self.addresses):
                na = norm(a)
                if a2 and (a2 in na or na in a2):
                    j = idx
                    break
        
        # if either index still not found, return reasonable default instead of crashing
        if i is None or j is None:
            print(f"Distance: 2.0 (default - no match found)")
            return 2.0
        
        # Handle same location
        if i == j:
            print(f"Distance: 0.0 (same location)")
            return 0.0
        
        # For lower triangular matrix: larger index is row, smaller is column
        row = max(i, j)
        col = min(i, j)
        
        try:
            if row < len(self.distance_matrix) and col < len(self.distance_matrix[row]):
                distance = float(self.distance_matrix[row][col])
                print(f"Distance: {distance}")
                return distance
        except (IndexError, ValueError):
            pass
        
        # Fallback
        print(f"Distance: 2.0 (default - matrix error)")
        return 2.0


# top-level helper function expected by routing.py: get_distance(addr1, addr2, distance_table)
def get_distance(addr1, addr2, distance_table):
    """
    Convenience wrapper so routing.py can `from DistanceTable import get_distance`.
    Delegates to the DistanceTable instance method.
    """
    return distance_table.get_distance(addr1, addr2)