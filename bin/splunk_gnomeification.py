#!/usr/bin/env python3
import sys
import json
import os
import gzip
import csv
import subprocess


def send_notification(title, message, urgency='normal', icon='dialog-information'):
    """
    Send notification to Gnome desktop using gdbus

    Args:
        title: Notification title
        message: Notification message
        urgency: low, normal, or critical
        icon: Icon name from theme
    """
    try:
        # Map urgency levels
        urgency_map = {
            'low': 0,
            'normal': 1,
            'critical': 2
        }
        urgency_level = urgency_map.get(urgency, 1)

        # Escape strings for D-Bus
        title_escaped = title.replace('"', '\\"').replace("'", "\\'")
        message_escaped = message.replace('"', '\\"').replace("'", "\\'")
        icon_escaped = icon.replace('"', '\\"').replace("'", "\\'")

        # Use gdbus to call the notification service
        cmd = [
            'gdbus', 'call',
            '--session',
            '--dest', 'org.freedesktop.Notifications',
            '--object-path', '/org/freedesktop/Notifications',
            '--method', 'org.freedesktop.Notifications.Notify',
            'Splunk',  # app_name
            '0',  # replaces_id
            icon_escaped,
            title_escaped,
            message_escaped,
            '[]',  # actions
            f'{{"urgency": <byte {urgency_level}>}}',  # hints
            '-1'  # timeout
        ]

        # Get environment
        env = os.environ.copy()

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return True

    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"gdbus error: {e}\n")
        sys.stderr.write(f"stderr: {e.stderr}\n")
        return False
    except FileNotFoundError:
        sys.stderr.write("gdbus command not found. Please ensure glib2 tools are installed.\n")
        return False
    except Exception as e:
        sys.stderr.write(f"Error sending notification: {e}\n")
        return False


def main():
    """Main alert action handler"""
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        # Read configuration from stdin
        payload = json.loads(sys.stdin.read())

        # Get configuration parameters
        config = payload.get('configuration', {})
        title = config.get('title', 'Splunk Alert')
        message = config.get('message', 'Alert triggered')
        urgency = config.get('urgency', 'normal')
        icon = config.get('icon', 'dialog-information')

        # Get search results if available
        results_file = payload.get('results_file')
        if results_file and os.path.exists(results_file):
            try:
                # Read first result to include in notification
                with gzip.open(results_file, 'rt') as f:
                    reader = csv.DictReader(f)
                    first_row = next(reader, None)
                    if first_row:
                        # Add result count or first result details to message
                        message += f"\n\nFirst result: {str(first_row)[:100]}"
            except Exception as e:
                sys.stderr.write(f"Error reading results: {e}\n")

        # Send the notification
        success = send_notification(title, message, urgency, icon)

        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.stderr.write("This script should be called by Splunk as an alert action\n")
        sys.exit(1)


if __name__ == "__main__":
    main()