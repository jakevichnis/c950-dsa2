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

    # insert method to add a key-value pair to the hash table
    # - use _hash to find the bucket index
    # - check if the key already exists in the bucket
    # - else, append the key-value pair to the bucket

    def insert(self, key, value):

        """Add a key-value pair to the hashmap."""
        if key in self.data:

            raise KeyError(f"Key '{key}' already exists.")

        self.data[key] = value

        # redundant, please decide!!
    def insert(self, key, value):
        """Insert a key-value pair into the hash table."""
        index = self._hash(key)
        bucket = self.table[index]
        # Check if the key already exists in the bucket
        for i, (k, v) in enumerate(bucket):
            if k == key:
                # If it exists, update the value
                bucket[i] = (key, value)
                return
    # 
    # 
    # 
    # 
    # TODO: Write a get(self, key) method to retrieve a value by its key
    # use _hash to find the bucket index
    # search the bucket for the key
    # return the value if found, else return None
    # 


    def get(self, key):

        """Retrieve the value associated with the given key."""
        # If the key does not exist, return none
        if key not in self.data:
            bucket.append(key, value)
            # FIX FIX FIX
        return self.data.get(key, None)

    
        
        




    # TODO: Write a remove(self, key) method to remove a key-value pair from the hash table
    # use _hash to find the bucket index
    # search the bucket for the key (and delete it if found)
    # 
    # 

    def remove(self, key):

        """Remove the key-value pair associated with the given key."""
        if key not in self.data:

            raise KeyError(f"Key '{key}' does not exist.")
        # Only remove the key if it exists
        # This is to prevent KeyError if the key does not exist

        if key in self.data:

            del self.data[key]



    # TODO: Write a __str__(self) method to return a string representation for debugging
    # Loop through buckets and print contents in a readable way    

    def __str__(self):
        """Return a string representation of the HashMap."""
        
        return str(self.data)


