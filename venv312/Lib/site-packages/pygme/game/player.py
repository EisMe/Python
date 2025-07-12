import uuid
import threading

from curtsies import Input


class Player(object):

    def __init__(self, computer=True):
        self.player_id = uuid.uuid4()
        self.finished_game = False
        self.computer = computer
        self.keys = {"up": "'<UP>'", "right": "'<RIGHT>'", "left": "'<LEFT>'", "down": "'<DOWN>'"}
        self.event_to_key_map = {val: key for key, val in self.keys.items()}
        self.key_pressed_map = {key: False for key in self.keys}
        self.monitoring_lock = threading.Lock()
        self.thread = None
        self.winner = False

    def _detect_key_pressed(self) -> None:
        """ Detects presses of individual keys and marks those keys as pressed in common object """
        while True:
            # Check to see if any keys have been pressed
            with Input(keynames='curtsies') as input_generator:
                for e in input_generator:
                    # Iterate over the applicable keys the player can press
                    for key in self.event_to_key_map:
                        pretty_key = self.event_to_key_map[key]
                        # If the player has pressed a key that is being tracked
                        if repr(e) == key:
                            # Signal that the key has been pressed in common object
                            self.key_pressed_map = {key: False for key in self.key_pressed_map}
                            self.key_pressed_map[pretty_key] = True
                    break
            if self.finished_game:
                break

    def monitor_key_presses(self, key: str = None, how: str = "thread") -> None:
        """ Determines how to monitor for key presses by the player; whether in a separete thread or as a blocking call

        :param key - a specific key to monitor for
        :param how - how to monitor for keys pressed (thread or block)
        """
        assert how in {"thread", "block"}
        if how == "block" and not key:
            raise ValueError("A keyboard key name must be provided to block until key is pressed")
        if how == "thread":
            self.thread = threading.Thread(target=self._detect_key_pressed, args=())
            self.thread.start()
        # TODO blocking key press

    def wait_for_player_to_finish(self):
        """ Waits for the player to finish doing an action if this is being performed in another thread """
        self.thread.join()

    def __eq__(self, other):
        return self.player_id == other.player_id

    def __ne__(self, other):
        return self.player_id != other.player_id

    def __hash__(self):
        return hash(self.player_id)
