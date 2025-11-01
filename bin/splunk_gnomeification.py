#!/usr/bin/env python3
import glob
import os
import subprocess
import sys
import json

def get_dbus_address():
    """Try to find the active user's DBus session bus."""
    user_id = os.getuid()
    bus_path = f"/run/user/{user_id}/bus"
    if os.path.exists(bus_path):
        return f"unix:path={bus_path}"

    # Fallback: try to auto-detect via environment files
    runtime_dirs = glob.glob(f"/run/user/{user_id}/**/bus", recursive=True)
    if runtime_dirs:
        return f"unix:path={runtime_dirs[0]}"

    return None

def main():
    # Splunk passes parameters as JSON to stdin
    payload = sys.stdin.read()
    if not payload:
        return

    try:
        data = json.loads(payload)
        title = data.get('result', {}).get('title', 'Splunk Alert')
        message = data.get('result', {}).get('message', 'New alert triggered')
    except Exception as e:
        subprocess.run(["notify-send", "Splunk Alert Error", f"Error parsing payload: {e}"])
        return

    # Set DBus address for GNOME session
    dbus_address = get_dbus_address()
    if dbus_address:
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = dbus_address

    # Run GNOME notification
    subprocess.run([
        "notify-send",
        "--icon=dialog-information",
        title,
        message
    ])

if __name__ == "__main__":
    main()
