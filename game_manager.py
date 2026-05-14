import sys
import time
import typing

import pygame

from colors import *
from game_objects import Bullet, Coin, Player, Villain

WIDTH, HEIGHT = 1200, 800

font = pygame.font.SysFont("malgungothic", 24)
big_font = pygame.font.SysFont("malgungothic", 40)


class Game:
    player: Player
    villains: typing.List[Villain] = []
    coins: typing.List[Coin] = []
    bullets: typing.List[Bullet] = []

    current_level: int

    start_time: float

    def __init__(self, _game_config, _screen):
        self._game_config = _game_config
        self.screen = _screen

        self.total_level = self._game_config["total_level"]

        self.load_images()

        self.player = Player(self._game_config)
        self.clear_objects()

        self.current_level = 0

    def load_images(self):
        self.background = pygame.image.load(self._game_config["background_dir"])

        heart_width, heart_height = (
            self._game_config["heart_width"],
            self._game_config["heart_height"],
        )

        full_heart = pygame.image.load(self._game_config["full_heart_dir"])
        broken_heart = pygame.image.load(self._game_config["broken_heart_dir"])

        self.full_heart = pygame.transform.scale(
            full_heart, (heart_width, heart_height)
        )
        self.broken_heart = pygame.transform.scale(
            broken_heart, (heart_width, heart_height)
        )

    def clear_objects(self):
        self.villains.clear()
        self.coins.clear()
        self.bullets.clear()

    def reset_game(self):
        self.player = Player(self._game_config)
        self.clear_objects()

        self.start_time = time.time()

        self.current_level = 0

    def draw_ui(self):
        cnt = 0
        heart_margin = 10

        heart_width = self._game_config["heart_width"]

        for alive_hp in range(self.player.hp):
            self.screen.blit(
                self.full_heart,
                (20 + heart_margin * cnt + heart_width * cnt, 20),
            )
            cnt += 1
        for dead_hp in range(self.player.max_hp - self.player.hp):
            self.screen.blit(
                self.broken_heart,
                (20 + heart_margin * cnt + heart_width * cnt, 20),
            )
            cnt += 1

        level_text = font.render(f"Level {self.current_level}", True, BLACK)
        self.screen.blit(level_text, (20, 60))

    def draw_game_over(self):
        msg1 = big_font.render("GAME OVER", True, RED)
        msg2 = font.render(f"Max Level: {self.current_level}", True, BLACK)

        self.screen.blit(msg1, (WIDTH // 2 - msg1.get_width() // 2, 220))
        self.screen.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, 280))

    def draw_game_win(self, end_time):
        took_time = int(end_time - self.start_time)
        took_min = took_time // 60
        took_sec = took_time % 60

        msg1 = big_font.render("YOU WIN", True, BLUE)
        msg2 = font.render(
            f"You took {took_min} minutes {took_sec} seconds", True, BLACK
        )
        msg3 = font.render("Press ESC to quit, R to start again", True, BLACK)

        self.screen.blit(msg1, (WIDTH // 2 - msg1.get_width() // 2, 220))
        self.screen.blit(msg2, (WIDTH // 2 - msg2.get_width() // 2, 280))
        self.screen.blit(msg3, (WIDTH // 2 - msg3.get_width() // 2, 320))

    def draw_game_play(self):
        self.screen.fill(WHITE)
        self.screen.blit(self.background, (0, HEIGHT / 3))

        objects = [self.player] + self.villains + self.coins + self.bullets
        for obj in objects:
            obj.draw(self.screen)

        if self.current_level > self.total_level:
            self.draw_game_win(time.time())
        elif self.player.is_dead:
            self.draw_game_over()
        else:
            self.draw_ui()

    def start_new_level(self):
        if self.current_level == 0:
            self.start_time = time.time()

        self.current_level += 1
        self.player.start_new_level()

        self.player.x = (WIDTH / 2) - (self.player.image_width / 2)
        self.player.y = (HEIGHT / 2) - (self.player.image_height / 2)

        self.clear_objects()

        if self.current_level <= self.total_level:
            level_info: dict = self._game_config["levels"][self.current_level - 1]

            villain_width, villain_height = (
                self._game_config["villain_width"],
                self._game_config["villain_height"],
            )
            villain_types = self._game_config["villain_types"]

            coin_width, coin_height = (
                self._game_config["coin_width"],
                self._game_config["coin_height"],
            )

            for t in range(villain_types):
                for cnt in range(level_info["villains"][t]):
                    random_pos = self.player.generate_position_randomly(
                        WIDTH - villain_width, HEIGHT - villain_height
                    )
                    self.villains.append(Villain(self._game_config, random_pos, t + 1))

            for cnt in range(level_info["coins"]):
                random_pos = self.player.generate_position_randomly(
                    WIDTH - coin_width, HEIGHT - coin_height
                )
                self.coins.append(Coin(self._game_config, random_pos))
        else:
            self.draw_game_win(time.time())

    def game_play(self, action=None):
        if len(self.coins) == 0:
            self.start_new_level()

        if self.player.is_dead:
            return

        objects = self.villains + self.coins + self.bullets

        self.player.update(action=action)
        for obj in objects:
            obj.update(self.player)
        for obj in self.villains:
            bullet = obj.shoot_bullet()
            if bullet is not None:
                self.bullets.append(bullet)

        self.villains = list(
            filter(lambda villain_obj: villain_obj.is_alive, self.villains)
        )
        self.coins = list(filter(lambda coin_obj: coin_obj.is_alive, self.coins))
        self.bullets = list(
            filter(lambda bullet_obj: bullet_obj.is_alive, self.bullets)
        )

        if self.current_level > self.total_level:
            self.player.destroy()

        self.draw_game_play()

    def handle_game(self, action=None):
        if self.current_level > self.total_level:
            pass
        else:
            self.game_play(action)
        return pygame.surfarray.array3d(self.screen)
