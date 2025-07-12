
def validate_user_input(input_variable: str, value_received: any, expected_type: type) -> any:
    """ Validates the given input variable value by checking if it can be converted to the expected type and if
    so, converts the variable to that type

    :param input_variable - the name of the variable to validate
    :param value_received - the value of the variable to validate
    :param expected_type an expected type that the variable should have
    returns the same variable as is or converted to the expected type that it was validated to be
    """
    expected_type_name = expected_type.__name__
    try:
        return expected_type(value_received)
    except ValueError:
        raise ValueError("Your input for {0} cannot be represented as {1}".format(input_variable, expected_type_name))


def validate_out_of_possible_options(user_input: str, options: set):
    """ Raises an exception is the given input in not contained within the given input options

    :param user_input - an input to validate
    :param options - the options that the input must be part of
    """
    if user_input not in options:
        raise ValueError("Your input of {0} is not one of {1}".format(user_input, options))


def validate_grid_index(grid_length: int, grid_width: int, x_coordinate: int, y_coordinate: int) -> bool:
    # TODO already implemented in space.py as are_coordinates_between_limits
    if x_coordinate < 0 or x_coordinate >= grid_length or y_coordinate < 0 or y_coordinate >= grid_width:
        return False
    return True
