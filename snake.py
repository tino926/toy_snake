import curses
import random

def main(stdscr):
    # Clear screen and turn off cursor blinking
    stdscr.clear()
    curses.curs_set(0)

    # Set up the snake
    snake_position = [10, 10]
    snake_body = [[10, 10], [10, 11]]
    snake_direction = curses.KEY_RIGHT

    # Set up the food
    food_position = [20, 20]

    score = 0

    while True:
        stdscr.clear()

        # Get user input
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            snake_direction = key
        else:
            continue

        # Move the snake
        new_head = move_snake(snake_position, snake_direction)

        snake_body.insert(0, new_head)

        if check_collision(new_head, snake_body, food_position):
            food_position = generate_new_food_position(food_position, stdscr)
            score += 1
        else:
            snake_body.pop()

        draw_game(stdscr, snake_body, food_position, score)
        for pos in snake_body:
            stdscr.addstr(pos[0], pos[1], "#")

        if food_position:
            stdscr.addstr(food_position[0], food_position[1], "*")

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)

def move_snake(position, direction):
    """
    Moves the snake according to the specified direction.

    This function takes the snake's current position and the direction of 
    movement as inputs, and returns the new position after the move. Directions 
    are represented by key values defined in the curses library, including up, 
    down, left, and right.

    Parameters:
    position: A list of two integers representing the snake's current coordinate 
    position, [x, y]. direction: An integer representing the direction in which 
    the snake is moving, using key values from the curses library.

    Returns:
    A list of two integers representing the snake's new coordinate position 
    after moving, [x, y].
    """
    # Calculates the snake's new position based on the given direction
    if direction == curses.KEY_DOWN:
        return [position[0] + 1, position[1]]
    elif direction == curses.KEY_UP:
        return [position[0] - 1, position[1]]
    elif direction == curses.KEY_LEFT:
        return [position[0], position[1] - 1]
    elif direction == curses.KEY_RIGHT:
        return [position[0], position[1] + 1]
    else:
        raise ValueError("Invalid direction")

def check_collision(new_head, body, food_position):
    """
    Check if a collision occurs in the game.

    This function is used to determine if the new head of the snake collides 
    with the food or the body of the snake.

    Parameters:
    new_head (tuple): The coordinates of the new head of the snake.
    body (list): The list of coordinates for the snake's body.
    food_position (tuple): The coordinates of the food.

    Returns:
    bool: True if a collision occurs, False otherwise.
    """
    # Check if the new head of the snake collides with the food or the body
    return new_head == food_position or new_head in body

def generate_new_food_position(old_position, stdscr):
    max_y, max_x = stdscr.getmaxyx()
    min_x, min_y = 1, 1  # Assuming the top-left corner is (1, 1)

    # Calculate a new position that is outside the bounds of the old position
    new_x = (old_position[0] + random.choice([-1, 1])) % (max_x - 2) + min_x
    new_y = (old_position[1] + random.choice([-1, 1])) % (max_y - 2) + min_y

    return [new_x, new_y]

def draw_game(stdscr, snake_body, food_position, score):
    stdscr.addstr(0, 0, f"Score: {score}")
    for pos in snake_body:
        stdscr.addstr(pos[0], pos[1], "#")

    if food_position:
        stdscr.addstr(food_position[0], food_position[1], "*")


