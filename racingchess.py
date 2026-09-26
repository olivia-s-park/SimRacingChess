import pygame
import sys
import random
import os
from stockfish import Stockfish

STOCKFISH_PATH = r"C:\stockfish-windows-x86-64-avx2\stockfish\stockfish-windows-x86-64-avx2.exe"

#I'm using CAMMUS C5, where the steering wheel and the pedals are separate devices. If your device is combined, only use axis id not the device id.
STEERING_INPUT = (0, 0)
GAS_INPUT = (1, 0)
BRAKE_INPUT = (1, 1)
PADDLE_LEFT = 8
PADDLE_RIGHT = 9
BRAKE_PRESS_THRESHOLD = -0.9
BRAKE_RELEASE_THRESHOLD = -0.95
GAS_LAUNCH_THRESHOLD = 0.0

IMAGE_EXT = ".png"
IMAGE_FOLDER = "images"
TILE_SIZE = 100

pygame.init()
pygame.joystick.init()
pygame.font.init()

stockfish = Stockfish(STOCKFISH_PATH)
stockfish.make_moves_from_start()
verify_legal = stockfish.is_move_legal if hasattr(stockfish, "is_move_legal") else stockfish.is_move_correct

move_history = []

def update_and_print_pgn():
    os.system('cls' if os.name == 'nt' else 'clear')
    pgn_turns = []
    for i in range(0, len(move_history), 2):
        turn_num = (i // 2) + 1
        white_move = move_history[i]
        black_move = move_history[i+1] if (i+1) < len(move_history) else ""
        pgn_turns.append(f"{turn_num}. {white_move} {black_move}".strip())
    print(" ".join(pgn_turns))

joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

#Colors and images chosen to resemble chess.com UI, if you don't like it feel free to change

piece_names = ["bB", "bK", "bN", "bP", "bQ", "bR", "wB", "wK", "wN", "wP", "wQ", "wR"]
pieces = [pygame.transform.scale(pygame.image.load(f"{IMAGE_FOLDER}\\{name}{IMAGE_EXT}"), (TILE_SIZE, TILE_SIZE)) for name in piece_names]

CHESS_LIGHT = [238, 238, 210]
CHESS_DARK = [118, 150, 86]
CHESS_HOVER = [140, 162, 198]
CHESS_ERROR = [235, 110, 110]
CHESS_SELECT_LIGHT = [247, 247, 105]
CHESS_SELECT_DARK = [186, 202, 68]
MENU_BG = [48, 46, 43]
TEXT_COLOR = [255, 255, 255]
HIGHLIGHT_BG = [65, 62, 58]

font_large = pygame.font.SysFont("Segoe UI", 42, bold=True)
font_medium = pygame.font.SysFont("Segoe UI", 28)
font_small = pygame.font.SysFont("Segoe UI", 20, italic=True)

board = [[12] * 8 for _ in range(8)]
board[0], board[1] = [5, 2, 0, 4, 1, 0, 2, 5], [3] * 8
board[6], board[7] = [9] * 8, [11, 8, 6, 10, 7, 6, 8, 11]

def apply_move_to_matrix(move_str):
    sFile, sRank = ord(move_str[0]) - 97, 7 - (ord(move_str[1]) - 49)
    dFile, dRank = ord(move_str[2]) - 97, 7 - (ord(move_str[3]) - 49)

    #If you don't understand this part, google en passant. You'll gonna be saying "holy hell!"
    if board[dRank][dFile] == 12 and board[sRank][sFile] in (3, 9) and sFile != dFile:
        board[sRank][dFile] = 12

    board[dRank][dFile] = board[sRank][sFile]
    board[sRank][sFile] = 12

    if move_str == "e1g1": board[7][7], board[7][5] = 12, 11
    elif move_str == "e1c1": board[7][0], board[7][3] = 12, 11
    elif move_str == "e8g8": board[0][7], board[0][5] = 12, 5
    elif move_str == "e8c8": board[0][0], board[0][3] = 12, 5

    if len(move_str) == 5:
        prom = move_str[4]
        is_w = (dRank == 0)
        if prom == 'q': board[dRank][dFile] = 10 if is_w else 4
        elif prom == 'r': board[dRank][dFile] = 11 if is_w else 5
        elif prom == 'b': board[dRank][dFile] = 6 if is_w else 0
        elif prom == 'n': board[dRank][dFile] = 8 if is_w else 2

game_started = False
menu_cursor = 0
setup_level = 5
setup_color_idx = 0
color_modes = ["WHITE", "BLACK", "RANDOM"]
gas_released_after_launch = False

left_paddle_down = False
right_paddle_down = False
both_shifters_triggered = False

playerSide = 0
mode = 1
visual_file = 4
visual_rank = 7
sRank = sFile = 0

screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Chess Rig")
clock = pygame.time.Clock()

while True:
    cFile, cRank = (visual_file, visual_rank) if playerSide == 0 else (7 - visual_file, 7 - visual_rank)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.JOYBUTTONDOWN:
            if not game_started:
                if event.button == PADDLE_LEFT: left_paddle_down = True
                elif event.button == PADDLE_RIGHT: right_paddle_down = True
                if left_paddle_down and right_paddle_down: both_shifters_triggered = True

        elif event.type == pygame.JOYBUTTONUP:
            if not game_started:
                if event.button == PADDLE_LEFT:
                    left_paddle_down = False
                    if both_shifters_triggered:
                        if not right_paddle_down:
                            both_shifters_triggered = False
                            menu_cursor = (menu_cursor + 1) % 2
                    else:
                        if menu_cursor == 0: setup_level = max(0, setup_level - 1)
                        elif menu_cursor == 1: setup_color_idx = (setup_color_idx - 1) % 3

                elif event.button == PADDLE_RIGHT:
                    right_paddle_down = False
                    if both_shifters_triggered:
                        if not left_paddle_down:
                            both_shifters_triggered = False
                            menu_cursor = (menu_cursor + 1) % 2
                    else:
                        if menu_cursor == 0: setup_level = min(20, setup_level + 1)
                        elif menu_cursor == 1: setup_color_idx = (setup_color_idx + 1) % 3

        elif event.type == pygame.JOYAXISMOTION:
            joy_id, axis_id, val = event.joy, event.axis, event.value

            if not game_started and (joy_id, axis_id) == GAS_INPUT:
                if val > GAS_LAUNCH_THRESHOLD:
                    stockfish.set_skill_level(setup_level)
                    playerSide = random.choice([0, 1]) if setup_color_idx == 2 else setup_color_idx
                    visual_rank, visual_file = 7, 4
                    gas_released_after_launch = False
                    mode = 4 if playerSide == 1 else 1
                    game_started = True

            elif game_started:
                if (joy_id, axis_id) == STEERING_INPUT:
                    visual_file = int(max(0, min(7.999, (val * 6 + 1) * 4)))

                elif (joy_id, axis_id) == GAS_INPUT:
                    if not gas_released_after_launch:
                        if val < -0.8: gas_released_after_launch = True
                    else:
                        visual_rank = int(max(0, min(7.999, (1 - val) * 4)))

                elif (joy_id, axis_id) == BRAKE_INPUT:
                    if mode == 1 and val > BRAKE_PRESS_THRESHOLD:
                        current_piece = board[cRank][cFile]
                        if current_piece != 12 and (0 if current_piece > 5 else 1) == playerSide:
                            mode, sRank, sFile = 3, cRank, cFile
                        else: mode = 2

                    elif val < BRAKE_RELEASE_THRESHOLD and mode in (2, 3):
                        if mode == 2: mode = 1
                        elif mode == 3:
                            dRank, dFile = cRank, cFile
                            move = chr(sFile + 97) + str(8 - sRank) + chr(dFile + 97) + str(8 - dRank)
                            if board[sRank][sFile] in (3, 9) and (dRank == 0 or dRank == 7):
                                move += "q"  #Possible addition: underpromotion. 
                            if verify_legal(move):
                                move_history.append(move)
                                stockfish.make_moves_from_start(move_history)
                                apply_move_to_matrix(move)
                                update_and_print_pgn()
                                mode = 4
                            else:
                                mode = 1

    if game_started and mode == 4:
        mode = 1
        best_move = stockfish.get_best_move()
        if best_move:
            move_history.append(best_move)
            stockfish.make_moves_from_start(move_history)
            apply_move_to_matrix(best_move)
            update_and_print_pgn()

    if not game_started:
        screen.fill(MENU_BG)
        title_surf = font_large.render("SIM RACING CHESS", True, TEXT_COLOR)
        screen.blit(title_surf, (400 - title_surf.get_width()//2, 80))

        if menu_cursor == 0: pygame.draw.rect(screen, HIGHLIGHT_BG, (100, 220, 600, 90), border_radius=8)
        lbl_lvl = font_medium.render(f"Stockfish Level:   <  {setup_level}  >", True, TEXT_COLOR if menu_cursor != 0 else CHESS_SELECT_LIGHT)
        screen.blit(lbl_lvl, (140, 240))

        if menu_cursor == 1: pygame.draw.rect(screen, HIGHLIGHT_BG, (100, 360, 600, 90), border_radius=8)
        lbl_col = font_medium.render(f"Play As:      <  {color_modes[setup_color_idx]}  >", True, TEXT_COLOR if menu_cursor != 1 else CHESS_SELECT_LIGHT)
        screen.blit(lbl_col, (140, 380))

        pygame.draw.rect(screen, CHESS_DARK, (150, 540, 500, 90), border_radius=12)
        lbl_start = font_medium.render("PRESS THE THROTTLE TO LAUNCH", True, TEXT_COLOR)
        screen.blit(lbl_start, (400 - lbl_start.get_width()//2, 565))

    else:
        for vr in range(8):
            for vc in range(8):
                r, c = (vr, vc) if playerSide == 0 else (7 - vr, 7 - vc)
                is_light = ((vr ^ vc) & 1) == 0

                if mode == 3 and r == sRank and c == sFile: color = CHESS_SELECT_LIGHT if is_light else CHESS_SELECT_DARK
                elif vr == visual_rank and vc == visual_file: color = CHESS_ERROR if mode == 2 else CHESS_HOVER
                else: color = CHESS_LIGHT if is_light else CHESS_DARK

                pygame.draw.rect(screen, color, (vc * TILE_SIZE, vr * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                p = board[r][c]
                if p < 12 and not (mode == 3 and r == sRank and c == sFile):
                    screen.blit(pieces[p], (vc * TILE_SIZE, vr * TILE_SIZE))

        if mode == 3 and board[sRank][sFile] < 12:
            screen.blit(pieces[board[sRank][sFile]], (visual_file * TILE_SIZE, visual_rank * TILE_SIZE))

    pygame.display.flip()
    clock.tick(60)