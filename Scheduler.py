import operator
from builtins import set, list
import copy
from datetime import datetime, timedelta

from Truck import Truck

initial_time = "8:00 AM"
travel_speed_mph = 18


class Scheduler:
    # Scheduler needs to keep track of the current tie and the previous time for the plan execution operations.
    current_time = None
    previous_time = None

    package_manager = None
    location_graph = None

    # The scheduled_plan_queue is a FIFO queue. It will also operation as a stack after initialization and being used
    # by the execution operations.
    scheduled_plan_queue = []
    executed_stack = []

    truck1 = Truck(1)
    truck2 = Truck(2)

    # Time: O(N^2) Space: O(N^2)
    def __init__(self, pack_man, location_graph, time=initial_time):
        self.current_time = datetime.strptime(time, "%I:%M %p")
        self.previous_time = self.current_time
        self.package_manager = pack_man
        self.location_graph = location_graph

        # The scheduler object initializes and plans the package delivery order. It then runs the execute plan
        # operation to bring the application to the initialized time.
        self.plan()
        self.execute_plan()

    # Every time the time changes the previous time needs to be recorded and the the execution of the plan need to be
    # ran.
    def change_time(self, new_time):
        self.previous_time = self.current_time
        self.current_time = new_time
        self.execute_plan()

    # Time: O(N^2) Space: O(N^2)
    # This function will plan the order of operations and store them as action objects in the scheduled plan queue so
    # that the execution plan function can operation on them.
    def plan(self):

        # This inner function will take a list of packages and return the path to the package closest to the
        # starting_location.
        def nearest_neighbor(starting_location, list_of_packages):
            lowest_mileage_seen = 1000
            best_choice = None

            for pack in list_of_packages:
                path_to_pack = self.location_graph.distance_between(starting_location,
                                                                    self.location_graph.location_name_from_address(
                                                                        pack.address))
                if path_to_pack[1][1] < lowest_mileage_seen:
                    lowest_mileage_seen = path_to_pack[1][1]
                    best_choice = pack

            return best_choice

        # This inner function is used by the optimized_trip function to check if the selected package loaded into the
        # selected truck will result in a valid delivery condition.
        def constraints_valid(truck, pack, copy_of_packages):
            result = True
            truck_copy = copy.deepcopy(truck)
            wrong_package_correction = None

            if "Delayed" in pack.constraints.keys() and pack.constraints["Deadline"]:
                if not truck.on_hold:
                    truck.hold_until(pack.constraints["Delayed"])

            elif "Delayed" in pack.constraints.keys() and "Wrong" not in pack.constraints.keys():
                if pack.constraints["Delayed"] > truck.loading_time:
                    result = False

            elif "Wrong" in pack.constraints.keys():
                fixed_wrong_address = pack.constraints["Wrong"].split(',')
                wrong_package_correction = copy.deepcopy(pack)
                wrong_package_correction.address = fixed_wrong_address[0].strip().strip('.')
                wrong_package_correction.city = fixed_wrong_address[1].strip()
                wrong_package_correction.state = fixed_wrong_address[2].strip().partition(' ')[0]
                wrong_package_correction.package_zip = fixed_wrong_address[2].strip().partition(' ')[2]
                pack = wrong_package_correction

            elif "Delivered_With" in pack.constraints.keys():
                count = 1
                for pack_id in pack.constraints["Delivered_With"]:
                    if truck.package_onboard(pack_id):
                        continue
                    elif pack_id in map(operator.attrgetter("package_id"), copy_of_packages):
                        count += 1

                if len(truck.packages) + count > 16:
                    result = False

            # If the package must be delivered on truck 2 then this operation will place it on truck 2 if it has
            # space. If there is no room then the package loading is skipped until the next loading phase.
            if "Truck" in pack.constraints.keys():
                if pack.constraints["Truck"] == 2:
                    if truck.number != 2:
                        result = False

            # So far if the result is still true then we can calculate the time and if there is a deadline associated
            # with the package then we would test it here.
            if result:
                path_to_pack = self.location_graph.distance_between(truck.last_location,
                                                                    self.location_graph.location_name_from_address(
                                                                        pack.address))

                miles_traveled = path_to_pack[1][1]

                truck.time = truck.time + timedelta(hours=(miles_traveled / travel_speed_mph))

                truck.last_location = path_to_pack[1][0]

                if pack.constraints["Deadline"]:

                    # If the package will be delivered late then set result to false.
                    if truck.time > pack.constraints["Deadline"]:
                        result = False
                    else:
                        return True

                else:
                    return True

            # If the result is false at this point then the truck needs to be reset to before it was handled by this
            # function.
            if not result:
                truck.on_hold = truck_copy.on_hold
                truck.time = truck_copy.time
                truck.loading_time = truck_copy.loading_time
                truck.holding_until = truck_copy.holding_until
                truck.last_location = truck_copy.last_location

                return False

        # This inner function will take a truck and a list of packages and load the truck with all the packages that
        # result in a valid delivery condition from the provided list of packages.
        def optimized_trip(truck, package_list):
            # A copy is made of the list so the iteration and modification of the lists are independent.
            copy_of_packages = package_list.copy()
            skipped_addresses = set(list())
            # A copy of the truck is needed so that the truck can be reset to its last good configuration easily.
            truck_copy = copy.deepcopy(truck)
            packages_loaded = []
            while copy_of_packages:
                if truck.has_space():
                    pack = nearest_neighbor(truck.last_location, copy_of_packages)
                    if pack.address not in skipped_addresses and constraints_valid(truck, pack, copy_of_packages):
                        truck.load_package(pack)
                        truck.last_location = self.location_graph.location_name_from_address(pack.address)
                        copy_of_packages.remove(pack)
                        package_list.remove(pack)
                        packages_loaded.append(pack)

                    # Hard abort this package list and reset truck to before calculating the Delivered_With packages.
                    elif "Delivered_With" in pack.constraints.keys():
                        copy_of_packages.remove(pack)
                        skipped_addresses.add(pack.address)

                        for pack_id in pack.constraints["Delivered_With"]:
                            pack_bound = self.package_manager.packages.get_package(pack_id)
                            if truck.package_onboard(pack_id):
                                truck.unload_package_id(pack_id)
                                package_list.append(pack_bound)
                            if pack_bound in copy_of_packages:
                                copy_of_packages.remove(pack_bound)
                        skipped_addresses.add(pack.address)
                        time = truck_copy.time
                        location = truck_copy.last_location
                        for packs in packages_loaded:
                            path = self.location_graph.distance_between(location,
                                                                        self.location_graph.location_name_from_address(
                                                                            packs.address))

                            miles_traveled = path[1][1]

                            time = time + timedelta(hours=(miles_traveled / travel_speed_mph))

                            location = path[1][0]

                        truck.last_location = location
                        truck.time = time

                    else:
                        copy_of_packages.remove(pack)
                        skipped_addresses.add(pack.address)

                        for loaded_pack in packages_loaded:
                            if pack.address == loaded_pack.address:
                                packages_loaded.remove(loaded_pack)
                                truck.unload_package(loaded_pack)
                                package_list.append(loaded_pack)
                else:
                    break

        virtual_truck1 = Truck(1)
        virtual_truck2 = Truck(2)

        package_priority_list = self.package_manager.priority_list()

        # Time: O(N^2) Space: O(N^2)
        # The planning function will run until all packages have been processed and a delivery has been planned for
        # them.
        loading_list = []
        while package_priority_list[0] or package_priority_list[1] or package_priority_list[2]:

            loading_truck = virtual_truck1 if virtual_truck1.trips <= virtual_truck2.trips else virtual_truck2
            loading_truck.trips += 1

            loading_truck_starting_time = loading_truck.time
            loading_truck_starting_location = loading_truck.last_location

            # Select the most optimal packages from the Delayed and Deadlined priority to load into a truck.
            optimized_trip(loading_truck, package_priority_list[0])

            # Select the most optimal packages from the Delivered With and Deadlined priority to load into a truck.
            optimized_trip(loading_truck, package_priority_list[1])

            # Select the most optimal packages from the EOD priority to load into a truck.
            optimized_trip(loading_truck, package_priority_list[2])

            loading_truck.time = loading_truck_starting_time if not loading_truck.on_hold \
                else loading_truck.holding_until
            loading_truck.last_location = loading_truck_starting_location

            # The original package priority list will be updated as packages are pulled from it so a copy is made to
            # prevent skips in the package iteration process.
            packages_on_truck_iterator = loading_truck.packages.copy()

            # Each package is processed and actions are created for them.
            for package in packages_on_truck_iterator:

                # Adds a status update action for the delayed packages that are not delayed due to a wrong address.
                if "Delayed" in package.constraints.keys():
                    if "Wrong" not in package.constraints.keys():
                        loading_list.append(Action("DelayStatus", package.constraints["Delayed"],
                                                   (loading_truck.number, package.package_id,
                                                    "Delayed on flight.", "At HUB")))

                # Adds a status update action for delayed packages due to a wrong address.
                if "Wrong" in package.constraints.keys():
                    fixed_address = package.constraints["Wrong"].split(',')
                    old_address = [package.address, package.city, package.state, package.package_zip]
                    fixed_address_action = Action("FixedAddress", package.constraints["Delayed"],
                                                  (loading_truck.number, package.package_id,
                                                   fixed_address, old_address))
                    loading_list.append(fixed_address_action)

                # Creates a Load Truck action, loads the virtual truck selected, and removes the package from the
                # priority list.
                loading_action = Action("LoadTruck",
                                        loading_truck.loading_time, (loading_truck.number, package.package_id))
                loading_list.append(loading_action)

            loading_truck_trip = self.prep_trip_actions(loading_truck)

            self.scheduled_plan_queue += loading_list + loading_truck_trip

            loading_truck.reloading()

        self.scheduled_plan_queue.sort(key=lambda action: action.time)

    # Time: O(N) Space: O(N)
    def optimize_trip_order(self, truck: Truck):

        def nearest_neighbor(starting_location, list_of_packages):
            lowest_mileage_seen = 1000
            best_choice = None

            for pack in list_of_packages:
                path_to_pack = self.location_graph.distance_between(starting_location,
                                                                    self.location_graph.location_name_from_address(
                                                                        pack.address))
                if path_to_pack[1][1] < lowest_mileage_seen:
                    lowest_mileage_seen = path_to_pack[1][1]
                    best_choice = pack

            return best_choice

        optimized_trip_actions = []
        deadline_list = []
        eod_list = []
        visited_set = set(list())

        # Time: O(N) Space: O(N)
        # First organize each package based on 2 criteria, deadline and EOD. If a package destination has already been
        # seen in the deadline list then add the current EOD package to the deadline list. This way both packages are
        # delivered simultaneously.
        for package in truck.packages:
            if package.constraints["Deadline"]:
                deadline_list.append(package)
                visited_set.add(package.address)
            else:
                if package.address in visited_set:
                    deadline_list.append(package)
                else:
                    eod_list.append(package)

        front_last_location = "Western Governors University"
        back_last_location = "Western Governors University"
        front_optimized_order = []
        back_optimized_order = []
        while deadline_list or eod_list:
            if deadline_list:
                nearest_package = nearest_neighbor(front_last_location, deadline_list)
                front_last_location = self.location_graph.location_name_from_address(nearest_package.address)
                front_optimized_order.append(nearest_package)
                deadline_list.remove(nearest_package)
            elif eod_list:
                nearest_package = nearest_neighbor(front_last_location, eod_list)
                front_last_location = self.location_graph.location_name_from_address(nearest_package.address)
                front_optimized_order.append(nearest_package)
                eod_list.remove(nearest_package)

            if eod_list:
                nearest_package = nearest_neighbor(back_last_location, eod_list)
                back_last_location = self.location_graph.location_name_from_address(nearest_package.address)
                back_optimized_order.insert(0, nearest_package)
                eod_list.remove(nearest_package)
            elif deadline_list:
                nearest_package = nearest_neighbor(back_last_location, deadline_list)
                back_last_location = self.location_graph.location_name_from_address(nearest_package.address)
                back_optimized_order.insert(0, nearest_package)
                deadline_list.remove(nearest_package)

        truck.packages = front_optimized_order + back_optimized_order

    # Time: O(N) Space: O(N)
    # Finally we create actions that will be used by the execute plan function in the optimized order.
    def prep_trip_actions(self, truck: Truck) -> list:
        trip_actions = []
        for package in truck.packages:
            # Calculate package delivery mileage for the provided order
            path_to_package = self.location_graph.distance_between(truck.last_location,
                                                                   self.location_graph.location_name_from_address(
                                                                       package.address))
            miles_traveled = path_to_package[1][1]

            trip_actions.append(Action("DeliverPackage", truck.time, (truck.number, package.package_id,
                                                                      path_to_package[0],
                                                                      path_to_package[1][0])))

            truck.time = truck.time + timedelta(hours=(miles_traveled / travel_speed_mph))

            trip_actions.append(
                Action("DeliveredPackage", truck.time, (truck.number, miles_traveled, package.package_id)))

            truck.last_location = path_to_package[1][0]
            truck.add_miles(miles_traveled)

        # Calculate return trip
        path_to_hub = self.location_graph.distance_between(truck.last_location,
                                                           "Western Governors University")
        miles_traveled = path_to_hub[1][1]

        trip_actions.append(Action("Returning", truck.time, (truck.number, miles_traveled,
                                                             truck.last_location,
                                                             "Western Governors University")))

        truck.time = truck.time + timedelta(hours=miles_traveled / travel_speed_mph)
        truck.last_location = "Western Governors University"
        truck.add_miles(miles_traveled)

        return trip_actions

    # Time: O(N) Space: O(1)
    # The execute plan will process the actions in the scheduled plan queue based on the current time.
    def execute_plan(self):
        # This branch will run if the current time is greater than the previous time. Actions are popped off the front
        # of the scheduled plan queue and their values applied.
        if self.current_time > self.previous_time:
            try:
                current_action = self.scheduled_plan_queue.pop(0)
            except IndexError:
                return

            # Actions are popped off the front of the scheduled plan queue continuously until the current time is
            # reached.
            while current_action.time <= self.current_time:

                # The truck is selected based on the current action.
                truck = None
                if current_action.value[0] == 1:
                    truck = self.truck1
                else:
                    truck = self.truck2

                # Will load the specified package onto the truck and update the package status message.
                if current_action.action_type == "LoadTruck":  # (Truck Number, Package ID)

                    package = self.package_manager.packages.get_package(current_action.value[1])
                    truck.load_package(package)

                    package.status = f"In transit via Truck {truck.number}."

                # Will update the package status message of the delayed package.
                elif current_action.action_type == "DelayStatus":  # (Truck Number, Package ID, Old Status, New Status)
                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.status = current_action.value[3]

                # Will update the package that will be delivered next.
                elif current_action.action_type == "DeliverPackage":  # (Truck Number, Package ID, Start, Destination)

                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.status = f"En route to Destination via Truck {truck.number}."

                # Updates the package that has been delivered and unloads it from the truck.
                elif current_action.action_type == "DeliveredPackage":  # (Truck Number, Miles, Package ID)

                    package = self.package_manager.packages.get_package(current_action.value[2])
                    package.status = "Delivered at " + str(current_action.time.time()) + " via Truck " + \
                                     str(current_action.value[0])
                    package.delivered = True
                    package.delivery_time = current_action.time
                    truck.add_miles(current_action.value[1])

                    truck.unload_package_id(package.package_id)

                # Makes sure to include the return trips mileage in the total.
                elif current_action.action_type == "Returning":  # (Truck Number, Miles, Last Location, HUB)
                    truck.add_miles(current_action.value[1])

                # Fixes the address of the packages with the wrong address.
                elif current_action.action_type == "FixedAddress":  # (Truck Number, Package ID, Fixed Address,
                    # Old Address)
                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.address = current_action.value[2][0].strip()
                    package.city = current_action.value[2][1].strip()
                    package.state = current_action.value[2][2].strip().partition(' ')[0]
                    package.package_zip = current_action.value[2][2].strip().partition(' ')[2]

                    package.status = "Address has been fixed. Package at HUB"

                # Inserts the action in the executed stack in a FILO order.
                self.executed_stack.insert(0, current_action)

                # Changes the current action to the next action if available.
                if len(self.scheduled_plan_queue) == 0:
                    break
                else:
                    current_action = self.scheduled_plan_queue.pop(0)

        # Will undo the actions performed so far by popping actions from the executed stack, changing statuses, and
        # reinserting actions into the scheduled plan queue.
        elif self.current_time < self.previous_time:
            try:
                current_action = self.executed_stack.pop(0)
            except IndexError:
                return

            # Will perform actions up to the current time.
            while current_action.time >= self.current_time:

                # Selects the appropriate truck to operate on.
                truck = None
                if current_action.value[0] == 1:
                    truck = self.truck1
                else:
                    truck = self.truck2

                # Unloads the package from the truck and set its status to chow it is at the HUB.
                if current_action.action_type == "LoadTruck":  # (Truck Number, Package ID)

                    package = self.package_manager.packages.get_package(current_action.value[1])
                    truck.unload_package_id(package.package_id)

                    package.status = "At HUB"

                # Change the status message on the package to show that it is delayed again.
                elif current_action.action_type == "DelayStatus":  # (Truck Number, Package ID, Old Status, New Status)
                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.status = current_action.value[2]

                # Change the package to chow that it is on a truck but not en route.
                elif current_action.action_type == "DeliverPackage":  # (Truck Number, Package ID, Start, Destination)

                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.status = f"In transit via Truck {truck.number}."

                # Undeliver the package, change the status, undue the mileage added, and reload the package onto the
                # truck.
                elif current_action.action_type == "DeliveredPackage":  # (Truck Number, Miles, Package ID)

                    package = self.package_manager.packages.get_package(current_action.value[2])
                    package.status = f"En route to Destination via Truck {truck.number}."
                    package.delivered = False
                    package.delivery_time = None
                    truck.add_miles(-current_action.value[1])

                    truck.load_package(package.package_id)

                # Undue the mileage added to the truck for the return trip.
                elif current_action.action_type == "Returning":  # (Truck Number, Miles, Last Location, HUB)
                    truck.add_miles(-current_action.value[1])

                # Change the package back to the wrong address listed and change the status back.
                elif current_action.action_type == "FixedAddress":  # (Truck Number, Package ID, Fixed Address,
                    # Old Address)
                    package = self.package_manager.packages.get_package(current_action.value[1])
                    package.address = current_action.value[3][0].strip()
                    package.city = current_action.value[3][1].strip()
                    package.state = current_action.value[3][2].strip()
                    package.package_zip = current_action.value[3][3]

                    package.status = "Wrong address provided. Will be updated soon."

                # Reinsert the action into the front of the scheduled plan queue.
                self.scheduled_plan_queue.insert(0, current_action)

                # Grab the next action from the executed stack if there are still actions available.
                if len(self.executed_stack) == 0:
                    break
                else:
                    current_action = self.executed_stack.pop(0)


class Action:

    def __init__(self, action_type, time, value):
        self.action_type = action_type
        self.time = time
        self.value = value
