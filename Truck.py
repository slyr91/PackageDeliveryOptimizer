from datetime import datetime

from PackageManager import Package


class Truck:

    capacity = 16

    # Initialize a Truck object with some initial values. Currently the truck numbering can only be 1, 2, or 3.
    def __init__(self, number):
        self.trips = 0
        self.holding_until = None
        self.on_hold = False
        if number in range(1, 4):
            self.number = number
        self.packages = []
        self.last_location = "Western Governors University"
        self.time = datetime.strptime("8:00 AM", "%I:%M %p")
        self.loading_time = self.time
        self.returning = False
        self.miles_traveled = 0

    # Add miles to total miles traveled.
    def add_miles(self, miles):
        self.miles_traveled += miles
        if self.miles_traveled < 0.1:
            self.miles_traveled = 0

    # Check that the truck has space for additional packages.
    def has_space(self):
        if len(self.packages) != self.capacity:
            return True
        else:
            return False

    # Return the number of packages currently on board the truck.
    def current_load(self):
        return len(self.packages)

    # Load the package onto the truck given there is available space.
    def load_package(self, package):
        if self.has_space():
            self.packages.append(package)
            return True
        else:
            return False

    # Unload the package object from the truck.
    def unload_package(self, package: Package):
        return self.unload_package_id(package.package_id)

    # Unload the package with the given package ID from the truck.
    def unload_package_id(self, package_id):
        for package in self.packages:
            if type(package) == Package:
                if package_id == package.package_id:
                    self.packages.remove(package)
                    break

    # Checks if a package with the package ID is on board the truck.
    def package_onboard(self, package_id):
        for package in self.packages:
            if type(package) == Package:
                if package.package_id == package_id:
                    return True
        return False

    # Empties the truck of all packages
    def unload_all(self):
        self.packages = []

    # Change the location of the truck.
    def change_location(self, new_location):
        self.last_location = new_location

    # Reset the truck so that it is available for more packages at the current time.
    def reloading(self):
        self.unload_all()
        self.returning = False
        self.loading_time = self.time
        self.on_hold = False

    # Set up the truck to not start delivering packages until after the hold time.
    def hold_until(self, holding_until):
        self.time = holding_until
        self.loading_time = holding_until
        self.holding_until = holding_until
        self.on_hold = True
        pass
