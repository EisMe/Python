from pygme.battleship.ships import Ship, ShipFleet
from pygme.game import board

from pygme.utils import space


class BattleshipBoard(board.GameBoard):
    """ Implements specific battleship board functionality

    Constructor parameters:

    :param length - the length of the board to create
    :param width - the width of the board to create
    :param empty_square - how to represent empty squares on the board
    """
    def __init__(self, length: int, width: int, empty_square: str = "_") -> None:
        super().__init__(length, width, empty_square)

    def place_ship(self, ship: Ship) -> None:
        """ Refreshes the board with the coordinates of a given ship """
        self.refresh(ship.coordinates, ship.representation, clear_board=False)

    def attack(self, coordinate: tuple, fleet: ShipFleet) -> tuple:
        """ Accepts an attack from a player to a given fleet on the board by transmitting the attack to the fleet and
        refreshing the board with ship coordinates (which should include newly damaged segments of ships)

        :param coordinate - a tuple of x and y coordinates to attack on the board
        :param fleet - a fleet residing on the board to attack
        :returns a tuple containing booleans denoting whether a ship was successfully hit and destroyed or whether a
            ship has already been hit at the given coordinates
        """
        assert space.are_coordinates_between_limits(coordinate, self.width, self.length)
        successful_hit, ship_destroyed, already_hit = False, False, False
        if fleet.ship_is_hit(coordinate):
            already_hit = True
        else:
            # Attack the fleet
            successful_hit, ship_destroyed, representation = fleet.accept_attack(coordinate)
            # If the attack was successful, then refresh the board with the new damaged representation of the ship
            self.refresh([coordinate], representation="@", clear_board=False)
            if successful_hit:
                self.refresh([coordinate], representation, clear_board=False)
        # Emit whether the attack was successful and if a ship was destroyed
        return successful_hit, ship_destroyed, already_hit
