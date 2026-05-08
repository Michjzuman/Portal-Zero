import os
import shutil
import json
import time
import random
import sys
import termios
import tty
import select
import subprocess
import math

with open("hosts.json", "r") as file:
    hosts = json.load(file)

THEME = {
    "reset": "\033[0m",
    "effect": "\033[38;2;50;255;180m",
    "logo": "\033[38;2;255;255;255m\033[1m",
    "border": "\033[38;2;100;100;100m",
    "bg": "\033[38;2;100;100;100m",
    "text": "\033[38;2;230;255;250m",
    "button_border": "\033[38;2;100;100;100m",
    "arrow": "\033[38;2;100;100;100m",
    "selected_box": "\033[38;2;255;255;255m\033[1m",
    "selected_button": "\033[38;2;0;200;240m\033[1m",
    "selected_arrow": "\033[38;2;0;200;240m\033[1m",
    "window_border": "\033[38;2;0;100;50m\033[1m",
}

FPS = 10
FRAME_TIME = 1 / FPS

EFFECT_SYMBOLS = "▪▫◼◻■□▢▣"

LOGO = [
    "▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄   █████ ███████ █████ ███████  ",
    "█▄█ █ █ █▄█  █  █▄█ █     ▄▀  █▄▄▄▄▄█ █▄▄▄█ █     █  ",
    "█   █▄█ █▀▄  █  █ █ █▄▄ ▄█▄▄▄ █▄▄▄▄▄▄ █ ▀▄▄ █▄▄▄▄▄█  ",
]


def color(name, text):
    return f"{THEME[name]}{text}{THEME['reset']}"


def safe_len(text):
    # Grobe Terminal-Breite: Emojis werden meistens als 2 Spalten gerendert.
    length = 0

    for char in text:
        length += 2 if ord(char) > 0xFFFF else 1

    return length


def read_key():
    if not select.select([sys.stdin], [], [], 0)[0]:
        return None

    key = sys.stdin.read(1)

    if key == "\033":
        key += sys.stdin.read(2)

    return key


def make_effect(width, direction):
    return "\n".join([
        "".join([
            color("effect", random.choice(EFFECT_SYMBOLS))
            if random.randint(0, chance) == 0 else " "
            for _ in range(width)
        ])
        for chance in direction
    ])


def build_ssh_command(host):
    user = host.get("user")
    hostname = host.get("host")
    port = host.get("port", 22)

    if not hostname:
        return None

    target = hostname

    if user:
        target = f"{user}@{hostname}"

    return ["ssh", "-p", str(port), target]


def launch_host(host):
    command = build_ssh_command(host)

    if command is None:
        show_message("Host hat keine Adresse.")
        return

    os.system("clear")
    print("\033[?25h\033[0m", end="", flush=True)
    print(color("logo", "PORTAL ZERO"))
    print()
    print(color("text", f"Verbinde mit {host.get('title', host.get('host', 'Unknown'))}..."))
    print(color("border", " ".join(command)))
    print()

    subprocess.run(command)

    print()
    input(color("text", "Verbindung beendet. Enter drücken, um zum Launcher zurückzukehren..."))
    print("\033[?25l", end="", flush=True)
    os.system("clear")


def show_message(message):
    os.system("clear")
    print("\033[?25h\033[0m", end="", flush=True)
    print(color("logo", "PORTAL ZERO"))
    print()
    print(color("text", message))
    print()
    input(color("text", "Enter drücken, um zurückzukehren..."))
    print("\033[?25l", end="", flush=True)
    os.system("clear")


def draw(selected_index, hidden = False):
    width, _ = shutil.get_terminal_size()
    width = min(width, 100)

    table = [
        f"{host.get('emoji', '#')}  {host.get('title', 'No title')}"
        for host in hosts
    ]

    if not table:
        table = ["No hosts found"]

    table_max = max(safe_len(line) for line in table)

    logo = "\n".join([
        f"{' ' * max(0, width - len(line))}{color('logo', line)}"
        for line in LOGO
    ])

    table_top = color("border", f"╭────{'─' * table_max}───────────╮")
    table_separator = color("border", f"├────{'─' * table_max}───────────┤")
    table_bottom = color("border", f"╰────{'─' * table_max}───────────╯")

    rows = []

    for index, line in enumerate(table):
        selected = index == selected_index
        box_color = "selected_box" if selected else "border"
        button_color = "selected_button" if selected else "button_border"
        arrow_color = "selected_arrow" if selected else "arrow"
        text_color = "selected_box" if selected else "text"
        padding = " " * (table_max - safe_len(line))

        rows.append("\n".join([
            f"{color(box_color, '│')}    {' ' * table_max}    {color(button_color, '╭────╮')} {color(box_color, '│')}",
            f"{color(box_color, '│')}  {color(text_color, line)} {padding}     {color(button_color, '│')} {color(arrow_color, '➜')}  {color(button_color, '│')} {color(box_color, '│')}",
            f"{color(box_color, '│')}    {' ' * table_max}    {color(button_color, '╰────╯')} {color(box_color, '│')}",
        ]))

    table_rows = f"\n{table_separator}\n".join(rows)

    picture = (
        make_effect(width, range(5)) +
        "\n\n" +
        logo +
        "\n\n" +
        table_top +
        "\n" +
        table_rows +
        "\n" +
        table_bottom +
        "\n\n" +
        make_effect(width, reversed(range(5)))
    )

    if not hidden:
        print(picture + f"\033[{picture.count(chr(10)) + 1}F", end="", flush=True)
    
    return picture


