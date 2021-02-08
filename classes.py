from inventory_attributes import *
from math import degrees, atan2, sqrt
from collections import deque
import random
import pygame
import sqlite3

pygame.init()
DISPLAY = pygame.display.set_mode((WIDTH, HEIGHT))


class VS_Menu:
    def __init__(self):
        pygame.init()
        self.running, self.playing = True, False
        self.UP_KEY, self.DOWN_KEY, self.START_KEY, self.BACK_KEY = False, False, False, False
        self.display = DISPLAY
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        self.font_name = 'data/8-BIT WONDER.TTF'
        self.BLACK, self.WHITE = (0, 0, 0), (255, 255, 255)
        self.main_menu = MainMenu(self)
        self.options = OptionsMenu(self)
        self.credits = CreditsMenu(self)
        self.curr_menu = self.main_menu
        self.lvl = int(self.options.state) - 1

    def game_loop(self):
        while self.playing:
            self.check_events()
            if self.START_KEY:
                self.lvl = int(self.options.state) - 1
                self.playing = False
            self.window.blit(self.display, (0, 0))
            pygame.display.update()
            self.reset_keys()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running, self.playing = False, False
                self.curr_menu.run_display = False
            if event.type == pygame.KEYDOWN:
                self.lvl = int(self.options.state) - 1
                self.running, self.playing = True, False
                if event.key == pygame.K_RETURN:
                    self.START_KEY = True
                if event.key == pygame.K_BACKSPACE:
                    self.BACK_KEY = True
                if event.key == pygame.K_DOWN:
                    self.DOWN_KEY = True
                if event.key == pygame.K_UP:
                    self.UP_KEY = True

    def reset_keys(self):
        self.UP_KEY, self.DOWN_KEY, self.START_KEY, self.BACK_KEY = False, False, False, False

    def draw_text(self, text, size, x, y, color=(255, 255, 255)):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.center = (x, y)
        self.display.blit(text_surface, text_rect)


class Game:
    def __init__(self, screen, map, clock):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 36, bold=True)
        self.clock = clock
        self.Sprites = list()
        self.map = map
        self.player = None

    def fps(self, screen):
        fps = str(int(self.clock.get_fps()))
        render = self.font.render(fps, False, DARKORANGE)
        screen.blit(render, FPS_POS)

    def add_sprite(self, obj):
        self.Sprites.append(obj)

    def move_player(self):
        sprites_collision = [pygame.Rect(el.x, el.y, el.side, el.side)
                             for el in self.Sprites if el.blocked and el.is_live != 0]
        self.player.move_player(self.map.collision_walls + sprites_collision)
        self.player.move_camera()

    def new_main_player(self, start_pos):
        x = start_pos[0] * TILE + TILE // 2
        y = start_pos[1] * TILE + TILE // 2
        self.player = Player((x, y))

    def player_render_screen(self):
        self.player.camera.render_background(self.screen)
        objects = [obj.object_locate(self.player.camera) for obj in self.Sprites]
        self.player.camera.render_walls(self.screen, objects, self.map.size, self.map.world_map)

    def player_render_inventory(self):
        self.player.render_inventory(self.screen, self.map, self.Sprites)

    def player_render_helth_bar(self):
        self.player.render_helth_bar(self.screen)

    def is_end(self):
        return not any([obj.is_npc if obj.is_live else 0 for obj in self.Sprites])

    def run_sprites(self):
        for spr in self.Sprites:
            spr.run(self.player, self.map)


class Camera:
    def __init__(self, start_pos):
        self.pos = start_pos
        self.angle = start_angle
        self.textures = {
            1: load_image("wall2.png"),
            2: load_image("wall1.png"),
        }

    def render_walls(self, screen, sprites, size, world_map):
        rays = ray_casting_walls(self.pos, self.angle, size, world_map, self.textures)
        for _, texture, coords in sorted(sprites + rays, key=lambda x: x[0], reverse=True):
            if _:
                screen.blit(texture, coords)

    def render_background(self, screen):
        screen.fill(LIGHTGRAY, pygame.Rect(0, 0, WIDTH, HALF_HEIGHT))
        screen.fill(GRAY, pygame.Rect(0, HALF_HEIGHT, WIDTH, HALF_HEIGHT))


