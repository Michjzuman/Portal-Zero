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
import re
import shlex

ansi_regex = re.compile(r"\033\[[0-9;]*m")


def ansi_cells(line):
    cells = []
    style = ""
    i = 0

    while i < len(line):
        match = ansi_regex.match(line, i)

        if match:
            code = match.group(0)
            style = "" if code == THEME["reset"] else style + code
            i = match.end()
            continue

        char = line[i]
        cells.append(f"{style}{char}{THEME['reset']}" if style else char)
        i += 1

    return cells

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOSTS_FILE = os.path.join(BASE_DIR, "hosts.json")
STATE_FILE = os.path.expanduser("~/.portal-zero/state.json")

DEFAULT_HOSTS = [
    {
        "title": "Example Server",
        "host": "example.com",
        "user": "user",
        "port": 22
    }
]


def load_hosts():
    if not os.path.exists(HOSTS_FILE):
        with open(HOSTS_FILE, "w") as file:
            json.dump(DEFAULT_HOSTS, file, indent=4)

        print(f"{HOSTS_FILE} was not found and has been created with an example host.")
        print("Edit the file and restart portal-zero if needed.")
        return DEFAULT_HOSTS

    try:
        with open(HOSTS_FILE, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        print(f"{HOSTS_FILE} contains invalid JSON: {error}")
        return []
    except OSError as error:
        print(f"{HOSTS_FILE} could not be read: {error}")
        return []

    if not isinstance(data, list):
        print(f"{HOSTS_FILE} must contain a JSON list.")
        return []

    return data


hosts = load_hosts()

THEME = {
    "reset": "\033[0m",
    "effect": "\033[38;2;0;200;100m\033[1m",
    "logo": "\033[38;2;255;255;255m\033[1m",
    "border": "\033[38;2;100;100;100m",
    "bg": "\033[38;2;100;100;100m",
    "text": "\033[38;2;230;255;250m",
    "button_border": "\033[38;2;100;100;100m",
    "arrow": "\033[38;2;100;100;100m",
    "selected_box": "\033[38;2;255;255;255m\033[1m",
    "selected_button": "\033[38;2;0;200;240m\033[1m",
    "selected_arrow": "\033[38;2;0;200;240m\033[1m",
    "window_border": "\033[38;2;0;200;100m\033[1m",
}

FPS = 10
FRAME_TIME = 1 / FPS
INTRO_FPS = 50
INTRO_FRAME_TIME = 1 / INTRO_FPS
INTRO_QUANTITY = 12
INTRO_LAYER_FACTOR = 10
INTRO_ZOOM_START = 0.83
INTRO_ZOOM_STEP = 0.004

EFFECT_SYMBOLS = "▪▫◼◻■□▢▣"

LOGO = [
    "▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄▄▄ ▄   █████ ███████ █████ ███████  ",
    "█▄█ █ █ █▄█  █  █▄█ █     ▄▀  █▄▄▄▄▄█ █▄▄▄█ █     █  ",
    "█   █▄█ █▀▄  █  █ █ █▄▄ ▄█▄▄▄ █▄▄▄▄▄▄ █ ▀▄▄ █▄▄▄▄▄█  ",
]


def required_terminal_size():
    table = [host.get("title", "No title") for host in hosts] or ["No hosts found"]
    table_max = max(len(line) for line in table)
    table_width = len(f"  ╭────{'─' * table_max}───────────╮")
    required_width = max(max(len(line) for line in LOGO), table_width) + 2

    rows = len(table)
    required_height = 19 + (4 * rows)

    return required_width, required_height


def terminal_size_ok():
    width, height = shutil.get_terminal_size()
    required_width, required_height = required_terminal_size()
    return width >= required_width and height >= required_height


def show_terminal_size_warning():
    width, height = shutil.get_terminal_size()
    required_width, required_height = required_terminal_size()

    os.system("clear")
    print("\033[?25h\033[0m", end="", flush=True)
    print("PORTAL ZERO")
    print()
    print(f"Terminal too small: {width}x{height}")
    print(f"Needs at least:     {required_width}x{required_height}")


def wait_for_terminal_size():
    warned = False

    while not terminal_size_ok():
        show_terminal_size_warning()
        warned = True
        time.sleep(0.25)

    if warned:
        os.system("clear")
        print("\033[?25l", end="", flush=True)


def color(name, text):
    return f"{THEME[name]}{text}{THEME['reset']}"


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


def normalize_ssh_options(options):
    if not options:
        return []

    if isinstance(options, str):
        return shlex.split(options)

    if isinstance(options, list):
        return [str(option) for option in options]

    return []


def build_ssh_command(host):
    user = host.get("user")
    hostname = host.get("host")
    port = host.get("port", 22)
    key = host.get("key") or host.get("identity_file")

    if not hostname:
        return None

    target = hostname

    if user:
        target = f"{user}@{hostname}"

    command = ["ssh", "-p", str(port)]

    if key:
        command.extend(["-i", os.path.expanduser(str(key))])

    command.extend(normalize_ssh_options(host.get("options")))
    command.append(target)

    return command


def launch_host(host):
    command = build_ssh_command(host)

    if command is None:
        show_message("Host has no address.")
        return

    os.system("clear")
    print("\033[?25h\033[0m", end="", flush=True)
    print(color("logo", "PORTAL ZERO"))
    print()
    print(color("text", f"Connecting to {host.get('title', host.get('host', 'Unknown'))}..."))
    print(color("border", " ".join(command)))
    print()

    subprocess.run(command)

    print()
    input(color("text", "Connection closed. Press Enter to return to the launcher..."))
    print("\033[?25l", end="", flush=True)
    os.system("clear")


def show_message(message):
    os.system("clear")
    print("\033[?25h\033[0m", end="", flush=True)
    print(color("logo", "PORTAL ZERO"))
    print()
    print(color("text", message))
    print()
    input(color("text", "Press Enter to return..."))
    print("\033[?25l", end="", flush=True)
    os.system("clear")


def host_identity(host):
    user = host.get("user", "")
    hostname = host.get("host", "")
    port = host.get("port", 22)
    return f"{user}@{hostname}:{port}"


def load_state():
    try:
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}


