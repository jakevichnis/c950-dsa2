# routing.py - FIXED VERSION

import Package
from Package import PackageStatus
from datetime import timedelta, datetime
from Truck import Truck
from HashTable import HashTable
from DistanceTable import get_distance
import csv

# ---------------------------------------------------
#  Core Routing Algorithm (Deadline-First Greedy + Nearest Neighbor)
# ---------------------------------------------------

def select_deadline_package(truck, hashtable, distance_table):
    """
    Check truck's remaining packages for any urgent deadlines.
    If multiple, pick the one closest to current truck location.
    Return the selected package.
    """

    earliest_package = None
    earliest_deadline = None

    # for loop iterating through each package on truck
    for package_id in truck.packages:
        # hashtable of truck.packages
        package = hashtable.get(package_id)

        # FIXED: Only skip if already delivered (allow EN_ROUTE packages)
        if package.status == PackageStatus.DELIVERED:
            continue

        # FIXED: Add safe checks for constraint attributes
        if hasattr(package, 'delayed_until') and package.delayed_until and truck.current_time < package.delayed_until:
            continue

        # selection process: pick earliest deadline
        if earliest_deadline is None or package.deadline < earliest_deadline:
            earliest_deadline = package.deadline
            earliest_package = package

    # fallback: if no package with deadline found, pick first eligible package
    if earliest_package:
        return earliest_package.package_id
    else:
        for package_id in truck.packages:
            package = hashtable.get(package_id)
            if package.status != PackageStatus.DELIVERED:
                # FIXED: Safe check for delayed_until
                if hasattr(package, 'delayed_until') and package.delayed_until:
                    if truck.current_time >= package.delayed_until:
                        return package.package_id
                else:
                    return package.package_id
        return None

def select_nearest_neighbor(truck, hashtable, distance_table):
    """
    If no urgent deadline package exists,
    find the package whose address is closest to truck's current location.
    Return that package.
    """
    nearest_package = None
    shortest_distance = float('inf')

    for package_id in truck.packages:
        # hashtable of truck.packages
        package = hashtable.get(package_id)

        # FIXED: Only skip if already delivered
        if package.status == PackageStatus.DELIVERED:
            continue

        # FIXED: Safe check for delayed_until
        if hasattr(package, 'delayed_until') and package.delayed_until and truck.current_time < package.delayed_until:
            continue

        # the heart of the greedy algorithm- pick the closest package
        distance_to_package = get_distance(truck.current_location, package.address, distance_table)

        # if there's a new shorter distance, reset location direction to this
        if distance_to_package < shortest_distance:
            shortest_distance = distance_to_package
            nearest_package = package

    # fallback: pick first eligible package if all distances were skipped
    if nearest_package:
        return nearest_package.package_id
    else:
        for package_id in truck.packages:
            package = hashtable.get(package_id)
            if package.status != PackageStatus.DELIVERED:
                # FIXED: Safe check for delayed_until
                if hasattr(package, 'delayed_until') and package.delayed_until:
                    if truck.current_time >= package.delayed_until:
                        return package.package_id
                else:
                    return package.package_id
        return None

def run_delivery(truck, hashtable, distance_table):
    """
    While truck still has undelivered packages:
        - check deadlines
        - else pick nearest neighbor
        - deliver package
        - update truck mileage, time, and package status
    End when all packages delivered.
    """
    
    # FIXED: Check for undelivered packages instead of just package count
    undelivered_packages = [pid for pid in truck.packages 
                           if hashtable.get(pid).status != PackageStatus.DELIVERED]
    
    while len(undelivered_packages) > 0:
        package_id = select_deadline_package(truck, hashtable, distance_table)
        if package_id is None:
            package_id = select_nearest_neighbor(truck, hashtable, distance_table)
        
        if package_id is None:
            # safety check - no more deliverable packages
            break

        # retrieves package object from hashtable
        package = hashtable.get(package_id)
        
        # travel logistics of how the distance is proportional to where the truck is
        distance = get_distance(truck.current_location, package.address, distance_table)
        print(f"DEBUG: From '{truck.current_location}' to '{package.address}' = {distance} miles")
        print(f"DEBUG: Available addresses in distance table: {distance_table.addresses[:5]}...")  # show first 5
        time_taken = timedelta(hours = distance / truck.speed)

        # logging the actual process of delivering the package, first by truck then by package
        truck.update_location(package.address, distance, time_taken)
        
        # calling the deliver package method from our truck class
        truck.deliver_package(package_id, hashtable)

        print(f"Truck {truck.truck_id} delivered package {package.package_id} at {truck.current_time.strftime('%I:%M %p')}")
        
        # FIXED: Update undelivered packages list
        undelivered_packages = [pid for pid in truck.packages 
                               if hashtable.get(pid).status != PackageStatus.DELIVERED]
        
        
        