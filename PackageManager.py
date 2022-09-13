from datetime import datetime
from operator import attrgetter


class PackageHashTable:
    default_size = 40

    def __init__(self, size=default_size):
        self.hash_table = [[] for i in range(size)]
        self.size = size

    def add_package_obj(self, item):
        if type(item) is Package:
            self.hash_table[int(item.package_id) % self.size].append(item)

    def add_package(self, package_id, address, city, state, package_zip, delivery_deadline, mass, special_notes):
        package = Package(package_id, address, city, state, package_zip, delivery_deadline, mass, special_notes)
        self.add_package_obj(package)

    def remove_package(self, package_id):
        list_in_slot = self.hash_table[package_id % self.size]
        list_in_slot.remove(self.get_package(package_id))

    def get_package(self, package_id):
        list_in_slot = self.hash_table[package_id % self.size]
        for package in list_in_slot:
            if package.package_id == package_id:
                return package
        return None

    def get_package_list(self):
        # Hold all packages in a sequential list.
        list_of_all_packages = []
        # Each hash table slot holds a list so we must iterate through each list individually.
        for list_in_slot in self.hash_table:
            for package in list_in_slot:
                list_of_all_packages.append(package)
        return sorted(list_of_all_packages, key=attrgetter("package_id"))


class Package:

    def __init__(self, package_id, address, city, state, package_zip, delivery_deadline, mass, special_notes):
        # Basic package information
        self.package_id = int(package_id)
        self.address = address
        self.city = city
        self.state = state
        self.package_zip = package_zip
        self.mass = mass
        self.constraints = {}

        # Status information
        self.delivered = False
        self.delivery_time = None
        self.status = "At HUB"

        # Every package has a deadline. Some are just at the end of the day. Because they are at the end of the day
        # they still need to be initialized but can be set to None.
        if delivery_deadline != "EOD":
            self.constraints["Deadline"] = datetime.strptime(delivery_deadline, "%I:%M %p")
        else:
            self.constraints["Deadline"] = None

        # package constraints a parsed at this step of the package creation process. This puts the special notes into a
        # format that the scheduler class and process and plan from.
        if "Can only be on" in special_notes:
            self.constraints["Truck"] = int(special_notes.partition("truck")[2])
        elif "Must be delivered with" in special_notes:
            extracted_packages = str(special_notes).partition("with")[2].strip().strip('"')
            extracted_packages = extracted_packages.split(",")
            packages = []
            for pack in extracted_packages:
                packages += [int(pack)]
            self.constraints["Delivered_With"] = packages
        elif "Delayed on flight" in special_notes:
            extracted_time_str = str(special_notes).partition("until")[2].strip()
            extracted_time = datetime.strptime(extracted_time_str, "%I:%M %p")
            self.constraints["Delayed"] = extracted_time
            self.status = "Delayed on flight."
        elif "Wrong" in special_notes:
            self.constraints["Delayed"] = datetime.strptime("10:20 AM", "%I:%M %p")
            self.constraints["Wrong"] = "410 S State St., Salt Lake City, UT 84111"
            self.status = "Wrong address provided. Will be updated soon."

    # Time: O(1)    Space: O(1)
    # This function is used to print the package information onto the standard output in a predetermined format. It
    # matches the header information in the printer operations of the Main.py class. There is an attempt to make the
    # columns line up as much as possible.
    def print_info(self):
        deadline_value = str(self.constraints["Deadline"].time()) if self.constraints["Deadline"] else "None"
        delivery_time_string = str(self.delivery_time.time()) if self.delivery_time else "N/A"
        delivered_value = "True" if self.delivered else "False"
        delivered_on_time = "N/A"
        if self.constraints["Deadline"]:
            if self.delivery_time is not None:
                if self.delivery_time > self.constraints["Deadline"]:
                    delivered_on_time = "FALSE!!!"
                elif self.delivery_time < self.constraints["Deadline"]:
                    delivered_on_time = "TRUE"

        print(f"{str(self.package_id):^10} | {self.address:^17} | {self.city:^4} | {self.state:^5} | "
              f"{self.package_zip:^3} | {deadline_value:^8} | {self.mass:^4} | {delivered_value:^9} | "
              f"{delivery_time_string:^13} | {delivered_on_time:^13} | {self.status:^6}")


