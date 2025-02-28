#from game import Game
import importlib
game_module = importlib.import_module('game')
Game = game_module.Game

if __name__ == "__main__":
    Game()
