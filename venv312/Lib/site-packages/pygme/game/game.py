from abc import ABC, abstractmethod
import random

from pygme.game.board import GameBoard
from pygme.utils.display import clear_console
from pygme.utils.validation import validate_user_input


class Game(ABC):

    DIFFICULTY_TYPES = {"easy", "normal", "hard"}

    def __init__(self, name: str, config: dict, difficulty: str = "normal") -> None:
        self.name = name
        self.number_of_players = config["number_of_players"]
        self.difficulty = difficulty
        self.players = []
        self.human_player = None
        self.player_turn = 0
        self.config = config
        self.required_inputs = {key: eval(key_type) for key, key_type in config["required_inputs"].items()}

    def _assign_human_player(self) -> None:
        """ Makes a random player in the list of players the human player """
        # Get random index based on length of player list
        random_index = random.randint(0, len(self.players) - 1)
        # Assign a random player in that list to be the human player
        # This player will require input from the current user while the others will play on their own
        self.players[random_index].computer = False
        self.human_player = self.players[random_index]

    def _get_user_input(self, initialization_object: dict = None) -> dict:
        """ Retrieves user input to begin a game

        :param initialization_object - some dictionary containing parameters to initialize with
        :returns the given initialization object or a newly created one if it's not provided
        """
        if not initialization_object:
            initialization_object = {}
            pre_prompt = ""
            while True:
                clear_console()
                try:
                    print("{0}Provide your inputs to begin your game. Difficulty levels: easy, normal, hard\n"
                          .format(pre_prompt))
                    for required_input, input_type in self.required_inputs.items():
                        input_val = input("Enter a value for {0}: ".format(required_input))
                        initialization_object[required_input] = validate_user_input(
                            required_input, input_val, input_type)
                    self._validate_initialization(initialization_object)
                    break
                except Exception as e:
                    pre_prompt = str(e) + "\n\n"
                    pass
        # Validate the input passed through the method arguments
        else:
            self._validate_initialization(initialization_object)
        return initialization_object

    def _next_player(self):
        """ Retrieves the next player in line to play

        :returns a player object retrieved from the list of current players
        """
        player_count = len(self.players)
        if player_count == 0:
            raise RuntimeError("There are no active players in the {0} game".format(self.name))
        # If it's the last player then get the first player in the list
        if self.player_turn == len(self.players) - 1:
            self.player_turn = 0
        # Otherwise get the next player in the list
        else:
            self.player_turn += 1
        return self.players[self.player_turn]

    def _other_players(self) -> list:
        """ Retrieves all the other players besides the one that has the current turn

        :returns a list of player objects
        """
        player_count = len(self.players)
        other_players = []
        if player_count == 0:
            raise RuntimeError("There are no active players in the {0} game".format(self.name))
        for idx in range(player_count):
            if idx == self.player_turn:
                continue
            other_players.append(self.players[idx])
        return other_players

    def print_result(self) -> None:
        """ Prints the result of the game to the user """
        print("Losers:\n")
        for player in self.players:
            if not player.winner:
                print(player.player_id)
        print("Winners:\n")
        for player in self.players:
            if player.winner:
                print(player.player_id)

    @staticmethod
    def construct_board(length: int, width: int, board: GameBoard = None) -> GameBoard:
        """ Creates a new board of the given length and width if an existing board is not provided

        :param length - the length of a new board to create
        :param width - the width of a new board to create
        :param board - an existing board to use
        """
        if not board:
            board = GameBoard(length, width)
        return board

    def _validate_base(self, initialization_object: dict) -> None:
        """ Validates the base config parameters required for any game

        :param initialization_object - a dictionary of game parameters to validate
        """
        # Validate completeness of inputs
        for required_input in self.required_inputs:
            if required_input not in initialization_object:
                raise ValueError("{0} is a required input to begin a {1} game".format(required_input, self.name))
        if initialization_object["difficulty"] not in self.DIFFICULTY_TYPES:
            raise ValueError("The game difficulty must be one of {0}".format(self.DIFFICULTY_TYPES))

    @abstractmethod
    def _validate_initialization(self, initialization_object: dict) -> None:
        pass

    @abstractmethod
    def _initialize(self, initialization_object: dict = None) -> None:
        pass

    @abstractmethod
    def _is_game_over(self) -> bool:
        pass

    @abstractmethod
    def run(self, initialization_object: dict) -> dict:
        pass
