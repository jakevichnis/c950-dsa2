
# This is the package class for the project
class Package:

    # intit method for the parameters of the package class
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


        # String representation of the package object for easy debugging and display
    def __str__(self):
        return f"Package ID: {self.id}, Address: {self.address}, Weight: {self.weight}kg, City: {self.city}, Zip: {self.zip_code}, Deadline: {self.deadline}, Status: {self.status}, Delivery Time: {self.delivery_time}"

            

