import curses
import random

def main(stdscr):
    """Main game loop."""
    stdscr.clear()
    curses.curs_set(0)

    # Initialize snake and food positions
    snake_position = [10, 10]
    snake_body = [{10, 10}, {10, 11}]
    snake_direction = curses.KEY_RIGHT
    score = 0
    food_position = [20, 20]

    score = 0

    while True:
        stdscr.clear()

        # Handle user input
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
            snake_direction = key

        # Update snake position
        new_head = move_snake(snake_position, snake_direction)
        update_snake_body(snake_position, new_head, snake_direction)

        if check_collision(new_head, snake_body, food_position):
            food_position = generate_new_food_position(food_position, stdscr)
            score += 1

        # Draw game elements
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

def update_snake_body(position, new_head, direction):
    """Update snake body by removing tail and adding new head."""
    global snake_body
    tail_position = get_tail_position(position, direction)
    snake_body.remove(tail_position)
    snake_body.add(new_head)

def get_tail_position(position, direction):
    """Determine tail position based on snake's direction."""
    x, y = position
    dx, dy = (-1 if direction in [curses.KEY_UP, curses.KEY_LEFT] else 1,
               -1 if direction in [curses.KEY_LEFT, curses.KEY_UP] else 1)
    return x + dx, y + dy

def check_collision(new_head, body, food_position):
    """Check for collision between new head, body, or food."""
    return new_head == food_position or new_head in body

def generate_new_food_position(old_position, stdscr):
    """Generate new food position outside the old one."""
    max_y, max_x = stdscr.getmaxyx()
    new_x = (old_position[0] + random.choice([-1, 1])) % (max_x - 2) + min_x
    new_y = (old_position[1] + random.choice([-1, 1])) % (max_y - 2) + min_y

    return [new_x, new_y]

def draw_game(stdscr, snake_body, food_position, score):
    """Draw the game elements on the screen."""
    stdscr.addstr(0, 0, f"Score: {score}")
    for pos in snake_body:
        stdscr.addstr(pos[0], pos[1], "#")

    if food_position:
        stdscr.addstr(food_position[0], food_position[1], "*")


        stdscr.refresh()
