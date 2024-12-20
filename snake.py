import curses
import random
import time
from typing import List, Tuple, Dict
import pygame
from collections import deque

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# --- Constants ---
MAX_X = 40
MAX_Y = 20
FRAME_RATE = 30
POWER_UP_TYPES = ['speed', 'grow', 'slow', 'obstacle_remove']
POINTS_PER_LEVEL = 10
SPEED_INCREASE_PER_LEVEL = 0.9
INITIAL_DELAY = 0.1
POWER_UP_DURATION = 5
OBSTACLE_COUNT_PER_LEVEL = 2
SNAKE_COLLISION_ENABLED = True
SNAKE_GROWTH_ON_FOOD = 1

# Score Multiplier
SCORE_MULTIPLIER_WINDOW = 2  # Seconds
score_multiplier_time = None
score_multiplier = 1

# Invincibility Power-Up
INVINCIBILITY_DURATION = 3  # Seconds

class GameState:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.delay = INITIAL_DELAY
        self.snake_body = deque([(10, 10), (10, 11)])
        self.snake_direction = curses.KEY_RIGHT
        self.food_position = self.generate_new_item_position()
        self.power_ups: List[Dict] = []
        self.obstacles: List[Dict] = []
        self.paused = False
        self.invincible = False
        self.invincibility_end_time = 0

    def generate_new_item_position(self):
        """Generate new position for food or power-ups, avoiding collisions."""
        while True:
            new_position = (
                random.randint(1, MAX_Y - 2),
                random.randint(1, MAX_X - 2),
            )
            if (
                new_position not in self.snake_body
                and new_position != self.food_position
                and all(new_position != obstacle['position'] for obstacle in self.obstacles)
                and all(new_position != power_up.get('position') for power_up in self.power_ups)
            ):
                return new_position


