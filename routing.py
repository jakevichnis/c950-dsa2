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
    Handles grouped packages that must be delivered together.
    Prioritizes: 9:00 AM -> 10:30 AM -> EOD
    """
    
    def deadline_to_time(deadline_str):
        """Convert deadline string to comparable time value"""
        if deadline_str == "EOD":
            return 999  # EOD has lowest priority
        try:
            time_obj = datetime.strptime(deadline_str, "%I:%M %p")
            return time_obj.hour + (time_obj.minute / 60.0)
        except:
            return 999
    
    def get_package_groups():
        """Define which packages must be delivered together"""
        return [
            [13, 14, 15, 16, 19, 20]  # All must be delivered together
        ]
    
    def find_group_for_package(package_id):
        """Find which group a package belongs to"""
        groups = get_package_groups()
        for group in groups:
            if package_id in group:
                return group
        return [package_id]  # Single package group
    
    def get_eligible_packages():
        """Get all packages that can be delivered now"""
        eligible = []
        for package_id in truck.packages:
            package = hashtable.get(package_id)
            
            if package.status == PackageStatus.DELIVERED:
                continue
            if package.status == PackageStatus.DELAYED:
                continue
            if hasattr(package, 'delayed_until') and package.delayed_until and truck.current_time < package.delayed_until:
                continue
                
            eligible.append(package_id)
        return eligible
    
    eligible_packages = get_eligible_packages()
    if not eligible_packages:
        return None
    
    # Find the package with earliest deadline (considering groups)
    best_package = None
    best_deadline_time = float('inf')
    best_distance = float('inf')
    
    for package_id in eligible_packages:
        package = hashtable.get(package_id)
        deadline_time = deadline_to_time(package.deadline)
        
        # For grouped packages, use the earliest deadline in the group
        group = find_group_for_package(package_id)
        group_earliest_deadline = float('inf')
        
        for group_pkg_id in group:
            if group_pkg_id in truck.packages:
                group_pkg = hashtable.get(group_pkg_id)
                group_deadline_time = deadline_to_time(group_pkg.deadline)
                group_earliest_deadline = min(group_earliest_deadline, group_deadline_time)
        
        distance = get_distance(truck.current_location, package.address, distance_table)
        
        # Select based on earliest group deadline, then distance
        if (group_earliest_deadline < best_deadline_time or 
            (group_earliest_deadline == best_deadline_time and distance < best_distance)):
            best_deadline_time = group_earliest_deadline
            best_distance = distance
            best_package = package_id
    
    return best_package

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

def deliver_package_group(truck, package_id, hashtable, distance_table):
    """
    Deliver a package and any grouped packages that must be delivered together
    """
    def get_package_groups():
        return [[13, 14, 15, 16, 19, 20]]
    
    def find_group_for_package(pkg_id):
        groups = get_package_groups()
        for group in groups:
            if pkg_id in group:
                return group
        return [pkg_id]
    
    group = find_group_for_package(package_id)
    
    # Filter to only packages that are on this truck and not delivered
    deliverable_group = []
    for group_pkg_id in group:
        if group_pkg_id in truck.packages:
            package = hashtable.get(group_pkg_id)
            if package.status != PackageStatus.DELIVERED:
                # Check if delayed packages are ready
                if hasattr(package, 'delayed_until') and package.delayed_until:
                    if truck.current_time >= package.delayed_until:
                        deliverable_group.append(group_pkg_id)
                else:
                    deliverable_group.append(group_pkg_id)
    
    if not deliverable_group:
        return
    
    # Sort by distance to deliver efficiently within the group
    deliverable_group.sort(key=lambda pid: get_distance(truck.current_location, 
                                                       hashtable.get(pid).address, 
                                                       distance_table))
    
    # Deliver all packages in the group
    for group_pkg_id in deliverable_group:
        package = hashtable.get(group_pkg_id)
        
        distance = get_distance(truck.current_location, package.address, distance_table)
        if distance < 0.1:
            distance = 0.1
            
        time_taken = timedelta(hours=distance / truck.speed)
        truck.update_location(package.address, distance, time_taken)
        truck.deliver_package(group_pkg_id, hashtable)
        
        print(f"Truck {truck.truck_id} delivered package {package.package_id} at {truck.current_time.strftime('%I:%M %p')} (group delivery)")

def run_delivery(truck, hashtable, distance_table):
    """
    Modified delivery run that handles grouped packages
    """
    undelivered_packages = [pid for pid in truck.packages 
                           if hashtable.get(pid).status != PackageStatus.DELIVERED]
    
    while len(undelivered_packages) > 0:
        # Select next package considering deadlines and groups
        package_id = select_deadline_package(truck, hashtable, distance_table)
        
        if package_id is None:
            package_id = select_nearest_neighbor(truck, hashtable, distance_table)
        
        if package_id is None:
            break
        
        # Check if this package is part of a group that needs to be delivered together
        def get_package_groups():
            return [[13, 14, 15, 16, 19, 20]]
        
        def find_group_for_package(pkg_id):
            groups = get_package_groups()
            for group in groups:
                if pkg_id in group:
                    return group
            return [pkg_id]
        
        group = find_group_for_package(package_id)
        
        if len(group) > 1:
            # Deliver the entire group
            deliver_package_group(truck, package_id, hashtable, distance_table)
        else:
            # Deliver single package normally
            package = hashtable.get(package_id)
            distance = get_distance(truck.current_location, package.address, distance_table)
            
            if distance < 0.1:
                distance = 0.1
                
            time_taken = timedelta(hours=distance / truck.speed)
            truck.update_location(package.address, distance, time_taken)
            truck.deliver_package(package_id, hashtable)
            
            print(f"Truck {truck.truck_id} delivered package {package.package_id} at {truck.current_time.strftime('%I:%M %p')}")
        
        # Update undelivered packages list
        undelivered_packages = [pid for pid in truck.packages 
                               if hashtable.get(pid).status != PackageStatus.DELIVERED]