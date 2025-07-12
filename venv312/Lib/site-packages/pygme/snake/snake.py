from pygme.game import movement


class Node(object):
    """ Represents each node in the body of the snake """

    def __init__(self, x_coordinate: int, y_coordinate: int, direction: str,
                 representation: str = '*', next_node=None, prev_node=None) -> None:
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.direction = direction
        self.representation = representation
        self.next_node = next_node
        self.prev_node = prev_node

    def __repr__(self):
        return self.representation

    def __str__(self):
        return self.__repr__()


class Body(object):
    """ Represents the body of the snake; Defines common functionality for growing and moving """

    def __init__(self, x_coordinate: int, y_coordinate: int, length: int = 1, direction: str = "left") -> None:
        self.x_coordinate = x_coordinate
        self.y_coordinate = y_coordinate
        self.head = Node(x_coordinate, y_coordinate, direction)
        self.tail = self.head
        self.length = 1
        self.direction = direction
        # Grow the body to the desired initial length
        if length > 1:
            self.grow(length - 1)

    @property
    def coordinates(self) -> list:
        coordinates_list = []
        tmp_node = self.head
        while tmp_node:
            coordinates_list.append((tmp_node.x_coordinate, tmp_node.y_coordinate))
            tmp_node = tmp_node.next_node
        return coordinates_list

    def change_direction(self, new_direction: str) -> None:
        """ Changes the current body's direction of movement

        :param new_direction - one of four possible directions to move the body in
        """
        opposite_direction = {"left": "right", "right": "left", "down": "up", "up": "down"}[self.direction]
        # Only change the current direction if it's not opposite of the current direction
        if new_direction != opposite_direction:
            self.direction = new_direction

    @staticmethod
    def _create_new_node(direction: str, prev_node: Node):
        x_coordinate = None
        y_coordinate = None
        if direction == "left":
            x_coordinate = prev_node.x_coordinate + 1
            y_coordinate = prev_node.y_coordinate
        elif direction == "right":
            x_coordinate = prev_node.x_coordinate - 1
            y_coordinate = prev_node.y_coordinate
        elif direction == "up":
            x_coordinate = prev_node.x_coordinate
            y_coordinate = prev_node.y_coordinate + 1
        elif direction == "down":
            x_coordinate = prev_node.x_coordinate
            y_coordinate = prev_node.y_coordinate - 1
        new_node = Node(x_coordinate, y_coordinate, direction, prev_node=prev_node)
        return new_node

    def grow(self, by: int = 1) -> None:
        """ Grows the current body by the specified amount of nodes

        :param by - the number of nodes to grow the body by
        """
        assert by > 0
        new_node_chain = None
        last_node = None
        # Create a new chain of nodes to append to the end of the body
        for new_node_num in range(by):
            # Create the first node in the chain
            if new_node_num == 0:
                new_node_chain = self._create_new_node(direction=self.tail.direction, prev_node=self.tail)
                last_node = new_node_chain
            # Create all the other nodes after the first one and add them to the chain
            else:
                tmp_node = self._create_new_node(direction=last_node.direction, prev_node=last_node)
                last_node.next_node = tmp_node
                last_node = tmp_node
        # Integrate the new chain as part of the current body
        self.tail.next_node = new_node_chain
        self.tail = last_node
        self.length += by

    def slither(self, speed: float = 1.0) -> None:
        """ Moves the body in its current direction of movement

        :param speed - the speed to move the body in
        """
        # Each node will assign its direction and coordinate to the next node
        tmp_node = self.head.next_node
        tmp_x_coordinate = self.head.x_coordinate
        tmp_y_coordinate = self.head.y_coordinate
        while tmp_node:
            new_x_coordinate = tmp_node.x_coordinate
            new_y_coordinate = tmp_node.y_coordinate
            tmp_node.x_coordinate = tmp_x_coordinate
            tmp_node.y_coordinate = tmp_y_coordinate
            tmp_node = tmp_node.next_node
            tmp_x_coordinate = new_x_coordinate
            tmp_y_coordinate = new_y_coordinate
        # Once all other nodes have moved, the head moves to new location
        self.head.x_coordinate, self.head.y_coordinate = movement.resolve_movement(
            self.head.x_coordinate, self.head.y_coordinate, self.direction)

    def __repr__(self):
        node_list = []
        tmp_node = self.head
        while tmp_node:
            node_list.append(str(tmp_node))
            tmp_node = tmp_node.next_node
        return "-".join(node_list)

    def __str__(self):
        return self.__repr__()


class Snake(object):
    """ Represents the snake itself

    Constructor arguments:

    :param x_coordinate - the starting x-coordinate of the snake's head
    :param y_coordinate - the starting y-coordinate of the snake's head
    :param starting_length - the snake's starting node length
    :param starting_direction - the starting direction of movement that the snake will immediately head in
    """
    def __init__(self,
                 x_coordinate: int, y_coordinate: int,
                 starting_length: int = 1, starting_direction: str = "left") -> None:
        self.body = Body(x_coordinate, y_coordinate, length=starting_length, direction=starting_direction)

    @property
    def current_location(self) -> list:
        """ Retrieves a list of coordinate tuples representing the snake's location on a snake grid

        Example: [(0,1), (1,1)] is a 2 node long snake and on a 3 x 3 grid will look like this:

        _ _ _
        * * _
        _ _ _

        :returns a list of coordinate tuples
        """
        return self.body.coordinates

    @property
    def current_direction(self) -> str:
        """ Retrieves the snake's current direction of movement

        :returns a direction string (left, up, right, down)
        """
        return self.body.direction

    def eat(self, food_to_eat: any) -> None:
        """ Eats a given food and makes the snake grow by the food's growth value

        :param food_to_eat - a food object as defined in food.py
        """
        self.body.grow(food_to_eat.growth_value)

    def move(self, new_direction: str) -> None:
        """ Moves the snake by changing the direction to the new direction and altering the corresponding
        coordinates based on that direction of movement

        :param new_direction - the direction of movement (left, up, right, down)
        """
        # Change direction
        self.body.change_direction(new_direction)
        # Move
        self.body.slither()

    def __repr__(self):
        return self.body.__repr__()

    def __str__(self):
        return self.body.__str__()