class PackageManager:

    # Time: O(N^2) Space: O(N)
    # This function will import the package information from the WGUPS Package File.csv, create package objects for
    # each package entry, and will place all packages into the package hashtable object.
    def __init__(self):
        package_file = open('WGUPS Package File.csv', 'r', encoding='UTF-8')

        self.constraints_on_packages = {"Delayed": [], "Wrong": [], "Deadline": [], "Delivered_With": [], "Truck": []}

        for i in range(4):
            package_file.readline()

        package_line = package_file.readline()
        self.packages = PackageHashTable()
        while package_line != '':
            package_line = package_line.strip('\n')
            package_fields = package_line.split(',')
            # There needs to be a test for if the package information contains an additional comma in the special notes
            # field. This is due to the "must be delivered with" constraint specifying 2 packages with a comma between
            # them.
            if len(package_fields) == 9:
                package = Package(package_fields[0], package_fields[1], package_fields[2], package_fields[3],
                                  package_fields[4], package_fields[5], package_fields[6],
                                  package_fields[7] + "," + package_fields[8])
            else:
                package = Package(package_fields[0], package_fields[1], package_fields[2], package_fields[3],
                                  package_fields[4], package_fields[5], package_fields[6], package_fields[7])

            self.packages.add_package_obj(package)

            package_line = package_file.readline()

        # All the constraints of every package are placed into a dictionary for easy retrieval. Function also doubles
        # to calculate all hidden constraints to make them obvious to the scheduler.
        self.gather_constraints()

    # Time: O(N) Space: O(1)
    def print_all_package_info(self):
        for package in self.packages.get_package_list():
            package.print_info()

    # Time: O(N^2) Space: O(N)
    # This function will create a dictionary of constraints and will place the packages with the corresponding
    # constraints in the appropriate list. It also checks for hidden constraints. The main hidden constraint is the
    # transitive constraint created from the "must be delivered with" special note. Some packages without constraints
    # will be impacted by another packages "must be delivered with" constraint.
    def gather_constraints(self):

        # Time: O(N) Space: O(N)
        # Places all packages with the corresponding constraint into the list of constraints.
        for package in self.packages.get_package_list():
            package_constraint_keys = package.constraints.keys()
            if "Delayed" in package_constraint_keys:
                self.constraints_on_packages["Delayed"].append([package.package_id, package.constraints["Delayed"]])
            if "Deadline" in package_constraint_keys:
                self.constraints_on_packages["Deadline"].append([package.package_id, package.constraints["Deadline"]])
            if "Wrong" in package_constraint_keys:
                self.constraints_on_packages["Wrong"].append([package.package_id, package.constraints["Wrong"]])
            if "Delivered_With" in package_constraint_keys:
                self.constraints_on_packages["Delivered_With"].append([package.package_id,
                                                                       package.constraints["Delivered_With"]])
            if "Truck" in package_constraint_keys:
                self.constraints_on_packages["Truck"].append([package.package_id, package.constraints["Truck"]])

        # Time: O(N^2) Space: O(N)
        # Checks for "must be delivered with" constraint and makes sure all packages involved in a constraint are
        # properly marked.
        # First grab a package with a known "Delivered_With" constraint.
        for constraint in self.constraints_on_packages["Delivered_With"]:
            pack_ids = constraint[1]
            # Delivered with constraints are a list of packages. Check each package in a constraint.
            for pack_id in constraint[1]:
                pack = self.packages.get_package(pack_id)

                # If the package being checked doesn't have the "Delivered_With" constraint then we need to add it. We
                # all need to add this package to the list of constraints.
                if "Delivered_With" not in pack.constraints.keys():
                    pack_ids_copy = pack_ids.copy()
                    pack_ids_copy.remove(pack_id)

                    pack.constraints["Delivered_With"] = []
                    pack.constraints["Delivered_With"] += [constraint[0], pack_ids_copy[0]]

                    self.constraints_on_packages["Delivered_With"].append([pack_id,
                                                                           [constraint[0], pack_ids_copy[0]]])
                # If the package already has constraints then we need to make sure that the list of packages it has in
                # it's "Delivered_With" constraint includes the original package we are checking.
                else:
                    # copy the pack_ids list so we don't accidently overwrite it.
                    pack_ids_copy = pack_ids.copy()
                    # Remove the package id we are checking
                    pack_ids_copy.remove(pack_id)
                    # Include the package id of the original package.
                    ids_to_check = [constraint[0]]
                    ids_to_check.extend(pack_ids_copy)

                    # Make sure there are no repeats in the list of constraints
                    pack.constraints["Delivered_With"].extend(ids_to_check)
                    pack.constraints["Delivered_With"] = list(set(pack.constraints["Delivered_With"]))

                    # Update the package in the list of package constraints.
                    for cons in self.constraints_on_packages["Delivered_With"]:
                        if cons[0] == pack_id:
                            cons[1] = pack.constraints["Delivered_With"]
                            break

    # Time: O(N) Space: O(N)
    # Creates a list of packages ordered by priority.
    def priority_list(self):
        # Highest Priority
        deadline_and_delayed = []
        deadline_and_delayed_set = set(list())
        # Second Highest Priority
        deadlines = []
        deadlines_set = set(list())
        # Moderate Priority
        delivered_with = []
        delivered_with_set = set(list())
        # Low Priority
        end_of_day = []
        # Lowest Priority
        end_of_day = []

        # Parse each package for constraints.
        for package in self.packages.get_package_list():
            if "Delayed" in package.constraints.keys() and package.constraints["Deadline"]:
                deadline_and_delayed.append(package)
                deadline_and_delayed_set.add(package.address)
            elif package.constraints["Deadline"] and "Delivered_With" not in package.constraints.keys():
                deadlines.append(package)
                deadlines_set.add(package.address)
                deadlines.sort(key=lambda pack: pack.constraints["Deadline"])
            elif "Delivered_With" in package.constraints.keys():
                delivered_with.append(package)
                delivered_with_set.add(package.address)
            else:
                end_of_day.append(package)

        for package in end_of_day:
            if package.address in deadline_and_delayed_set:
                end_of_day.remove(package)
                deadline_and_delayed.append(package)
            elif package.address in delivered_with_set:
                end_of_day.remove(package)
                delivered_with.append(package)
            elif package.address in deadlines_set:
                end_of_day.remove(package)
                deadlines.append(package)

        # Combine all list in order of priority
        return deadline_and_delayed, delivered_with + deadlines, end_of_day
