import curses
import random
import time
from typing import List, Tuple

# Global variable to control the delay
delay = 0.1  # Initial delay in seconds

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

    while True:
        try:
            stdscr.clear()

            # Handle user input
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                snake_direction = key

            # Update snake position
            new_head = move_snake(snake_position, snake_direction)
            snake_body = update_snake_body(snake_body, new_head, snake_direction, snake_position)

            if check_collision(new_head, snake_body, food_position):
                food_position = generate_new_food_position(food_position, stdscr, snake_position)
                score += 1
                increase_speed(score)  # Call the function to increase speed

            # Draw game elements
            draw_game(stdscr, snake_body, food_position, score)
            for pos in snake_body:
                stdscr.addstr(pos[0], pos[1], "#")

            if food_position:
                stdscr.addstr(food_position[0], food_position[1], "*")

            stdscr.refresh()
        except ValueError as e:
            stdscr.addstr(0, 0, f"Error: {e}\nPress any key to continue.")
            stdscr.getch()
            stdscr.clear()

if __name__ == "__main__":
    curses.wrapper(main)

def move_snake(position, direction):
    """
    Moves the snake according to the specified direction.

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

def update_snake_body(body, new_head, direction, position):
    """Update snake body by removing tail and adding new head."""
    # Removed global keyword, instead updated snake_body by returning new list
    tail_position = get_tail_position(position, direction)
    body.remove(tail_position)
    body.append(new_head)
    return body

def get_tail_position(position, direction):
    """Determine tail position based on snake's direction."""
    x, y = position
    dx, dy = (-1 if direction in [curses.KEY_UP, curses.KEY_LEFT] else 1,
               -1 if direction in [curses.KEY_LEFT, curses.KEY_UP] else 1)
    return x + dx, y + dy


def check_collision(new_head: Tuple[int, int], body: List[Tuple[int, int]], food_position: Tuple[int, int]) -> bool:
    """
    Check for collision between new head, body, or food.

    Args:
        new_head (Tuple[int, int]): New head position of the snake.
        body (List[Tuple[int, int]]): Current body positions of the snake.
        food_position (Tuple[int, int]): Position of the food item.

    Returns:
        bool: True if a collision occurs, False otherwise.
    """
    # Validate input types and lengths
    if not isinstance(new_head, tuple) or len(new_head) != 2:
        raise ValueError("New head must be a tuple of length 2.")
    if not all(isinstance(pos, tuple) and len(pos) == 2 for pos in body):
        raise ValueError("Body positions must be tuples of length 2.")
    if not isinstance(food_position, tuple) or len(food_position) != 2:
        raise ValueError("Food position must be a tuple of length 2.")
    
    # Convert body list to a set for faster lookup
    body_set = set(body)
    
    # Check for collision with food or self
    return new_head == food_position or new_head in body_set

def generate_new_food_position(old_position, stdscr, snake_position):
    """Generate new food position outside the old one and snake position."""
    max_y, max_x = stdscr.getmaxyx()
    min_x, min_y = 1, 1  # Ensuring these are dynamic and adjust to screen size, assuming a border

    # Ensure new food position is not in the snake's position
    while old_position == snake_position or old_position in snake_position:
        old_position = [random.randint(min_x, max_x - 2), random.randint(min_y, max_y - 2)]

    return old_position

def draw_game(stdscr, snake_body, food_position, score):
    """Draw the game elements on the screen."""
    stdscr.addstr(0, 0, f"Score: {score}")
    for pos in snake_body:
        stdscr.addstr(pos[0], pos[1], "#")

    if food_position:
        stdscr.addstr(food_position[0], food_position[1], "*")
    stdscr.refresh()

def increase_speed(score):
    global delay
    if score % 10 == 0:  # Example condition
        delay *= 0.9  # Decrease the delay by 10%, making the snake move faster
        print(f"Speed increased! New delay: {delay} seconds")

def check_level(score):
    if score >= 50:  # Example threshold
        # Activate advanced mode or new features
        pass

def generate_obstacle():
    # Generate obstacle position and type
    pass

def check_collision_with_obstacle(new_head, obstacles):
    # Check if new_head collides with any obstacle
    pass

def activate_power_up(type):
    # Apply effect based on type
    pass

def check_collision_with_power_up(new_head, power_ups):
    # Check if new_head collides with any power-up
    pass

def save_high_score(score):
    # Save score to a file or database
    pass

def load_high_score():
    # Load and return the highest score
    pass

def handle_multiplayer_input(player1_key, player2_key):
    # Process inputs for both players
    pass

def play_sound_effect(effect_type):
    # Play sound effect based on type
    pass

def play_background_music():
    # Start playing background music
    pass
