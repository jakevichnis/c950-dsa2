

class HashMap:
    def __init__(self):

        self.data = {}

    def add(self, key, value):

        """Add a key-value pair to the hashmap."""
        if key in self.data:

            raise KeyError(f"Key '{key}' already exists.")

        self.data[key] = value

    def get(self, key):

        """Retrieve the value associated with the given key."""
        if key not in self.data:

            raise KeyError(f"Key '{key}' does not exist.")

        return self.data.get(key, None)

    def remove(self, key):

        """Remove the key-value pair associated with the given key."""
        if key not in self.data:

            raise KeyError(f"Key '{key}' does not exist.")
        # Only remove the key if it exists
        # This is to prevent KeyError if the key does not exist

        if key in self.data:

            del self.data[key]

    def __str__(self):
        """Return a string representation of the HashMap."""
        
        return str(self.data)

