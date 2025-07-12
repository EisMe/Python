

def resolve_movement(x_coordinate: int, y_coordinate: int, direction: str) -> tuple:
    """ Given current coordinates and a movement around a 2D grid, this function will return new coordinates that
    reflect that movement in 2 dimensional space

    :param x_coordinate - x-coordinate identifying the starting point on a 2D grid
    :param y_coordinate - y-coordinate identifying the starting point on a 2D grid
    :param direction - one of four possible directions to move in
    :returns a tuple of integers representing a new point (x-coordinate, y-coordinate)
    """
    assert direction in {'up', 'right', 'down', 'left'}
    if direction == "up":
        return x_coordinate, y_coordinate - 1
    elif direction == "right":
        return x_coordinate + 1, y_coordinate
    elif direction == "down":
        return x_coordinate, y_coordinate + 1
    elif direction == "left":
        return x_coordinate - 1, y_coordinate
