# This class will implement a simple hash table with basic operations
class HashTable:
    
    # Set size to 40 because that's how many packages we have in the project
    # thoughts on making this size dynamic later?
    def __init__(self, size = 40):

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
    def insert(self, key, value):
       
        # - check if the key already exists in the bucket
        """Add a key-value pair to the hashmap."""
        if key in self.table:

            # if it exists, update the value
            self.table[key] = value

        # - else, append the key-value pair to the bucket
        else:

            # - if it does not exist, append the key-value pair to the bucket
            index = self._hash(key)
            bucket = self.table[index]

            # check if the key already exists in the bucket
            for i, (k, v) in enumerate(bucket):
                if k == key:

                    # if it exists, update the value
                    bucket[i] = (key, value)
                    return

            # if the key does not exist, append the new key-value pair
            bucket.append((key, value))
        
        


    def get(self, key):

        """Retrieve the value associated with the given key."""
        
        # - if key in self.data:

        # use _hash to find the bucket index
        index = self._hash(key)

        # search the bucket for the key
        bucket = self.table[index]

        # return the value if found, else return None
        for k, v in bucket:
            if k == key:

                    # if it exists,
                return v
        
            # else, return None
            
        return None

    

    def remove(self, key):

        """Remove the key-value pair associated with the given key."""
        # - if key in self.data:

        # use _hash to find the bucket index
        index = self._hash(key)

        # search the bucket for the key
        bucket = self.table[index]

        # return the value if found, else return None
        for i, (k, v) in enumerate(bucket):
            if k == key:

                # if it exists, delete the key-value pair 
                del bucket[i]
                return True
       
            # else, not found
            return False




    # # Loop through buckets and print contents in a readable way    

    def __str__(self):
         """Return a string representation of the HashMap."""
        
         return str(self.data)


