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
            
            # Delayed packages (6, 25, 28, 32) + any with "delayed" or "9:05" text
            if ("delayed" in notes_lower and "9:05" in notes_lower) or pkg_id in [6, 25, 28, 32]:
                pkg.delayed_until = datetime.strptime("09:05 AM", "%I:%M %p")
            
            # Package 9 address correction - goes on Truck 3 at 10:21 AM
            if pkg_id == 9:
                pkg.correct_address = "410 S State St"  # Store the correct address
                pkg.address_correction_time = datetime.strptime("10:20 AM", "%I:%M %p")
            
            # Packages that can only be on truck 2 (3, 18, 36, 38)
            if "can only be on truck 2" in notes_lower or "truck 2" in notes_lower:
                pkg.truck_restriction = 2
                
        hashtable.insert(pkg.id, pkg)
    return hashtable



def assign_packages_to_trucks(trucks, hashtable):
    """
    Load packages into trucks with corrected assignments for grouped deliveries
    and proper constraint handling.
    """
    print("=== Loading All Trucks (8:00 AM) ===")
    print("Loading trucks sequentially at 08:00 AM...")
    
    # Manual truck assignments to ensure grouped packages stay together
    # and all constraints are met
    
    truck1_packages = [
        15,  # 9:00 AM deadline - HIGHEST PRIORITY
        1, 13, 14, 16, 19, 20,  # Grouped packages (must be delivered together)
        29, 30, 31, 34, 37, 40,  # Other 10:30 AM deadlines
        2, 4, 5  # Fill remaining slots
    ]
    
    truck2_packages = [
        3, 18, 36, 38,  # Required on truck 2 (CSV notes)
        6, 25, 28, 32,  # Delayed packages (available after 9:05 AM)
        21, 22, 23, 24, 26, 27  # Fill remaining slots
    ]
    
    truck3_packages = [
        9,  # Wrong address - corrected at 10:20 AM
        7, 8, 10, 11, 12, 17, 33, 35, 39  # Remaining packages
    ]
    
    # Load Truck 1
    print(f"\nLoading Truck 1:")
    for package_id in truck1_packages:
        package = hashtable.get(package_id)
        if package:
            trucks[0].load_package(package_id, hashtable)
            package.assigned_truck = 1
            if package_id == 15:
                print(f"Package {package_id} → Truck 1 (9:00 AM deadline - PRIORITY)")
            elif package_id in [1, 13, 14, 16, 19, 20]:
                print(f"Package {package_id} → Truck 1 (grouped delivery)")
            elif package_id in [29, 30, 31, 34, 37, 40]:
                print(f"Package {package_id} → Truck 1 (10:30 AM deadline)")
            else:
                print(f"Package {package_id} → Truck 1")
    
    # Load Truck 2
    print(f"\nLoading Truck 2:")
    for package_id in truck2_packages:
        package = hashtable.get(package_id)
        if package:
            trucks[1].load_package(package_id, hashtable)
            package.assigned_truck = 2
            if package_id in [3, 18, 36, 38]:
                print(f"Package {package_id} → Truck 2 (required)")
            elif package_id in [6, 25, 28, 32]:
                print(f"Package {package_id} → Truck 2 (delayed until 9:05 AM)")
            else:
                print(f"Package {package_id} → Truck 2")
    
    # Load Truck 3
    print(f"\nLoading Truck 3:")
    for package_id in truck3_packages:
        package = hashtable.get(package_id)
        if package:
            trucks[2].load_package(package_id, hashtable)
            package.assigned_truck = 3
            if package_id == 9:
                print(f"Package {package_id} → Truck 3 (wrong address - corrected at 10:20 AM)")
            else:
                print(f"Package {package_id} → Truck 3")
    
    # Verify all packages assigned
    total_assigned = len(trucks[0].packages) + len(trucks[1].packages) + len(trucks[2].packages)
    
    print(f"\nFinal truck assignments:")
    print(f"Truck 1: {len(trucks[0].packages)} packages {sorted(trucks[0].packages)}")
    print(f"Truck 2: {len(trucks[1].packages)} packages {sorted(trucks[1].packages)}")
    print(f"Truck 3: {len(trucks[2].packages)} packages {sorted(trucks[2].packages)}")
    print(f"Total packages assigned: {total_assigned}/40")
    
    if total_assigned != 40:
        print("WARNING: Not all packages were assigned!")
    else:
        print("SUCCESS: All 40 packages assigned correctly!")


def initialize_trucks():
    """
    Initialize trucks with proper start times and constraints
    """
    trucks = []
    
    # Use keyword arguments to avoid parameter order confusion
    truck1 = Truck(truck_id=1, start_time=datetime.strptime("08:00", "%H:%M"))
    trucks.append(truck1)
    
    truck2 = Truck(truck_id=2, start_time=datetime.strptime("09:30", "%H:%M"))
    trucks.append(truck2)
    
    truck3 = Truck(truck_id=3, start_time=datetime.strptime("10:21", "%H:%M"))
    trucks.append(truck3)
    
    return trucks

