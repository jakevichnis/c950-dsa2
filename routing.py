
from Truck import Truck
from HashTable import HashTable
from DistanceTable import get_distance

# ---------------------------------------------------
#  Core Routing Algorithm (Deadline-First + Nearest Neighbor)
# ---------------------------------------------------

# TODO: implement function to select next package with earliest deadline
def select_deadline_package(truck, hashtable, distance_table):
    """
    Check truck's remaining packages for any with urgent deadlines.
    If multiple, pick the one closest to current truck location.
    Return the selected package.
    """
    pass  # replace with logic

# TODO: implement function to select nearest neighbor package
def select_nearest_neighbor(truck, hashtable, distance_table):
    """
    If no urgent deadline package exists,
    find the package whose address is closest to truck's current location.
    Return that package.
    """
    pass

# TODO: core loop that runs delivery for a single truck
def run_delivery(truck, hashtable, distance_table):
    """
    While truck still has undelivered packages:
        - check deadlines
        - else pick nearest neighbor
        - deliver package
        - update truck mileage, time, and package status
    End when all packages delivered.
    """
    pass

# ---------------------------------------------------
#  Helpers (optional)
# ---------------------------------------------------

# TODO: helper function to calculate distance between two addresses
# def calculate_distance(address1, address2, distance_table):
#     return distance_table.lookup(address1, address2)

# TODO: helper function to update package status + delivery timestamp
# def deliver_package(truck, package, current_time):
#     # mark package as delivered, update time, remove from truck
#     pass