class Player:
    def __init__(self, start_pos):
        self.x, self.y = start_pos
        self.angle = start_angle
        self.sens = 0.004
        self.side = 50
        self.hp = 1000
        self.is_live = 1
        self.last_keys = pygame.key.get_pressed()
        self.helth_bar_width = 300
        self.helth_bar_height = 30
        self.helth_bar_pos = (WIDTH - self.helth_bar_width - 20, 10)
        self.inventory = deque()
        self.rect = pygame.Rect(*start_pos, self.side, self.side)
        self.camera = Camera(start_pos)

    def move_player(self, collisions):
        self.keyboard(collisions)
        self.mouse()
        self.rect.center = self.x, self.y
        self.angle %= (2 * pi)

    def render_inventory(self, screen, map, sprites):
        if len(self.inventory) > 0:
            self.inventory[0].render(self, screen)
            if Weapon in type(self.inventory[0]).__bases__:
                self.inventory[0].shoting(self, sprites, map.world_map)

    def render_helth_bar(self, screen):
        fill = ((self.hp if self.hp > 0 else 0) / 1000) * self.helth_bar_width
        outline_rect = pygame.Rect(*self.helth_bar_pos, self.helth_bar_width, self.helth_bar_height)
        fill_rect = pygame.Rect(*self.helth_bar_pos, fill, self.helth_bar_height)
        pygame.draw.rect(screen, GREEN, fill_rect)
        pygame.draw.rect(screen, WHITE, outline_rect, 2)

    def add_to_inventory(self, obj):
        self.inventory.append(obj)

    def detect_collision(self, dx, dy, collisions):
        next_rect = self.rect.copy()
        next_rect.move_ip(dx, dy)
        hit_indexes = next_rect.collidelistall(collisions)

        if len(hit_indexes):
            delta_x, delta_y = 0, 0
            for hit_index in hit_indexes:
                hit_rect = collisions[hit_index]
                if dx > 0:
                    delta_x += next_rect.right - hit_rect.left
                else:
                    delta_x += hit_rect.right - next_rect.left
                if dy > 0:
                    delta_y += next_rect.bottom - hit_rect.top
                else:
                    delta_y += hit_rect.bottom - next_rect.top

            if abs(delta_x - delta_y) < 10:
                dx, dy = 0, 0
            elif delta_x > delta_y:
                dy = 0
            elif delta_y > delta_x:
                dx = 0

        self.x += dx
        self.y += dy

    def keyboard(self, collisions):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            exit()

        sin_a = sin(self.angle)
        cos_a = cos(self.angle)
        if keys[pygame.K_w]:
            dx = player_speed * cos_a
            dy = player_speed * sin_a
            self.detect_collision(dx, dy, collisions)
        if keys[pygame.K_s]:
            dx = -player_speed * cos_a
            dy = -player_speed * sin_a
            self.detect_collision(dx, dy, collisions)
        if keys[pygame.K_a]:
            dx = player_speed * sin_a
            dy = -player_speed * cos_a
            self.detect_collision(dx, dy, collisions)
        if keys[pygame.K_d]:
            dx = -player_speed * sin_a
            dy = player_speed * cos_a
            self.detect_collision(dx, dy, collisions)
        if keys[pygame.K_LEFT] and not self.last_keys[pygame.K_LEFT]:
            if len(self.inventory) > 1:
                self.inventory[0].rotateing()
                self.inventory.rotate(-1)
        if keys[pygame.K_RIGHT] and not self.last_keys[pygame.K_RIGHT]:
            if len(self.inventory) > 1:
                self.inventory[0].rotateing()
                self.inventory.rotate(1)
        self.last_keys = keys

    def mouse(self):
        if pygame.mouse.get_focused():
            dif = pygame.mouse.get_pos()[0] - HALF_WIDTH
            pygame.mouse.set_pos((HALF_WIDTH, HALF_HEIGHT))
            self.angle += dif * self.sens

    def move_camera(self):
        self.camera.angle = self.angle
        self.camera.pos = (self.x, self.y)

    def set_pos(self, pos):
        self.x, self.y = pos

    def set_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.is_live = 0


