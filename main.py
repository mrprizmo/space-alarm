from client import Client
from classes import VS_Menu


if __name__ == "__main__":
    m = VS_Menu()
    c = Client(0)
    while m.running:
        point = m.curr_menu.display_menu()
        if point:
            map_id = m.lvl
            c.new_game(map_id)
            c.run_game()