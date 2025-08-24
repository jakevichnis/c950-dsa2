# Jake Vichnis Student ID: 012633070


from datetime import datetime
import Package
from Truck import Truck
from HashTable import HashTable
from DistanceTable import DistanceTable
import routing
import csv


# initialize data structures

def load_packages(csv_file):
    """Loads packages from the csv into the hash table."""
    hashtable = HashTable()
    with open(csv_file, newline='') as f:
        reader = csv.DictReader(f)
                
        for row in reader:

            # had to add this due to some errors with my datetime with EOD
            deadline_str = row['Deadline']
            if deadline_str == "EOD":
                deadline = datetime.max.time()
            else:
                deadline = datetime.strptime(deadline_str, "%I:%M %p").time()

                # creation of package via parsed through the csv data into these fields
            package = Package(
                package_id =    int(row['Package ID']),
                address =           row['Address'],
                city =              row['City'],
                zip_code =          row['Zip'],
                deadline =              deadline,  # use parsed deadline here
                weight =            row['Weight'],
                special_notes =     row.get('Special Notes', '')
            )
            hashtable.insert(package.package_id, package)
        return hashtable



def load_distance_table(csv_file):
    """LOads the distance table from csv or other source."""
    
    # initialize distance table here
    distance_table = DistanceTable()
    addresses = []
    matrix = []

    # file handler
    with open(csv_file, newline='') as f:
        reader = csv.reader(f)

        # reads all rows into memory
        rows = list(reader)

        # first column contains addresses, rest are distances
        for row in rows:
            addresses.append(row[0])                                  # address at column 0
            matrix.append([float(x) if x else 0.0 for x in row[1:]])  # convert blanks to 0.0

    # save into distanceTable object
    distance_table.load(addresses, matrix)
    return distance_table




# initialize Trucks

def initialize_trucks():
    """Create our truck objects."""
    truck1 = Truck(truck_id = 1)
    truck2 = Truck(truck_id = 2)
    truck3 = Truck(truck_id = 3)
    return [truck1, truck2, truck3]




# assign packages to Trucks

def assign_packages_to_trucks(trucks, hashtable):
    """Distributes packages according to constraints"""

    # carryover from our initialize trucks function
    truck1, truck2, truck3 = trucks
    
    for package_id in hashtable.keys():
        package = hashtable.get(package_id)

        # since python doesn't have a typical "switch" case ordeal
        # i have to search around and found match/case, so I went with that
        # instead of doing a bunch of elifs (i probably could have done that on second thought)

        # match on constraint "type"
        match True:
            case _ if package.delayed_until:
                # delayed = truck 2
                truck2.packages.append(package.package_id)

            case _ if package.group_constrained:
                # grouped constraint = truck 1
                truck1.packages.append(package.package_id)

            case _ if package.truck_restriction == 2:
                # has to explicitly be on truck 2...
                truck2.packages.append(package.package_id)

            case _:
                # this is the default case, will go cleanly on truck 3
                truck3.packages.append(package.package_id)




# run delivery

def run_all_deliveries(trucks, hashtable, distance_table):
    """runs the delivery loop for all trucks."""
    for truck in trucks:
        routing.run_delivery(truck, hashtable, distance_table)

# user interfacing    
    


def print_delivery_statuses(hashtable):
    """ prints final delivery statuses for all packages."""
    for package_id in hashtable.keys():
        package = hashtable.get(package_id)
        time_str = package.delivery_time.strftime("%I:%M %p") if package.delivery_time else "N/A"
        print(f"Package {package.package_id}: {package.status} at {time_str}")



# main execution

if __name__ == "__main__":

    # parse the "packages" data from the csv into the hash table
    hashtable = load_packages("WGUPS_Package_File.csv")

    # use csv data to create the distance table map matrix
    distance_table = load_distance_table("WGUPS_Distance_table.csv")

    # create our trucks
    trucks = initialize_trucks()

    # arranges and signals all our packages to all our trucks
    assign_packages_to_trucks(trucks, hashtable)

    # literally runs the entire truck delivery service
    run_all_deliveries(trucks, hashtable, distance_table)

    # prints results
    print_delivery_statuses(hashtable)