class SpriteObject:
    def __init__(self, pos, angle, size, angle_shift, object, viewing_angles, shift, dist_scale, size_scale, animation,
                 animation_speed, blocked, side, hp, npc):
        self.angle = angle
        self.object = object
        self.size = size
        self.shift = shift
        self.dist_scale = dist_scale
        self.size_scale = size_scale
        self.animation = animation
        self.animation_speed = animation_speed
        self.animation_count = 0
        self.animating = 0
        self.blocked = blocked
        self.angle_shift = angle_shift
        self.rad_shift = self.angle_shift / 180 * pi
        self.side = side
        self.hp = hp
        self.init_hp = hp
        self.is_live = None if hp <= 0 else 1
        self.is_npc = npc
        self.x, self.y = pos[0] * TILE, pos[1] * TILE
        self.viewing_angles = viewing_angles
        self.view_angle = 360 // viewing_angles
        self.sprite_angles = [frozenset(range(i, i + self.view_angle)) for i in range(0, 360, self.view_angle)]

    def is_on_fire(self, max_distance):
        coef = 2.5 * self.distance_to_sprite / max_distance
        if CENTER_RAY - self.side // coef < self.current_ray < CENTER_RAY + self.side // coef and self.blocked:
            return self.distance_to_sprite, self
        return float('inf'), None

    def object_locate(self, camera):
        if not (self.is_live or self.is_live is None):
            return (False, False, False)
        self.incline = int(self.angle // self.view_angle)

        camera_x, camera_y = camera.pos
        dx, dy = self.x - camera_x, self.y - camera_y
        self.distance_to_sprite = sqrt(dx ** 2 + dy ** 2)

        self.theta = atan2(dy, dx)
        gamma = self.theta - camera.angle
        if dx > 0 and 180 <= degrees(camera.angle) <= 360 or dx < 0 and dy < 0:
            gamma += pi * 2

        delta_rays = int(gamma / DELTA_ANGLE)
        self.current_ray = CENTER_RAY + delta_rays
        self.distance_to_sprite *= cos(HALF_FOV - self.current_ray * DELTA_ANGLE)

        fake_ray = self.current_ray + FAKE_RAYS
        if 0 <= fake_ray <= FAKE_RAYS_RANGE and self.distance_to_sprite > 20:
            self.proj_height = min(int(PROJ_COEFF / self.distance_to_sprite * self.dist_scale), HEIGHT * 2)
            shift = self.proj_height // 2 * self.shift
            self.sprite_object = self.visible_sprite()
            self.sprite_animation()

            sprite_pos = (self.current_ray * SCALE - self.proj_height // 2, HALF_HEIGHT - self.proj_height // 2 + shift)
            size = int(self.proj_height * self.size_scale)
            sprite_object_with_helth_bar = self.helth_bar()
            sprite = pygame.transform.scale(sprite_object_with_helth_bar, (size, size))
            return (self.distance_to_sprite, sprite, sprite_pos)
        else:
            return (False, False, False)

    def viewing(self, camera):
        camera_x, camera_y = camera.pos
        dx, dy = self.x - camera_x, self.y - camera_y
        gamma = atan2(dy, dx) - self.angle + self.rad_shift
        if dx > 0 and 180 <= degrees(self.angle - self.rad_shift) <= 360 or dx < 0 and dy < 0:
            gamma += pi * 2

        delta_rays = int(gamma / DELTA_ANGLE)
        current_ray = CENTER_RAY + delta_rays
        fake_ray = current_ray + delta_rays

        if 0 <= fake_ray <= FAKE_RAYS_RANGE and self.distance_to_sprite > 20:
            return True
        else:
            return False

    def helth_bar(self):
        if not self.is_live:
            return self.sprite_object.copy()
        helth_bar_width = 60 / self.size_scale
        helth_bar_height = 8 / self.size_scale
        helth_bar_pos = ((self.size[0] - helth_bar_width) / 2, 5 / self.size_scale)
        sprite_object_with_helth_bar = self.sprite_object.copy()
        fill = ((self.hp if self.hp > 0 else 0) / self.init_hp) * helth_bar_width
        outline_rect = pygame.Rect(*helth_bar_pos, helth_bar_width, helth_bar_height)
        fill_rect = pygame.Rect(*helth_bar_pos, fill, helth_bar_height)
        pygame.draw.rect(sprite_object_with_helth_bar, RED, fill_rect)
        pygame.draw.rect(sprite_object_with_helth_bar, WHITE, outline_rect, 2)
        return sprite_object_with_helth_bar

    def sprite_animation(self):
        if self.animation and self.animating:
            self.sprite_object = self.animation[self.animating - 1][self.incline][0]
            if self.animation_count < self.animation_speed:
                self.animation_count += 1
            else:
                self.animation[self.animating - 1][self.incline].rotate()
                self.animation_count = 0

    def visible_sprite(self):
        sprite_object = self.object
        if self.viewing_angles > 1:
            if self.theta < 0:
                self.theta += pi * 2
            theta = (360 - int(degrees(self.theta)) + self.angle_shift) % 360
            for angles in self.sprite_angles:
                if theta in angles:
                    self.incline += int(self.sprite_angles.index(angles))
                    self.incline %= self.viewing_angles
                    sprite_object = self.object[self.incline]
                    break
        return sprite_object

    def npc_move_to_player(self, player):
        if abs(self.distance_to_sprite) > 2 * TILE:
            self.npc_move((player.y, player.x))

    def npc_move(self, pos):
        if self.is_live is None or self.is_live:
            dx = self.x - pos[1]
            dy = self.y - pos[0]
            self.x = self.x + 1 if dx < 0 else self.x - 1
            self.y = self.y + 1 if dy < 0 else self.y - 1
            self.angle = atan2(dy, dx)

    def set_damage(self, damage):
        self.hp -= damage
        if self.hp <= 0:
            self.is_live = 0

    def run(self, player, map):
        pass


ANIMATION = {
    "0": ([load_image(f"0\\{i}\\0.png", color_key=-1) for i in range(4)],
          [[deque((load_image(f"0\\{j}\\{i}.png", color_key=-1) for i in range(4))) for j in range(4)]]),
    "1": ([load_image(f"1\\{i}\\0.png", color_key=-1) for i in range(4)],
          [[deque((load_image(f"1\\{j}\\{i}.png", color_key=-1) for i in range(4))) for j in range(4)]]),
    "box": [load_image(f"box{i}.png", color_key=-1) for i in range(1, 3)]
}


class Spaceman(SpriteObject):
    def __init__(self, pos, angle, color):
        object = ANIMATION[str(color)][0].copy()
        animation = ANIMATION[str(color)][1].copy()
        viewing_angles = 4
        shift = 0.4
        size_scale = 1.3
        dist_scale = 1
        animation_speed = 25
        blocked = True
        angle_shift = 45
        side = 25
        hp = 1000
        size = (100, 100)
        npc = 1
        self.path = []
        self.damage = 30
        self.time_reload = 40
        self.reload_count = 0
        super().__init__(pos, angle, size, angle_shift, object, viewing_angles, shift, size_scale, dist_scale,
                         animation,
                         animation_speed, blocked, side, hp, npc)

    def run(self, player, map):
        if not self.is_live:
            return
        self.animating = 0
        if ray_casting_npc_player(self.x, self.y, (player.x, player.y), map.world_map) and \
                ((self.viewing(player.camera) or self.distance_to_sprite < 4 * TILE)):
            self.path = []
            self.npc_move_to_player(player)
            if self.reload_count == 0:
                dx, dy = player.x - self.x, player.y - self.y
                cof = tanh(TILE * 15 / sqrt(dx ** 2 + dy ** 2))
                if random.random() < 0.5 * cof:
                    player.set_damage(int(self.damage * cof))
                self.reload_count = self.time_reload
            else:
                self.reload_count -= 1
        else:
            if self.path:
                if self.time != 0:
                    self.time -= 1
                    return
                self.animating = 1
                dx, dy = self.x - self.path[0][1], self.y - self.path[0][0]
                if dx == 0 and dy == 0:
                    del self.path[0]
                if self.path:
                    self.npc_move(self.path[0])
            else:
                self.time = random.randint(100, 700)
                xm, ym = self.x // TILE, self.y // TILE
                self.dist = bfs(map.text_map, (ym, xm), 1)
                while not self.path:
                    end = (random.randint(0, len(self.dist) - 1), random.randint(0, len(self.dist[0]) - 1))
                    if self.dist[end[0]][end[1]] == INF:
                        continue
                    ans = [end]
                    while ans[-1] != (ym, xm):
                        for u in neighbors(ans[-1], map.text_map, 1):
                            if self.dist[u[0]][u[1]] == self.dist[ans[-1][0]][ans[-1][1]] - 1:
                                ans.append(u)
                                break
                    self.path = (ans[::-1])[1:]
                    for i in range(len(self.path)):
                        self.path[i] = (self.path[i][0] * TILE + TILE // 2, self.path[i][1] * TILE + TILE // 2)


class Menu:
    def __init__(self, game):
        self.game = game
        self.game.lvl = 1
        self.mid_w, self.mid_h = WIDTH / 2, HEIGHT / 2
        self.run_display = True
        self.cursor_rect = pygame.Rect(0, 0, 20, 20)
        self.offset = - 100

    def draw_cursor(self):
        self.game.draw_text('*', 15, self.cursor_rect.x, self.cursor_rect.y)

    def blit_screen(self):
        self.game.window.blit(self.game.display, (0, 0))
        pygame.display.update()
        self.game.reset_keys()


class MainMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game)
        self.state = "Start"
        self.startx, self.starty = self.mid_w, self.mid_h + 30
        self.optionsx, self.optionsy = self.mid_w, self.mid_h + 50
        self.creditsx, self.creditsy = self.mid_w, self.mid_h + 70
        self.cursor_rect.midtop = (self.startx + self.offset, self.starty)

    def display_menu(self):
        self.run_display = True
        while self.run_display:
            self.game.check_events()
            point = self.check_input()
            self.game.display.fill(self.game.BLACK)
            self.game.draw_text('SPACE ALARM', 20, WIDTH / 2, HEIGHT / 2 - 20)
            self.game.draw_text("Start Game", 20, self.startx, self.starty)
            self.game.draw_text("Levels", 20, self.optionsx, self.optionsy)
            self.game.draw_text("Credits", 20, self.creditsx, self.creditsy)
            self.draw_cursor()
            self.blit_screen()
        return point

    def move_cursor(self):
        if self.game.DOWN_KEY:
            if self.state == 'Start':
                self.cursor_rect.midtop = (self.optionsx + self.offset, self.optionsy)
                self.state = 'Options'
            elif self.state == 'Options':
                self.cursor_rect.midtop = (self.creditsx + self.offset, self.creditsy)
                self.state = 'Credits'
            elif self.state == 'Credits':
                self.cursor_rect.midtop = (self.startx + self.offset, self.starty)
                self.state = 'Start'
        elif self.game.UP_KEY:
            if self.state == 'Start':
                self.cursor_rect.midtop = (self.creditsx + self.offset, self.creditsy)
                self.state = 'Credits'
            elif self.state == 'Options':
                self.cursor_rect.midtop = (self.startx + self.offset, self.starty)
                self.state = 'Start'
            elif self.state == 'Credits':
                self.cursor_rect.midtop = (self.optionsx + self.offset, self.optionsy)
                self.state = 'Options'

    def check_input(self):
        self.move_cursor()
        if self.game.START_KEY:
            if self.state == 'Start':
                self.game.playing = True
            elif self.state == 'Options':
                self.game.curr_menu = self.game.options
            elif self.state == 'Credits':
                self.game.curr_menu = self.game.credits
            self.run_display = False
        return self.game.playing


class OptionsMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game)
        self.state = '1'
        self.lvl = int(self.state) - 1
        self.volx, self.voly = self.mid_w, self.mid_h + 20
        self.controlsx, self.controlsy = self.mid_w, self.mid_h + 40
        self.cursor_rect.midtop = (self.volx + self.offset, self.voly)
        con = sqlite3.connect("data/sa-bd.sqlite")
        self.cur = con.cursor()

    def display_menu(self):
        self.run_display = True
        while self.run_display:
            self.game.check_events()
            self.check_input()
            self.game.display.fill((0, 0, 0))
            done = [e[0] for e in self.cur.execute("""SELECT lvl FROM levels
                        WHERE done = 1""").fetchall()]
            self.game.draw_text('level:', 20, WIDTH / 2, HEIGHT / 2 - 30)
            self.game.draw_text("first", 15, self.volx, self.voly,
                                color=(0, 255, 0) if 1 in done else (255, 255, 255))
            self.game.draw_text("second", 15, self.controlsx, self.controlsy,
                                color=(0, 255, 0) if 2 in done else (255, 255, 255))
            self.draw_cursor()
            self.blit_screen()

    def check_input(self):
        if self.game.BACK_KEY:
            self.game.curr_menu = self.game.main_menu
            self.lvl = int(self.state) - 1
            self.run_display = False
        elif self.game.UP_KEY or self.game.DOWN_KEY:
            if self.state == '1':
                self.state = '2'
                self.cursor_rect.midtop = (self.controlsx + self.offset, self.controlsy)
            elif self.state == '2':
                self.state = '1'
                self.cursor_rect.midtop = (self.volx + self.offset, self.voly)
        elif self.game.START_KEY:
            self.game.curr_menu = self.game.main_menu
            self.game.lvl = int(self.state) - 1
            self.run_display = False


class CreditsMenu(Menu):
    def __init__(self, game):
        Menu.__init__(self, game)

    def display_menu(self):
        self.run_display = True
        while self.run_display:
            self.game.check_events()
            if self.game.START_KEY or self.game.BACK_KEY:
                self.game.curr_menu = self.game.main_menu
                self.run_display = False
            self.game.display.fill(self.game.BLACK)
            self.game.draw_text('Credits', 20, WIDTH / 2, HEIGHT / 2 - 20)
            self.game.draw_text('Made by Anton and Gordey', 15, WIDTH / 2, HEIGHT / 2 + 10)
            self.blit_screen()


class Dispenser(SpriteObject):
    def __init__(self, pos, surface, clock, obj):
        object = ANIMATION["box"].copy() + ANIMATION["box"].copy() + ANIMATION["box"].copy() + ANIMATION["box"].copy()
        animation = None
        viewing_angles = 8
        shift = 1
        size_scale = 0.7
        dist_scale = 1
        animation_speed = 0
        blocked = True
        angle_shift = 12
        side = 25
        hp = 0
        size = (100, 100)
        npc = 0
        self.clock = clock
        self.fps = 60
        self.barside = 300
        self.minmax = self.barside, surface.get_rect().width - self.barside * 2
        self.rect = pygame.Rect(self.minmax[0], 200, self.minmax[1], 30)
        self.bar = self.minmax[0]
        self.surface = surface
        self.obj = obj
        super().__init__(pos, 0, size, angle_shift, object, viewing_angles, shift, size_scale, dist_scale,
                         animation,
                         animation_speed, blocked, side, hp, npc)

    def run(self, player, map):
        if not self.obj:
            return
        delta = (self.fps / self.clock.get_fps()) if self.clock.get_fps() != 0 else 0
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.bar += delta * 3
            if self.bar >= self.minmax[1] + self.minmax[0]:
                player.add_to_inventory(self.obj)
                self.obj = None
        else:
            self.bar -= delta
            if self.bar < self.minmax[0]:
                self.bar = self.minmax[0]
        dx, dy = self.x - player.x, self.y - player.y
        if dx ** 2 + dy ** 2 <= 1.5 * TILE * TILE:
            pygame.draw.rect(self.surface, pygame.Color('gray60'), self.rect)

            if self.bar > self.minmax[0]:
                rect = self.rect.copy()
                rect.width = int(self.bar) - self.barside
                pygame.draw.rect(self.surface, BLUEGREEN, rect)
