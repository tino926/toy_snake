import curses
import random
import time
from typing import List, Tuple
import pygame
from collections import deque

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# --- Constants ---
# Define game dimensions
MAX_X = 40  # Set default game width
MAX_Y = 20  # Set default game height
FRAME_RATE = 30  # Target frames per second
# Define power-up types
POWER_UP_TYPES = ['speed', 'grow', 'slow']
# Define level-up criteria
POINTS_PER_LEVEL = 10
SPEED_INCREASE_PER_LEVEL = 0.9
# Define initial game speed (delay)
INITIAL_DELAY = 0.1
# Define power-up duration in seconds
POWER_UP_DURATION = 5 

# --- Game State ---


class GameState:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.delay = INITIAL_DELAY
        self.snake_body = deque([(10, 10), (10, 11)])
        self.snake_direction = curses.KEY_RIGHT
        self.food_position = self.generate_new_food_position()
        self.power_ups = []  # Now a list of dictionaries: {'type': ..., 'expiration_time': ...}
        self.obstacles = []

    def generate_new_food_position(self):
        """Generate new food position, avoiding snake and obstacles."""
        while True:
            new_position = (
                random.randint(1, MAX_X - 2),
                random.randint(1, MAX_Y - 2),
            )
            if (
                new_position not in self.snake_body
                and new_position != self.food_position
                and all(new_position != obstacle['position'] for obstacle in
                        self.obstacles)
            ):
                return new_position

# --- Game Functions ---


