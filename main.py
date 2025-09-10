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
            
            # FIXED: All delayed packages (6, 25, 28, 32) + any with "delayed" or "9:05" text
            if ("delayed" in notes_lower and "9:05" in notes_lower) or pkg_id in [6, 25, 28, 32]:
                pkg.delayed_until = datetime.strptime("09:05 AM", "%I:%M %p")
            
            # package 9 address correction at 10:20 AM
            if pkg_id == 9:
                pkg.correct_address = "410 S State St"  # Store the correct address
                pkg.address_correction_time = datetime.strptime("10:20 AM", "%I:%M %p")
            
            # FIXED: ALL packages that must be delivered together (13, 14, 15, 16, 19, 20)
            # Based on CSV notes: 14 with 15,19; 16 with 13,19; 20 with 13,15
            if pkg_id in [13, 14, 15, 16, 19, 20]:
                pkg.group_constrained = True
            
            # packages that can only be on truck 2
            if "can only be on truck 2" in notes_lower or "truck 2" in notes_lower:
                pkg.truck_restriction = 2

        hashtable.insert(pkg.id, pkg)

    return hashtable


def get_unassignable_packages(hashtable, current_time):
    """Returns packages that cannot be assigned to trucks yet due to delays."""
    unassignable_packages = []
    
    for package_id in hashtable.keys():
        package = hashtable.get(package_id)
        
        # If package is delayed and hasn't arrived yet, don't assign it
        if hasattr(package, 'delayed_until') and package.delayed_until:
            if package.delayed_until > current_time:
                unassignable_packages.append(package_id)
    
    return unassignable_packages


def scan_for_available_delayed_packages(hashtable, current_time):
    """
    Scan the entire hash table for ALL undelivered delayed packages that are now available
    """
    available_delayed_packages = []
    
    print(f"Scanning hash table for delayed packages available at {current_time.strftime('%I:%M %p')}...")
    
    # Use the hashtable.keys() method to get all package IDs, then check each package
    for package_id in hashtable.keys():
        package = hashtable.get(package_id)
        if package:
            # Debug: Print package status for delayed packages
            if hasattr(package, 'delayed_until') and package.delayed_until is not None:
                print(f"Package {package_id}: delayed_until={package.delayed_until.strftime('%I:%M %p')}, status={package.status}, delivery_time={getattr(package, 'delivery_time', 'None')}")
                
                # Check if package is delayed but now available and NOT YET DELIVERED
                if (package.delayed_until <= current_time and 
                    (not hasattr(package, 'delivery_time') or package.delivery_time is None)):
                    available_delayed_packages.append(package)
    
    return available_delayed_packages


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


def assign_packages_to_trucks(trucks, hashtable, current_time):
    """Distributes packages according to constraints - ONLY assigns available packages."""

    # Handle variable number of trucks
    available_trucks = trucks  # Use whatever trucks are passed in
    
    # Get packages that cannot be assigned yet
    unassignable = get_unassignable_packages(hashtable, current_time)
    print(f"Packages delayed until later: {unassignable}")

    # FIXED: Handle group packages first - ALL must go on same truck
    group_packages = [13, 14, 15, 16, 19, 20]
    
    # Only assign group packages if none are delayed
    available_group_packages = [pkg_id for pkg_id in group_packages if pkg_id not in unassignable]
    
    if available_group_packages:
        # Try to fit all available group packages on one truck
        group_truck = None
        for truck in available_trucks:
            if len(truck.packages) + len(available_group_packages) <= truck.capacity:
                group_truck = truck
                break
        
        if group_truck is None:
            raise Exception("No truck has enough capacity for available group packages")
        
        # Load all available group packages onto the selected truck
        for pkg_id in available_group_packages:
            group_truck.load_package(pkg_id, hashtable)
        
        print(f"Available group packages {available_group_packages} assigned to Truck {group_truck.truck_id}")

    # Helper function for remaining packages
    def safe_load(preferred_truck, package_id, hashtable):
        # Skip if package is delayed or already loaded
        if package_id in unassignable or package_id in available_group_packages:
            return True
            
        # list trucks in order: preferred first, then the others
        order = [preferred_truck] + [t for t in available_trucks if t is not preferred_truck]
        for t in order:
            try:
                t.load_package(package_id, hashtable)
                return True
            except Exception as e:
                if "full capacity" in str(e).lower():
                    continue
                else:
                    raise
        return False

    # Process remaining packages
    for package_id in hashtable.keys():
        # Skip group packages and delayed packages
        if package_id in group_packages or package_id in unassignable:
            continue
            
        package = hashtable.get(package_id)

        # Assign based on constraints
        if hasattr(package, "truck_restriction") and package.truck_restriction == 2:
            # Must be on truck 2 - find truck 2 in available trucks
            truck2 = next((t for t in available_trucks if t.truck_id == 2), None)
            if truck2 and not safe_load(truck2, package.package_id, hashtable):
                raise Exception(f"Package {package.package_id} requires truck 2 but truck 2 is full")
        else:
            # Default - try first available truck, then others
            if available_trucks and not safe_load(available_trucks[0], package.package_id, hashtable):
                raise Exception(f"All trucks full while assigning package {package.package_id}")


