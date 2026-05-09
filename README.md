# portal-zero

A clean terminal SSH launcher with an animated portal intro.

## Usage

```bash
python3 launcher.py
```

## Configuration

Hosts are configured in `hosts.json`. If the file is missing, portal-zero creates a small example file automatically.

```json
[
  {
    "title": "Raspberry Pi",
    "host": "192.168.1.10",
    "user": "pi",
    "port": 22,
    "key": "~/.ssh/id_ed25519",
    "options": ["-A"]
  }
]
```

Fields:

- `title`: name shown in the launcher
- `host`: hostname or IP address
- `user`: optional SSH user
- `port`: optional SSH port, defaults to `22`
- `key`: optional SSH identity file, passed as `-i`
- `identity_file`: alias for `key`
- `options`: optional extra SSH arguments as list or string

## Controls

- `↑` / `↓`: select host
- `Enter`: connect via SSH
- `q`: quit

## Notes

- The last connected host is remembered in `~/.portal-zero/state.json` and preselected on the next start.
- If the terminal is too small, portal-zero shows the required size and waits until the terminal is resized.

## Requirements

- Python 3
- `ssh` available in your terminal
