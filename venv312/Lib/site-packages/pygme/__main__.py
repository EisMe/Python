import argparse
import json
import os
import pkg_resources

from pygme.snake.game import SnakeGame
from pygme.battleship.game import BattleshipGame
from pygme.hangman.game import HangmanGame

SUPPORTED_GAMES = {"snake": SnakeGame, "battleship": BattleshipGame, "hangman": HangmanGame}


def _load_config() -> dict:
    """ Gets a config object from a JSON file packaged up with the distribution

    :returns a dictionary with key-value config parameters
    """
    directory_path = pkg_resources.resource_filename('pygme', 'data/')
    full_path = os.path.join(directory_path, "config.json")
    with open(full_path, "r") as f:
        config = json.load(f)
    return config


def _validate_config(config: dict) -> None:
    """ Validates a given config dictionary by raising exceptions when something is off before starting a game

    :param config - a configuration dictionary to validate
    """
    # Check to ensure that each game has an entry in the package's config
    for game_name in SUPPORTED_GAMES:
        if game_name not in config:
            raise ValueError("The provided config in pygme/data/config.json must have settings for {0}".format(
                game_name))


def _parse_args():
    """ Parse arguments passed in via the CLI
    :returns a parsed argument object from argparse
    """
    parser = argparse.ArgumentParser()
    # Accept the operation to perform
    parser.add_argument(
        'game', choices=[game_name for game_name, game_obj in SUPPORTED_GAMES.items() if game_obj],
        help="choose the game to play")
    return parser.parse_args()


def main():
    # Load configuration and validate it
    config = _load_config()
    _validate_config(config)
    # Get arguments from CLI
    args = _parse_args()
    # Instantiate and run corresponding game class with provided config
    game_class = SUPPORTED_GAMES[args.game]
    if not game_class:
        raise RuntimeError("Game is unavailable. Check back later!")
    game_config = config[args.game]
    # Assume a default dictionary if none provided for word games
    game_config["dictionary_filename"] = game_config.get("dictionary_filename", "dictionary.txt")
    game_object = game_class(config=game_config)
    game_object.run()


if __name__ == "__main__":
    main()
