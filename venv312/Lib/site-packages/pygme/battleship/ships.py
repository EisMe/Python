

class Ship(object):
    """ Represents a ship in the game of Battleship

    Constructor arguments:

    :param ship_type - one of the possible ship types in the game
    :param size - the size of the ship in number of grid squares
    :param representation - how the ship will be represented on a Battleship grid
    :param damaged_representation - how damaged ship segments will be represented on a Battleship grid
    """
    def __init__(self, ship_type, size, representation="0", damaged_representation="*") -> None:
        self.ship_type = ship_type
        self.size = size
        self.representation = representation
        self.damaged_representation = damaged_representation
        # Ship starts out without being placed on the grid and no destroyed segments
        self.coordinates = set()
        self.destroyed_coordinates = set()
        self.placed = False
        self.destroyed = False

    def is_destroyed(self) -> bool:
        """ Checks whether the ship has been destroyed and updates state if so

        :returns True if the ship has been destroyed, False otherwise
        """
        self.destroyed = False
        coordinate_length, destroyed_length = len(self.coordinates), len(self.destroyed_coordinates)
        if coordinate_length > 0 and destroyed_length > 0 and len(self.coordinates - self.destroyed_coordinates) == 0:
            self.destroyed = True
        return self.destroyed

    def place_ship(self, coordinates: list) -> None:
        """ Places the current ship by accepting the given coordinates (assumes ship is being placed on a 2D grid)

        :param coordinates - a list of x and y coordinate tuples
        """
        for coordinate in coordinates:
            self.coordinates.add(coordinate)
        self.placed = True
        self.destroyed = False
        self.destroyed_coordinates = set()

    def get_representation(self, coordinate: tuple) -> str:
        """ Returns the ship segment representation at the given coordinate depending on whether that segment is
        destroyed or not

        :param coordinate - a tuple of x-coordinate, y-coordinate for the segment to return
        :returns a character representation of the ship's segment at the given coordinate
        """
        representation = None
        # Segment is destroyed so return the damaged representation
        if coordinate in self.destroyed_coordinates:
            representation = self.damaged_representation
        # Segment is intact so ship is represented normally
        elif coordinate in self.coordinates:
            representation = self.representation
        return representation

    def take_damage(self, coordinate: tuple) -> tuple:
        """ Accepts damage at the given coordinate

        :param coordinate - tuple of x-coordinate, y-coordinate that was attacked
        :returns a tuple containing booleans for whether the attack was successful and if the ship has been destroyed
        """
        successful_hit, destroyed = False, False
        # Take damage only if part of the ship is on the coordinate
        if coordinate in self.coordinates and coordinate not in self.destroyed_coordinates:
            self.destroyed_coordinates.add(coordinate)
            successful_hit, destroyed = True, self.is_destroyed()
        return successful_hit, destroyed

    def __repr__(self) -> str:
        return "{0} of size {1} with coordinates {2}".format(self.ship_type, self.size, self.coordinates)

    def __str__(self) -> str:
        return "{0} of size {1}".format(self.ship_type, self.size)


class ShipFleet(dict):
    """ Keeps and manages a collection of ships in a dictionary where each ship type is the key and values are ship
    objects

    Constructor arguments:

    :param config - a configuration dictionary containing information on ship types, sizes, etc.
    """
    def __init__(self, config: dict) -> None:
        self.destroyed = False
        assert "ship_types" in config and "size_by_type" in config
        ship_types = config.get("ship_types", set())
        size_by_type = config.get("size_by_type", {})
        super().__init__({
            ship_type: Ship(ship_type, size) for ship_type, size in size_by_type.items() if ship_type in ship_types
        })

    def is_destroyed(self) -> bool:
        """ Checks whether the fleet has been destroyed and updates state accordingly

        :returns True if every ship in the fleet has been destroyed, False if at least 1 has not been destroyed
        """
        self.destroyed = True
        for _, ship in self.items():
            ship_destroyed = ship.is_destroyed()
            # If any one ship is still alive then the fleet is also still alive
            if not ship_destroyed:
                self.destroyed = False
        return self.destroyed

    def ship_is_hit(self, coordinate: tuple) -> bool:
        """ Checks whether a ship in the fleet has already been hit at the given coordinate

        :param coordinate - a tuple of x and y coordinates to check for hits
        :returns True if a ship has already been hit, False otherwise
        """
        for _, ship in self.items():
            if coordinate in ship.destroyed_coordinates:
                return True
        return False

    def accept_attack(self, coordinate: tuple) -> tuple:
        """ Accepts an attack on the fleet by transmitting the damage to a ship in the fleet

        :param coordinate - a tuple of x and y coordinates that are being attacked
        :returns whether there has been a successful hit and a ship has been destroyed and the new ship segment repr
        """
        successful_hit, ship_destroyed, representation = False, False, None
        for _, ship in self.items():
            successful_hit, ship_destroyed = ship.take_damage(coordinate)
            if successful_hit:
                representation = ship.get_representation(coordinate)
                break
        return successful_hit, ship_destroyed, representation

    def _print(self, print_function) -> str:
        """ Utility method for repr and str magic methods to print the fleet and each ship in it

        :param print_function - either repr or str to use for representing individual ship objects when printing the
            fleet object
        :returns a string representation of the fleet collection object
        """
        return_str = "Ship fleet: "
        for _, ship in self.items():
            return_str += "{0}, ".format(print_function(ship))
        return return_str[:-2]

    @property
    def unique_ship_representations(self) -> set:
        """ Provides a collection of unique ship representation characters when displayed in the terminal

        :returns a set of representation characters
        """
        ship_representations = set()
        for _, ship in self.items():
            ship_representations.add(ship.representation)
        return ship_representations

    def __repr__(self) -> str:
        return self._print(repr)

    def __str__(self) -> str:
        return self._print(str)
