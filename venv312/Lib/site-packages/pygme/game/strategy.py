from abc import ABC, abstractmethod

from pygme.game import board
from pygme.utils import space


class Strategy(ABC):
    """ Provides an interface for different game strategies

    Constructor parameters:

    @param game_board - a board on which the game is being played
    @param name - the name of the strategy
    """
    def __init__(self, game_board: board.GameBoard, name: str) -> None:
        self.game_board = game_board
        self.name = name
        self.previous_coordinate_attacked = None
        self.previous_attack_hit = False
        self.previous_attack_sank_ship = False
        self.already_guessed = set()

    def _process_information(self, information: dict) -> None:
        """ Retrieves the required pieces information needed to make a guess

        @param information - information about the previous round to base the guessing decision on
        """
        self.previous_coordinate_attacked = information["coordinate"]
        self.previous_attack_hit = information["successful_hit"]
        self.previous_attack_sank_ship = information["ship_destroyed"]

    def _random_guess(self) -> tuple:
        """ Guess randomly from the list of grid coordinates not already guessed

        :returns a tuple of X and Y coordinates
        """
        return space.get_coordinates_between_limits(
            self.game_board.width, self.game_board.length, exclusion_set=self.already_guessed)

    @abstractmethod
    def guess(self, information: dict) -> tuple:
        pass
