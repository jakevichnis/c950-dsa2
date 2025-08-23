# for status. I decided to have it as an enum so it could be more dynamic and cycle through
from enum import Enum
from datetime import datetime


class PackageStatus(Enum):
        AT_HUB = "At Hub"
        EN_ROUTE = "En Route"
        DELIVERED = "Delivered"
        DELAYED = "DELAYED"


# This is the package class for the project
class Package:

    # intit method for the parameters of the package class
    def __init__(self, package_id, address, weight, city, zip_code, deadline, status=PackageStatus.AT_HUB, notes=None):
        self.id = package_id
        self.address = address
        self.weight = weight
        self.city = city
        self.zip_code = zip_code
        self.deadline = deadline
        self.status = PackageStatus.AT_HUB # type: ignore

        self.notes = notes

        # Default value for it landing in the grouped list
        self.group_constrained = False

        # This will be used to track the delivery time of the package (updated later)
        self.delivery_time = None
        
        # store IDs of packages we have to group together
        self.group_ids = set()
        
        # I decided to personally add this as I thought it'd be fun to possibly see
        # when a package was first being loaded. I initially had the idea 
        # to do the enum because the idea of manually having all the statuses change via code 
        # i thought could have become more automatic. Also who doesn't love seeing when their 
        # amazon package gets loaded to start its journey, right?
        
        self.load_time = None



    def mark_delivered(self, current_time: datetime):
        """
        Marking the package as delivered at the give time.
        Automatically updates status and delivery_time.
        """
        
        self.status = PackageStatus.DELIVERED
        
        # Format time as HH:MM AM/PM
        self.delivery_time = current_time.strftime("%I:%M %p")
        
        
    def mark_en_route(self, current_time: datetime):
        """
        Marking the package as en route at the give time.
        Automatically updates status and delivery_time.
        """
        
        self.status = PackageStatus.EN_ROUTE
        
        # Format time as HH:MM AM/PM
        self.load_time = current_time.strftime("%I:%M %p")
        
        # String representation of the package object for easy debugging and display
    def __str__(self):
        return f"Package ID: {self.id}, Address: {self.address}, Weight: {self.weight}kg, City: {self.city}, Zip: {self.zip_code}, Deadline: {self.deadline}, Status: {self.status.value}, Delivery Time: {self.delivery_time}"

            

