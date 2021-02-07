from utils import *
from settings import *
from math import tanh
from collections import deque
import pygame


class Weapon:
    def __init__(self, base_sprite, shot_animation, reload_animation, shot_speed, reload_speed, shot_sound, clip_size,
                 damage, max_distance):
        self.weapon_base_sprite = base_sprite
        self.weapon_shot_animation = shot_animation.copy()
        self.weapon_reload_animation = reload_animation.copy()
        self.init_shot = shot_animation
        self.init_reload = reload_animation
        self.weapon_rect = self.weapon_base_sprite.get_rect()
        self.standard_weapon_pos = (HALF_WIDTH - self.weapon_rect.width // 2, HEIGHT - self.weapon_rect.height)
        self.shot_length = len(self.weapon_shot_animation)
        self.shot_length_count = 0
        self.shot_animation_speed = shot_speed
        self.shot_animation_count = 0
        self.reload_animation_speed = reload_speed
        self.reload_animation_count = 0
        self.reload_length = len(self.weapon_reload_animation)
        self.reload_length_count = 0
        self.clip = clip_size
        self.damage = damage
        self.max_distance = max_distance
        self.shot = False
        self.reload = False
        self.count_of_posible_shots = self.clip
        self.shot_sound = shot_sound

    def render_shot(self, screen):
        if not self.count_of_posible_shots:
            self.shot = False
        if self.shot:
            if self.shot_length_count ^ 1 and self.shot_sound:
                self.shot_sound.play()
            shot_sprite = self.weapon_shot_animation[0]
            weapon_rect = shot_sprite.get_rect()
            weapon_pos = (HALF_WIDTH - weapon_rect.width // 2, HEIGHT - weapon_rect.height)
            screen.blit(shot_sprite, weapon_pos)
            self.shot_animation_count += 1
            if self.shot_animation_count == self.shot_animation_speed:
                self.weapon_shot_animation.rotate(-1)
                self.shot_animation_count = 0
                self.shot_length_count += 1
            if self.shot_length_count == self.shot_length:
                self.shot = False
                self.shot_length_count = 0
                self.count_of_posible_shots -= 1
        elif not self.reload:
            screen.blit(self.weapon_base_sprite, self.standard_weapon_pos)

    def render(self, player, screen):
        event = pygame.mouse.get_pressed(5)
        if event[0] and not (self.shot or self.reload):
            self.shot = True
        elif event[2] and not (self.shot or self.reload or self.count_of_posible_shots):
            self.reload = True
        self.render_shot(screen)
        self.render_reload(screen)

    def render_reload(self, screen):
        if self.reload:
            reload_sprite = self.weapon_reload_animation[0]
            weapon_rect = reload_sprite.get_rect()
            weapon_pos = (HALF_WIDTH - weapon_rect.width // 2, HEIGHT - weapon_rect.height)
            screen.blit(reload_sprite, weapon_pos)
            self.reload_animation_count += 1
            if self.reload_animation_count == self.reload_animation_speed:
                self.weapon_reload_animation.rotate(-1)
                self.reload_animation_count = 0
                self.reload_length_count += 1
            if self.reload_length_count == self.reload_length:
                self.reload_length_count = 0
                self.count_of_posible_shots = self.clip
                self.reload = False

    def rotateing(self):
        self.shot = False
        self.reload = False
        self.shot_length_count = 0
        self.shot_animation_count = 0
        self.reload_length_count = 0
        self.reload_animation_count = 0
        self.weapon_reload_animation = self.init_reload.copy()
        self.weapon_shot_animation = self.init_shot.copy()

    def shoting(self, player, sprites, world_map):
        if self.shot and self.shot_length_count == self.shot_length // 2 and\
                self.shot_animation_count == self.shot_animation_speed // 2:
            shot_sprites = [obj.is_on_fire(self.max_distance) for obj in sprites if obj.is_live]
            if shot_sprites:
                try:
                    shot_sprite = min(shot_sprites, default=(float('inf'), None))
                except Exception:
                    shot_sprite = shot_sprites[0]
                if shot_sprite[1] is None:
                    return
                if ray_casting_npc_player(shot_sprite[1].x, shot_sprite[1].y, (player.x, player.y), world_map):
                    shot_sprite[1].set_damage(int(self.damage * tanh(self.max_distance / shot_sprite[0])))


class RetroGun(Weapon):
    def __init__(self):
        shot_scale = 1.3
        reload_scale = 1.3
        base_sprite = load_image(f"handgun\\shot\\0.png", scale=shot_scale)
        shot_animation = deque([load_image(f"handgun\\shot\\{i}.png", scale=shot_scale) for i in range(13)])
        reload_animation = deque([load_image(f"handgun\\reload\\{i}.png", scale=reload_scale) for i in range(26)])
        shot_speed = 4
        reload_speed = 7
        shot_sound = None
        clip_size = 5
        damage = 200
        max_distance = 500
        super().__init__(base_sprite, shot_animation, reload_animation, shot_speed, reload_speed, shot_sound, clip_size,
                         damage, max_distance)


class MiniMap:
    def __init__(self, map, pos):
        self.mini_map_width = WIDTH // MINI_MAP_SCALE
        self.mini_map_hight = HEIGHT // MINI_MAP_SCALE
        self.map_tile = min(WIDTH / map.size[0], HEIGHT / map.size[1]) / MINI_MAP_SCALE
        self.mini_map_scale = TILE / self.map_tile
        self.mini_map = [[-1 for __ in range(len(map.text_map[0]))] for _ in range(len(map.text_map))]
        dist = bfs(map.text_map, pos, 0)
        max_x, max_y = -1, -1
        min_x, min_y = INF, INF
        for j, row in enumerate(map.text_map):
            for i, ceil in enumerate(row):
                if dist[j][i] != INF or self.mini_map[j][i] > 50:
                    self.mini_map[j][i] = 0
                else:
                    if not ceil:
                        self.mini_map[j][i] = -1
                        continue
                    if ceil < 50:
                        self.mini_map[j][i] = 1
                        if j > max_y:
                            max_y = j
                        elif j < min_y:
                            min_y = j
                        if i > max_x:
                            max_x = i
                        elif i < min_x:
                            min_x = i
                    else:
                        self.mini_map[j][i] = 0
        self.map_pos = (self.mini_map_width // 2 + (self.mini_map_width - (max_x - min_x) * self.map_tile) // 2,
                        self.mini_map_hight + (self.mini_map_hight - (max_y - min_y) * self.map_tile) // 2 - self.map_tile - 10)
        self.minimap_fon = pygame.Surface((self.mini_map_width, self.mini_map_hight + 20), pygame.SRCALPHA)
        self.minimap_fon.fill((64, 255, 255, 150))
        self.minimap_fon_pos = (self.mini_map_width // 2, self.mini_map_hight - self.map_tile - 10)
        self.mini_map_screen = pygame.Surface((self.mini_map_width, self.mini_map_hight), pygame.SRCALPHA)

    def render(self, player, screen):
        self.mini_map_screen.fill((255, 255, 255, 0))
        map_x, map_y = player.x // self.mini_map_scale, player.y // self.mini_map_scale
        for j in range(len(self.mini_map)):
            for i in range(len(self.mini_map[0])):
                if self.mini_map[j][i] == 1:
                    pygame.draw.rect(self.mini_map_screen, LIGHTGRAY, (i * self.map_tile, j * self.map_tile,
                                                                       self.map_tile + 1, self.map_tile + 1))
                elif not self.mini_map[j][i]:
                    pygame.draw.rect(self.mini_map_screen, BLACK, (i * self.map_tile, j * self.map_tile,
                                                                   self.map_tile + 1, self.map_tile + 1))
        pygame.draw.line(self.mini_map_screen, YELLOW, (map_x, map_y), (map_x + 12 * cos(player.angle),
                                                                        map_y + 12 * sin(player.angle)), 2)
        pygame.draw.circle(self.mini_map_screen, RED, (int(map_x), int(map_y)), 5)
        screen.blit(self.minimap_fon, self.minimap_fon_pos)
        screen.blit(self.mini_map_screen, self.map_pos)

    def rotateing(self):
        pass