def main(stdscr):
    """Main game loop."""
    global MAX_X, MAX_Y, SNAKE_COLLISION_ENABLED, SNAKE_GROWTH_ON_FOOD, score_multiplier_time, score_multiplier
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(int(1000 / FRAME_RATE))

    max_y, max_x = stdscr.getmaxyx()
    MAX_X = min(MAX_X, max_x - 2)
    MAX_Y = min(MAX_Y, max_y - 2)

    game_state = GameState()

    # Start background music AFTER initializing curses
    play_background_music("background_music.mp3")  # Replace with your actual music file

    target_frame_time = 1.0 / FRAME_RATE
    last_frame_time = time.perf_counter()

    while True:
        current_time = time.perf_counter()
        elapsed_time = current_time - last_frame_time
        last_frame_time = current_time

        try:
            # Handle Input (Improvement 1: consolidate input handling)
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == ord('p'):
                game_state.paused = not game_state.paused
                stdscr.addstr(MAX_Y // 2, MAX_X // 2 - 4, "Paused" if game_state.paused else "      ")  # Toggle pause message
                stdscr.refresh() #Immediately reflect pause status
                continue # Skip the rest of the loop if paused


            elif key == ord('c'):
                SNAKE_COLLISION_ENABLED = not SNAKE_COLLISION_ENABLED
                message = "Snake Collision: ON" if SNAKE_COLLISION_ENABLED else "Snake Collision: OFF"
                stdscr.addstr(0, MAX_X // 2 - len(message) // 2, message)
                stdscr.timeout(0)  # Non-blocking getch() for the pause
                stdscr.getch()  # Wait for any key press
                stdscr.timeout(int(1000/FRAME_RATE))  # Restore timeout for game loop
            elif key == ord('+') and SNAKE_GROWTH_ON_FOOD < 5:
                SNAKE_GROWTH_ON_FOOD += 1
            elif key == ord('-') and SNAKE_GROWTH_ON_FOOD > 1:
                SNAKE_GROWTH_ON_FOOD -= 1


            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT] and not game_state.paused:
                if (key, game_state.snake_direction) not in [
                    (curses.KEY_UP, curses.KEY_DOWN),
                    (curses.KEY_DOWN, curses.KEY_UP),
                    (curses.KEY_LEFT, curses.KEY_RIGHT),
                    (curses.KEY_RIGHT, curses.KEY_LEFT),
                ]:
                    game_state.snake_direction = key

           # Game Logic (Improvement 2: Apply power-ups before moving)
            if elapsed_time >= game_state.delay and not game_state.paused:

                game_state.delay = apply_power_up_effect(game_state, current_time) # Apply BEFORE moving

                new_head = move_snake(game_state.snake_body[-1], game_state.snake_direction)


                # Teleport
                new_head = (new_head[0] % MAX_Y, new_head[1] % MAX_X)


                if check_collision(new_head, game_state.snake_body, game_state.food_position, game_state.obstacles, game_state):
                    
                    game_state.food_position = game_state.generate_new_item_position(
                        food=True)

                    if score_multiplier_time and current_time - score_multiplier_time <= SCORE_MULTIPLIER_WINDOW:
                        score_multiplier += 1
                    else:
                        score_multiplier = 1
                    score_multiplier_time = current_time

                    game_state.score += 1 * score_multiplier
                    for _ in range(SNAKE_GROWTH_ON_FOOD):
                        game_state.snake_body.append(game_state.snake_body[-1])


                    if random.random() < 0.15:
                        game_state.power_ups.append(
                            generate_power_up(current_time, game_state))

                else:
                    game_state.snake_body.popleft()

                if game_state.invincible and current_time > game_state.invincibility_end_time:
                    game_state.invincible = False

                #Append the new head after potential growth/powerup application.
                game_state.snake_body.append(new_head)



                if not game_state.invincible:
                   #Check for obstacle collisions
                    for obstacle in list(game_state.obstacles):
                        if check_collision(new_head, game_state.snake_body, obstacle['position'], game_state.obstacles, game_state):
                            raise ValueError("Game Over! You hit an obstacle.")
                    if SNAKE_COLLISION_ENABLED and game_over(new_head, game_state.snake_body):
                       raise ValueError("Game Over! You ran into yourself.")


                #Power-Up Pickup
                for power_up in list(game_state.power_ups):
                    if check_collision(new_head, game_state.snake_body, power_up['position'], game_state.obstacles, game_state):
                        if power_up['type'] == 'invincible':
                            game_state.invincible = True
                            game_state.invincibility_end_time = current_time + INVINCIBILITY_DURATION
                        #Note: Effects are now applied before the move.

                        game_state.power_ups.remove(power_up)


            # Drawing and Level Updates
            stdscr.clear()
            draw_game(stdscr, game_state, score_multiplier)
            increase_speed(game_state)
            check_level(game_state)



            sleep_time = target_frame_time - (time.perf_counter() - current_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

        except ValueError as e:
            game_over_screen(stdscr, str(e), game_state.score)
            break



def move_snake(position, direction):
    """Moves the snake."""
    if direction == curses.KEY_DOWN:
        return position[0] + 1, position[1]
    elif direction == curses.KEY_UP:
        return position[0] - 1, position[1]
    elif direction == curses.KEY_LEFT:
        return position[0], position[1] - 1
    elif direction == curses.KEY_RIGHT:
        return position[0], position[1] + 1
    else:
        return position  # Don't raise an error, just return current position


def check_collision(new_head, snake_body, target_position, obstacles, game_state):
    """Checks for collision with target position or snake body."""
    global score_multiplier_time, score_multiplier

    if new_head == target_position:
        if score_multiplier_time and current_time - score_multiplier_time <= SCORE_MULTIPLIER_WINDOW:
            score_multiplier += 1
        else:
            score_multiplier = 1
        score_multiplier_time = current_time
        return True
    if new_head in list(snake_body)[:-1]: # Exclude the tail from self-collision check
        return True

    return False


def draw_game(stdscr, game_state, score_multiplier):
    """Draws the game elements."""
    stdscr.addstr(0, 0, f"Score: {game_state.score} Level: {game_state.level} Growth: {SNAKE_GROWTH_ON_FOOD} Multiplier: {score_multiplier}")
    for pos in game_state.snake_body:
        stdscr.addstr(pos[0], pos[1], "#")
    if game_state.food_position:
        stdscr.addstr(game_state.food_position[0], game_state.food_position[1], "*")

    for power_up in game_state.power_ups:
       char = {
            'speed': 'S',
            'grow': 'G',
            'slow': 'L',
            'obstacle_remove': 'R',
            'invincible': 'I'
        }.get(power_up['type'], '?')
       stdscr.addstr(power_up['position'][0], power_up['position'][1], char)


    for obstacle in game_state.obstacles:
       stdscr.addstr(obstacle['position'][0], obstacle['position'][1], "O")

    stdscr.refresh()



def increase_speed(game_state):
    """Increases speed based on level."""
    if game_state.score % POINTS_PER_LEVEL == 0 and game_state.score != 0:
        game_state.level += 1
        game_state.delay = max(0.05, game_state.delay * SPEED_INCREASE_PER_LEVEL)


def check_level(game_state):
    """Checks the current level and updates game state (obstacles)."""
    while len(game_state.obstacles) < game_state.level * OBSTACLE_COUNT_PER_LEVEL:
        game_state.obstacles.append(generate_obstacle(game_state))


def generate_obstacle(game_state):
    """Generates an obstacle, avoiding collisions."""
    return {'position': game_state.generate_new_item_position(), 'type': random.choice(['small', 'large'])}



def game_over(new_head, snake_body):
    """Checks for game over (collision with self)."""
    return new_head in list(snake_body)[:-1] #Exclude tail from self collision


def game_over_screen(stdscr, message, score):
    """Displays the game over screen."""
    stdscr.clear()
    stdscr.addstr(MAX_Y // 2, MAX_X // 2 - len(message) // 2, message)
    stdscr.addstr(MAX_Y // 2 + 1, MAX_X // 2 - len(str(score)) // 2, f"Score: {score}")
    stdscr.refresh()
    stdscr.getch()




def apply_power_up_effect(game_state, current_time):
    """Applies power-up effects and updates the game state."""
    for power_up in list(game_state.power_ups):
        if 'expiration_time' not in power_up or power_up['expiration_time'] > current_time:
            if power_up['type'] == "speed":
                game_state.delay *= 0.8
            elif power_up['type'] == "grow":
                for _ in range(3):  # Grow snake by 3 units
                    game_state.snake_body.appendleft(game_state.snake_body[0])
            elif power_up['type'] == "slow":
                game_state.delay *= 1.2
            elif power_up['type'] == "obstacle_remove":
                if game_state.obstacles:
                    game_state.obstacles.pop(random.randrange(len(game_state.obstacles)))
            # Add expiration time if it doesn't exist
            if 'expiration_time' not in power_up:
                power_up['expiration_time'] = current_time + POWER_UP_DURATION
        else: # Expired power-ups:
            if power_up['type'] == "speed":
                game_state.delay /= 0.8  # Restore speed
            elif power_up['type'] == "slow":
                game_state.delay /= 1.2  # Restore speed
            game_state.power_ups.remove(power_up) # Remove expired power-up

    return game_state.delay



def generate_power_up(current_time, game_state):
    """Generates a power-up with a position avoiding other objects."""

    power_up_type = random.choice(POWER_UP_TYPES + ['invincible'])
    return {'position': game_state.generate_new_item_position(power_up=True), 'type': power_up_type}


def play_background_music(music_file):
    """Plays background music indefinitely."""
    try:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except Exception as e:  # Catch any exception during music playback
        print(f"Error playing background music: {e}")



if __name__ == "__main__":
    curses.wrapper(main)