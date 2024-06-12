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
    if direction == curses.KEY_DOWN:
        return [position[0] + 1, position[1]]
    elif direction == curses.KEY_UP:
        return [position[0] - 1, position[1]]
    elif direction == curses.KEY_LEFT:
        return [position[0], position[1] - 1]
    elif direction == curses.KEY_RIGHT:
        return [position[0], position[1] + 1]

def check_collision(new_head, body, food_position):
    return new_head == food_position or new_head in body

def generate_new_food_position(old_position, stdscr):
    max_y, max_x = stdscr.getmaxyx()
    while True:
        new_position = [random.randint(1, max_x - 1), random.randint(1, max_y - 1)]
        if new_position!= old_position:
            return new_position

def draw_game(stdscr, snake_body, food_position, score):
    stdscr.addstr(0, 0, f"Score: {score}")
    for pos in snake_body:
        stdscr.addstr(pos[0], pos[1], "#")

    if food_position:
        stdscr.addstr(food_position[0], food_position[1], "*")


