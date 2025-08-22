# This class will implement a simple hash table with basic operations
class HashTable:
    
    # Set size to 40 because that's how many packages we have in the project
    def __init__(self, size=40):

        # Initialize the hash table with a specified size
        self.size = size

        # list of empty lists
        self.table = [[] for _ in range(40)]  
       
    # hash function to get keys for indices in the table
    def _hash(self, key):
        """Private method to compute the hash value for a given key."""

        # modulo to map a key (like package_id) to a bucket index
        return key % self.size

        




