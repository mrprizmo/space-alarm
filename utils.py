from settings import *
from math import sin, cos, atan2
from numba import njit
import pygame
import numpy as np
import os


@njit(fastmath=True, cache=True)
def mapping(a, b):
    return int((a // TILE) * TILE), int((b // TILE) * TILE)


def load_image(name, *, color_key=None, scale=1):
    fullname = os.path.join('data', name)
    image = pygame.image.load(fullname)
    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((1, 1))
            image.set_colorkey(color_key)
    image = image.convert_alpha()
    image = pygame.transform.scale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
    return image


@njit(fastmath=True, cache=True)
def ray_casting(pos, angle, map_size, map):
    ox, oy = pos
    xm, ym = mapping(ox, oy)
    texture_v, texture_h = 1, 1
    cur_angle = angle - HALF_FOV
    rays = []
    for ray in range(NUM_RAYS):
        sin_a = sin(cur_angle)
        cos_a = cos(cur_angle)
        sin_a = sin_a if sin_a else 0.000001
        cos_a = cos_a if cos_a else 0.000001

        if cos_a >= 0:
            x = xm + TILE
            dx = 1
        else:
            x = xm
            dx = -1
        for i in range(0, map_size[0] * TILE, TILE):
            depth_v = (x - ox) / cos_a
            yv = oy + depth_v * sin_a
            tile_v = mapping(x + dx, yv)
            if tile_v in map:
                texture_v = map[tile_v]
                break
            x += dx * TILE

        if sin_a >= 0:
            y = ym + TILE
            dy = 1
        else:
            y = ym
            dy = -1
        for i in range(0, map_size[1] * TILE, TILE):
            depth_h = (y - oy) / sin_a
            xh = ox + depth_h * cos_a
            tile_h = mapping(xh, y + dy)
            if tile_h in map:
                texture_h = map[tile_h]
                break
            y += dy * TILE

        if depth_v < depth_h:
            depth = depth_v
            offset = yv
            texture = texture_v
        else:
            depth = depth_h
            offset = xh
            texture = texture_h
        offset = int(offset) % TILE
        depth *= cos(angle - cur_angle)
        depth = max(depth, 0.00001)
        proj_height = min(int(PROJ_COEFF / depth), 2 * HEIGHT)

        rays.append((depth, offset, proj_height, texture))
        cur_angle += DELTA_ANGLE
    return rays


def ray_casting_walls(pos, angle, map_size, map, textures):
    rays = ray_casting(pos, angle, map_size, map)
    walls = []
    ray = 0
    for depth, offset, proj_height, texture in rays:
        if proj_height > HEIGHT:
            coeff = proj_height / HEIGHT
            texture_height = TEXTURE_HEIGHT / coeff
            wall_column = textures[texture].subsurface(offset * TEXTURE_SCALE,
                                                       TEXTURE_HEIGHT // 2 - texture_height // 2,
                                                       TEXTURE_SCALE, texture_height)
            wall_column = pygame.transform.scale(wall_column, (SCALE, HEIGHT))
            wall_pos = (ray * SCALE, 0)
        else:
            wall_column = textures[texture].subsurface(offset * TEXTURE_SCALE, 0, TEXTURE_SCALE, TEXTURE_HEIGHT)
            wall_column = pygame.transform.scale(wall_column, (SCALE, proj_height))
            wall_pos = (ray * SCALE, HALF_HEIGHT - proj_height / 2)
        walls.append((depth, wall_column, wall_pos))
        ray += 1
    return walls


@njit(fastmath=True, cache=True)
def ray_casting_npc_player(npc_x, npc_y, player_pos, world_map):
    ox, oy = player_pos
    xm, ym = mapping(ox, oy)
    delta_x, delta_y = ox - npc_x, oy - npc_y
    cur_angle = atan2(delta_y, delta_x)
    cur_angle += pi

    sin_a = sin(cur_angle)
    sin_a = sin_a if sin_a else 0.000001
    cos_a = cos(cur_angle)
    cos_a = cos_a if cos_a else 0.000001

    x, dx = (xm + TILE, 1) if cos_a >= 0 else (xm, -1)
    for i in range(0, int(abs(delta_x)) // TILE):
        depth_v = (x - ox) / cos_a
        yv = oy + depth_v * sin_a
        tile_v = mapping(x + dx, yv)
        if tile_v in world_map:
            return False
        x += dx * TILE

    y, dy = (ym + TILE, 1) if sin_a >= 0 else (ym, -1)
    for i in range(0, int(abs(delta_y)) // TILE):
        depth_h = (y - oy) / sin_a
        xh = ox + depth_h * cos_a
        tile_h = mapping(xh, y + dy)
        if tile_h in world_map:
            return False
        y += dy * TILE
    return True


@njit(cache=True)
def neighbors(v, text_map, flag):
    y, x = v
    ans = []
    if flag:
        if x + 1 < len(text_map[0]):
            ans.append((y, x + 1))
            if y + 1 < len(text_map):
                ans.append((y + 1, x + 1))
            if y - 1 >= 0:
                ans.append((y - 1, x + 1))
        if x - 1 >= 0:
            ans.append((y, x - 1))
            if y + 1 < len(text_map):
                ans.append((y + 1, x - 1))
            if y - 1 >= 0:
                ans.append((y - 1, x - 1))
        if y + 1 < len(text_map):
            ans.append((y + 1, x))
        if y - 1 >= 0:
            ans.append((y - 1, x))

    else:
        if x + 1 < len(text_map[0]):
            ans.append((y, x + 1))
        if x - 1 >= 0:
            ans.append((y, x - 1))
        if y + 1 < len(text_map):
            ans.append((y + 1, x))
        if y - 1 >= 0:
            ans.append((y - 1, x))

    return ans


def bfs(text_map, start, flag):
    dist = np.array([[INF for __ in range(len(text_map[0]))] for _ in range(len(text_map))])
    dist[start[0]][start[1]] = 0
    q = list()
    q.append(start)
    while len(q):
        v = q.pop(0)
        for u in neighbors(v, text_map, flag):
            if dist[u[0]][u[1]] == INF and text_map[u[0]][u[1]] == 0:
                dist[u[0]][u[1]] = dist[v[0]][v[1]] + 1
                q.append(u)
    return dist