"""Project entry point for Burst Defense.

This file stays intentionally small so a future teammate can immediately see
where the game starts without digging through engine code.
"""

from burst_defense.game import Game


if __name__ == "__main__":
    Game().run()
