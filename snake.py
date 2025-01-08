import curses
import random
import time
from typing import List, Tuple, Dict
import pygame
from collections import deque
import json

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# --- Constants ---
MAX_X = 40
MAX_Y = 20
FRAME_RATE = 30
POWER_UP_TYPES = ['speed', 'grow', 'slow', 'obstacle_remove', 'shrink']
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

# High Score
HIGH_SCORE_FILE = "highscore.json"

SOUND_EFFECTS = {
    'food': 'food.wav',
    'power_up': 'power_up.wav',
    'collision': 'collision.wav'
}
FLASH_DURATION = 0.2  # seconds
FLASH_COLORS = [curses.A_NORMAL, curses.A_REVERSE]

SPECIAL_FOOD_TYPES = {
    'golden': {
        'char': '$', 
        'points': 5, 
        'probability': 0.1
    },
    'poison': {
        'char': '!', 
        'points': -2, 
        'probability': 0.15
    }
}

def load_high_score():
    """Load the high score from a file."""
    try:
        with open(HIGH_SCORE_FILE, 'r') as f:
            return json.load(f).get('high_score', 0)
    except FileNotFoundError:
        return 0

def save_high_score(high_score):
    """Save the high score to a file."""
    with open(HIGH_SCORE_FILE, 'w') as f:
        json.dump({'high_score': high_score}, f)

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
        self.high_score = load_high_score()
        self.food_type = 'normal'

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
                rand = random.random()
                for food_type, props in SPECIAL_FOOD_TYPES.items():
                    if rand < props['probability']:
                        self.food_type = food_type
                        break
                else:
                    self.food_type = 'normal'
                return new_position

    def save_game(self, filename="savegame.json"):
        """Save the current game state to a file."""
        with open(filename, 'w') as f:
            json.dump(self.__dict__, f)

    def load_game(self, filename="savegame.json"):
        """Load the game state from a file."""
        with open(filename, 'r') as f:
            self.__dict__ = json.load(f)
            self.snake_body = deque(self.snake_body)  # Convert list back to deque


