import os
import pkg_resources
import random
import sys


class Word(object):
    """ Represents a word in a dictionary. Used to provide supplements to existing str class by not taking into
    account capitalization when comparing words and hiding certain characters when returning the word to a caller.

    Constructor parameters:

    @param word - a regular string word
    @param show_only - an optional set containing characters to exclude from the word when repr or str are called
    """

    def __init__(self, word: str, show_only: set = None):
        super().__init__()
        if " " in word:
            raise ValueError("The given word {0} contains whitespace".format(word))
        self.word = word.lower()
        self.show_only = show_only
        self.hide_all = False
        if not show_only:
            self.show_only = set()

    def __len__(self):
        return len(self.word)

    def __contains__(self, letter: str) -> bool:
        """ Checks whether the given letter is within the word without taking capitalization into account

        For example:
        "a" in action == True
        "A" in action == True
        "p" in action == False

        :param letter - the letter to check
        :returns True if the letter is in the word, False otherwise
        """
        return letter.lower() in self.word

    def __repr__(self) -> str:
        """ When repr() is called on the string, exclude characters not in the self.show_only set if it's nonempty

        :returns either the string as is or the string with excluded
        """
        return_str = self.word
        if self.show_only or self.hide_all:
            return_str = ""
            # Only show characters that are in the given show_only set
            for char in self.word:
                if char.lower() in self.show_only or char.upper() in self.show_only:
                    return_str += char
                else:
                    return_str += "_"
        return return_str

    def __str__(self) -> str:
        return self.__repr__()

    def __setattr__(self, key: str, value: any) -> None:
        """ Overrides the set attribute functionality to always take the lowercase of a word

        For example:
        my_word = Word("hello")
        my_word.word = "Hi"
        my_word.word == "hi" # True

        :param key - the object attribute to set
        :param value - the value to assign to the attribute
        """
        # Any attribute other than word will be set normally and word will always be taken as lowercase
        self.__dict__[key] = value
        if key == "word":
            self.__dict__[key] = value.lower()

    def __iter__(self):
        yield from self.word


class Dictionary(object):
    """ Represents a dictionary to get words from for word games

    Constructor arguments:

    :param config - a configuration dictionary containing the file packaged up with pygme containing all words
    """
    def __init__(self, config: dict) -> None:
        self.dictionary_filename = config["dictionary_filename"]
        self.words = []
        self._load_dictionary()

    def _load_dictionary(self):
        """ Reads the dictionary file specified in the config assumed to be stored in data subdirectory """
        directory_path = pkg_resources.resource_filename('pygme', 'data/')
        full_path = os.path.join(directory_path, self.dictionary_filename)
        with open(full_path, "r") as f:
            words = f.readlines()
        self.words = [Word(word.strip("\n")) for word in words]

    def get_random_word(self, min_length: int = 1, max_length: int = sys.maxsize) -> str:
        """ Retrieves a random word with length between the given minimum and max length arguments

        :param min_length - the minimum length that the word should have
        :param max_length - the maximum length that the word should have

        :returns a random word from the dictionary matching the given length criteria
        """
        eligible_words = [word for word in self.words if min_length <= len(word) <= max_length]
        return random.choice(eligible_words)
