
from Package import Package
from datetime import timedelta, datetime

class Truck:

    # Fixing this start location had me debugging for hours :')
    # (originally was "at hub")
    def __init__(self, truck_id, capacity=16, start_location="Western Governors University\n4001 South 700 East, \nSalt Lake City, UT 84107", start_time=0, speed=18):
        
        """
        Initialize a Truck object with:
        - truck_id: unique identifier for the truck
        - capacity: maximum number of packages it can carry (default 16)
        - current_location (starts at hub with correct address)
        - mileage (starts at 0)
        - current_time (track delivery progress)
        - start_time: initial time when the truck starts (default 0)
        """
        self.truck_id = truck_id
        self.capacity = capacity
        
        # FIXED: Use the actual hub address from the distance table
        self.current_location = start_location
        self.mileage = 0
        self.current_time = start_time
        self.speed = speed

        # stores packageIDs
        self.packages = []
    
        # need method to load packages onto truck
    def load_package(self, package_id, hashtable):
        """
        Load a package onto the truck by its ID.
        If truck is at capacity, raise an error.
        """
        
        # exception handling...
        if package_id is None:
            raise ValueError(f"Tried to load None into Truck {self.truck_id}")
        
        if len(self.packages) >= self.capacity:
            raise Exception(f"Truck {self.truck_id} is at full capacity. Cannot load more packages.")
            
        self.packages.append(package_id)
        
        # automatically update the package's status to en_route and record the load time
        # after grabbing the package_id from the hash table
        package = hashtable.get(package_id)
        package.truck_id = self.truck_id
        package.mark_en_route(self.current_time)
        
    def deliver_package(self, package_id, hashtable):
        
        """
        Delivers package from the truck by its ID.
        If the package is not found, it raises an error.
        """
        
        # checks to see if the package_id is in the package list
        if package_id not in self.packages:
            raise Exception(f"Package {package_id} not found on Truck {self.truck_id}. Cannot unload.")
          
        package = hashtable.get(package_id)
        package.mark_delivered(self.current_time)
        self.packages.remove(package_id)
        return package_id
    
    def update_location(self, new_location, distance, time_taken):
        
        """
        Updates the truck's current location, mileage, and time after a delivery.
        """

        self.current_location = new_location
        self.mileage += distance
        # calculate time taken as timedelta based on speed
        time_taken = timedelta(hours=distance / self.speed)
        self.current_time += time_taken
            
    def has_package(self, package_id):
        """
        Check if the truck has a specific package by its ID.
        Returns True if the package is loaded, returns False otherwise.
        """
        return package_id in self.packages