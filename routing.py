
import Package
from datetime import timedelta, datetime
from Truck import Truck
from HashTable import HashTable
from DistanceTable import get_distance
import csv

# ---------------------------------------------------
#  Core Routing Algorithm (Deadline-First Greedy + Nearest Neighbor)
# ---------------------------------------------------

# implement function to select next package with earliest deadline
def select_deadline_package(truck, hashtable, distance_table):
    """
    Check truck's remaining packages for any with urgent deadlines.
    If multiple, pick the one closest to current truck location.
    Return the selected package.
    """

    # creating a group list for the constraint of having those packages together
    grouped = []
    
    # for loop iterating through each package on truck
    for package_id in truck.packages:
        
        # hashtable of truck.packages, earliest deadline of = "at hub"
        package = hashtable.get(package_id)
        
        # skip the package if already delivered
        if package.status in (PackageStatus.DELIVERED, PackageStatus.EN_ROUTE):
            continue 

        # skip the package if it's delayed
        if package.delayed_until and truck.current_time < package.delayed_until:
            continue
        
        # add package to 
        if package.group_constrained:
            grouped.append(package)

    # if package must be delivered with a group (six together rule) and the truck cannot
    # deliver entire group in sequence (group members not on board or some are ineligible),
    # this package status = ineligible for this pass and
    #    continue

        # if multiple, while loop greedy for package closest to truck current_location

        # return in distance order package_id
    return     

    

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

