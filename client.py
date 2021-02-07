from classes import *
from map import *
import sqlite3


class Client:
    def __init__(self, fps):
        self.fps = fps
        self.game = None
        self.clock = pygame.time.Clock()
        self.screen = DISPLAY
        self.you_win = load_image("youwin.png")
        self.game_over = load_image("gameover.png")
        self.end_speed = 200

    def new_game(self, map_id):
        self.map_id = map_id
        self.game = Game(self.screen, Map(text_maps[map_id]), self.clock)
        for j, row in enumerate(text_maps[map_id]):
            for i, ceil in enumerate(row):
                if ceil:
                    if ceil == 50:
                        self.game.add_sprite(Spaceman((i, j), 0, 0))
                    elif ceil == 51:
                        self.game.add_sprite(Spaceman((i, j), 0, 1))
                    elif ceil == 53:
                        self.game.new_main_player((i, j))
                    elif ceil == 54:
                        self.game.add_sprite(
                            Dispenser((i, j), self.screen, self.clock, MiniMap(self.game.map, (i, j))))
        self.game.player.add_to_inventory(RetroGun())

    def run_game(self):
        pygame.mouse.set_visible(False)
        GAME_FLAG = True
        while GAME_FLAG:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    GAME_FLAG = False
                    break
            self.update()
            pygame.display.flip()
            if not self.game.player.is_live or self.game.is_end():
                GAME_FLAG = False
        cor = -WIDTH
        if self.game.is_end():
            end_image = self.you_win
            con = sqlite3.connect("data/sa-bd.sqlite")
            cur = con.cursor()
            cur.execute(f"UPDATE levels SET done = 1 WHERE lvl = {self.map_id + 1}")
            con.commit()

        else:
            end_image = self.game_over
        end = True
        while end:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                        end = False
                        break
                elif event.type == pygame.QUIT:
                    exit()
            if cor < 0:
                cor += self.clock.tick(FPS) / FPS * self.end_speed
            self.screen.blit(end_image, (cor, 0))
            pygame.display.flip()
        pygame.mouse.set_visible(True)

    def update(self):
        self.game.move_player()
        self.game.player_render_screen()
        self.game.player_render_inventory()
        self.game.player_render_helth_bar()
        self.game.run_sprites()
        if self.fps:
            self.game.fps(self.game.screen)
        self.game.clock.tick(FPS)