def run_all_deliveries(trucks, hashtable, distance_table):
    """
    Run deliveries with sequential truck loading and departure times.
    """
    
    truck1, truck2, truck3 = trucks
    
    # SINGLE ASSIGNMENT PHASE: Load all trucks at start but they leave at different times
    initial_time = datetime.strptime("08:00 AM", "%I:%M %p")
    
    # Load all trucks according to strategy
    assign_packages_to_trucks([truck1, truck2, truck3], hashtable)
    
    # Phase 1: Truck 1 leaves at 8:00 AM
    print("\n=== Phase 1: Truck 1 Deliveries (8:00 AM) ===")
    if truck1.packages:
        valid_packages = [pid for pid in truck1.packages if pid is not None]
        truck1.packages = valid_packages
        print(f"Truck 1 starting deliveries at 8:00 AM...")
        routing.run_delivery(truck1, hashtable, distance_table)
    
    # Phase 2: Truck 2 leaves at 9:30 AM
    print("\n=== Phase 2: Truck 2 Deliveries (9:30 AM) ===")
    if truck2.packages:
        valid_packages = [pid for pid in truck2.packages if pid is not None]
        truck2.packages = valid_packages
        print(f"Truck 2 starting deliveries at 9:30 AM...")
        routing.run_delivery(truck2, hashtable, distance_table)
    
    # Phase 3: Truck 3 leaves at 10:21 AM
    print("\n=== Phase 3: Truck 3 Deliveries (10:21 AM) ===")
    if truck3.packages:
        valid_packages = [pid for pid in truck3.packages if pid is not None]
        truck3.packages = valid_packages
        print(f"Truck 3 starting deliveries at 10:21 AM...")
        routing.run_delivery(truck3, hashtable, distance_table)
    
    print("\n=== All deliveries completed ===")
    
    # Verify all packages were delivered
    undelivered = []
    for package_id in hashtable.keys():
        package = hashtable.get(package_id)
        if not hasattr(package, 'delivery_time') or package.delivery_time is None:
            undelivered.append(package_id)
    
    if undelivered:
        print(f"WARNING: {len(undelivered)} packages not delivered: {sorted(undelivered)}")
    else:
        print("SUCCESS: All 40 packages were delivered")


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

def print_delivery_statuses(trucks, hashtable):
    """ prints final delivery statuses for all packages at the hard-coded snapshots."""

    # predefined snapshot times for package status checks (keeps hard-coded approach)
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









def debug_mileage(trucks, hashtable, distance_table):
    """Debug mileage calculation by checking each truck's route"""
    
    print("\n=== MILEAGE DEBUG REPORT ===")
    total_mileage = 0
    
    for truck in trucks:
        print(f"\nTruck {truck.truck_id}:")
        print(f"  Reported mileage: {truck.mileage:.2f}")
        print(f"  Number of packages: {len(truck.packages)}")
        print(f"  Start location: {truck.current_location}")
        
        # Check if truck has a route history or delivery order
        if hasattr(truck, 'route') or hasattr(truck, 'delivery_order'):
            route = getattr(truck, 'route', getattr(truck, 'delivery_order', []))
            print(f"  Route taken: {route}")
        
        # Manual distance calculation check
        hub_address = "Western Governors University 4001 South 700 East"
        current_location = hub_address
        manual_distance = 0
        
        print(f"  Package delivery addresses:")
        for package_id in truck.packages:
            package = hashtable.get(package_id)
            if package:
                address = package.address
                print(f"    Package {package_id}: {address}")
                
                # Get distance from current location to this package
                try:
                    distance = distance_table.get_distance(current_location, address)
                    manual_distance += distance
                    print(f"      Distance from {current_location[:20]}... to {address[:20]}...: {distance}")
                    current_location = address
                except Exception as e:
                    print(f"      ERROR getting distance: {e}")
        
        # Add return to hub distance
        try:
            return_distance = distance_table.get_distance(current_location, hub_address)
            manual_distance += return_distance
            print(f"    Return to hub: {return_distance}")
        except Exception as e:
            print(f"    ERROR getting return distance: {e}")
        
        print(f"  Manual calculation: {manual_distance:.2f}")
        print(f"  Difference: {abs(truck.mileage - manual_distance):.2f}")
        
        total_mileage += truck.mileage
    
    print(f"\nTOTAL MILEAGE: {total_mileage:.2f}")
    
    # Check distance table integrity
    print(f"\n=== DISTANCE TABLE DEBUG ===")
    print(f"Number of addresses in distance table: {len(distance_table.addresses) if hasattr(distance_table, 'addresses') else 'Unknown'}")
    
    # Test a few known distances
    hub = "Western Governors University 4001 South 700 East"
    test_addresses = []
    
    # Get first few package addresses for testing
    for i in range(min(5, len(hashtable.keys()))):
        package_id = list(hashtable.keys())[i]
        package = hashtable.get(package_id)
        if package:
            test_addresses.append(package.address)
    
    print(f"Sample distance calculations:")
    for addr in test_addresses[:3]:
        try:
            dist = distance_table.get_distance(hub, addr)
            print(f"  Hub to {addr[:30]}...: {dist}")
        except Exception as e:
            print(f"  ERROR: {e}")










            
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

    debug_mileage(trucks, hashtable, distance_table)

    # start command-line interface for any adhoc checks
    delivery_interface(trucks, hashtable)

    # prints required snapshots and total mileage
    print_delivery_statuses(trucks, hashtable)