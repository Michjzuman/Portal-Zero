#!/usr/bin/env python3

import curses
import json
import math
import random
import subprocess
import sys
import time
from pathlib import Path


APP_NAME = "PORTAL ZERO"
TAGLINE = "Open a shell to home."
HOSTS_FILE = Path(__file__).parent / "hosts.json"


BANNER_BIG = [
    "██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗        ███████╗███████╗██████╗  ██████╗",
    "██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║        ╚══███╔╝██╔════╝██╔══██╗██╔═══██╗",
    "██████╔╝██║   ██║██████╔╝   ██║   ███████║██║          ███╔╝ █████╗  ██████╔╝██║   ██║",
    "██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║         ███╔╝  ██╔══╝  ██╔══██╗██║   ██║",
    "██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗   ███████╗███████╗██║  ██║╚██████╔╝",
    "╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝",
]

BANNER_SMALL = [
    "██████╗  ██████╗ ██████╗ ████████╗ █████╗ ██╗",
    "██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝██╔══██╗██║",
    "██████╔╝██║   ██║██████╔╝   ██║   ███████║██║",
    "██╔═══╝ ██║   ██║██╔══██╗   ██║   ██╔══██║██║",
    "██║     ╚██████╔╝██║  ██║   ██║   ██║  ██║███████╗",
    "╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝",
    "                    ZERO",
]

LOADING_STEPS = [
    "stabilizing wormhole edge",
    "igniting usb event horizon",
    "folding pocket lan space",
    "locking home tunnel vector",
    "loading host manifest",
    "arming ssh jump matrix",
    "opening portal",
]

GLYPHS = "01░▒▓█<>[]{}//$#@&*+-=╱╲╳◇◆○●◌◍◎◉"
PORTAL_CHARS = "@%#*+=-:. "
SPARK_CHARS = "·•*+xX<>/\|-=~"
RUNE_CHARS = "ᚠᚢᚦᚨᚱᚲᚷᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛟ"
FRAME_CHARS = ["╱", "─", "╲", "│"]


class Theme:
    ERROR = 1
    OK = 2
    BRAND = 3
    ACCENT = 4
    SELECTED = 5
    MUTED = 6
    PANEL = 7
    WARNING = 8
    HOT = 9
    VOID = 10


def safe_add(stdscr, y, x, text, color=0, bold=False, reverse=False):
    height, width = stdscr.getmaxyx()

    if y < 0 or y >= height or x >= width:
        return

    if x < 0:
        text = text[abs(x):]
        x = 0

    max_len = width - x - 1
    if max_len <= 0:
        return

    text = str(text)[:max_len]
    attr = curses.color_pair(color)

    if bold:
        attr |= curses.A_BOLD
    if reverse:
        attr |= curses.A_REVERSE

    try:
        stdscr.addstr(y, x, text, attr)
    except curses.error:
        pass


