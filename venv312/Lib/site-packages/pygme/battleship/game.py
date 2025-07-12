from pygme.battleship import ships, player, board
from pygme.game.game import Game


class BattleshipGame(Game):

    def __init__(self,
                 config: dict, name: str = "Battleship", difficulty: str = "normal"):
        super().__init__(name, config, difficulty)
        self.players = []
        # Each player will have their own board and fleet of ships to play with
        self.boards = {}
        self.ship_fleets = {}
        # These will change depending on the current turn
        self.current_player = None
        self.other_player = None
        self.current_player_board = None
        self.other_player_board = None
        self.other_player_fleet = None
        # These maintain current ship hit stats
        self.hits_by_player = {}
        self.ships_destroyed_by_player = {}
        self.round_information = {}

    @staticmethod
    def construct_board(length: int, width: int, game_board: board.BattleshipBoard = None) -> board.BattleshipBoard:
        """ Constructs a battleship board for the game to run on

        :param length - the length of the board
        :param width - the width of the board
        :param game_board - an optional board to use instead of instantiating one
        :returns a game board to play Battleship on
        """
        if not game_board:
            game_board = board.BattleshipBoard(length, width)
        return game_board

    def _validate_initialization(self, initialization_object: dict) -> None:
        """ Validates the Battleship game initialization

        :param initialization_object - a dictionary containing starting parameters to run the game with
        """
        self._validate_base(initialization_object)
        # A default game of Battleship includes an 8x8 board
        assert (initialization_object["board_width"] >= self.config["minimum_board_width"]
                and initialization_object["board_length"] >= self.config["minimum_board_length"])

    def _initialize(self, initialization_object: dict = None) -> None:
        """ Initializes the game of battleship by choosing a human player, receiving input about the size of the
         board, creating each player's board, and placing each player's ships

        :param initialization_object - a dictionary containing starting parameters to run the game with
        """
        # Get input from the user if no initialization_object is provided
        initialization_object = self._get_user_input(initialization_object)
        board_width = initialization_object["board_width"]
        board_length = initialization_object["board_length"]
        human_player_involved = initialization_object.get("human_player_involved", True)
        self.difficulty = initialization_object["difficulty"]
        # Create boards and fleets
        board_list = [self.construct_board(board_length, board_width) for _ in range(self.number_of_players)]
        fleet_list = [ships.ShipFleet(self.config) for _ in range(self.number_of_players)]
        # Create players and associate boards, fleets, and round information objects with each one
        for idx in range(self.number_of_players):
            player_obj = player.BattleshipPlayer(board_list[idx], difficulty=self.difficulty)
            self.players.append(player_obj)
            player_obj.place_ships(
                fleet=fleet_list[idx],
            )
            self.boards[player_obj.player_id] = board_list[idx]
            self.ship_fleets[player_obj.player_id] = fleet_list[idx]
            self.hits_by_player[player_obj.player_id] = 0
            self.ships_destroyed_by_player[player_obj.player_id] = 0
            self.round_information[player_obj.player_id] = {
                "coordinate": None,
                "successful_hit": False,
                "ship_destroyed": False,
                "already_hit": False
            }
        # Assign a random player to be the human player unless specified otherwise in initialization input
        if human_player_involved:
            self._assign_human_player()

    def _is_game_over(self) -> bool:
        """ Checks whether the game has finished and determines a winner

        :returns True if the game has finished, False otherwise
        """
        players_encountered = set()
        game_over = False
        losing_player = None
        for player_in_game in self.players:
            players_encountered.add(player_in_game)
            if self.ship_fleets[player_in_game.player_id].is_destroyed():
                # Set the player with the destroyed fleet as the loser
                player_in_game.winner = False
                losing_player = player_in_game
                game_over = True
        # Set other players as the winners if the game has ended
        if game_over:
            for encountered_player in players_encountered:
                if encountered_player != losing_player:
                    encountered_player.winner = True
        return game_over

    @staticmethod
    def _get_toggle_input() -> str:
        return input("Press b to toggle between boards or a when you're ready to make a move:")

    def _display_player_status(self, enemy_board_displayed: bool) -> None:
        """ Prints out a status consisting of number of hits and ships destroyed

        :param enemy_board_displayed - whether the enemy's board is currently displayed or not
        """
        if enemy_board_displayed:
            player_id = self.current_player.player_id
        else:
            player_id = self.other_player.player_id
        successful_hits = self.hits_by_player[player_id]
        ships_destroyed = self.ships_destroyed_by_player[player_id]
        print("Hits: {0}".format(successful_hits))
        print("Ships destroyed: {0}\n".format(ships_destroyed))

    def _display_boards(self) -> None:
        """ Displays the two players' boards by providing a toggle option to switch between the current or enemy
        player's board"""
        # Start out with the other player's board displayed
        # Hide the locations of the enemy ships whenever the enemy's board is printed out
        ship_representations_to_hide = self.other_player_fleet.unique_ship_representations
        enemy_board_displayed = True
        self.other_player_board.print(include_reference=True, ignore_characters=ship_representations_to_hide)
        print("\nYou're looking at the other player's board.\n")
        # Provide the option to switch between boards or attack
        while True:
            self._display_player_status(enemy_board_displayed)
            player_input = self._get_toggle_input()
            # Print current player's board
            if player_input == "b" and enemy_board_displayed:
                self.current_player_board.print(include_reference=True)
                enemy_board_displayed = False
                print("\nYou're looking at your board.\n")
            # Print other player's board
            elif player_input == "b":
                self.other_player_board.print(include_reference=True, ignore_characters=ship_representations_to_hide)
                enemy_board_displayed = True
                print("\nYou're looking at the other player's board.\n")
            elif player_input == "a":
                break

    def _tally_hit(self, successful_hit: bool, ship_destroyed: bool) -> None:
        """ Increments ship hit status by player based on given arguments

        :param successful_hit - whether a hit was successful or not
        :param ship_destroyed - whether a hit destroyed a ship or not
        """
        if successful_hit:
            self.hits_by_player[self.current_player.player_id] += 1
        if ship_destroyed:
            self.ships_destroyed_by_player[self.current_player.player_id] += 1

    def run(self, initialization_object: dict = None) -> dict:
        """ The Battleship game loop that performs all of the resource management and user input handling to run
        the game

        :param initialization_object - a dictionary containing starting parameters to run the game with
        """
        self._initialize(initialization_object)
        already_hit = False
        # Keep running the game as long as no one has lost
        while not self._is_game_over():
            # Continue a turn if the previous hit was not for a coordinate that has not been hit before
            if not already_hit:
                # Get the players involved and resolve the current turn
                self.current_player = self._next_player()
                current_player_id = self.current_player.player_id
                other_players = self._other_players()
                assert (len(other_players) == 1)
                self.other_player = other_players[0]
                self.current_player_board = self.boards[current_player_id]
                # Get other player's information
                self.other_player_board = self.boards[self.other_player.player_id]
                self.other_player_fleet = self.ship_fleets[self.other_player.player_id]
            # Display the boards to the current player if they're human
            if not self.current_player.computer:
                self._display_boards()
            # Attack fleet
            attack_coordinate = self.current_player.guess(self.round_information[current_player_id])
            successful_hit, ship_destroyed, already_hit = self.other_player_board.attack(
                attack_coordinate, self.other_player_fleet)
            # Keep track of round status to inform next strategy
            self.round_information[current_player_id]["coordinate"] = attack_coordinate
            self.round_information[current_player_id]["successful_hit"] = successful_hit
            self.round_information[current_player_id]["ship_destroyed"] = ship_destroyed
            self.round_information[current_player_id]["already_hit"] = already_hit
            # Keep track of successful hits and ships destroyed
            self._tally_hit(successful_hit, ship_destroyed)
        self.print_result()
        return {}
