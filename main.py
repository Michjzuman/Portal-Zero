import os
import shutil
from pathlib import Path
import json
import time
import random
import math

with open("hosts.json", "r") as file:
    hosts: list[list] = json.load(file)

def draw():
    w, h = shutil.get_terminal_size()
    w = min(w, 100)
    
    table = [
        f"{host.get('emoji')}  {host.get('title')}"
        for host in hosts
    ]
    
    table_max = max(len(l) for l in table)
    
    effect_symbols = "▪▫◼◻■□▢▣"
    
    picture = (
        "\n".join([
            ("".join([
                random.choice(list(effect_symbols))
                if random.randint(0, a) == 0 else " "
                for _ in range(w)
            ]))
            for a in range(5)
        ]) +
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
        f"╭────{'─' * table_max}───────────╮\n" +
        f"\n├────{'─' * table_max}───────────┤\n"
        .join([
            "\n".join([
                f"│    {' ' * table_max}    ╭────╮ │",
                f"│  {line} {' ' * (table_max - len(line))}    │ ➜  │ │",
                f"│    {' ' * table_max}    ╰────╯ │"
            ])
            for line in table
        ]) +
        f"\n╰────{'─' * table_max}───────────╯\n\n" +
        "\n".join([
            ("".join([
                random.choice(list(effect_symbols))
                if random.randint(0, a) == 0 else " "
                for _ in range(w)
            ]))
            for a in reversed(range(5))
        ])
    )
    
    # ─  │    └  ┘  ├  ┤  ┬  ┴  ┼ ╭ ╮ ╰ ╯
    
    print(picture + f"\033[{picture.count('\n') + 1}F", end = "", flush = True)



old_w = 10000
while True:
    w, h = shutil.get_terminal_size()
    if old_w > w:
        os.system("clear")
    draw()
    old_w = w
    time.sleep(0.1)