def save_state_for_host(host):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as file:
            json.dump({"last_host": host_identity(host)}, file, indent=4)
    except OSError:
        pass


def initial_selected_index():
    if not hosts:
        return 0

    last_host = load_state().get("last_host")

    for index, host in enumerate(hosts):
        if host_identity(host) == last_host:
            return index

    return 0


def draw(selected_index, hidden = False):
    width, _ = shutil.get_terminal_size()
    width = max(1, min(width - 2, 100))

    table = [
        host.get('title', 'No title')
        for host in hosts
    ]

    if not table:
        table = ["No hosts found"]

    table_max = max(len(line) for line in table)

    logo = "\n".join([
        f"{' ' * max(0, width - len(line))}{color('logo', line)}"
        for line in LOGO
    ])

    table_top = color("border", f"  ╭────{'─' * table_max}───────────╮")
    table_separator = color("border", f"  ├────{'─' * table_max}───────────┤")
    table_bottom = color("border", f"  ╰────{'─' * table_max}───────────╯")

    rows = []

    for index, line in enumerate(table):
        selected = index == selected_index
        box_color = "border"
        button_color = "selected_button" if selected else "button_border"
        arrow_color = "selected_arrow" if selected else "arrow"
        text_color = "selected_box" if selected else "text"
        padding = " " * (table_max - len(line))

        rows.append("\n".join([
            f"  {color(box_color, '│')}    {' ' * table_max}     {color(button_color, '╭───╮')} {color(box_color, '│')}",
            f"  {color(box_color, '│')}  {color(text_color, line)} {padding}      {color(button_color, '│')} {color(arrow_color, '>')} {color(button_color, '│')} {color(box_color, '│')}",
            f"  {color(box_color, '│')}    {' ' * table_max}     {color(button_color, '╰───╯')} {color(box_color, '│')}",
        ]))

    table_rows = f"\n{table_separator}\n".join(rows)

    picture = (
        f"{color('window_border', '▄' * (width+2))}\n" +
        "\n".join([
            f"{THEME['window_border']}█{THEME['reset']}{line}{' ' * (width - len(ansi_regex.sub('', line)))}{THEME['window_border']}█{THEME['reset']}"
            for line in (
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
            ).split("\n")
        ]) +
        f"\n{color('window_border', '▀' * (width+2))}"
    )

    if not hidden:
        print(picture + f"\033[{picture.count(chr(10))}F", end="", flush=True)
    
    return picture


