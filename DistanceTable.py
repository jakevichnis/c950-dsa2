
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
            return "" if s is None else str(s).lower().strip().replace('"', "").replace("\n", " ")

        a1 = norm(address1)
        a2 = norm(address2)

        # try exact matches first
        try:
            i = next(i for i, a in enumerate(self.addresses) if norm(a) == a1)
            j = next(j for j, a in enumerate(self.addresses) if norm(a) == a2)
        except StopIteration:

            # fallback: try substring / token matches
            i = j = None

            for idx, a in enumerate(self.addresses):
                na = norm(a)
                if a1 and (a1 in na or na in a1):
                    i = idx
                    break

            for idx, a in enumerate(self.addresses):
                na = norm(a)
                if a2 and (a2 in na or na in a2):
                    j = idx
                    break

        # if either index still not found, raise KeyError so caller can decide
        if i is None or j is None:
            raise KeyError(f"Address not found in distance table: '{address1}' or '{address2}'")

        # matrix may be triangular or full; try both orders
        try:
            return float(self.distance_matrix[i][j])

        except Exception:

            try:
                return float(self.distance_matrix[j][i])

            except Exception:

                # if both fail, return 0.0 as safe fallback
                return 0.0


# top-level helper function expected by routing.py: get_distance(addr1, addr2, distance_table)
def get_distance(addr1, addr2, distance_table):
    """
    Convenience wrapper so routing.py can `from DistanceTable import get_distance`.
    Delegates to the DistanceTable instance method.
    """
    return distance_table.get_distance(addr1, addr2)