



from datetime import datetime
from Package import Package, PackageStatus
from Truck import Truck
from HashTable import HashTable
from DistanceTable import DistanceTable
import routing
import csv
import pandas as pd # type: ignore


# initialize data structures

def load_packages(csv_file):
    """Load packages from WGUPS_Package_File.csv into a hash table (robust to messy headers)."""
    hashtable = HashTable()

    with open(csv_file, newline='') as f:
        rows = list(csv.reader(f))

    # Find header row by looking for 'Package' and 'Address'
    header_idx = None
    for i, row in enumerate(rows):
        joined = ",".join(cell.strip().lower() for cell in row)
        if "package" in joined and "address" in joined:
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not find header row in CSV")

    header = [cell.replace("\n", " ").strip().lower() for cell in rows[header_idx]]

    # Helper to find column index
    def find_col(name):
        for j, h in enumerate(header):
            if name.lower() in h:
                return j
        return None

    idx_pkg =       find_col("package")
    idx_address =   find_col("address")
    idx_city =      find_col("city")
    idx_zip =       find_col("zip")
    idx_deadline =  find_col("deadline")
    idx_weight =    find_col("weight")
    idx_notes =     find_col("special") or find_col("notes")

    # Process each row after header
    for row in rows[header_idx + 1:]:
        if not any(cell.strip() for cell in row):
            continue

        try:
            pkg_id = int(row[idx_pkg])
        except Exception:
            continue

        address = row[idx_address].strip() if idx_address is not None else ""
        city = row[idx_city].strip() if idx_city is not None else ""
        zip_code = row[idx_zip].strip() if idx_zip is not None else ""
        weight = row[idx_weight].strip() if idx_weight is not None else ""
        notes = row[idx_notes].strip() if idx_notes is not None else ""

        # Parse deadline
        raw_deadline = row[idx_deadline].strip() if idx_deadline is not None else ""
        if raw_deadline.upper() in ("", "EOD"):
            deadline = datetime.max.time()
        else:
            try:
                deadline = datetime.strptime(raw_deadline, "%I:%M %p").time()
            except Exception:
                deadline = datetime.max.time()

        pkg = Package(
            package_id = pkg_id,
            address = address,
            city = city,
            zip_code = zip_code,
            weight = weight,
            deadline = deadline,
            status = PackageStatus.AT_HUB,
            notes = notes
        )

        # process special notes to set constraints
        if notes:
            notes_lower = notes.lower()
            
            # delayed packages that can't leave before 9:05 AM
            if "delayed" in notes_lower or "9:05" in notes_lower:
                pkg.delayed_until = datetime.strptime("09:05 AM", "%I:%M %p")
            
            # package 9 address correction at 10:20 AM
            if pkg_id == 9:
                pkg.delayed_until = datetime.strptime("10:20 AM", "%I:%M %p")
            
            # packages that must be delivered together
            if "must be delivered with" in notes_lower or "delivered with" in notes_lower:
                pkg.group_constrained = True
            
            # packages that can only be on truck 2
            if "can only be on truck 2" in notes_lower or "truck 2" in notes_lower:
                pkg.truck_restriction = 2

        hashtable.insert(pkg.id, pkg)

    return hashtable


