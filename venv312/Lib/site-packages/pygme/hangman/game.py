import string

from pygme.game.board import GameBoard
from pygme.game.game import Game
from pygme.hangman import noose
from pygme.utils import dictionary


class HangmanGame(Game):
    """ Contains the necessary logic to run a game of Hangman

    Constructor parameters:

    @param config - the configuration dictionary to use for the game (should be defined in data packaged with pygme)
    @param name - the name of the game to feed to parent class
    @param difficulty - a difficulty to assume (provided by user during initialization)
    """

    def __init__(self, config: dict, name: str = "hangman", difficulty: str = "normal") -> None:
        super().__init__(name, config, difficulty)
        self.dictionary = None
        self.noose = None
        self.min_word_length = None
        self.max_word_length = None
        self.guessed_characters = set()
        self.board = None
        self.noose = None
        self.word = None

    def _validate_initialization(self, initialization_object: dict) -> None:
        """ Validates the initialization object to ensure a Hangman game can occur

        :param initialization_object - required game parameters to follow
        """
        self._validate_base(initialization_object)

    def _initialize(self, initialization_object: dict = None) -> None:
        """ Initializes the game of Hangman

        :param initialization_object - an optional dictionary containing the required game parameters to use
        """
        initialization_object = self._get_user_input(initialization_object)
        self.difficulty = initialization_object["difficulty"]
        self.dictionary = dictionary.Dictionary(self.config)
        word_sizes_by_difficulty = self.config["word_sizes_by_difficulty"][self.difficulty]
        self.min_word_length = word_sizes_by_difficulty["min_word_length"]
        self.max_word_length = word_sizes_by_difficulty["max_word_length"]
        self.board = GameBoard(self.config["board_length"], self.config["board_width"], " ")
        self.noose = noose.Noose(self.board)
        self.noose.draw()

    def _has_won(self) -> bool:
        """ Checks whether the player has won the game by checking if all the letters in the word have been guessed

        :returns True if the game has been won; False otherwise
        """
        for letter in self.word:
            if letter not in self.guessed_characters:
                return False
        return True

    def _man_died(self) -> bool:
        """ Checks whether the man has died by checking if the noose is complete

        :returns True if the man is dead; False otherwise
        """
        return self.noose.is_complete()

    def _is_game_over(self) -> bool:
        """ Checks whether the game has finished from two possible options - the player has won (guessed all letters) or
        the man has died

        :returns True if the game is over; False otherwise
        """
        if self._has_won() or self._man_died():
            return True
        return False

    def _display_word(self) -> None:
        """ Prints the current word to be guessed by hiding characters that have not been guessed yet when displaying
        the word to the user """
        if not self.guessed_characters:
            self.word.hide_all = True
        else:
            self.word.hide_all = False
            self.word.show_only = self.guessed_characters
        print("Word to guess:\n{0}\n".format(repr(self.word)))
        print("Guessed character: {0}\n".format(self.guessed_characters))

    def _display_final_status(self) -> None:
        """ Displays a message to let the user know how they did after the game finishes """
        self.word.show_only = set()
        self.word.hide_all = False
        print("\nThe word was: {0}\n".format(repr(self.word)))
        if self._has_won():
            print("Congratulations, you won!")
        else:
            print("Better luck next time!")

    def _get_guess_input(self) -> str:
        """ Accepts string input from the user to be the next guess (for monkeypatching instead of built-in input func)

        :returns the string input received from the user
        """
        return input("Enter a character to guess next:")

    def _get_guess(self) -> str:
        """ Retrieves a letter guess from the user and validates it before returning it to be used in the game

        :returns a single ASCII character to be the next letter guess in the game
        """
        guess_valid = False
        guess = None
        while not guess_valid:
            guess = self._get_guess_input()
            # Ensure the guess has not been already provided
            if guess in self.guessed_characters:
                print("You already guessed that character. Try again.")
            # There must be a guess
            elif len(guess) > 1:
                print("You can only enter one character at a time")
            # The guess must be either a lowercase or upper case letter
            elif guess not in string.ascii_letters:
                print("Guesses must be one of {0}".format(string.ascii_letters))
            else:
                guess_valid = True
        self.guessed_characters.add(guess)
        return guess

    def run(self, initialization_object: dict = None) -> dict:
        """ Runs the game of Hangman

        :param initialization_object - an optional dictionary containing the required game parameters to use
        """
        self._initialize(initialization_object)
        self.word = self.dictionary.get_random_word(min_length=self.min_word_length, max_length=self.max_word_length)
        assert len(self.word) > 1
        while not self._is_game_over():
            # Display noose and word on board
            self.board.print(join_char="")
            self._display_word()
            guess = self._get_guess()
            # Get the noose to display a new piece if the guess is wrong
            if guess not in self.word:
                self.noose.update()
            # Update the current noose on the board to be displayed to the user
            self.noose.draw()
        self.board.print(join_char="")
        self._display_final_status()
        return {}
