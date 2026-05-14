import json

import gradio
import numpy
import pygame

pygame.init()

from game_manager import Game

WIDTH, HEIGHT = 1200, 800
screen = pygame.Surface((WIDTH, HEIGHT))

CONFIG_FILE_DIR = "./config.json"

with open(CONFIG_FILE_DIR, "r") as config_file:
    json_data = json.load(config_file)
    game_config = json_data["game_config"]

game = Game(game_config, screen)

current_action = 0


def step(action):
    global current_action
    if action is not None:
        frame = game.handle_game(action)
    else:
        frame = game.handle_game(0)
    frame = numpy.transpose(frame, (1, 0, 2))
    return frame


game.start_new_level()


with gradio.Blocks() as demo:
    gradio.Markdown("### Game")
    img = gradio.Image()

    timer = gradio.Timer(0.1)
    timer.tick(lambda: step(0), outputs=img)

    with gradio.Row():
        btn_up = gradio.Button("⬆️")
    with gradio.Row():
        btn_left = gradio.Button("⬅️")
        btn_down = gradio.Button("⬇️")
        btn_right = gradio.Button("➡️")

    btn_up.click(lambda: step(1), outputs=img)
    btn_down.click(lambda: step(2), outputs=img)
    btn_left.click(lambda: step(3), outputs=img)
    btn_right.click(lambda: step(4), outputs=img)

    demo.load(lambda: step(0), outputs=img)

demo.launch(server_port=10000, server_name="0.0.0.0")
