class Truck:
    def __init__(self, truck_id, capacity=16, start_location="At Hub", start_time=0, speed=18):

        """
        Initialize a Truck object with:
        - truck_id: unique identifier for the truck
        - capacity: maximum number of packages it can carry (default 16)
        - current_location (starts at hub)
        - mileage (starts at 0)
        - current_time (track delivery progress)
        - start_time: initial time when the truck starts (default 0)
        """

        self.truck_id = truck_id
        self.capacity = capacity
        self.current_location = start_location
        self.mileage = 0
        self.current_time = start_time
        self.speed = speed

        # stores packageIDs
        self.packages = []
    
        # need method to load packages onto truck
    def load_package(self, package_id):
        """
        Load a package onto the truck by its ID.
        If truck is at capacity, raise an error.
        """
        if len(self.packages) >= self.capacity:
            raise Exception(f"Truck {self.truck_id} is at full capacity. Cannot load more packages.")
            
        self.packages.append(package_id)
        


    # method to unload packages from the truck
    def deliver_package(self, package_id):
        """
        Delivers package from the truck by its ID.
        If the package is not found, it raises an error.
        """

        # checks to see if the package_id is in the package list
        if package_id not in self.packages:
            raise Exception(f"Package {package_id} not found on Truck {self.truck_id}. Cannot unload.")
            
        self.packages.remove(package_id)
        return package_id



    # method to time track the truck's delivery progress
    def update_location(self, new_location, distance, time_taken):
        """
        Updates the truck's current location, mileage, and time after a delivery.
        """
        self.current_location = new_location
        self.mileage += distance

        # added this for further functionality to calculate time taken based on distance and speed
        time_taken = distance / self.speed

        self.current_time += time_taken
        
            

    # method to check to see if a package is loaded onto the truck    
    def has_package(self, package_id):
        """
        Check if the truck has a specific package by its ID.
        Returns True if the package is loaded, returns False otherwise.
        """
        return package_id in self.packages
            


