import os
import shutil
from pathlib import Path
import json

def draw():
    w, h = shutil.get_terminal_size()
    w = min(w, 70)
    h = min(h, 25)
    
    os.system("clear")

    line = "\\\\\\\\\\\\\\"
    title = "\n".join([
        f" ______              ______   __________    __        __       ",
        f"|   _  \   @@@@@@@  |   _  \ |___    ___|  /  \      |  |      ",
        f"|  |_)  | @{line }@ |  |_)  |    |  |     /    \     |  |      ",
        f"|   ___/  @///////@ |     _/     |  |    /  /\  \    |  |      ",
        f"|  |      @{line }@ |  |\ \      |  |   /  /__\  \   |  |      ",
        f"|  |      @///////@ |  | \ \     |  |  /  _____   \  |  |_____ ",
        f"|__|       @@@@@@@  |__|  \_\    |__| /__/     \___\ |________|",
    ])

    box = "\n".join(
        [f"╭{'─' * (w - 2)}╮"] +
        [
            "│" + " " * (w - 2) + "│" for y in range(h - 2)
        ] +
        [f"╰{'─' * (w - 2)}╯"]
    )
    
    def overlay(background, artwork, x, y):
        return background

    result = box
    result = overlay(result, title, 2, 2)
    
    print(result, end = "", flush = True)

draw()

#  ╭────────────────────────────────╮
#  │  ●  PORTAL ZERO        VPN: OK │
#  │                                │
#  │  [ USB-C ]                     │
#  │                                │
#  │  Home Access Terminal          │
#  │  SSH · WireGuard · Pocket LAN  │
#  ╰────────────────────────────────╯
