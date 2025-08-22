
# This is the package class for the project
class Package:
    def __init__(self, package_id, address, weight, city, zip_code, deadline, status="At Hub"):
        self.id = package_id
        self.address = address
        self.weight = weight
        self.city = city
        self.zip_code = zip_code
        self.deadline = deadline
        self.status = status

        # This will be used to track the delivery time of the package (updated later)
        self.delivery_time = None
       
        
    pass