def run_all_deliveries(trucks, hashtable, distance_table):
    """runs the delivery loop for all trucks with proper delayed package handling."""
    
    truck1, truck2, truck3 = trucks
    
    # Phase 1: Initial deliveries (8:00 AM start)
    print("=== Phase 1: Initial Deliveries (8:00 AM) ===")
    initial_time = datetime.strptime("08:00 AM", "%I:%M %p")
    
    # Assign packages that are available at 8:00 AM to ALL trucks (not just 2)
    assign_packages_to_trucks([truck1, truck2, truck3], hashtable, initial_time)
    
    # Print initial package assignments
    for truck in [truck1, truck2, truck3]:
        if truck.packages:
            print(f"Truck {truck.truck_id} assigned packages: {sorted(truck.packages)}")
    
    # Run deliveries for trucks 1 and 2 (they have drivers)
    active_trucks = []
    for truck in [truck1, truck2]:
        if hasattr(truck, "packages") and truck.packages:
            valid_packages = [pid for pid in truck.packages if pid is not None]
            truck.packages = valid_packages
            print(f"Truck {truck.truck_id} starting deliveries...")
            routing.run_delivery(truck, hashtable, distance_table)
            active_trucks.append(truck)
    
    # Determine when first driver becomes available
    if active_trucks:
        first_free_time = min(truck.current_time for truck in active_trucks)
        print(f"First driver becomes available at {first_free_time.strftime('%I:%M %p')}")
        
        # FIXED: Assign driver to Truck 3 and deliver its initial packages
        if truck3.packages:  # If truck3 has packages assigned
            truck3.start_time = first_free_time  # Give truck3 a driver
            truck3.current_time = first_free_time
            truck3.current_location = "Western Governors University 4001 South 700 East Salt Lake City UT 84107"
            
            print(f"Truck 3 gets driver at {first_free_time.strftime('%I:%M %p')} and starts deliveries...")
            routing.run_delivery(truck3, hashtable, distance_table)
    
    # Phase 2: Handle delayed packages with hash table scanning
    print("\n=== Phase 2: Delayed Package Handling ===")
    
    # Handle package 9 and other delayed packages (available at 10:20 AM)
    address_correction_time = datetime.strptime("10:20 AM", "%I:%M %p")
    
    # Scan for all available delayed packages
    available_delayed_packages = scan_for_available_delayed_packages(hashtable, address_correction_time)
    
    if available_delayed_packages:
        # Sort by package ID for consistent output
        available_delayed_packages.sort(key=lambda p: p.package_id)
        package_ids = [p.package_id for p in available_delayed_packages]
        
        print(f"Found ALL available delayed packages: {package_ids}")
        
        # Correct package 9's address if needed
        pkg9 = hashtable.get(9)
        if pkg9 and hasattr(pkg9, 'correct_address'):
            pkg9.address = pkg9.correct_address
            print(f"Package 9 address corrected to: {pkg9.address}")
        
        # Determine which truck should handle delayed packages
        # Use the truck that finished earliest and has capacity
        best_truck = None
        earliest_finish = None
        
        for truck in [truck1, truck2, truck3]:
            if truck.current_time:
                if earliest_finish is None or truck.current_time < earliest_finish:
                    earliest_finish = truck.current_time
                    best_truck = truck
        
        if best_truck:
            # Reset truck to hub for delayed package pickup
            best_truck.current_time = max(best_truck.current_time, address_correction_time)
            best_truck.current_location = "Western Governors University 4001 South 700 East Salt Lake City UT 84107"
            
            # Add delayed packages to the truck
            for package in available_delayed_packages:
                best_truck.packages.append(package.package_id)
                package.status = PackageStatus.EN_ROUTE
                package.truck_id = best_truck.truck_id
                package.load_time = best_truck.current_time.strftime("%I:%M %p")
            
            print(f"Truck {best_truck.truck_id} loading ALL delayed packages {package_ids} for delivery...")
            routing.run_delivery(best_truck, hashtable, distance_table)
    
    # Phase 3: All deliveries completed
    print("\n=== Phase 3: All deliveries completed ===")
    print("All trucks have completed their deliveries for the day.")

