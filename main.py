import os
import shutil
from pathlib import Path
import json
import time

with open("hosts.json", "r") as file:
    hosts: list[list] = json.load(file)

def draw():
    w, h = shutil.get_terminal_size()
    w = min(w, 100)
    h = min(h, 25)
    
    table = [
        f"{host.get('emoji')}  {host.get('title')}"
        for host in hosts
    ]
    
    picture = (
        ("#" * w) +
        "\n\n" +
        "\n".join([
            f"{' ' * (w - len(line))}{line}"
            for line in [
                "▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄   █████ ███████ █████ ███████  ",
                "█▄█ █ █ █▄█  █  █▄█ █     ▄▀  █▄▄▄▄▄█ █▄▄▄█ █     █  ",
                "█   █▄█ █▀▄  █  █ █ █▄▄ ▄█▄▄▄ █▄▄▄▄▄▄ █ ▀▄▄ █▄▄▄▄▄█  ",
            ]
        ]) +
        "\n\n" +
        f"╭────{'─' * max([len(l) for l in table])}───────────╮\n" +
        f"\n├────{'─' * max([len(l) for l in table])}───────────┤\n"
        .join([
            "\n".join([
                f"│    {' ' * max([len(l) for l in table])}    ╭────╮ │",
                f"│  {line} {' ' * (max([len(l) for l in table]) - len(line))}    │ ➜  │ │",
                f"│    {' ' * max([len(l) for l in table])}    ╰────╯ │"
            ])
            for line in table
        ]) +
        f"\n╰────{'─' * max([len(l) for l in table])}───────────╯\n" +
        ("#" * w)
    )
    
    # ─  │    └  ┘  ├  ┤  ┬  ┴  ┼ ╭ ╮ ╰ ╯
    
    print(picture + f"\033[{picture.count('\n') + 1}F", end = "", flush = True)



os.system("clear")
while True:
    draw()
    time.sleep(0.1)