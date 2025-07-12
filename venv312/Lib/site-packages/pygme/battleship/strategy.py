from pygme.game import strategy
from pygme.battleship import board
from pygme.utils import space


class RandomGuessStrategy(strategy.Strategy):

    def __init__(self, game_board: board.BattleshipBoard, name: str = "Random Guess"):
        super().__init__(game_board, name)
        self.targets = []

    def guess(self, information: dict) -> tuple:
        """ Guesses a coordinate to attack purely at random

        :param information - the information about the last round (not used)
        :returns a coordinate tuple to attack next
        """
        guess = self._random_guess()
        self.already_guessed.add(guess)
        return guess


class HuntTargetStrategy(strategy.Strategy):
    """ Hunt/Target guessing strategy

    - If the last hit was successful and a ship has yet to be destroyed, add adjacent squares to stack
    - If the last hit was successful and a ship was sunk, empty the current stack
    - Always guess the last target in the stack (Target)
    - If the stack is empty, return a random guess (Hunt)

    Constructor parameters:

    @param game_board - a Battleship board on which the game is being played
    @param name - the name of the strategy
    """
    def __init__(self, game_board: board.BattleshipBoard, name: str = "Hunt and Target"):
        super().__init__(game_board, name)
        self.targets = []

    def _add_coordinates_to_targets(self, coordinates: list) -> None:
        """ Adds the given list of coordinates to the stack of target coordinates to attack

        :param coordinates - a list of coordinates to target
        """
        for coordinate in coordinates:
            if coordinate not in self.targets:
                self.targets.append(coordinate)

    def guess(self, information: dict) -> tuple:
        """ Guesses a coordinate to attack based on previous information according to the Hunt/Target strategy

        :param information - the information about the last round to base the guessing decision on
        :returns a coordinate tuple to attack next
        """
        self._process_information(information)
        guess = tuple()
        valid_guess = False
        while not valid_guess:
            if not self.previous_coordinate_attacked:
                break
            # Target mode: previous attack resulted in hit but did not destroy ship so add adjacent squares to stack
            if (self.previous_attack_hit and not self.previous_attack_sank_ship
                    and self.previous_coordinate_attacked not in self.already_guessed):
                coordinates = space.get_adjacent_coordinates(
                    self.previous_coordinate_attacked, self.game_board.width, self.game_board.length)
                self._add_coordinates_to_targets(coordinates)
            # Previous attack sank ship so empty the list of targets and resume hunt mode with random guess
            elif self.previous_attack_sank_ship:
                self.targets = []
            # The last target will always be first guess if there are targets available; otherwise it will be random
            if len(self.targets) > 0:
                guess = self.targets.pop()
            else:
                guess = self._random_guess()
            if guess not in self.already_guessed:
                valid_guess = True
            self.already_guessed.add(self.previous_coordinate_attacked)
        return guess


class ProbabilityDensityStrategy(strategy.Strategy):

    def __init__(self, game_board: board.BattleshipBoard, name: str = "Random Guess"):
        super().__init__(game_board, name)
        self.targets = []

    def guess(self, information: dict) -> tuple:
        """ Guesses a coordinate to attack based on the probability densities of each ship

        :param information - the information about the last round
        :returns a coordinate tuple to attack next
        """
        raise NotImplementedError
