from abc import ABC

from pygme.game.board import GameBoard


class Part(ABC):
    """ A base Part interface to be inherited by different types of concrete parts

    Constructor parameters:

    @param part - the name of the part
    @param part_char_map - how the part will be represented to the user on a grid
    """
    def __init__(self, part: str, part_char_map: dict):
        self.part = part
        self.part_char_map = part_char_map

    def __repr__(self):
        return self.part_char_map[self.part]

    def __str__(self):
        return self.__repr__()


class BodyPart(Part):
    """ Represents part of the man in Hangman

    Constructor parameters:

    @param part - the name of the part
    """

    PART_CHAR_MAP = {
        "head": "O",
        "left_arm": "-",
        "right_arm": "-",
        "left_leg": "/",
        "right_leg": "\\",
        "body": "|"
    }

    def __init__(self, part: str):
        super().__init__(part, self.PART_CHAR_MAP)


class NoosePart(Part):
    """ Represents part of noose in Hangman

    Constructor parameters:

    @param part - the name of the part
    """

    PART_CHAR_MAP = {
        "base": "_",
        "top": "_",
        "pole": "|",
        "rope": "|"
    }

    def __init__(self, part: str):
        super().__init__(part, self.PART_CHAR_MAP)


class Noose(object):
    """ Combines noose and body parts together to make up the Hangman noose that is displayed to the user

    Constructor parameters:

    @param game_board - the board to draw the noose on
    """
    def __init__(self, game_board: GameBoard) -> None:
        self.game_board = game_board
        self.noose_components = [
            # The base of the noose and rope
            {"x_index": 0, "y_index": 5, "part": NoosePart("base"), "displayed": True},
            {"x_index": 1, "y_index": 5, "part": NoosePart("pole"), "displayed": True},
            {"x_index": 2, "y_index": 5, "part": NoosePart("base"), "displayed": True},
            {"x_index": 1, "y_index": 4, "part": NoosePart("pole"), "displayed": True},
            {"x_index": 1, "y_index": 3, "part": NoosePart("pole"), "displayed": True},
            {"x_index": 1, "y_index": 2, "part": NoosePart("pole"), "displayed": True},
            {"x_index": 1, "y_index": 1, "part": NoosePart("pole"), "displayed": True},
            {"x_index": 2, "y_index": 0, "part": NoosePart("top"), "displayed": True},
            {"x_index": 3, "y_index": 0, "part": NoosePart("top"), "displayed": True},
            {"x_index": 4, "y_index": 1, "part": NoosePart("rope"), "displayed": True},
            # The body
            {"x_index": 4, "y_index": 2, "part": BodyPart("head"), "displayed": False},
            {"x_index": 4, "y_index": 3, "part": BodyPart("body"), "displayed": False},
            {"x_index": 3, "y_index": 3, "part": BodyPart("left_arm"), "displayed": False},
            {"x_index": 5, "y_index": 3, "part": BodyPart("right_arm"), "displayed": False},
            {"x_index": 3, "y_index": 4, "part": BodyPart("left_leg"), "displayed": False},
            {"x_index": 5, "y_index": 4, "part": BodyPart("right_leg"), "displayed": False},
        ]
        self.next_piece = self.get_last_displayed() + 1

    def draw(self) -> None:
        """ Refreshes the associated grid with the latest noose representation """
        self.game_board.clear()
        for component in self.noose_components:
            if not component["displayed"]:
                continue
            part = component["part"]
            coordinate = (component["x_index"], component["y_index"])
            self.game_board.refresh([coordinate], repr(part), clear_board=False)

    def is_complete(self) -> bool:
        """ Checks whether all components have been displayed, meaning the noose is complete

        :returns True if the entire noose has been build during the course of the Hangman game; False otherwise
        """
        complete = True
        for component in self.noose_components:
            if not component["displayed"]:
                complete = False
        return complete

    def get_last_displayed(self) -> int:
        """ Retrieves the last component of the Hangman noose that is currently displayed to the user

        :returns an index to the last displayed component in the noose_components class attribute
        """
        complete_idx = len(self.noose_components) - 1
        for idx, component in enumerate(self.noose_components):
            if not component["displayed"]:
                complete_idx = idx - 1
                break
        return complete_idx

    def update(self) -> None:
        """ Updates the noose by displaying a new component """
        if not self.is_complete():
            component_to_update = self.noose_components[self.next_piece]
            component_to_update["displayed"] = True
            self.next_piece += 1
