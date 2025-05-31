import os
from pathlib import Path
import string
import sys 

def handle_os_error(e):
    """
    Error handler for os.walk to suppress permission errors.
    """
    if isinstance(e, PermissionError):
        print(f"Permission denied: {e.filename}") 
        pass # Silently ignore permission errors
    else:
        print(f"Error accessing: {e.filename} - {e.strerror}")

def find_virtualenvs(search_paths, venv_names=['.venv', 'venv']):
    found_envs = []
    for search_path in search_paths:
        if not Path(search_path).exists():
            print(f"Skipping non-existent path: {search_path}")
            continue

        print(f"Searching in: {search_path}")
        # Use onerror to handle permission denied errors gracefully
        for root, dirs, files in os.walk(search_path, onerror=handle_os_error):
            for d in dirs:
                if d in venv_names:
                    venv_path = Path(root) / d
                    # Check for typical venv markers
                    # This helps confirm it's truly a venv and not just a folder with a similar name
                    if (venv_path / 'Scripts' / 'python.exe').exists():
                        found_envs.append(venv_path)
            # Prevent os.walk from descending into found venvs to avoid redundant checks
            # and potential issues within them 
            dirs[:] = [d for d in dirs if d not in venv_names]
    return found_envs

if __name__ == "__main__":
    system_drives = []
    # Identify available drives on Windows
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if Path(drive).exists():
            system_drives.append(drive)

    if not system_drives:
        print("No drives found to search. This script is intended for Windows.")
        sys.exit(1)

    print(f"Identified drives for search: {', '.join(system_drives)}")
    print("This might take a significant amount of time and could generate 'Permission denied' messages (which will be suppressed).")
    print("Please be patient...\n")

    all_found_envs = find_virtualenvs(system_drives)

    if all_found_envs:
        print("\n--- Found Virtual Environments ---")
        for env_path in all_found_envs:
            print(env_path)
    else:
        print("\nNo virtual environments found on the system.")