def main():
    selected_index = initial_selected_index()
    old_settings = termios.tcgetattr(sys.stdin)

    try:
        tty.setcbreak(sys.stdin.fileno())
        print("\033[?25l", end="", flush=True)

        while True:
            frame_start = time.monotonic()

            if not terminal_size_ok():
                show_terminal_size_warning()
                time.sleep(0.25)
                print("\033[?25l", end="", flush=True)
                continue

            key = read_key()

            if key == "\033[A" and hosts:
                selected_index = (selected_index - 1) % len(hosts)
            elif key == "\033[B" and hosts:
                selected_index = (selected_index + 1) % len(hosts)
            elif key in ["\n", "\r"] and hosts:
                save_state_for_host(hosts[selected_index])
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                launch_host(hosts[selected_index])
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            elif key in ["q", "\x03"]:
                break

            draw(selected_index)

            elapsed = time.monotonic() - frame_start
            time.sleep(max(0, FRAME_TIME - elapsed))
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        print("\033[?25h\033[0m", end="", flush=True)


def intro():
    wait_for_terminal_size()
    menu = draw(initial_selected_index(), True)
    
    #w, h = shutil.get_terminal_size()
    w, _ = shutil.get_terminal_size()
    w = max(1, min(w - 2, 100))
    h = len(menu.split("\n")) - 2
    menu_cells = [
        ansi_cells(line)[1:-1]
        for line in menu.split("\n")[1:-1]
    ]
    
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
        " " for _ in range(w)
        for _ in range(h)
    ])

    radius = max(round(w/2), round(h/2))
    quantity = INTRO_QUANTITY
    layers = int(max(w / 2, h) * INTRO_LAYER_FACTOR)
    pixels = [
        (
            random.choice(EFFECT_SYMBOLS),
            center_x + (radius + layer) * math.sin(math.radians(360 / quantity * i)),
            center_y + (radius + layer) * math.cos(math.radians(360 / quantity * i)),
            f"\033[38;2;{[200, 50, 50, 100][i % 4]};{[255, 100, 200, 150][i % 4]};{[200, 50, 50, 100][i % 4]}m"
        )
        for layer in range(layers)
        for i in range(quantity)
    ]
    
    swirl_strength = 0.063
    zoom = INTRO_ZOOM_START
    
    empty = True
    while zoom < 1 or not empty:
        empty = True
        new_lines = [[" " for _ in range(w)] for _ in range(h)]
        new_pixels = []
        smallest_radius = float("inf")
        
        frame_start = time.monotonic()
        swirl_strength -= 0.0002
        zoom += INTRO_ZOOM_STEP

        for char, x, y, color_code in pixels:
            dx = x - center_x
            dy = y - center_y

            radius = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)

            swirl_strength += 0
            speed = swirl_strength / max(0.001, radius / 8)

            angle += speed
            radius *= zoom
            smallest_radius = min(smallest_radius, radius)

            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius

            new_pixels.append((char, x, y, color_code))

            ix = round(x * 2)
            iy = round(y)

            if 0 <= ix < w and 0 <= iy < h:
                new_lines[iy][ix] = color_code + char + THEME["reset"]
                empty = False

        pixels = new_pixels
        
        #== Menu =============================
        
        if zoom > 1 and math.isfinite(smallest_radius):
            menu = draw(initial_selected_index(), True)
            menu_cells = [
                ansi_cells(line)[1:-1]
                for line in menu.split("\n")[1:-1]
            ]
            min_y = max(0, math.floor(center_y - smallest_radius))
            max_y = min(h, math.ceil(center_y + smallest_radius) + 1)
            min_x = max(0, math.floor((center_x - smallest_radius) * 2))
            max_x = min(w, math.ceil((center_x + smallest_radius) * 2) + 1)

            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    dx = (x / 2) - center_x
                    dy = y - center_y
                    distance = math.hypot(dx, dy)

                    if distance <= smallest_radius:
                        menu_y = y
                        menu_x = x

                        if menu_y < len(menu_cells) and menu_x < len(menu_cells[menu_y]):
                            new_lines[y][x] = menu_cells[menu_y][menu_x]
        
        #=====================================
        
        picture = (
            f"{color('window_border', '▄' * (w+2))}\n" +
            "\n".join([
                f"{THEME['window_border']}█{THEME['reset']}{''.join(line)}{THEME['window_border']}█{THEME['reset']}"
                for line in new_lines
            ]) +
            f"\n{color('window_border', '▀' * (w+2))}"
        )
        
        print(
            picture + "\033[" + str(len(picture.split('\n')) - 1) + "F",
            end="", flush=True
        )
        
        elapsed = time.monotonic() - frame_start
        time.sleep(max(0, INTRO_FRAME_TIME - elapsed))

if __name__ == "__main__":
    try:
        intro()
        main()
    except KeyboardInterrupt:
        exit()