def main():
    selected_index = 0
    old_width = 10000
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())
        print("\033[?25l", end="", flush=True)

        while True:
            frame_start = time.monotonic()
            width, _ = shutil.get_terminal_size()
            key = read_key()

            if key == "\033[A" and hosts:
                selected_index = (selected_index - 1) % len(hosts)
            elif key == "\033[B" and hosts:
                selected_index = (selected_index + 1) % len(hosts)
            elif key in ["\n", "\r"] and hosts:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                launch_host(hosts[selected_index])
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            elif key in ["q", "\x03"]:
                break

            if old_width != width:
                os.system("clear")

            draw(selected_index)
            old_width = width

            elapsed = time.monotonic() - frame_start
            time.sleep(max(0, FRAME_TIME - elapsed))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("\033[?25h\033[0m", end="", flush=True)
        os.system("clear")


def intro():
    menu = draw(0, True)
    
    #os.system("clear")
    
    #w, h = shutil.get_terminal_size()
    w, _ = shutil.get_terminal_size()
    w = min(w, 100)
    h = len(menu.split("\n"))
    
    #== Window Border =================
    
    steps = 100
    for i in range(steps):
        border_w = round(i / steps * w)
        border_h = round(i / steps * h)
        picture = (
            f"{color('window_border', '▄' * (border_w+2))}\n" +
            "\n".join([
                f"{THEME['window_border']}█{THEME['reset']}{' ' * border_w}{THEME['window_border']}█{THEME['reset']}"
                for _ in range(border_h)
            ]) +
            f"\n{color('window_border', '▀' * (border_w+2))}"
        )
        print(
            picture + "\033[" + str(len(picture.split('\n')) - 1) + "F",
            end="", flush=True
        )
        time.sleep(0.01)
    
    #==================================
    
    center_x = w / 4
    center_y = h / 2
    
    picture = "\n".join([
        " " for _ in range(round(w/2))
        for _ in range(h)
    ])

    radius = max(round(w/2), round(h/2))
    quantity = 20
    layers = 900
    pixels = [
        (
            random.choice(EFFECT_SYMBOLS),
            center_x + (radius + layer) * math.sin(math.radians(360 / quantity * i)),
            center_y + (radius + layer) * math.cos(math.radians(360 / quantity * i)),
            f"""\033[38;2;{
                [200,  50, 50, 100, 100, 100][i % 4]
            };{
                [255, 100, 200, 150, 200, 255][i % 4]
            };{
                [200,  50, 50, 100, 100, 100][i % 4]
            }m"""
        )
        for layer in range(layers)
        for i in range(quantity)
    ]
    
    swirl_strength = 0.063
    zoom = 0.97
    
    while True:
        new_lines = [[" " for _ in range(round(w/2))] for _ in range(h)]
        new_pixels = []
        
        swirl_strength -= 0.0002
        zoom += 0.000115

        for char, x, y, color_code in pixels:
            dx = x - center_x
            dy = y - center_y

            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)

            swirl_strength += 0
            speed = swirl_strength / max(0, radius / 8)

            angle += speed
            radius *= zoom

            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius

            new_pixels.append((char, x, y, color_code))

            ix = round(x)
            iy = round(y)

            if 0 <= ix < round(w/2) and 0 <= iy < h:
                new_lines[iy][ix] = color_code + char + THEME["reset"]

        pixels = new_pixels
        picture = (
            f"{color('window_border', '▄' * (w+1))}\n" +
            "\n".join([
                f"{THEME['window_border']}█{THEME['reset']}{' '.join(line)}{THEME['window_border']}█{THEME['reset']}"
                for line in new_lines
            ]) +
            f"\n{color('window_border', '▀' * (w+1))}"
        )
        
        print(
            picture + "\033[" + str(len(picture.split('\n')) - 1) + "F",
            end="", flush=True
        )
        
        time.sleep(0.0)

if __name__ == "__main__":
    #main()
    intro()