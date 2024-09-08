import curses
import random
import time
from typing import List, Tuple
import pygame

# Global variable to control the delay
delay = 0.1  # Initial delay in seconds
level = 1  # Starting level

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# Define power-up types
POWER_UP_TYPES = ['speed', 'grow', 'slow']

# Define game dimensions
max_x, max_y = 100, 100  # Set default game dimensions, should be dynamically determined

def main(stdscr):
    """Main game loop."""
    global delay, level, max_x, max_y
    stdscr.clear()
    curses.curs_set(0)

    # Get terminal size dynamically
    max_y, max_x = stdscr.getmaxyx()
    min_x, min_y = 1, 1

    # Initialize snake and food positions
    snake_position = [10, 10]
    snake_body = [{10, 10}, {10, 11}]
    snake_direction = curses.KEY_RIGHT
    score = 0
    food_position = generate_new_food_position(
        food_position, stdscr, snake_position)

    # Initialize power-ups and obstacles
    power_ups = []
    obstacles = []

    # Initialize background music
    play_background_music("background_music.mp3")  # Replace with your music file

    while True:
        try:
            stdscr.clear()

            # Handle user input
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                # Only change direction if it's not the opposite of the current direction
                if not (key == curses.KEY_UP and snake_direction == curses.KEY_DOWN or 
                        key == curses.KEY_DOWN and snake_direction == curses.KEY_UP or
                        key == curses.KEY_LEFT and snake_direction == curses.KEY_RIGHT or
                        key == curses.KEY_RIGHT and snake_direction == curses.KEY_LEFT):
                    snake_direction = key

            # Update snake position
            new_head = move_snake(snake_position, snake_direction)
            snake_body = update_snake_body(
                snake_body, new_head, snake_direction, snake_position)

            # Check for collisions
            if check_collision(new_head, snake_body, food_position):
                food_position = generate_new_food_position(
                    food_position, stdscr, snake_position)
                score += 1
                # Example usage of power-up
                power_up = generate_power_up()
                power_ups.append(power_up)
                delay = apply_power_up_effect(power_up['type'], snake_body, delay)
                increase_speed(score)
            elif check_collision_with_obstacle(new_head, obstacles):
                # Handle collision with an obstacle
                print("Game Over! You hit an obstacle.")
                break
            # Optimized power-up collision check
            elif (power_up := check_collision_with_power_up(new_head, power_ups)):
                delay = apply_power_up_effect(power_up['type'], snake_body, delay)

            # Draw game elements
            draw_game(
                stdscr, snake_body, food_position, score, power_ups, obstacles)

            # Check and adjust game parameters based on current level
            check_level(score)

            # Control game speed
            time.sleep(delay)

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
    """Update snake body by removing tail and adding new head.

    Args:
        body (list): The current snake body.
        new_head (tuple): The new head position.
        direction (str): The moving direction of the snake.
        position (dict): A dictionary containing positions related to the snake's movement.

    Returns:
        list: The updated snake body.
    """
    # Optimization 1: Efficient tail removal
    del body[0] 

    # Add the new head to the updated body
    body.append(new_head)

    return body


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

    # Check for collision with food
    if new_head == food_position:
        return True

    # Check for collision with self (skip the head)
    for pos in body[1:]:
        if new_head == pos:
            return True

    return False


def generate_new_food_position(old_position, stdscr, snake_position):
    """Generate new food position outside the old one and snake position."""
    max_y, max_x = stdscr.getmaxyx()
    # Ensuring these are dynamic and adjust to screen size, assuming a border
    min_x, min_y = 1, 1

    # Ensure new food position is not in the snake's position
    while old_position == snake_position or old_position in snake_position:
        old_position = [random.randint(
            min_x, max_x - 2), random.randint(min_y, max_y - 2)]

    return old_position

def draw_game(stdscr, snake_body, food_position, score, power_ups, obstacles):
    """Draw the game elements on the screen."""
    stdscr.addstr(0, 0, f"Score: {score}")
    for pos in snake_body:
        stdscr.addstr(pos[0], pos[1], "#")

    if food_position:
        stdscr.addstr(food_position[0], food_position[1], "*")

    for power_up in power_ups:
        stdscr.addstr(power_up['position'][0], power_up['position'][1], "P")

    for obstacle in obstacles:
        stdscr.addstr(obstacle['position'][0], obstacle['position'][1], "O")

    stdscr.refresh()

def increase_speed(score):
    global delay, level
    # Increase speed every 10 points scored
    if score % 10 == 0 and score != 0:
        delay *= 0.9  # Decrease the delay by 10%, making the snake move faster
        level += 1  # Increase the level
        print(f"Level Up! You are now on Level {level}. New delay: {delay} seconds")

def check_level(score):
    """Check the current level based on score and adjust game parameters accordingly."""
    global level
    # Example of adjusting game parameters based on level (this is a placeholder)
    # For demonstration, we're just printing the level, but you could add more logic here
    print(f"Current Level: {level}")
    # Placeholder for other level-based adjustments