def print_delivery_statuses(trucks, hashtable):
    """ prints final delivery statuses for all packages at the hard-coded snapshots."""

    # predefined snapshot times for package status checks (keeps your hard-coded approach)
    snapshot_times = ["08:50 AM", "09:50 AM", "12:30 PM"]

    # iterate through each snapshot time
    for snap in snapshot_times:

        # convert snapshot time string into a time object for comparison
        snap_time = datetime.strptime(snap, "%I:%M %p").time()
        snap_datetime = datetime.strptime(snap, "%I:%M %p")

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

                # FIXED: Check if package is delayed and snapshot is before delay time
                if hasattr(loaded_package, 'delayed_until') and loaded_package.delayed_until:
                    if snap_datetime < loaded_package.delayed_until:
                        # Show appropriate delayed status instead of "At Hub"
                        if package_id in [6, 25, 28, 32]:
                            status = "Delayed - En Route to Hub"  # These are on a plane
                        elif package_id == 9:
                            status = "At Hub - Awaiting Address Correction"  # Different delay reason
                        else:
                            status = "DELAYED"
                        pkg_id_display = getattr(loaded_package, "id", getattr(loaded_package, "package_id", package_id))
                        print(f"Package {pkg_id_display}: {status}")
                        continue

                # convert load_time string to a time if it exists, else max time
                if getattr(loaded_package, "load_time", None):
                    try:
                        load_time = datetime.strptime(loaded_package.load_time, "%I:%M %p").time()
                    except Exception:
                        # if it's already a datetime, pull the time portion
                        load_time = loaded_package.load_time.time() if hasattr(loaded_package.load_time, "time") else datetime.max.time()
                else:
                    # FIXED: Use truck start time as load time if no specific load_time
                    if truck.start_time and hasattr(truck.start_time, 'time'):
                        load_time = truck.start_time.time()
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
                snap_datetime = datetime.strptime(time_input, "%I:%M %p")
            except ValueError:
                print("Invalid time format. Try again.")
                continue
            
            print(f"\n--- Package Statuses at {time_input} ---")
            
            # iterate trucks and packages
            for truck in trucks:
                print(f"\nTruck {truck.truck_id}:")
                
                # get unique packages assigned to this truck
                truck_packages = set()  # Use set to avoid duplicates
                
                for package_id in hashtable.keys():
                    package = hashtable.get(package_id)
                    if hasattr(package, 'truck_id') and package.truck_id == truck.truck_id:
                        truck_packages.add(package_id)
                
                # processes each package once
                for package_id in sorted(truck_packages):
                    package = hashtable.get(package_id)
                    
                    # FIXED: Check delayed packages first
                    if hasattr(package, 'delayed_until') and package.delayed_until:
                        if snap_datetime < package.delayed_until:
                            status = "DELAYED"
                            pkg_id = getattr(package, 'id', getattr(package, 'package_id', package_id))
                            print(f"Package {pkg_id} | {package.address} | {status} | {package.deadline} | Truck {truck.truck_id}")
                            continue
                    
                    # FIXED: Better time parsing with consistent fallbacks
                    load_time = None
                    delivery_time = None
                    
                    # Parse load time
                    if getattr(package, "load_time", None):
                        try:
                            if isinstance(package.load_time, str):
                                load_time = datetime.strptime(package.load_time, "%I:%M %p").time()
                            elif hasattr(package.load_time, "time"):
                                load_time = package.load_time.time()
                            else:
                                load_time = package.load_time
                        except:
                            # Use truck start time as fallback
                            if truck.start_time and hasattr(truck.start_time, 'time'):
                                load_time = truck.start_time.time()
                            else:
                                load_time = datetime.strptime("08:00 AM", "%I:%M %p").time()  # Default start time
                    else:
                        # Use truck start time as fallback
                        if truck.start_time and hasattr(truck.start_time, 'time'):
                            load_time = truck.start_time.time()
                        else:
                            load_time = datetime.strptime("08:00 AM", "%I:%M %p").time()  # Default start time

                    # Parse delivery time - CRITICAL FIX HERE
                    if getattr(package, "delivery_time", None):
                        try:
                            if isinstance(package.delivery_time, str):
                                delivery_time = datetime.strptime(package.delivery_time, "%I:%M %p").time()
                            elif hasattr(package.delivery_time, "time"):
                                delivery_time = package.delivery_time.time()
                            else:
                                delivery_time = package.delivery_time
                        except:
                            print(f"DEBUG: Failed to parse delivery_time for package {package_id}: {package.delivery_time}")
                            delivery_time = None  # Set to None instead of max time
                    else:
                        delivery_time = None
                
                    # FIXED: Status logic with proper None handling
                    if delivery_time is None:
                        # Package not yet delivered
                        if snap_time < load_time:
                            status = "At Hub"
                        else:
                            status = "En Route"
                    else:
                        # Package has delivery time
                        if snap_time < load_time:
                            status = "At Hub"
                        elif load_time <= snap_time < delivery_time:
                            status = "En Route"
                        else:
                            status = f"Delivered at {getattr(package, 'delivery_time', 'N/A')}"
                    
                    # FIXED: Handle Package 9 address change
                    display_address = package.address
                    if package_id == 9:
                        # Package 9 address changes at 10:20 AM
                        address_change_time = datetime.strptime("10:20 AM", "%I:%M %p").time()
                        if snap_time < address_change_time:
                            display_address = "300 State St, Salt Lake City, UT 84103"
                        else:
                            display_address = "410 S State St, Salt Lake City, UT 84111"
                    
                    pkg_id = getattr(package, 'id', getattr(package, 'package_id', package_id))
                    print(f"Package {pkg_id} | {display_address} | {status} | {package.deadline} | Truck {truck.truck_id}")

        elif choice == "2":
            # checks single package by ID
            package_id_input = input("Enter package ID: ").strip()
            if not package_id_input.isdigit():
                print("Invalid package ID. Must be a number.")
                continue
            package_id = int(package_id_input)
            package = hashtable.get(package_id)
            if package is None:
                print(f"No package found with ID {package_id}.")
                continue
            
            # Handle Package 9 address display in single package view
            display_address = package.address
            if package_id == 9:
                print("Package 9 address updated at 10:20 AM")
                print("Before 10:20 AM: 300 State St, Salt Lake City, UT 84103")
                print("After 10:20 AM: 410 S State St, Salt Lake City, UT 84111")
            
            print(f"\nPackage {getattr(package, 'id', getattr(package, 'package_id', package_id))} info:")
            print(f"Address: {display_address}, City: {package.city}, Zip: {package.zip_code}")
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

    # literally runs the entire truck delivery service (with proper delayed package handling)
    run_all_deliveries(trucks, hashtable, distance_table)

    # start command-line interface for any adhoc checks
    delivery_interface(trucks, hashtable)

    # prints required snapshots and total mileage
    print_delivery_statuses(trucks, hashtable)