def main(stdscr):
    """Main game loop."""
    global MAX_X, MAX_Y, SNAKE_COLLISION_ENABLED, SNAKE_GROWTH_ON_FOOD, score_multiplier_time, score_multiplier
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(int(1000 / FRAME_RATE))

    while True:
        max_y, max_x = stdscr.getmaxyx()
        MAX_X = min(MAX_X, max_x - 2)
        MAX_Y = min(MAX_Y, max_y - 2)

        game_state = GameState()

        # Load game state if available
        try:
            game_state.load_game()
        except FileNotFoundError:
            pass

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
                    return
                elif key == ord('p'):
                    game_state.paused = True
                    if not pause_menu(stdscr, game_state):
                        return  # Quit game
                    game_state.paused = False
                    continue

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
                elif key == ord('s'):
                    game_state.save_game()
                    stdscr.addstr(0, MAX_X // 2 - 5, "Game Saved")
                    stdscr.refresh()
                    time.sleep(1)


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


                    if check_collision(new_head, game_state.snake_body, game_state.food_position, game_state.obstacles, game_state, current_time):
                        
                        game_state.food_position = game_state.generate_new_item_position()

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
                            if check_collision(new_head, game_state.snake_body, obstacle['position'], game_state.obstacles, game_state, current_time):
                                raise ValueError("Game Over! You hit an obstacle.")
                        if SNAKE_COLLISION_ENABLED and game_over(new_head, game_state.snake_body):
                            play_sound_effect('collision')
                            flash_effect(stdscr, new_head)
                            raise ValueError("Game Over! You ran into yourself.")


                    #Power-Up Pickup
                    for power_up in list(game_state.power_ups):
                        if check_collision(new_head, game_state.snake_body, power_up['position'], game_state.obstacles, game_state, current_time):
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
                if game_state.score > game_state.high_score:
                    game_state.high_score = game_state.score
                    save_high_score(game_state.high_score)
                if not game_over_screen(stdscr, str(e), game_state.score):
                    return  # Exit the game if the player chooses not to restart
                break  # Restart the game loop
            except Exception as e:
                stdscr.addstr(0, 0, f"Error: {e}")
                stdscr.refresh()
                time.sleep(2)
                break

        # Save game state on exit
        game_state.save_game()


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


def check_collision(
    new_head, 
    snake_body, 
    target_position, 
    obstacles, 
    game_state, 
    current_time
):
    """Checks for collision with target position or snake body."""
    global score_multiplier_time, score_multiplier

    if new_head == target_position:
        play_sound_effect('food')
        if game_state.food_type in SPECIAL_FOOD_TYPES:
            points = SPECIAL_FOOD_TYPES[game_state.food_type]['points']
            game_state.score += points
        else:
            if (score_multiplier_time and 
                current_time - score_multiplier_time <= SCORE_MULTIPLIER_WINDOW):
                score_multiplier += 1
            else:
                score_multiplier = 1
            score_multiplier_time = current_time
            game_state.score += 1 * score_multiplier
        return True
    if new_head in list(snake_body)[:-1]: # Exclude the tail from self-collision check
        return True

    return False


def draw_game(stdscr, game_state, score_multiplier):
    """Draws the game elements."""
    status = (
        f"Score: {game_state.score} Level: {game_state.level} "
        f"Growth: {SNAKE_GROWTH_ON_FOOD} Multiplier: {score_multiplier} "
        f"High Score: {game_state.high_score}"
    )
    stdscr.addstr(0, 0, status)

    for pos in game_state.snake_body:
        stdscr.addstr(pos[0], pos[1], "#")
    
    if game_state.food_position:
        food_char = '*'
        if game_state.food_type in SPECIAL_FOOD_TYPES:
            food_char = SPECIAL_FOOD_TYPES[game_state.food_type]['char']
        stdscr.addstr(
            game_state.food_position[0], 
            game_state.food_position[1], 
            food_char
        )

    power_up_chars = {
        'speed': 'S',
        'grow': 'G',
        'slow': 'L',
        'obstacle_remove': 'R',
        'invincible': 'I',
        'multiplier': 'M'
    }

    for power_up in game_state.power_ups:
        char = power_up_chars.get(power_up['type'], '?')
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
    """Displays the game over screen and asks the player if they want to restart."""
    stdscr.clear()
    center_y = MAX_Y // 2
    center_x = MAX_X // 2
    
    stdscr.addstr(center_y, center_x - len(message) // 2, message)
    stdscr.addstr(
        center_y + 1, 
        center_x - len(str(score)) // 2, 
        f"Score: {score}"
    )
    stdscr.addstr(
        center_y + 2, 
        center_x - 10, 
        "Press 'r' to restart or 'q' to quit"
    )
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        if key == ord('r'):
            return True
        elif key == ord('q'):
            return False


def apply_power_up_effect(game_state, current_time):
    """Applies power-up effects and updates the game state."""
    for power_up in list(game_state.power_ups):
        if 'expiration_time' not in power_up or power_up['expiration_time'] > current_time:
            play_sound_effect('power_up')
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
            elif power_up['type'] == "multiplier":
                global score_multiplier
                score_multiplier *= 2  # Double the score multiplier
            elif power_up['type'] == "shrink":
                if len(game_state.snake_body) > 3:
                    for _ in range(3):  # Shrink snake by 3 units
                        game_state.snake_body.popleft()
            # Add expiration time if it doesn't exist
            if 'expiration_time' not in power_up:
                power_up['expiration_time'] = current_time + POWER_UP_DURATION
        else: # Expired power-ups:
            if power_up['type'] == "speed":
                game_state.delay /= 0.8  # Restore speed
            elif power_up['type'] == "slow":
                game_state.delay /= 1.2  # Restore speed
            elif power_up['type'] == "multiplier":
                score_multiplier /= 2  # Restore score multiplier
            game_state.power_ups.remove(power_up) # Remove expired power-up

    return game_state.delay


def generate_power_up(current_time, game_state):
    """Generates a power-up with a position avoiding other objects and too close to the snake's head."""
    while True:
        position = game_state.generate_new_item_position()
        if abs(position[0] - game_state.snake_body[-1][0]) > 2 and abs(position[1] - game_state.snake_body[-1][1]) > 2:
            break
    power_up_type = random.choice(POWER_UP_TYPES + ['invincible', 'multiplier'])
    return {'position': position, 'type': power_up_type}


def play_background_music(music_file):
    """Plays background music indefinitely."""
    try:
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except Exception as e:  # Catch any exception during music playback
        print(f"Error playing background music: {e}")

def play_sound_effect(effect_type):
    """Play a specific sound effect."""
    try:
        sound = pygame.mixer.Sound(SOUND_EFFECTS.get(effect_type))
        sound.play()
    except Exception:
        pass  # Silently fail if sound file is missing

def flash_effect(stdscr, position, duration=FLASH_DURATION):
    """Create a flashing effect at the given position."""
    start_time = time.perf_counter()
    while time.perf_counter() - start_time < duration:
        for attr in FLASH_COLORS:
            stdscr.attron(attr)
            stdscr.addstr(position[0], position[1], "#")
            stdscr.attroff(attr)
            stdscr.refresh()
            time.sleep(0.1)

def pause_menu(stdscr, game_state):
    """Display an improved pause menu with options."""
    menu_items = [
        "Resume Game",
        "Save Game",
        "Toggle Collision",
        "Adjust Growth Rate",
        "Adjust Volume",
        "Quit Game"
    ]
    current_item = 0
    
    while True:
        stdscr.clear()
        for i, item in enumerate(menu_items):
            x = MAX_X // 2 - len(item) // 2
            y = MAX_Y // 2 - len(menu_items) // 2 + i
            if i == current_item:
                stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, x, item)
            if i == current_item:
                stdscr.attroff(curses.A_REVERSE)
        
        key = stdscr.getch()
        if key == curses.KEY_UP:
            current_item = (current_item - 1) % len(menu_items)
        elif key == curses.KEY_DOWN:
            current_item = (current_item + 1) % len(menu_items)
        elif key == ord('\n'):  # Enter key
            if current_item == 0:  # Resume
                return True
            elif current_item == 1:  # Save
                game_state.save_game()
                stdscr.addstr(MAX_Y-1, 0, "Game Saved!")
                stdscr.refresh()
                time.sleep(1)
            elif current_item == 2:  # Toggle Collision
                global SNAKE_COLLISION_ENABLED
                SNAKE_COLLISION_ENABLED = not SNAKE_COLLISION_ENABLED
            elif current_item == 3:  # Adjust Growth
                global SNAKE_GROWTH_ON_FOOD
                SNAKE_GROWTH_ON_FOOD = (SNAKE_GROWTH_ON_FOOD % 5) + 1
            elif current_item == 4:  # Adjust Volume
                adjust_volume(stdscr)
            elif current_item == 5:  # Quit
                return False
        elif key == ord('p'):  # Resume on 'p' key
            return True

def adjust_volume(stdscr):
    """Adjust the game volume."""
    volume = pygame.mixer.music.get_volume()
    while True:
        stdscr.clear()
        stdscr.addstr(MAX_Y // 2, MAX_X // 2 - 10, f"Volume: {int(volume * 100)}%")
        stdscr.addstr(MAX_Y // 2 + 1, MAX_X // 2 - 15, "Use '+' or '-' to adjust, 'Enter' to confirm")
        stdscr.refresh()
        
        key = stdscr.getch()
        if key == ord('+') and volume < 1.0:
            volume += 0.1
        elif key == ord('-') and volume > 0.0:
            volume -= 0.1
        elif key == ord('\n'):
            pygame.mixer.music.set_volume(volume)
            return

if __name__ == "__main__":
    curses.wrapper(main)