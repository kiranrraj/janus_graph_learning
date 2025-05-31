# -*- coding: utf-8 -*-
# D:\JanusGraph\learning\setup\setup_janusgraph_env.py

import subprocess
import venv
from pathlib import Path
import sys
import argparse
import shutil # Import shutil for rmtree

# --- Configuration ---
# Define the root directory for your JanusGraph learning project.
# This is where the virtual environment (.venv) will be created.
base_dir = Path(__file__).resolve().parent.parent

# Define the path for the virtual environment within the base directory.
venv_dir = base_dir / ".venv"

# Define the Python executable and pip executable paths within the virtual environment.
# These paths are specific to Windows (Scripts\python.exe, Scripts\pip.exe).
python_exe = venv_dir / "Scripts" / "python.exe"
pip_exe = venv_dir / "Scripts" / "pip.exe"

# Define the path to your requirements.txt file.
requirements_file = Path(__file__).resolve().parent / "requirements.txt"


# --- Argument Parsing ---
parser = argparse.ArgumentParser(
    description="Sets up the Python virtual environment for the JanusGraph learning project. "
                "By default, it checks for an existing environment and updates dependencies. "
                "Use options for specific actions."
)
parser.add_argument(
    "--force", "-f",
    action="store_true",
    help="Force deletion and recreation of the virtual environment if it exists. "
         "This will reinstall all dependencies from scratch."
)
parser.add_argument(
    "--activate", "-a",
    action="store_true",
    help="Activates the virtual environment after successful setup. "
         "This option is handled by the calling batch script."
)
args = parser.parse_args()


# --- Create Base Directory if it doesn't exist ---
print(f"Ensuring base directory exists at: {base_dir}")
base_dir.mkdir(parents=True, exist_ok=True)

# --- Virtual Environment Management ---
venv_exists = venv_dir.exists() and (venv_dir / "Scripts" / "python.exe").exists()
venv_created_this_run = False

if args.force:
    if venv_exists:
        print(f"\n--- Force option detected: Deleting existing virtual environment at: {venv_dir} ---")
        try:
            shutil.rmtree(venv_dir) # Use shutil.rmtree to remove the directory
            print("Existing virtual environment deleted.")
        except Exception as e:
            print(f"WARNING: Could not delete existing virtual environment: {e}")
            print("Attempting to proceed, but manual cleanup might be needed.")
    print(f"Creating new virtual environment at: {venv_dir}")
    try:
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)
        print("New virtual environment created successfully.")
        venv_created_this_run = True
    except Exception as e:
        print(f"ERROR: Failed to create new virtual environment: {e}")
        sys.exit(1)
elif venv_exists:
    print(f"\n--- Virtual environment already exists at: {venv_dir} ---")
    print("Skipping virtual environment creation.")
    print("Dependencies will be checked and updated within the existing environment.")
else:
    print(f"\n--- Creating virtual environment at: {venv_dir} ---")
    try:
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_dir)
        print("Virtual environment created successfully.")
        venv_created_this_run = True
    except Exception as e:
        print(f"ERROR: Failed to create virtual environment: {e}")
        sys.exit(1)


# --- Upgrade pip and Install Dependencies from requirements.txt ---
# This section runs regardless of whether the venv was newly created or already existed.
print("\n--- Installing/Upgrading dependencies ---")
try:
    # Ensure pip is up-to-date in the (new or existing) virtual environment.
    print("Upgrading pip...")
    result_pip_upgrade = subprocess.run(
        [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
        check=True, capture_output=True, text=True
    )
    print(result_pip_upgrade.stdout)
    if result_pip_upgrade.stderr:
        print(f"Pip upgrade warnings/errors:\n{result_pip_upgrade.stderr}")
    print("pip upgraded.")

    # Install all dependencies listed in requirements.txt.
    print(f"\nInstalling dependencies from {requirements_file}...")
    print("This may take a while as many packages are being installed/checked...")
    result_install_deps = subprocess.run(
        [str(pip_exe), "install", "-r", str(requirements_file)],
        check=True,
        capture_output=True,
        text=True
    )

    # Print the entire output from pip's installation process
    print(result_install_deps.stdout)
    if result_install_deps.stderr:
        print(f"Installation warnings/errors:\n{result_install_deps.stderr}")

    print("\nAll dependencies from requirements.txt installed successfully.")

except subprocess.CalledProcessError as e:
    print(f"\nERROR during package installation:")
    print(f"Command: {' '.join(e.cmd)}")
    print(f"Return Code: {e.returncode}")
    print(f"Stdout (partial):\n{e.stdout}")
    print(f"Stderr:\n{e.stderr}")
    sys.exit(1)
except Exception as e:
    print(f"\nAn unexpected error occurred during dependency installation: {e}")
    sys.exit(1)

# --- Final Message ---
print("\n--- JanusGraph Python environment setup complete ---")
if venv_created_this_run:
    print("A new virtual environment was created and all dependencies were installed.")
else:
    print("Existing virtual environment used. All dependencies were checked and updated.")

print(f"To activate the virtual environment, run: {venv_dir}\\Scripts\\activate.bat")
print(f"Then you can run your Python scripts using: python your_script_name.py")