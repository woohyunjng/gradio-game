import math
import random
import time
from abc import ABC, abstractmethod

import pygame

WIDTH, HEIGHT = 1200, 800


def is_colliding(obj1_left_top, obj1_right_bottom, obj2_left_top, obj2_right_bottom):
    return (
        obj1_left_top[0] < obj2_right_bottom[0]
        and obj2_left_top[0] < obj1_right_bottom[0]
        and obj1_left_top[1] < obj2_right_bottom[1]
        and obj2_left_top[1] < obj1_right_bottom[1]
    )


class GameObject(ABC):
    def __init__(self, game_config):
        self._x = 0
        self._y = 0

        self._game_config = game_config
        self._config: dict = {}

        self._rect_padding = self._game_config["rect_padding"]

        self.image_dir = None
        self.image = None
        self.image_width = None
        self.image_height = None

        self._alive = False

    def load_image(self):
        self.image = pygame.image.load(self.image_dir)
        self.image = pygame.transform.scale(
            self.image, (self.image_width, self.image_height)
        )

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        if isinstance(val, (int, float)):
            self._x = max(0, min(WIDTH - self.image_width, val))

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        if isinstance(val, (int, float)):
            self._y = max(0, min(HEIGHT - self.image_height, val))

    @property
    def is_alive(self):
        return self._alive

    @property
    def is_dead(self):
        return not self.is_alive

    def destroy(self):
        self._alive = False

    @abstractmethod
    def update(self, player_obj=None):
        pass

    def draw(self, surface):
        surface.blit(self.image, (self.x, self.y))

    def get_rec(self):
        return (self.x + self._rect_padding, self.y + self._rect_padding), (
            self.x + self.image_width - self._rect_padding,
            self.y + self.image_height - self._rect_padding,
        )

    def collides_with(self, external_obj):
        return is_colliding(*self.get_rec(), *external_obj.get_rec())


class Bullet(GameObject):
    def __init__(self, game_config, x, y):
        super().__init__(game_config)

        self._x = x
        self._y = y

        self.image_dir = self._game_config["bullet_dir"]
        self.image_width = self._game_config["bullet_width"]
        self.image_height = self._game_config["bullet_height"]
        self.load_image()

        self._alive = True

        self._speed = self._game_config["bullet_speed"]
        angle = random.random() * 2 * math.pi
        self.dx = self._speed * math.cos(angle)
        self.dy = self._speed * math.sin(angle)

    def update(self, player_obj):
        if self.x + self.dx < 0 or self.x + self.dx > WIDTH - self.image_width:
            self.destroy()
        if self.y + self.dy < 0 or self.y + self.dy > HEIGHT - self.image_height:
            self.destroy()

        self.x += self.dx
        self.y += self.dy

        if self.collides_with(player_obj):
            player_obj.take_damage(1)
            self.destroy()


class Player(GameObject):
    def __init__(self, game_config):
        super().__init__(game_config)

        self._config = self._game_config["player"]
        self.hp_refill = self._config["hp_refill"]

        self.image_dir = self._config["image_dir"]
        self.image_width = self._config["width"]
        self.image_height = self._config["height"]
        self.load_image()

        self._x = (WIDTH / 2) - (self.image_width / 2)
        self._y = (HEIGHT / 2) - (self.image_height / 2)

        self._alive = True

        self._max_hp = self._config["max_hp"]
        self._hp = self._max_hp
        self._speed = self._config["speed"]

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        if isinstance(value, (int, float)):
            self._hp = max(0, min(self._max_hp, int(value)))

    @property
    def is_invincible(self):
        return False

    def take_damage(self, val):
        if self.is_invincible or self.is_dead or val <= 0:
            return
        self.hp -= val
        if self.hp == 0:
            self.destroy()

    @property
    def speed(self):
        return self._speed

    def update(self, player_obj=None, action=None):
        if not self.is_alive:
            return

        if action is None:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.x -= self._speed
            if keys[pygame.K_RIGHT]:
                self.x += self._speed
            if keys[pygame.K_UP]:
                self.y -= self._speed
            if keys[pygame.K_DOWN]:
                self.y += self._speed
        else:
            if action == 1:
                self.y -= self._speed
            elif action == 2:
                self.y += self._speed
            elif action == 3:
                self.x -= self._speed
            elif action == 4:
                self.x += self._speed

    def start_new_level(self):
        if self.hp_refill:
            self.hp = self.max_hp

    def generate_position_randomly(self, max_x, max_y):
        while True:
            random_x = random.random() * max_x
            random_y = random.random() * max_y

            if (
                math.dist((self.x, self.y), (random_x, random_y))
                < self._game_config["beginning_dis"]
            ):
                continue

            return (random_x, random_y)


class Villain(GameObject):
    def __init__(self, game_config, pos, villain_type):
        super().__init__(game_config)

        self._x = pos[0]
        self._y = pos[1]

        self._config = self._game_config["villain"][villain_type - 1]
        self._following_player = self._config.get("following_player", False)
        self._shooting_bullet = self._config.get("shooting_bullet", False)

        self.image_dir = self._config["image_dir"]
        self.image_width = self._game_config["villain_width"]
        self.image_height = self._game_config["villain_height"]
        self.load_image()

        self._alive = True
        self._collide_with_player = False
        self._speed = self._config["speed"]
        self._bullet_cooltime = self._game_config["bullet_cooltime"]

        angle = random.random() * 2 * math.pi
        self.dx = self._speed * math.cos(angle)
        self.dy = self._speed * math.sin(angle)

        self._last_bullet_shot = time.time()

    def update(self, player_obj):
        if self._following_player:
            dir_x = player_obj.x - self.x
            dir_y = player_obj.y - self.y
            length = math.hypot(dir_x, dir_y)

            if length == 0:
                self.dx, self.dy = 0, 0
            else:
                self.dx = (dir_x / length) * self._speed
                self.dy = (dir_y / length) * self._speed
        else:
            if random.random() < 0.02:
                angle = random.random() * 2 * math.pi
                self.dx = self._speed * math.cos(angle)
                self.dy = self._speed * math.sin(angle)

        if self.x + self.dx < 0 or self.x + self.dx > WIDTH - self.image_width:
            self.dx = -self.dx
        if self.y + self.dy < 0 or self.y + self.dy > HEIGHT - self.image_height:
            self.dy = -self.dy

        self.x += self.dx
        self.y += self.dy

        if self.collides_with(player_obj):
            if not self._collide_with_player:
                self._collide_with_player = True
                player_obj.take_damage(1)
        else:
            self._collide_with_player = False

    def shoot_bullet(self):
        current_time = time.time()
        if (
            not self._shooting_bullet
            or current_time < self._last_bullet_shot + self._bullet_cooltime
        ):
            return None

        self._last_bullet_shot = current_time
        return Bullet(self._game_config, self.x, self.y)


class Coin(GameObject):
    def __init__(self, game_config, pos):
        super().__init__(game_config)

        self._x = pos[0]
        self._y = pos[1]

        self.image_dir = self._game_config["coin_dir"]
        self.image_width = self._game_config["coin_width"]
        self.image_height = self._game_config["coin_height"]
        self.load_image()

        self._alive = True

    def update(self, player_obj):
        if not self.collides_with(player_obj):
            return
        self.destroy()
