# Daryl Arouchian #000984402
# C950 Task 1
# Overall Time Complexity is O(N^2)
from datetime import datetime

from Location import LocationGraph
from PackageManager import PackageManager
from Scheduler import Scheduler


# Time: O(N) Space: O(1)
# Ask the user what time they want to change to and then update the time displayed and update the scheduler object.
def change_time():
    """This function is used to change the time of the application and will run the execute plan function of the
    scheduler object """

    hour = int(input("What time would you like to change to (Military Time)?\n\nHour (0-23): "))
    while hour not in range(0, 24):
        hour = int(input("Hour (0-23): "))

    minute = int(input("Minute (0-59): "))
    while minute not in range(0, 60):
        minute = int(input("Minute (0-59): "))

    time = datetime.strptime(str(hour) + ":" + str(minute), "%H:%M")
    scheduler.change_time(time)

    return "{:02d}".format(hour) + ":" + "{:02d}".format(minute)


def lookup_package(pack_man):
    package_id = int(input("Package ID: "))
    package = pack_man.packages.get_package(package_id)
    print("Package ID |      Address      |      City      | State |  Zip  | Deadline | Mass | Delivered | "
          "Delivery Time | Delivered On Time | Status")
    package.print_info()
    input("Press enter to continue.")


def print_all_package_info(pack_man):
    print("Package ID |      Address      |      City      | State |  Zip  | Deadline | Mass | Delivered | "
          "Delivery Time | Delivered On Time | Status")
    pack_man.print_all_package_info()
    input("Press enter to continue.")


# --- Start of Application ---
location_graph = LocationGraph()

package_manager = PackageManager()

# Time: O(N^2) Space: O(N^2)
scheduler = Scheduler(package_manager, location_graph)

current_time = "8:00"
# set the reoccurring prompt up.
input_prompt = "\n" + "Please type the number next to the option you would like " \
                      "to perform\n1) Change the current time\n2) Lookup Package " \
                      "by ID\n3) Print All Packages\n4) Quit\n\n" \
                      "Your option: "

print("Current Time: " + current_time)
print("Truck 1 Mileage: " + str(scheduler.truck1.miles_traveled))
print("Truck 2 Mileage: " + str(scheduler.truck2.miles_traveled))

current_option = input(input_prompt)

# Make sure the input provided is a number and nothing else.
while not current_option.isdigit():
    current_option = input("Input must be a number: ")

# Check for the quit option to end the application loop.
while int(current_option) != 4:

    current_int_option = int(current_option)

    # Change the time and update the application to match the time.
    if current_int_option == 1:
        current_time = change_time()

    # Lookup a single package and display its status on the screen.
    if current_int_option == 2:
        lookup_package(package_manager)

    # Show all package status information on the screen.
    if current_int_option == 3:
        print_all_package_info(package_manager)

    # Repeat the status information and the input prompt.
    print("Current Time: " + current_time)
    print("Truck 1 Mileage: " + str(scheduler.truck1.miles_traveled))
    print("Truck 2 Mileage: " + str(scheduler.truck2.miles_traveled))
    current_option = input(input_prompt)
    while not current_option.isdigit():
        current_option = input("Input must be a number: ")
