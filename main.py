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
    with open(csv_file, newline'') as f:
        reader = csv.DictReader(f)
        for row in reader:
            package = Package(
                package_id = int(row['Package ID']),
                address =        row['Address'],
                city =           row['City'],
                zip_code =       row['Zip'],
                deadline =       row['Deadline'],
                weight =         row['Weight'],
                special_notes =  row.get('Special Notes', '')
            )
            hashtable.insert(package.package_id, package)
        return hashtable



def load_distance_table(csv_file):
    """LOads the distance table from csv or other source."""
    # initialize distance table here