def load_distance_table(csv_file):
    """Load addresses + distance matrix from WGUPS CSV (finds the actual data rows)."""
    addresses = []
    matrix = []

    with open(csv_file, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Find the header row by looking for "DISTANCE BETWEEN HUBS"
    header_row_idx = None
    for i, row in enumerate(rows):
        if any("DISTANCE BETWEEN HUBS" in str(cell) for cell in row):
            header_row_idx = i
            break
    
    if header_row_idx is None:
        raise ValueError("Could not find header row in distance CSV")

    # The actual addresses are in the row after "DISTANCE BETWEEN HUBS"
    # Look for the row that contains the hub address
    data_start_idx = None
    for i in range(header_row_idx + 1, len(rows)):
        if any("Western Governors University" in str(cell) for cell in rows[i]):
            data_start_idx = i
            break
    
    if data_start_idx is None:
        raise ValueError("Could not find data start row in distance CSV")

    # Extract addresses and build matrix
    for i in range(data_start_idx, len(rows)):
        row = rows[i]
        if len(row) < 2:  # Skip empty rows
            continue
        
        # First column is the address
        address = row[0].strip().strip('"')
        if not address:  # Skip empty addresses
            continue
            
        addresses.append(address)
        
        # Rest of the columns are distances
        distances = []
        for j in range(2, len(row)):  # Skip first column (address) and second column (short name)
            try:
                dist = float(row[j].strip()) if row[j].strip() else 0.0
                distances.append(dist)
            except ValueError:
                distances.append(0.0)
        
        matrix.append(distances)

    # Load into DistanceTable
    distance_table = DistanceTable()
    distance_table.load(addresses, matrix)
    return distance_table


# initialize Trucks with driver constraint logic
def initialize_trucks():
    """Create our truck objects with driver availability logic."""
    # ensure trucks start with a real datetime object for proper time math/strftime usage
    start_dt = datetime.strptime("08:00 AM", "%I:%M %p")
    
    # truck 1 and 2 get drivers immediately (start at 8:00 AM)
    truck1 = Truck(truck_id = 1, start_time = start_dt)
    truck2 = Truck(truck_id = 2, start_time = start_dt)
    
    # truck 3 waits for a driver (will be updated later)
    # set to None initially to indicate no driver available
    truck3 = Truck(truck_id = 3, start_time = None)
    
    return [truck1, truck2, truck3]


# assign packages to Trucks
def assign_packages_to_trucks(trucks, hashtable):
    """Distributes packages according to constraints (tries preferred truck first; falls back if full)."""

    # carryover from our initialize trucks function
    truck1, truck2, truck3 = trucks

    # helper: attempt to load onto a preferred truck, otherwise try the others
    def safe_load(preferred_truck, package_id, hashtable):
        # list trucks in order: preferred first, then the others
        order = [preferred_truck] + [t for t in trucks if t is not preferred_truck]
        for t in order:
            try:
                # use your Truck.load_package so load_time/status get set
                t.load_package(package_id, hashtable)
                return True
            except Exception as e:
                # if it's full, move on to next truck; if it's a different error, re-raise
                if "full capacity" in str(e).lower():
                    continue
                else:
                    raise
        # none of the trucks accepted the package
        return False

    for package_id in hashtable.keys():
        package = hashtable.get(package_id)

        # since python doesn't have a typical "switch" case ordeal
        # i have to search around and found match/case, so I went with that
        # instead of doing a bunch of elifs (i probably could have done that on second thought)

        # match on constraint "type" and use safe_load to avoid overfilling a truck
        match True:
            case _ if hasattr(package, "delayed_until") and package.delayed_until:
                # delayed = truck 2 (try truck2 first, fallback to others)
                if not safe_load(truck2, package.package_id, hashtable):
                    raise Exception(f"All trucks full while assigning delayed package {package.package_id}")

            case _ if hasattr(package, "group_constrained") and package.group_constrained:
                # grouped constraint = truck 1 (try truck1 first)
                if not safe_load(truck1, package.package_id, hashtable):
                    raise Exception(f"All trucks full while assigning grouped package {package.package_id}")

            case _ if hasattr(package, "truck_restriction") and package.truck_restriction == 2:
                # has to explicitly be on truck 2... try truck2 then fail hard if full
                if not safe_load(truck2, package.package_id, hashtable):
                    raise Exception(f"Package {package.package_id} requires truck 2 but truck 2 is full and no alternative available")

            case _:
                # default case -> try truck3 first then others
                if not safe_load(truck3, package.package_id, hashtable):
                    raise Exception(f"All trucks full while assigning package {package.package_id}")


# run delivery with driver constraint logic
def run_all_deliveries(trucks, hashtable, distance_table):
    """runs the delivery loop for all trucks with 2-driver constraint."""
    
    truck1, truck2, truck3 = trucks
    
    # only truck 1 and truck 2 can start initially (they have the 2 drivers)
    available_trucks = [truck1, truck2]
    
    # run deliveries for trucks with drivers
    for truck in available_trucks:
        # ensure truck has packages and all IDs are valid before running delivery
        if hasattr(truck, "packages") and truck.packages:
            valid_packages = [pid for pid in truck.packages if pid is not None]
            truck.packages = valid_packages
            routing.run_delivery(truck, hashtable, distance_table)
    
    # determine which truck finishes first to free up a driver for truck 3
    if truck1.current_time <= truck2.current_time:
        first_free_driver_time = truck1.current_time
        print(f"Driver from Truck 1 becomes available at {first_free_driver_time.strftime('%I:%M %p')}")
    else:
        first_free_driver_time = truck2.current_time
        print(f"Driver from Truck 2 becomes available at {first_free_driver_time.strftime('%I:%M %p')}")
    
    # truck 3 can now start with the freed driver
    # but must wait until at least 9:05 AM for delayed packages anyway
    min_start_time = datetime.strptime("09:05 AM", "%I:%M %p")
    truck3_start_time = max(first_free_driver_time, min_start_time)
    
    # update truck 3's start time and current time
    truck3.current_time = truck3_start_time
    truck3.start_time = truck3_start_time
    
    print(f"Truck 3 starts deliveries at {truck3_start_time.strftime('%I:%M %p')}")
    
    # now run delivery for truck 3
    if hasattr(truck3, "packages") and truck3.packages:
        valid_packages = [pid for pid in truck3.packages if pid is not None]
        truck3.packages = valid_packages
        routing.run_delivery(truck3, hashtable, distance_table)


def print_delivery_statuses(trucks, hashtable):
    """ prints final delivery statuses for all packages at the hard-coded snapshots."""

    # predefined snapshot times for package status checks (keeps your hard-coded approach)
    snapshot_times = ["08:50 AM", "09:50 AM", "12:30 PM"]

    # iterate through each snapshot time
    for snap in snapshot_times:

        # convert snapshot time string into a time object for comparison
        snap_time = datetime.strptime(snap, "%I:%M %p").time()

        # print header for current snapshot
        print(f"\n--- Package Statuses at {snap} ---")

        # iterate through each truck
        for truck in trucks:

            # print truck identifier
            print(f"\nTruck {truck.truck_id}:")

            # iterate through each package id on the truck (assignment requires IDs)
            for package_id in truck.packages:

                # get the package object from the hashtable
                loaded_package = hashtable.get(package_id)

                # convert load_time string to a time if it exists, else max time
                if getattr(loaded_package, "load_time", None):
                    try:
                        load_time = datetime.strptime(loaded_package.load_time, "%I:%M %p").time()
                    except Exception:
                        # if it's already a datetime, pull the time portion
                        load_time = loaded_package.load_time.time() if hasattr(loaded_package.load_time, "time") else datetime.max.time()
                else:
                    load_time = datetime.max.time()

                # convert delivery_time string to a time if it exists, else max time
                if getattr(loaded_package, "delivery_time", None):
                    try:
                        delivery_time = datetime.strptime(loaded_package.delivery_time, "%I:%M %p").time()
                    except Exception:
                        delivery_time = loaded_package.delivery_time.time() if hasattr(loaded_package.delivery_time, "time") else datetime.max.time()
                else:
                    delivery_time = datetime.max.time()

                # determine package status based on snapshot time
                if snap_time < load_time:
                    status = "At Hub"

                elif load_time <= snap_time < delivery_time:
                    status = "En Route"

                else:
                    # show original formatted string if available
                    status = f"Delivered at {getattr(loaded_package, 'delivery_time', 'N/A')}"

                # defensive id lookup (works whether Package uses .id or .package_id)
                pkg_id_display = getattr(loaded_package, "id", getattr(loaded_package, "package_id", package_id))

                # print package ID and current status
                print(f"Package {pkg_id_display}: {status}")

    # calculate total mileage across all trucks
    total_mileage = sum(truck.mileage for truck in trucks)

    # print total mileage
    print(f"\nTotal mileage traveled by all trucks: {total_mileage:.2f}")


def delivery_interface(trucks, hashtable):
    """
    Command-line interface for checking package delivery statuses.
    Users can:
    1. View all packages at a specific time
    2. Check a single package by ID
    3. View total mileage
    4. Exit
    """
    while True:
        # print menu
        print("\n--- WGUPS Delivery Interface ---")
        print("1. View all package statuses at a specific time")
        print("2. View status of a single package by ID")
        print("3. View total mileage traveled by all trucks")
        print("4. Exit")
        
        # get user choice
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            # prompt user for snapshot time
            time_input = input("Enter time (HH:MM AM/PM, e.g., 09:30 AM): ").strip()
            try:
                snap_time = datetime.strptime(time_input, "%I:%M %p").time()
            except ValueError:
                print("Invalid time format. Try again.")
                continue
            
            print(f"\n--- Package Statuses at {time_input} ---")
            # iterate trucks and packages
            for truck in trucks:
                print(f"\nTruck {truck.truck_id}:")
                for package_id in truck.packages:
                    package = hashtable.get(package_id)
                    # safely parse load/delivery times
                    if getattr(package, "load_time", None):
                        try:
                            load_time = datetime.strptime(package.load_time, "%I:%M %p").time()
                        except Exception:
                            load_time = package.load_time.time() if hasattr(package.load_time, "time") else datetime.max.time()
                    else:
                        load_time = datetime.max.time()

                    if getattr(package, "delivery_time", None):
                        try:
                            delivery_time = datetime.strptime(package.delivery_time, "%I:%M %p").time()
                        except Exception:
                            delivery_time = package.delivery_time.time() if hasattr(package.delivery_time, "time") else datetime.max.time()
                    else:
                        delivery_time = datetime.max.time()
                    
                    if snap_time < load_time:
                        status = "At Hub"
                    elif load_time <= snap_time < delivery_time:
                        status = "En Route"
                    else:
                        status = f"Delivered at {getattr(package, 'delivery_time', 'N/A')}"
                    
                    print(f"Package {getattr(package, 'id', getattr(package, 'package_id', package_id))}: {status}")
        
        elif choice == "2":
            # check single package by ID
            package_id_input = input("Enter package ID: ").strip()
            if not package_id_input.isdigit():
                print("Invalid package ID. Must be a number.")
                continue
            package_id = int(package_id_input)
            package = hashtable.get(package_id)
            if package is None:
                print(f"No package found with ID {package_id}.")
                continue
            print(f"\nPackage {getattr(package, 'id', getattr(package, 'package_id', package_id))} info:")
            print(f"Address: {package.address}, City: {package.city}, Zip: {package.zip_code}")
            print(f"Deadline: {package.deadline}, Status: {package.status.value}")
            print(f"Load time: {package.load_time}, Delivery time: {package.delivery_time}")
        
        elif choice == "3":
            # total mileage
            total_mileage = sum(truck.mileage for truck in trucks)
            print(f"\nTotal mileage traveled by all trucks: {total_mileage:.2f}")
        
        elif choice == "4":
            # exit interface
            print("Exiting delivery interface.")
            break
        
        else:
            print("Invalid choice. Enter a number between 1-4.")


# main execution
if __name__ == "__main__":

    # quick starting message so we can see the script ran
    # print("scripting running")

    # parse the "packages" data from the xlsx into the hash table
    hashtable = load_packages("WGUPS_Package_File.csv")

    # use excel data to create the distance table map matrix
    distance_table = load_distance_table("WGUPS_Distance_Table.csv")

    # create our trucks
    trucks = initialize_trucks()

    # arranges and signals all our packages to all our trucks
    assign_packages_to_trucks(trucks, hashtable)

    # literally runs the entire truck delivery service (with driver constraint)
    run_all_deliveries(trucks, hashtable, distance_table)

    # start command-line interface for any adhoc checks
    delivery_interface(trucks, hashtable)

    # prints required snapshots and total mileage
    print_delivery_statuses(trucks, hashtable)