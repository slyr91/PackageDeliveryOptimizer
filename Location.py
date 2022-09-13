class Location:

    def __init__(self, name, address):
        self.name = name
        self.address = address


class LocationGraph:

    #  Time: O(N)    Space: O(N)
    # Location information is imported from the WGUPS Distance Table.csv file and converted into location objects. The
    # distance information is also imported in this function and is stored in a dictionary data structure.
    def __init__(self):
        location_file = open('WGUPS Distance Table.csv', 'r', encoding='UTF-8', newline='\r\n')

        location_name_addresses = location_file.readline().partition(',,"')[2].split('","')

        self.locations = []
        # Time: O(N)    Space: O(N)
        for location in location_name_addresses:
            part_location = location.split("\n")
            location_name = part_location[0]
            address = ""
            for i in range(1, len(part_location)):
                address += part_location[i]
                if " Sta " in address:
                    address = address.replace(" Sta ", " Station ")
            location_node = Location(location_name.strip(), address.replace('"', '').strip())
            self.locations.append(location_node)

        distance_row = location_file.readline()
        self.location_edges = {}
        # Time: O(N)    Space: O(N)
        while distance_row != "":
            part_distance_row = distance_row.partition('",')
            row_name = part_distance_row[0].replace('"', '').partition("\n")[0].strip()
            if row_name not in self.location_edges:
                self.location_edges[row_name] = {}
            distance_values = part_distance_row[2].split(",")[1:]

            for i in range(len(distance_values)):
                if distance_values[i] == '' or distance_values[i] == '\r\n':
                    continue
                # edge = (row_name, locations[i].name, distance_values[i].strip('\r\n'))
                self.location_edges[row_name][self.locations[i].name] = float(distance_values[i].strip('\r\n'))

            distance_row = location_file.readline()

    def location_name_from_address(self, address):
        for location in self.locations:
            if address == location.address:
                return location.name

        return None

    # This function will attempt to return the distance between 2 locations. Because the location distance data is
    # reflective, if there doesn't exist a distance value from start to destination then there might exist a distance
    # value from destination to start.
    def distance_between(self, start, destination):
        shortest_path_to_destination = [start]

        # Each node is reach able from either the start or destination node so both must be tested.
        if destination in self.location_edges[start].keys():
            shortest_path_to_destination.append((destination, self.location_edges[start][destination]))
        elif start in self.location_edges[destination].keys():
            shortest_path_to_destination.append((destination, self.location_edges[destination][start]))
        else:
            # This branch is unlikely to occur.
            shortest_path_to_destination = None

        return shortest_path_to_destination


# TODO create a method to trim the location graph so that the nodes are all connected via the shortest path.
# basically every location node will connect to one other node using the shortest distance between nodes.
# This will trim down the complete graph into a connected graph.