def generate_obstacle():
    # Define possible obstacle types
    OBSTACLE_TYPES = ['small', 'large']

    # Generate random position for the obstacle
    x = random.randint(0, max_x - 2)  # Ensure within the screen boundaries
    y = random.randint(0, max_y - 2)

    # Select a random type of obstacle
    obstacle_type = random.choice(OBSTACLE_TYPES)

    # Return the obstacle as a dictionary
    return {'position': (x, y), 'type': obstacle_type}

def check_collision_with_obstacle(new_head, obstacles):
    """
    Checks if the new_head collides with any obstacles.

    :param new_head: A tuple (x, y) representing the new position.
    :param obstacles: A list of tuples, each representing the coordinates of an obstacle.
    :return: True if there is a collision, False otherwise.
    """
    for obstacle in obstacles:
        if new_head == obstacle['position']:
            return True
    return False


def activate_power_up(type):
    """
    Applies the effect of a power-up based on its type.
    
    Args:
    - type: A string indicating the type of power-up to activate.
    
    Returns:
    None
    """
    print(f"Activated power-up: {type}")

def check_collision_with_power_up(new_head, power_ups):
    """
    Checks if the new_head collides with any power-up and removes the collided power-up.

    Args:
    - new_head (tuple): A tuple (x, y) representing the new head position.
    - power_ups (list): A list of dictionaries, each representing a power-up.

    Returns:
    - dict: The power-up dictionary if a collision occurs, None otherwise.
    """
    for i, power_up in enumerate(power_ups):
        if new_head == power_up['position']:
            return power_ups.pop(i)  # Remove and return the collided power-up
    return None  # No collision found

def save_high_score(score):
    """
    Saves the given score to a file named 'high_scores.txt'.
    
    Args:
        score (int): The score to be saved.
    """
    try:
        # Open the file in append mode; create it if it doesn't exist
        with open('high_scores.txt', 'a') as file:
            # Write the score followed by a newline character
            file.write(f"{score}\n")
    except Exception as e:
        print(f"An error occurred while saving the score: {e}")

def load_high_score():
    """
    Loads and returns the highest score from the 'high_scores.txt' file.
    
    Returns:
        int: The highest score found in the file, or None if the file is empty or does not exist.
    """
    try:
        # Attempt to open the file in read mode
        with open('high_scores.txt', 'r') as file:
            scores = file.readlines()
            if scores:
                # Convert scores to integers and find the maximum
                max_score = max(int(score.strip()) for score in scores)
                return max_score
            else:
                return None
    except FileNotFoundError:
        # File does not exist
        return None
    except Exception as e:
        print(f"An error occurred while loading the high score: {e}")
        return None

def handle_multiplayer_input(player1_key, player2_key):
    """
    Processes inputs for both players.
    
    Args:
    - player1_key: The key pressed by player 1.
    - player2_key: The key pressed by player 2.
    
    Returns:
    None
    """
    if player1_key == 'a':
        print("Player 1 pressed 'a'")
    if player2_key == 'd':
        print("Player 2 pressed 'd'")

def play_sound_effect(effect_type):
    """
    Plays a sound effect based on the given type.
    
    Args:
    - effect_type: A string indicating the type of sound effect to play.
    
    Returns:
    None
    """
    print(f"Playing sound effect: {effect_type}")

    # Replace this with actual sound effect playback based on effect_type

def play_background_music(file_path):
    # Initialize pygame mixer
    pygame.mixer.init()

    # Load the background music
    pygame.mixer.music.load(file_path)

    # Start playing the background music
    pygame.mixer.music.play(-1)  # The argument -1 means the music will loop indefinitely

def apply_power_up_effect(power_up_type, snake_body, delay):
    """
    Applies the effect of a power-up based on its type.

    Args:
    - power_up_type (str): The type of power-up to activate.
    - snake_body (list): The current body positions of the snake.
    - delay (float): The current delay in seconds.

    Returns:
    float: Updated delay value.
    """
    if power_up_type == "speed":
        delay *= 0.9  # Decrease the delay by 10%, making the snake move faster
        print("Speed power-up activated!")
    elif power_up_type == "grow":
        # Grow the snake by adding extra segments
        for _ in range(3):
            tail = snake_body[0].copy()
            snake_body.insert(0, tail)
        print("Grow power-up activated!")
    elif power_up_type == "slow":
        delay *= 1.1  # Increase the delay by 10%, slowing down the snake
        print("Slow power-up activated!")
    else:
        print(f"Unknown power-up type: {power_up_type}")

    return delay

def generate_power_up():
    """
    Generates a random power-up and its position.

    Returns:
    - dict: A dictionary containing the power-up type and position.
    """
    x = random.randint(1, max_x - 2)
    y = random.randint(1, max_y - 2)
    power_up_type = random.choice(POWER_UP_TYPES)
    return {'position': (x, y), 'type': power_up_type}