from pygme.utils.display import clear_console
from pygme.utils.validation import validate_grid_index
from pygme.utils.space import are_coordinates_between_limits


class GameBoard(object):
    """ Represents a base board to play a game on which may be extended by more specific types of boards

    Constructor arguments:

    :param length - the length of the board to create
    :param width - the width of the board to create
    :param empty_square - how to represent empty squares on the board
    """
    def __init__(self, length: int, width: int, empty_square: str = "_") -> None:
        assert length > 0 and width > 0
        self.length = length
        self.width = width
        self.empty_square = empty_square
        self.board = []
        self._create_board()

    def is_square_clear(self, coordinate: tuple) -> bool:
        """ Returns True if the square at a given coordinate is empty; False if it's not empty

        :param coordinate - an x,y coordinate to check
        :returns whether the given coordinate is empty in the board
        """
        assert are_coordinates_between_limits(coordinate, self.width, self.length)
        if self.board[coordinate[0]][coordinate[1]] == self.empty_square:
            return True
        return False

    def _create_board(self) -> None:
        """ Creates an empty 2D list with the given board dimensions"""
        for i in range(self.length):
            self.board.append([self.empty_square for _ in range(self.width)])

    def print(self, include_reference: bool = False, ignore_characters: set = None, join_char: str = " ") -> None:
        """ Prints out the board to stdout

        :param include_reference - whether to include grid references when printing the board out in the console
        :param ignore_characters - a collection of characters to replace with empty characters
        :param join_char - how to join a row list together to produce a row on the terminl screen
        """
        # Clear the terminal
        clear_console()
        if not ignore_characters:
            ignore_characters = set()
        # Add an index before each column if applicable
        if include_reference:
            header_items = [str(x) for x in range(self.length)]
            header = "    "
            for item in header_items:
                if len(item) == 1:
                    header += item + "   "
                else:
                    header += item + "  "
            print(header)
        # Print the board
        for i in range(self.width):
            # Print an index before each row if applicable
            header = ""
            space = ""
            if include_reference:
                header = "{0}".format(i)
                if len(header) == 1:
                    space = " " * 3
                else:
                    space = " " * 2
                row_string = ""
                for square in range(self.length):
                    column_spacing = "   "
                    if self.board[square][i] and self.board[square][i] not in ignore_characters:
                        row_string += self.board[square][i]
                    else:
                        row_string += self.empty_square
                    row_string += column_spacing
                print(header + space + row_string + "\n")
            else:
                row_string = join_char.join([self.empty_square if (not self.board[square][i]
                                                                   or self.board[square][i] in ignore_characters)
                                             else self.board[square][i] for square in range(self.length)])
                print(row_string)

    def clear(self) -> None:
        """ Clears the current board by replacing every square with the given empty square character """
        for i in range(self.width):
            for j in range(self.length):
                self.board[j][i] = self.empty_square

    def refresh(self,
                coordinates: list, representation: str, clear_board: bool = True) -> None:
        """ Refreshes the board by adding the given representation character to the given coordinates

        Example: representation = '*' at coordinates [(0, 1), (2, 1)] on a 3x3 board will result in the following:
        _ _ _
        * _ *
        _ _ _

        :param coordinates - a list of coordinate tuples to update
        :param representation - the character to be placed in the given coordinates
        :param clear_board - whether to first clear the current board before placing the new characters or not
        """
        # Clear the current board first if the provided argument is true
        if clear_board:
            self.clear()
        for coordinate_tuple in coordinates:
            x_coordinate, y_coordinate = coordinate_tuple[0], coordinate_tuple[1]
            # Only refresh the board with the coordinate if the coordinate is valid
            if validate_grid_index(self.length, self.width, x_coordinate, y_coordinate):
                # Refresh the board
                self.board[x_coordinate][y_coordinate] = representation

    def __repr__(self):
        return "GameBoard ({0} by {1})".format(self.length, self.width)

    def __str__(self):
        return self.__repr__()
