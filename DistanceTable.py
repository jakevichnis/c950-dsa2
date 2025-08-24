


class DistanceTable:
    def __init__(self, addresses, distance_matrix):
        """
        Initialize the DistanceTable with a list of addresses and a 2D list of distances.
        
        :param addresses: List of addresses (strings).
        :param distances: 2D list where distances[i][j] is the distance from address[i] to address[j].
        """
        self.addresses = addresses
        self.distance_matrix = distance_matrix
    
    def get_distance(self, address1, address2):
        """
        Look up the distance between two addresses.
        
        :param address1: The first address (string).
        :param address2: The second address (string).
        :return: Distance between the two addresses.
        """
        if address1 not in self.addresses or address2 not in self.addresses:
            raise ValueError("One or both addresses not found in distance table.")
        
        index1 = self.addresses.index(address1)
        index2 = self.addresses.index(address2)
        
        return self.distance_matrix[index1][index2]

    # had to add this for better usage with my main.py
    def load(self, addresses, distance_matrix):
        self.address = addresses
        self.distance_matrix = distance_matrix


