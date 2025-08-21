

class HashMap:
    def __init__(self):
        self.data = {}
    def add(self, key, value):
        self.data[key] = value
    def get(self, key):
        return self.data.get(key, None)
    def remove(self, key):
        if key in self.data:
            del self.data[key]
    def __str__(self):
        return str(self.data)

