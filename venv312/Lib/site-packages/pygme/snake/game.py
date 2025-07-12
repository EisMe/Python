import random
import time

from pygme.game.game import Game
from pygme.game.player import Player
from pygme.snake import snake, food


class SnakeGame(Game):
    """ Defines the main Snake game loop and initialization functionality """

    def __init__(self,
                 config: dict, name: str = "Snake", difficulty: str = "normal") -> None:
        super().__init__(name, config, difficulty)
        self.board = None
        self.snake = None
        self.food_collection = None
        self.current_food = []
        self.player = Player(computer=False)

    def _validate_initialization(self, initialization_object: dict) -> None:
        """ Ensures that the given initialization_object containing parameters to run the Snake game has complete
        and valid parameters

        :param initialization_object - a dictionary containing game parameter names and their values for operation
        """
        self._validate_base(initialization_object)
        # Validate correct board dimensions
        board_width = initialization_object["board_width"]
        board_length = initialization_object["board_length"]
        # Required min coordinates for a game of snake
        required_width = self.config.get("minimum_board_width", 10)
        required_length = self.config.get("minimum_board_length", 10)
        if initialization_object["board_width"] < required_width \
                or initialization_object["board_length"] < required_length:
            raise ValueError("The Snake board must be at least {0}x{1}".format(required_length, required_width))
        if board_width != board_length:
            raise ValueError("The Snake board must be a square where width == length")

    def _initialize(self, initialization_object: dict = None) -> None:
        """ Initializes a game of Snake from the given object of game parameters or user input if one is not provided

        :param initialization_object - a dictionary containing game parameter names and their values for operation
        """
        initialization_object = self._get_user_input(initialization_object)
        board_width = initialization_object["board_width"]
        board_length = initialization_object["board_length"]
        difficulty = initialization_object["difficulty"]
        self.board = self.construct_board(board_length, board_width)
        # Pick a random point to place the snake on and a starting snake length based on chosen difficulty
        starting_x_coordinate = random.randint(2, board_length-3)
        starting_y_coordinate = random.randint(2, board_width-3)
        starting_length = {"easy": 2, "normal": 4, "hard": 8}[difficulty]
        self.snake = snake.Snake(
            x_coordinate=starting_x_coordinate, y_coordinate=starting_y_coordinate, starting_length=starting_length)
        # Start monitoring player key presses
        self.player.monitor_key_presses()
        # Create a snake food collector and generator
        self.food_collection = food.FoodCollection(grid_width=board_width, grid_length=board_length)

    def _is_game_over(self) -> bool:
        """ Checks the board to see if the game is over

        :returns True if the game is over, False otherwise
        """
        game_over = False
        current_snake_location = self.snake.current_location
        for coordinate in current_snake_location:
            # check if any coordinate is outside of the board
            # TODO: maybe only check if the head is outside for cases when snake grows into edge
            if coordinate[0] < 0 or coordinate[0] > self.board.length - 1:
                game_over = True
                break
            elif coordinate[1] < 0 or coordinate[1] > self.board.width - 1:
                game_over = True
                break
        return game_over

    def _get_food(self) -> None:
        """ Randomly generates food into the current grid """
        # TODO this should be in config
        difficulty_to_frequency_map = {
            "normal": 5, "easy": 10, "hard": 3}
        # If there is any current food on the grid that is not eaten then just return and don't generate new food
        for current_food_obj in self.current_food:
            if not current_food_obj.eaten:
                return
        # Randomly generate food based on frequency of appearance by difficulty level
        if random.randint(1, difficulty_to_frequency_map[self.difficulty]) == 1:
            generated_food_ok = False
            generated_foods = []
            # Keep generating until the food falls in a spot where it's ok
            while not generated_food_ok:
                generated_food_ok = True
                generated_foods = self.food_collection.generate()
                for generated_food in generated_foods:
                    # Don't place food in same place as Snake's head
                    if (generated_food.x_coordinate == self.snake.current_location[0][0]
                            or generated_food.y_coordinate == self.snake.current_location[0][1]):
                        # Regenerate if food is located at Snake's head
                        generated_food_ok = False
            self.current_food = generated_foods
            return
        self.current_food = []

    def _resolve_food(self, current_snake_location: list) -> None:
        """ Makes the snake eat the food and marks the food as eaten when that happens, which makes the object
        disappear from the grid; otherwise refresh the board with each uneaten piece of food

        :param current_snake_location - a list of current snake coordinates
        """
        # Check each of the current food items on the grid
        for food_obj in self.current_food:
            # If the snake's head is in the same square as the given food, then make the snake eat the food
            if (current_snake_location[0][0] == food_obj.x_coordinate
                    and current_snake_location[0][1] == food_obj.y_coordinate):
                self.snake.eat(food_obj)
                # Marking the food object as eaten will make it disappear from the grid
                food_obj.eaten = True
            # If the food still exists, show it again on the grid
            if not food_obj.eaten:
                self.board.refresh(
                    [(food_obj.x_coordinate, food_obj.y_coordinate)],
                    representation=food_obj.representation,
                    clear_board=False
                )

    def _move_snake(self, current_direction: str) -> None:
        """ Moves the snake along the grid and checks for user input entered in separate thread

        :param current_direction - the direction the snake is current traveling in with respect to the grid
        """
        # Get directional input from the user about where to go
        snake_direction = current_direction
        for key in ["left", "right", "up", "down"]:
            # Change direction only if there is a valid directional key event in the key press map
            if self.player.key_pressed_map[key]:
                snake_direction = key
                break
        # Move the snake in either the current or new direction depending on whether player pressed a key
        self.snake.move(snake_direction)

    def _finish_game(self) -> None:
        print("Game over! Hit <Enter> to play again or <q> to exit.")
        self.player.finished_game = True
        self.player.wait_for_player_to_finish()

    def run(self, initialization_object: dict = None) -> dict:
        """ Game loop that accepts player events to move the snake around the board and keeps the state of the game
        until the game finishes

        :param initialization_object - a dictionary containing game parameter names and their values for operation
        :returns a dictionary containing various metrics and their values about the game that was played
        """
        self._initialize(initialization_object)
        representation = str(self.snake)[0]
        while True:
            current_snake_location = self.snake.current_location
            self._get_food()
            self.board.refresh(current_snake_location, representation=representation)
            self._resolve_food(current_snake_location)
            self.board.print()
            print("\nHit arrow keys on your keyboard to move the snake")
            # Get the current direction of the snake
            snake_direction = self.snake.current_direction
            self._move_snake(snake_direction)
            game_over = self._is_game_over()
            if game_over:
                self._finish_game()
                break
            else:
                time.sleep(.25)
        return {}
