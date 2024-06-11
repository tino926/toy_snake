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

    while True:
        stdscr.clear()

        # Get user input
        key = stdscr.getch()
        if key == ord('q'):
            break

        # Move the snake
        if snake_direction == curses.KEY_DOWN:
            new_head = [snake_position[0] + 1, snake_position[1]]
        elif snake_direction == curses.KEY_UP:
            new_head = [snake_position[0] - 1, snake_position[1]]
        elif snake_direction == curses.KEY_LEFT:
            new_head = [snake_position[0], snake_position[1] - 1]
        elif snake_direction == curses.KEY_RIGHT:
            new_head = [snake_position[0], snake_position[1] + 1]

        snake_body.insert(0, new_head)

        # Check for food collision
        if snake_body[0] == food_position:
            food_position = None
            while food_position is None:
                nf_pos = [
                    random.randint(1, stdscr.getmaxyx()[0] - 1),
                    random.randint(1, stdscr.getmaxyx()[1] - 1)
                ]
                food_position = nf_pos
        else:
            tail = snake_body.pop()
            if tail == food_position:
                food_position = None
                while food_position is None:
                    nf_pos = [
                        random.randint(1, stdscr.getmaxyx()[0] - 1),
                        random.randint(1, stdscr.getmaxyx()[1] - 1)
                    ]
                    food_position = nf_pos

        # Draw the snake and food
        stdscr.addstr(0, 0, "Score: 0")
        for pos in snake_body:
            stdscr.addstr(pos[0], pos[1], "#")

        if food_position!= None:
            stdscr.addstr(food_position[0], food_position[1], "*")

        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)