def main(stdscr):
    """Main game loop."""
    global MAX_X, MAX_Y
    curses.curs_set(0)
    stdscr.nodelay(True)  # Make getch() non-blocking
    # Set a timeout for consistent frame rate
    stdscr.timeout(int(1000 / FRAME_RATE))

    # Get terminal size dynamically, adjust game dimensions if needed
    max_y, max_x = stdscr.getmaxyx()
    MAX_X = min(MAX_X, max_x - 2)
    MAX_Y = min(MAX_Y, max_y - 2)

    game_state = GameState()

    # Initialize background music (replace with your music file)
    play_background_music("background_music.mp3")

    # --- Game Loop Timing ---
    target_frame_time = 1.0 / FRAME_RATE  # Target time per frame
    last_frame_time = time.perf_counter()

    while True:
        # --- Calculate time since last frame ---
        current_time = time.perf_counter()
        elapsed_time = current_time - last_frame_time
        last_frame_time = current_time

        try:
            # --- Handle user input ---
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT,
                         curses.KEY_RIGHT]:
                # Only change direction if it's not the opposite of the current
                # direction
                if (key, game_state.snake_direction) not in [
                    (curses.KEY_UP, curses.KEY_DOWN),
                    (curses.KEY_DOWN, curses.KEY_UP),
                    (curses.KEY_LEFT, curses.KEY_RIGHT),
                    (curses.KEY_RIGHT, curses.KEY_LEFT),
                ]:
                    game_state.snake_direction = key

            # --- Update game state ---
            # Only update if enough time has passed since the last update
            if elapsed_time >= game_state.delay:
                new_head = move_snake(game_state.snake_body[-1],
                                      game_state.snake_direction)

                # Wall teleport
                new_head = (new_head[0] % MAX_Y, new_head[1] % MAX_X)

                game_state.snake_body.append(new_head)

                # Check for collisions
                if check_collision(new_head, game_state.snake_body,
                                   game_state.food_position):
                    game_state.food_position = game_state.generate_new_food_position()
                    game_state.score += 1
                    # Example usage of power-up
                    if random.random() < 0.1:  # 10% chance to spawn a power-up
                        game_state.power_ups.append(generate_power_up(current_time))
                    
                    # Apply power-up effects immediately upon pickup
                    game_state.delay = apply_power_up_effect(
                        game_state.power_ups, game_state.snake_body,
                        game_state.delay, current_time
                    )
                    increase_speed(game_state)
                else:
                    game_state.snake_body.popleft()  # Remove tail if no food eaten

                if any(check_collision(new_head, game_state.snake_body,
                                       obstacle['position']) for obstacle in
                       game_state.obstacles):
                    # Handle collision with an obstacle
                    print("Game Over! You hit an obstacle.")
                    break

                # Optimized power-up collision check
                collided_power_up = next(
                    (
                        power_up
                        for power_up in game_state.power_ups
                        if check_collision(new_head, game_state.snake_body,
                                           power_up['position'])
                    ),
                    None,
                )
                if collided_power_up:
                    game_state.power_ups.remove(collided_power_up)
                    game_state.delay = apply_power_up_effect(
                        [collided_power_up], game_state.snake_body,
                        game_state.delay, current_time
                    )

                # Check for game over (collision with self ONLY)
                if game_over(new_head, game_state.snake_body):
                    print("Game Over!")
                    break

                # --- Adjust delay for next frame based on level ---
                game_state.delay = INITIAL_DELAY / game_state.level

            # --- Draw game elements ---
            stdscr.clear()
            draw_game(stdscr, game_state)

            # Check and adjust game parameters based on current level
            check_level(game_state)

            # --- Sleep to maintain frame rate ---
            sleep_time = target_frame_time - \
                (time.perf_counter() - current_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        except ValueError as e:
            stdscr.addstr(0, 0, f"Error: {e}\nPress any key to continue.")
            stdscr.getch()


def move_snake(position, direction):
    """
    Moves the snake according to the specified direction.
    """
    if direction == curses.KEY_DOWN:
        return position[0] + 1, position[1]
    elif direction == curses.KEY_UP:
        return position[0] - 1, position[1]
    elif direction == curses.KEY_LEFT:
        return position[0], position[1] - 1
    elif direction == curses.KEY_RIGHT:
        return position[0], position[1] + 1
    else:
        raise ValueError("Invalid direction")


def check_collision(new_head, snake_body, target_position):
    """
    Check for collision between new head and another position.
    """
    return new_head == target_position or new_head in list(snake_body)[:-1]


def draw_game(stdscr, game_state):
    """Draw the game elements on the screen."""
    stdscr.addstr(0, 0, f"Score: {game_state.score} Level: {game_state.level}")
    for pos in game_state.snake_body:
        stdscr.addstr(pos[0], pos[1], "#")
    if game_state.food_position:
        stdscr.addstr(
            game_state.food_position[0], game_state.food_position[1], "*")
    for power_up in game_state.power_ups:
        stdscr.addstr(power_up['position'][0], power_up['position'][1], "P")
    for obstacle in game_state.obstacles:
        stdscr.addstr(obstacle['position'][0], obstacle['position'][1], "O")
    stdscr.refresh()


def increase_speed(game_state):
    """Increase speed every 10 points scored."""
    if game_state.score % POINTS_PER_LEVEL == 0 and game_state.score != 0:
        game_state.level += 1


def check_level(game_state):
    """Check the current level and adjust game parameters accordingly."""
    # Example (add more logic as needed based on game_state.level):
    if game_state.level > 1 and len(game_state.obstacles) < game_state.level // 2:
        game_state.obstacles.append(generate_obstacle())


def generate_obstacle():
    """Generates a random obstacle."""
    while True:
        x = random.randint(1, MAX_X - 2)
        y = random.randint(1, MAX_Y - 2)
        new_obstacle = {'position': (
            x, y), 'type': random.choice(['small', 'large'])}
        # Ensure the obstacle doesn't spawn on top of other game elements
        if (
            new_obstacle['position'] not in game_state.snake_body
            and new_obstacle['position'] != game_state.food_position
            and all(
                new_obstacle['position'] != power_up['position']
                for power_up in game_state.power_ups
            )
        ):
            return new_obstacle


def game_over(new_head, snake_body):
    """Check if the game is over (only collision with self)."""
    return new_head in list(snake_body)[:-1]


def play_sound_effect(effect_type):
    """Plays a sound effect based on the given type."""
    # Add your sound effect logic here
    print(f"Playing sound effect: {effect_type}")


def play_background_music(file_path):
    """Plays background music."""
    try:
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"Error playing background music: {e}")


def apply_power_up_effect(power_ups, snake_body, delay, current_time):
    """Applies the effect of collected power-ups."""
    for power_up in power_ups:
        if power_up['type'] == "speed":
            delay *= 0.9  # Increase speed
        elif power_up['type'] == "grow":
            for _ in range(3):
                snake_body.appendleft(snake_body[0])  # Grow the snake
        elif power_up['type'] == "slow":
            delay *= 1.1  # Decrease speed

        # Set expiration time for the power-up
        power_up['expiration_time'] = current_time + POWER_UP_DURATION
    return delay


def generate_power_up(current_time):
    """Generates a random power-up with an expiration time."""
    x = random.randint(1, MAX_X - 2)
    y = random.randint(1, MAX_Y - 2)
    power_up_type = random.choice(POWER_UP_TYPES)
    return {'position': (x, y), 'type': power_up_type, 'expiration_time': current_time + POWER_UP_DURATION}


if __name__ == "__main__":
    curses.wrapper(main)