def center_x(stdscr, text):
    _, width = stdscr.getmaxyx()
    return max(0, (width - len(text)) // 2)


def add_center(stdscr, y, text, color=0, bold=False):
    safe_add(stdscr, y, center_x(stdscr, text), text, color, bold)


def draw_box(stdscr, y, x, h, w, color=Theme.PANEL, title=None):
    height, width = stdscr.getmaxyx()

    if h < 2 or w < 4:
        return

    if y >= height or x >= width:
        return

    right = min(width - 1, x + w - 1)
    bottom = min(height - 1, y + h - 1)
    w = right - x + 1
    h = bottom - y + 1

    if w < 4 or h < 2:
        return

    safe_add(stdscr, y, x, "╭" + "─" * (w - 2) + "╮", color)
    for row in range(1, h - 1):
        safe_add(stdscr, y + row, x, "│", color)
        safe_add(stdscr, y + row, x + w - 1, "│", color)
    safe_add(stdscr, y + h - 1, x, "╰" + "─" * (w - 2) + "╯", color)

    if title:
        safe_add(stdscr, y, x + 3, f" {title} ", Theme.ACCENT, True)


def draw_progress(stdscr, y, x, w, progress, color=Theme.OK):
    progress = max(0.0, min(1.0, progress))
    fill_w = max(0, int((w - 2) * progress))
    empty_w = max(0, (w - 2) - fill_w)
    bar = "[" + "█" * fill_w + "░" * empty_w + "]"
    safe_add(stdscr, y, x, bar, color, True)


def matrix_rain(stdscr, frames=14, delay=0.028):
    height, width = stdscr.getmaxyx()
    columns = max(1, min(width, 140))
    drops = [random.randint(-height, 0) for _ in range(columns)]

    for frame in range(frames):
        stdscr.erase()
        for x in range(columns):
            y = drops[x]
            if 0 <= y < height:
                char = random.choice(GLYPHS)
                color = Theme.OK if random.random() > 0.18 else Theme.ACCENT
                safe_add(stdscr, y, x, char, color, random.random() > 0.75)
            drops[x] += random.choice([1, 1, 1, 2])
            if drops[x] > height + random.randint(1, 8):
                drops[x] = random.randint(-8, 0)

        if frame > 4:
            add_center(stdscr, height // 2, APP_NAME, Theme.BRAND, True)
            add_center(stdscr, height // 2 + 2, "signal acquired", Theme.ACCENT, True)
        stdscr.refresh()
        time.sleep(delay)


def draw_scanlines(stdscr, frame, strength=1):
    height, width = stdscr.getmaxyx()

    for y in range(frame % 2, height, 2):
        if random.random() < 0.72:
            safe_add(stdscr, y, 0, "·" * max(1, width - 1), Theme.MUTED)

    for _ in range(strength):
        glitch_y = random.randint(0, max(0, height - 1))
        glitch_x = random.randint(0, max(0, width // 2))
        glitch_w = random.randint(6, max(7, min(36, width - glitch_x - 1)))
        safe_add(stdscr, glitch_y, glitch_x, random.choice(["═", "─", "▒", "░", "█"]) * glitch_w, random.choice([Theme.BRAND, Theme.ACCENT, Theme.HOT]))


def draw_hex_frame(stdscr, frame):
    height, width = stdscr.getmaxyx()

    if width < 60 or height < 18:
        return

    inset = 2 + int(abs(math.sin(frame * 0.08)) * 2)
    top = inset
    bottom = height - inset - 1
    left = inset * 2
    right = width - inset * 2 - 1

    for x in range(left + 3, right - 2):
        char = "═" if (x + frame) % 6 else "╪"
        safe_add(stdscr, top, x, char, Theme.PANEL, True)
        safe_add(stdscr, bottom, x, char, Theme.PANEL, True)

    for y in range(top + 2, bottom - 1):
        char = "║" if (y + frame) % 5 else "╫"
        safe_add(stdscr, y, left, char, Theme.PANEL, True)
        safe_add(stdscr, y, right, char, Theme.PANEL, True)

    corners = [
        (top, left + 2, "╭─"),
        (top, right - 3, "─╮"),
        (bottom, left + 2, "╰─"),
        (bottom, right - 3, "─╯"),
    ]
    for y, x, text in corners:
        safe_add(stdscr, y, x, text, Theme.ACCENT, True)


def draw_shockwave(stdscr, center_y, center_x, radius, color):
    height, width = stdscr.getmaxyx()

    for index in range(360):
        angle = math.radians(index)
        x = int(center_x + math.cos(angle) * radius * 1.95)
        y = int(center_y + math.sin(angle) * radius * 0.86)

        if 0 <= y < height and 0 <= x < width:
            char = FRAME_CHARS[(index // 18) % len(FRAME_CHARS)]
            safe_add(stdscr, y, x, char, color, True)


def draw_logo_hologram(stdscr, frame, y):
    height, width = stdscr.getmaxyx()
    banner = BANNER_BIG if width >= 100 else BANNER_SMALL

    for row, line in enumerate(banner):
        jitter = random.choice([-1, 0, 0, 0, 1]) if frame % 3 == 0 else 0
        color = random.choice([Theme.BRAND, Theme.ACCENT, Theme.OK]) if random.random() < 0.09 else Theme.BRAND
        corrupted = "".join(random.choice([char, char, char, "█", "▓", "▒"]) if random.random() < 0.018 else char for char in line)
        safe_add(stdscr, y + row, center_x(stdscr, line) + jitter, corrupted, color, True)


def draw_warp_streaks(stdscr, center_y, center_x, frame, density):
    height, width = stdscr.getmaxyx()

    for index in range(density):
        angle = (index * 2.399963 + frame * 0.13) % (math.pi * 2)
        length = random.randint(4, max(5, min(width, height) // 2))
        start_radius = random.randint(2, max(3, min(width, height) // 5))
        end_radius = start_radius + length

        sx = int(center_x + math.cos(angle) * start_radius * 1.9)
        sy = int(center_y + math.sin(angle) * start_radius * 0.85)
        ex = int(center_x + math.cos(angle) * end_radius * 1.9)
        ey = int(center_y + math.sin(angle) * end_radius * 0.85)

        steps = max(1, int(abs(ex - sx) + abs(ey - sy)) // 3)
        for step in range(steps):
            t = step / max(1, steps - 1)
            x = int(sx + (ex - sx) * t)
            y = int(sy + (ey - sy) * t)

            if random.random() < 0.55:
                continue

            char = random.choice(["-", "=", "~", "·", "*", "+", "|"])
            color = random.choice([Theme.BRAND, Theme.ACCENT, Theme.OK, Theme.HOT])
            safe_add(stdscr, y, x, char, color, random.random() > 0.7)


def draw_portal_vortex(stdscr, frame, intensity=1.0, title=True):
    height, width = stdscr.getmaxyx()
    center_y = height // 2
    center_x = width // 2
    radius_limit = max(6, min(width // 2 - 4, height - 5))

    draw_warp_streaks(stdscr, center_y, center_x, frame, int(22 * intensity))

    points = int(520 * intensity)
    for index in range(points):
        base_angle = index * 0.19
        swirl = frame * 0.24
        radius = (index / points) * radius_limit
        wave = math.sin(index * 0.07 + frame * 0.33) * 2.2
        angle = base_angle + swirl + radius * 0.27

        x = int(center_x + math.cos(angle) * (radius + wave) * 1.85)
        y = int(center_y + math.sin(angle) * (radius + wave) * 0.82)

        distance_ratio = radius / max(1, radius_limit)
        char_index = min(len(PORTAL_CHARS) - 1, int(distance_ratio * (len(PORTAL_CHARS) - 1)))
        char = PORTAL_CHARS[char_index]

        if distance_ratio < 0.17:
            char = random.choice([" ", "·", "○"])
            color = Theme.VOID
        elif distance_ratio < 0.38:
            char = random.choice(["◌", "○", "◍", "◎"])
            color = Theme.BRAND
        elif distance_ratio < 0.72:
            char = random.choice(["*", "+", "x", "X", "#", "%"])
            color = random.choice([Theme.ACCENT, Theme.BRAND, Theme.OK])
        else:
            char = random.choice(["@", "#", "█", "▓", "▒"])
            color = random.choice([Theme.HOT, Theme.ACCENT, Theme.BRAND])

        safe_add(stdscr, y, x, char, color, True)

    ring_radius = int(radius_limit * (0.64 + math.sin(frame * 0.18) * 0.04))
    for index in range(260):
        angle = (index / 260) * math.pi * 2 + frame * 0.12
        wobble = math.sin(index * 0.2 + frame * 0.5) * 1.5
        x = int(center_x + math.cos(angle) * (ring_radius + wobble) * 1.85)
        y = int(center_y + math.sin(angle) * (ring_radius + wobble) * 0.82)
        char = random.choice(["█", "▓", "▒", "#", "@", "*"])
        color = random.choice([Theme.HOT, Theme.ACCENT, Theme.BRAND])
        safe_add(stdscr, y, x, char, color, True)

    core = [
        "       .-''''-.       ",
        "    .-'  .--.  '-.    ",
        "  .'   .'    '.   '.  ",
        " /    /  HOME  \\    \\ ",
        "|     | PORTAL |     |",
        " \\    \\  ZERO  /    / ",
        "  '.   '.____.'   .'  ",
        "    '-.        .-'    ",
        "       '-....-'       ",
    ]

    core_y = center_y - len(core) // 2
    for offset, line in enumerate(core):
        flicker_line = "".join(random.choice([char, char, "#", "█", " "]) if random.random() < 0.025 else char for char in line)
        add_center(stdscr, core_y + offset, flicker_line, Theme.SELECTED if offset in (3, 4, 5) else Theme.BRAND, True)

    if title:
        glitch = random.choice(["", "_", "//", "<>", "█", "::"])
        add_center(stdscr, max(1, center_y - radius_limit // 2 - 3), f"{glitch} WORMHOLE BOOTSTRAP {glitch}", Theme.ACCENT, True)
        add_center(stdscr, min(height - 3, center_y + radius_limit // 2 + 3), "stand clear · local reality folding · skibidi gateway online", Theme.MUTED, False)


def portal_opening_sequence(stdscr):
    curses.curs_set(0)
    height, width = stdscr.getmaxyx()

    if width < 50 or height < 16:
        matrix_rain(stdscr, frames=10, delay=0.025)
        return

    center_y = height // 2
    center_x = width // 2

    # Phase 1: cold boot noise
    for frame in range(18):
        stdscr.erase()
        draw_scanlines(stdscr, frame, strength=2)
        draw_hex_frame(stdscr, frame)

        for _ in range(90):
            safe_add(
                stdscr,
                random.randint(1, max(1, height - 2)),
                random.randint(0, max(0, width - 2)),
                random.choice(GLYPHS + RUNE_CHARS),
                random.choice([Theme.MUTED, Theme.BRAND, Theme.ACCENT]),
                random.random() > 0.82,
            )

        add_center(stdscr, center_y - 1, "PORTAL ZERO", Theme.BRAND, True)
        add_center(stdscr, center_y + 1, "cold boot // reality interface", Theme.ACCENT, True)
        stdscr.refresh()
        time.sleep(0.026)

    # Phase 2: singularity forming
    for frame in range(52):
        stdscr.erase()
        draw_scanlines(stdscr, frame, strength=1)
        draw_hex_frame(stdscr, frame)
        draw_portal_vortex(stdscr, frame, intensity=0.42 + frame / 52 * 0.72)

        ring_radius = 2 + frame * 0.38
        if frame % 5 == 0:
            draw_shockwave(stdscr, center_y, center_x, ring_radius, random.choice([Theme.ACCENT, Theme.BRAND, Theme.HOT]))

        box_w = min(width - 8, 82)
        box_x = max(2, (width - box_w) // 2)
        box_y = min(height - 6, max(2, height - 7))
        draw_box(stdscr, box_y, box_x, 4, box_w, Theme.PANEL, "WORMHOLE SPIN-UP")
        safe_add(stdscr, box_y + 1, box_x + 3, "> vortex angular velocity rising", Theme.ACCENT, True)
        draw_progress(stdscr, box_y + 2, box_x + 3, box_w - 6, frame / 51, Theme.OK)

        stdscr.refresh()
        time.sleep(0.024)

    # Phase 3: aggressive vortex + rune ring
    for frame in range(54):
        stdscr.erase()
        draw_portal_vortex(stdscr, frame + 80, intensity=1.28, title=False)
        draw_scanlines(stdscr, frame, strength=3 if frame % 7 == 0 else 1)

        radius = min(width // 2 - 6, height - 6) * 0.72
        for index, rune in enumerate((RUNE_CHARS * 8)[:96]):
            angle = (index / 96) * math.pi * 2 - frame * 0.11
            x = int(center_x + math.cos(angle) * radius * 1.9)
            y = int(center_y + math.sin(angle) * radius * 0.84)
            safe_add(stdscr, y, x, rune, random.choice([Theme.ACCENT, Theme.BRAND, Theme.HOT]), True)

        add_center(stdscr, max(1, center_y - 10), "<<< HOME VECTOR LOCK >>>", Theme.HOT if frame % 2 else Theme.ACCENT, True)
        add_center(stdscr, min(height - 3, center_y + 10), "usb event horizon stable · ssh singularity armed", Theme.OK, True)

        stdscr.refresh()
        time.sleep(0.022)

    # Phase 4: white-out blast / portal opens
    for radius in range(1, min(width // 2, height) + 8, 2):
        stdscr.erase()
        draw_shockwave(stdscr, center_y, center_x, radius, random.choice([Theme.HOT, Theme.ACCENT, Theme.BRAND]))
        draw_shockwave(stdscr, center_y, center_x, max(1, radius - 5), Theme.OK)
        add_center(stdscr, center_y, "PORTAL OPEN", random.choice([Theme.HOT, Theme.ACCENT, Theme.BRAND]), True)
        stdscr.refresh()
        time.sleep(0.011)

    for flash in range(7):
        stdscr.erase()
        if flash % 2 == 0:
            for y in range(height):
                safe_add(stdscr, y, 0, "█" * max(1, width - 1), Theme.SELECTED, True)
            add_center(stdscr, height // 2, "PORTAL OPEN", Theme.SELECTED, True)
        else:
            draw_logo_hologram(stdscr, flash, max(1, height // 2 - 5))
            add_center(stdscr, min(height - 2, height // 2 + 5), "home access terminal online", Theme.OK, True)
        stdscr.refresh()
        time.sleep(0.055)


def boot_sequence(stdscr):
    curses.curs_set(0)
    portal_opening_sequence(stdscr)
    matrix_rain(stdscr, frames=8, delay=0.022)

    height, width = stdscr.getmaxyx()
    stdscr.erase()

    banner = BANNER_BIG if width >= 100 else BANNER_SMALL
    start_y = max(1, height // 2 - len(banner) // 2 - 4)

    for i, line in enumerate(banner):
        visible = ""
        for char in line:
            visible += char
            if random.random() < 0.032:
                stdscr.erase()
                for old_i in range(i):
                    add_center(stdscr, start_y + old_i, banner[old_i], Theme.BRAND, True)
                add_center(stdscr, start_y + i, visible + random.choice("█▓▒░@#"), random.choice([Theme.ACCENT, Theme.HOT, Theme.BRAND]), True)
                stdscr.refresh()
                time.sleep(0.003)
        add_center(stdscr, start_y + i, line, Theme.BRAND, True)
        stdscr.refresh()
        time.sleep(0.028)

    add_center(stdscr, start_y + len(banner) + 1, TAGLINE, Theme.ACCENT, True)
    add_center(stdscr, start_y + len(banner) + 2, "SSH · WireGuard · Pocket LAN · Wormhole UX", Theme.MUTED, False)

    box_w = min(width - 6, 76)
    box_x = max(1, (width - box_w) // 2)
    box_y = start_y + len(banner) + 5
    draw_box(stdscr, box_y, box_x, 6, box_w, Theme.PANEL, "BOOT")

    for index, step in enumerate(LOADING_STEPS):
        progress = (index + 1) / len(LOADING_STEPS)
        safe_add(stdscr, box_y + 2, box_x + 3, " " * (box_w - 6), 0)
        safe_add(stdscr, box_y + 2, box_x + 3, f"> {step}...", random.choice([Theme.ACCENT, Theme.BRAND, Theme.HOT]), True)
        draw_progress(stdscr, box_y + 4, box_x + 3, box_w - 6, progress, Theme.OK if progress < 0.85 else Theme.HOT)
        stdscr.refresh()
        time.sleep(0.13)

    safe_add(stdscr, box_y + 2, box_x + 3, "PORTAL READY · HOME VECTOR LOCKED", Theme.OK, True)
    stdscr.refresh()
    time.sleep(0.35)


def load_hosts():
    if not HOSTS_FILE.exists():
        return [], f"hosts.json fehlt: {HOSTS_FILE}"

    try:
        with HOSTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        return [], f"hosts.json ist kaputt: {error}"

    if not isinstance(data, list):
        return [], "hosts.json muss ein Array sein."

    hosts = []

    for item in data:
        if not isinstance(item, dict):
            continue

        host = str(item.get("host", "")).strip()
        title = str(item.get("title", host)).strip()
        emoji = str(item.get("emoji", "🖥️")).strip()

        try:
            port = int(item.get("port", 22))
        except (TypeError, ValueError):
            port = 22

        user = item.get("user")
        if user is not None:
            user = str(user).strip()

        note = item.get("note")
        if note is not None:
            note = str(note).strip()

        group = item.get("group")
        if group is not None:
            group = str(group).strip()

        if not host:
            continue

        hosts.append({
            "host": host,
            "port": port,
            "title": title or host,
            "emoji": emoji or "🖥️",
            "user": user,
            "note": note or "",
            "group": group or "HOME",
        })

    return hosts, ""


def ssh_target(host):
    if host.get("user"):
        return f"{host['user']}@{host['host']}"
    return host["host"]


def launch_ssh(host):
    command = [
        "ssh",
        "-p",
        str(host["port"]),
        ssh_target(host),
    ]
    subprocess.run(command)


def filter_hosts(hosts, query):
    query = query.strip().lower()
    if not query:
        return hosts

    result = []
    for host in hosts:
        haystack = " ".join([
            host["title"],
            host["host"],
            str(host["port"]),
            host.get("user") or "",
            host["emoji"],
            host.get("group") or "",
            host.get("note") or "",
        ]).lower()

        if query in haystack:
            result.append(host)

    return result


def draw_top_bar(stdscr, query, total_hosts, visible_hosts, message):
    height, width = stdscr.getmaxyx()
    now = time.strftime("%H:%M:%S")
    left = f" {APP_NAME} "
    middle = f" Hosts {visible_hosts}/{total_hosts} "
    search = f" Search: {query or '-'} "
    right = f" {now} "

    safe_add(stdscr, 0, 0, " " * (width - 1), Theme.SELECTED, True)
    safe_add(stdscr, 0, 1, left, Theme.SELECTED, True)
    safe_add(stdscr, 0, max(1, width // 2 - len(middle) // 2), middle, Theme.SELECTED, True)
    safe_add(stdscr, 0, max(1, width - len(right) - 2), right, Theme.SELECTED, True)

    if height > 2:
        safe_add(stdscr, 1, 2, search, Theme.ACCENT, True)
        if message:
            safe_add(stdscr, 1, 25, message, Theme.WARNING, True)


def draw_brand_header(stdscr):
    height, width = stdscr.getmaxyx()

    if height < 18:
        add_center(stdscr, 2, f"{APP_NAME} · {TAGLINE}", Theme.BRAND, True)
        return 4

    banner = BANNER_BIG if width >= 100 else BANNER_SMALL
    y = 3
    for line in banner:
        add_center(stdscr, y, line, Theme.BRAND, True)
        y += 1

    add_center(stdscr, y + 1, TAGLINE, Theme.ACCENT, True)
    add_center(stdscr, y + 2, "portable home access terminal", Theme.MUTED, False)
    return y + 4


def draw_status_panel(stdscr, y, x, w):
    draw_box(stdscr, y, x, 7, w, Theme.PANEL, "STATUS")

    pulse = int(time.time() * 2) % 2
    vpn_dot = "●" if pulse else "◉"

    safe_add(stdscr, y + 2, x + 3, "USB", Theme.MUTED, True)
    safe_add(stdscr, y + 2, x + 13, "● connected", Theme.OK, True)

    safe_add(stdscr, y + 3, x + 3, "VPN", Theme.MUTED, True)
    safe_add(stdscr, y + 3, x + 13, f"{vpn_dot} tunnel armed", Theme.OK, True)

    safe_add(stdscr, y + 4, x + 3, "HOME", Theme.MUTED, True)
    safe_add(stdscr, y + 4, x + 13, "◆ reachable", Theme.ACCENT, True)

    safe_add(stdscr, y + 5, x + 3, "MODE", Theme.MUTED, True)
    safe_add(stdscr, y + 5, x + 13, "launcher", Theme.BRAND, True)


def draw_host_card(stdscr, y, x, w, host, selected=False):
    color = Theme.SELECTED if selected else Theme.PANEL
    title_color = Theme.SELECTED if selected else Theme.ACCENT
    text_color = Theme.SELECTED if selected else 0
    muted_color = Theme.SELECTED if selected else Theme.MUTED

    if selected:
        for row in range(4):
            safe_add(stdscr, y + row, x, " " * w, Theme.SELECTED, True)

    icon = host["emoji"]
    title = host["title"]
    target = f"{ssh_target(host)}:{host['port']}"
    group = host.get("group") or "HOME"
    note = host.get("note") or ""

    safe_add(stdscr, y, x, "╭" + "─" * (w - 2) + "╮", color)
    safe_add(stdscr, y + 1, x, "│", color)
    safe_add(stdscr, y + 1, x + w - 1, "│", color)
    safe_add(stdscr, y + 2, x, "│", color)
    safe_add(stdscr, y + 2, x + w - 1, "│", color)
    safe_add(stdscr, y + 3, x, "╰" + "─" * (w - 2) + "╯", color)

    safe_add(stdscr, y + 1, x + 3, icon, title_color, True)
    safe_add(stdscr, y + 1, x + 7, title, title_color, True)
    safe_add(stdscr, y + 1, x + w - min(18, w // 3), f"[{group}]", muted_color, True)
    safe_add(stdscr, y + 2, x + 7, target, text_color, False)

    if note:
        safe_add(stdscr, y + 2, x + min(w - 24, 38), f"// {note}", muted_color, False)


def draw_hosts_panel(stdscr, hosts, selected_index, y, x, h, w):
    draw_box(stdscr, y, x, h, w, Theme.PANEL, "HOSTS")

    if not hosts:
        add_center(stdscr, y + h // 2 - 1, "Keine Hosts gefunden.", Theme.ERROR, True)
        add_center(stdscr, y + h // 2 + 1, "Drücke r zum Reload oder prüfe hosts.json.", Theme.MUTED, False)
        return

    card_h = 4
    gap = 1
    rows = max(1, (h - 3) // (card_h + gap))

    start = 0
    if selected_index >= rows:
        start = selected_index - rows + 1

    end = min(len(hosts), start + rows)
    card_w = w - 6
    card_x = x + 3
    current_y = y + 2

    for index in range(start, end):
        draw_host_card(stdscr, current_y, card_x, card_w, hosts[index], index == selected_index)
        current_y += card_h + gap

    if len(hosts) > rows:
        scroll_progress = selected_index / max(1, len(hosts) - 1)
        scroll_h = h - 4
        scroll_y = y + 2 + int(scroll_progress * max(0, scroll_h - 1))
        for row in range(scroll_h):
            safe_add(stdscr, y + 2 + row, x + w - 3, "│", Theme.MUTED)
        safe_add(stdscr, scroll_y, x + w - 3, "█", Theme.ACCENT, True)


def draw_footer(stdscr):
    height, width = stdscr.getmaxyx()
    help_text = " ↑/↓ or j/k select  ·  Enter connect  ·  / search  ·  r reload  ·  b portal anim  ·  q quit "
    safe_add(stdscr, height - 1, 0, " " * (width - 1), Theme.SELECTED, True)
    safe_add(stdscr, height - 1, max(0, (width - len(help_text)) // 2), help_text, Theme.SELECTED, True)


def draw_background_noise(stdscr):
    height, width = stdscr.getmaxyx()
    if width < 60 or height < 18:
        return

    random.seed(int(time.time() * 2))
    for _ in range(max(8, width // 10)):
        y = random.randint(2, max(2, height - 3))
        x = random.randint(0, max(0, width - 2))
        safe_add(stdscr, y, x, random.choice(["·", "'", "`", "."]), Theme.MUTED)

    # subtle idle mini-vortex in the empty background
    center_y = height - 7
    center_x = width - 18
    for index in range(80):
        angle = index * 0.38 + time.time() * 1.7
        radius = (index / 80) * 8
        x = int(center_x + math.cos(angle) * radius * 1.8)
        y = int(center_y + math.sin(angle) * radius * 0.78)
        char = random.choice(["·", "*", "+", "○", "◌"])
        safe_add(stdscr, y, x, char, random.choice([Theme.MUTED, Theme.BRAND, Theme.ACCENT]), random.random() > 0.82)


def draw_launcher(stdscr, all_hosts, hosts, selected_index, query, message):
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    draw_background_noise(stdscr)
    draw_top_bar(stdscr, query, len(all_hosts), len(hosts), message)
    header_end = draw_brand_header(stdscr)

    if height < 16 or width < 50:
        add_center(stdscr, height // 2, "Terminal zu klein für Portal Zero.", Theme.ERROR, True)
        stdscr.refresh()
        return

    main_y = header_end
    main_h = height - main_y - 2
    panel_gap = 2

    if width >= 100 and main_h >= 12:
        side_w = 31
        hosts_w = width - side_w - panel_gap - 4
        hosts_x = 2
        side_x = hosts_x + hosts_w + panel_gap
        draw_hosts_panel(stdscr, hosts, selected_index, main_y, hosts_x, main_h, hosts_w)
        draw_status_panel(stdscr, main_y, side_x, side_w)

        draw_box(stdscr, main_y + 8, side_x, min(8, main_h - 8), side_w, Theme.PANEL, "DEVICE")
        safe_add(stdscr, main_y + 10, side_x + 3, "codename", Theme.MUTED, True)
        safe_add(stdscr, main_y + 10, side_x + 14, "portal-zero", Theme.BRAND, True)
        safe_add(stdscr, main_y + 11, side_x + 3, "profile", Theme.MUTED, True)
        safe_add(stdscr, main_y + 11, side_x + 14, "pocket-bastion", Theme.ACCENT, True)
        safe_add(stdscr, main_y + 12, side_x + 3, "theme", Theme.MUTED, True)
        safe_add(stdscr, main_y + 12, side_x + 14, "wormhole cyan", Theme.OK, True)
    else:
        draw_hosts_panel(stdscr, hosts, selected_index, main_y, 2, main_h, width - 4)

    draw_footer(stdscr)
    stdscr.refresh()


def search_mode(stdscr, current_query):
    curses.curs_set(1)
    query = current_query

    while True:
        height, width = stdscr.getmaxyx()
        prompt = f"Search hosts > {query}"
        safe_add(stdscr, height - 2, 0, " " * (width - 1), Theme.PANEL)
        safe_add(stdscr, height - 2, 2, prompt, Theme.ACCENT, True)
        stdscr.move(height - 2, min(width - 2, 17 + len(query)))
        stdscr.refresh()

        key = stdscr.getch()

        if key in (10, 13):
            curses.curs_set(0)
            return query

        if key == 27:
            curses.curs_set(0)
            return current_query

        if key in (curses.KEY_BACKSPACE, 127, 8):
            query = query[:-1]
            continue

        if key == 21:
            query = ""
            continue

        if 32 <= key <= 126:
            query += chr(key)


def connection_screen(stdscr, host):
    height, width = stdscr.getmaxyx()

    if width >= 50 and height >= 16:
        for frame in range(44):
            stdscr.erase()
            draw_portal_vortex(stdscr, frame + 140, intensity=0.98, title=False)
            draw_scanlines(stdscr, frame, strength=1)

            if frame % 6 == 0:
                draw_shockwave(stdscr, height // 2, width // 2, 3 + frame * 0.6, Theme.HOT)

            add_center(stdscr, max(1, height // 2 - 8), "TARGET VECTOR LOCKED", Theme.ACCENT if frame % 2 else Theme.HOT, True)
            add_center(stdscr, height // 2 + 5, f"{host['emoji']}  {host['title']}", Theme.HOT, True)
            add_center(stdscr, height // 2 + 6, f"ssh -p {host['port']} {ssh_target(host)}", Theme.MUTED, False)

            if frame > 24:
                add_center(stdscr, height // 2 + 8, "jump sequence armed", Theme.OK, True)

            stdscr.refresh()
            time.sleep(0.022)

    stdscr.erase()
    box_w = min(width - 4, 72)
    box_h = 11
    box_x = max(1, (width - box_w) // 2)
    box_y = max(1, (height - box_h) // 2)

    draw_box(stdscr, box_y, box_x, box_h, box_w, Theme.PANEL, "CONNECT")
    add_center(stdscr, box_y + 2, APP_NAME, Theme.BRAND, True)
    add_center(stdscr, box_y + 4, f"{host['emoji']}  {host['title']}", Theme.ACCENT, True)
    add_center(stdscr, box_y + 5, f"ssh -p {host['port']} {ssh_target(host)}", Theme.MUTED, False)

    for i in range(20):
        progress = (i + 1) / 20
        draw_progress(stdscr, box_y + 8, box_x + 5, box_w - 10, progress, Theme.OK if progress < 0.75 else Theme.HOT)
        safe_add(stdscr, box_y + 7, box_x + 5, "opening encrypted shell" + "." * ((i % 3) + 1), Theme.ACCENT, True)
        if i % 4 == 0:
            safe_add(stdscr, box_y + 1, box_x + random.randint(4, max(5, box_w - 10)), random.choice(SPARK_CHARS), Theme.HOT, True)
        stdscr.refresh()
        time.sleep(0.032)


def init_colors():
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(Theme.ERROR, curses.COLOR_RED, -1)
    curses.init_pair(Theme.OK, curses.COLOR_GREEN, -1)
    curses.init_pair(Theme.BRAND, curses.COLOR_CYAN, -1)
    curses.init_pair(Theme.ACCENT, curses.COLOR_YELLOW, -1)
    curses.init_pair(Theme.SELECTED, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(Theme.MUTED, curses.COLOR_BLUE, -1)
    curses.init_pair(Theme.PANEL, curses.COLOR_MAGENTA, -1)
    curses.init_pair(Theme.WARNING, curses.COLOR_YELLOW, -1)
    curses.init_pair(Theme.HOT, curses.COLOR_RED, -1)
    curses.init_pair(Theme.VOID, curses.COLOR_BLACK, -1)


def main(stdscr):
    init_colors()
    stdscr.keypad(True)
    stdscr.timeout(250)
    curses.curs_set(0)

    boot_sequence(stdscr)

    all_hosts, load_message = load_hosts()
    query = ""
    selected_index = 0
    message = load_message

    while True:
        hosts = filter_hosts(all_hosts, query)

        if selected_index >= len(hosts):
            selected_index = max(0, len(hosts) - 1)

        draw_launcher(stdscr, all_hosts, hosts, selected_index, query, message)
        key = stdscr.getch()
        message = ""

        if key == -1:
            continue

        if key in (ord("q"), ord("Q")):
            break

        if key in (curses.KEY_UP, ord("k"), ord("K")):
            selected_index = max(0, selected_index - 1)

        elif key in (curses.KEY_DOWN, ord("j"), ord("J")):
            selected_index = min(max(0, len(hosts) - 1), selected_index + 1)

        elif key in (ord("r"), ord("R")):
            all_hosts, load_message = load_hosts()
            message = load_message or "hosts.json reloaded"
            selected_index = 0

        elif key in (ord("b"), ord("B")):
            boot_sequence(stdscr)

        elif key == ord("/"):
            query = search_mode(stdscr, query)
            selected_index = 0

        elif key in (10, 13):
            if not hosts:
                message = "no host selected"
                continue

            selected_host = hosts[selected_index]
            connection_screen(stdscr, selected_host)
            curses.endwin()

            print()
            print("╭────────────────────────────────────────╮")
            print("│              PORTAL ZERO               │")
            print("╰────────────────────────────────────────╯")
            print()
            print(f"Target: {selected_host['emoji']} {selected_host['title']}")
            print(f"Command: ssh -p {selected_host['port']} {ssh_target(selected_host)}")
            print()

            launch_ssh(selected_host)

            print()
            input("Enter drücken, um zum Portal zurückzukehren...")
            stdscr.clear()
            curses.curs_set(0)


def run():
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print()
        sys.exit(0)


if __name__ == "__main__":
    run()
