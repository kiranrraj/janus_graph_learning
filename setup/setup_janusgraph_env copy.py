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


# --- Helper Functions for Status Check ---
# In setup_janusgraph_env.py

def parse_requirements_file(req_file_path):
    """Parses a requirements.txt file into a dictionary of {package_name: {'specifier': '==', 'version': 'X.Y.Z'}}."""
    required_packages = {}
    if not req_file_path.exists():
        return required_packages
    with open(req_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith(('#', '-e', '-f')):
                original_req_line = line # Store the original line for reporting if needed

                # Step 1: Split off version specifier first (e.g., 'uvicorn[standard]==0.34.2' -> 'uvicorn[standard]', '0.34.2')
                name_part = line
                version = None
                specifier = None

                if '==' in line:
                    parts = line.split('==', 1)
                    name_part = parts[0].strip()
                    version = parts[1].strip()
                    specifier = '=='
                elif '>=' in line:
                    parts = line.split('>=', 1)
                    name_part = parts[0].strip()
                    version = parts[1].strip()
                    specifier = '>='
                elif '~=' in line:
                    parts = line.split('~=', 1)
                    name_part = parts[0].strip()
                    version = parts[1].strip()
                    specifier = '~='
                # Add other specifiers if you use them, like '<', '<=', '!=', etc.

                # Step 2: Strip off the [extras] part from the name_part (e.g., 'uvicorn[standard]' -> 'uvicorn')
                base_name = name_part.split('[', 1)[0].strip() if '[' in name_part else name_part.strip()

                required_packages[base_name] = {
                    'specifier': specifier,
                    'version': version,
                    'original_req': original_req_line # Keep original for better error messages
                }
    return required_packages

# The reporting loop for missing packages (in the status check part of your script)
# should remain as it is currently, as it already uses 'req_info.get('original_req', req_name)':
# for req_name, req_info in required_packages.items():
#     if req_name not in installed_packages:
#         missing_packages.append(f"{req_info.get('original_req', req_name)} (Not Found)")

def get_installed_packages_from_venv(pip_exe_path):
    """Runs 'pip freeze' in the venv and parses its output."""
    installed_packages = {}
    try:
        result = subprocess.run(
            [str(pip_exe_path), "freeze"],
            check=True, capture_output=True, text=True,
            encoding='utf-8', errors='ignore' # Ensure consistent decoding
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if '==' in line:
                name, version = line.split('==', 1)
                installed_packages[name.strip()] = version.strip()
        return installed_packages
    except FileNotFoundError:
        print(f"ERROR: pip executable not found at {pip_exe_path}. Is the virtual environment set up?")
        return None
    except subprocess.CalledProcessError as e:
        print(f"ERROR: 'pip freeze' failed with error code {e.returncode}.")
        print(f"Stdout:\n{e.stdout}")
        print(f"Stderr:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while getting installed packages: {e}")
        return None


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
# No --status argument as it will run automatically at the end.
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
        check=True, capture_output=True, text=True,
        encoding='utf-8', errors='ignore'
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
        text=True,
        encoding='utf-8', errors='ignore'
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

# --- Automated Virtual Environment Status Check (Always Runs) ---
print("\n--- Automated Virtual Environment Status Report ---")

# Initialize a flag to track if any packages are missing
has_missing_packages = False

if not venv_dir.exists():
    print(f"  Status: VIRTUAL ENVIRONMENT MISSING.")
    print(f"  Expected at: {venv_dir}")
    print("  Recommendation: Run the script without --force to create it, or with --force to recreate if needed.")
elif not python_exe.exists() or not pip_exe.exists():
    print(f"  Status: VIRTUAL ENVIRONMENT CORRUPT or INCOMPLETE.")
    print(f"  Missing python.exe or pip.exe in: {venv_dir.relative_to(base_dir)} (within {base_dir})")
    print("  Recommendation: Run the script with --force to recreate it.")
else:
    print(f"  Status: Virtual environment structure looks healthy at: {venv_dir}")

    if not requirements_file.exists():
        print(f"  WARNING: requirements.txt not found at {requirements_file}. Cannot perform package compliance check.")
    else:
        # These functions are assumed to be defined elsewhere in your script
        required_packages = parse_requirements_file(requirements_file)
        installed_packages = get_installed_packages_from_venv(pip_exe)

        # --- Data Collection for the new report format ---
        error_missing_list = []          # List of original_req_line
        comparison_table_data = []       # List of (package_name, req_line, pip_freeze_output)
        extra_packages_list = []         # List of "name==version" for extra packages

        if installed_packages is None:
            print("  [ERROR] Cannot perform package compliance check due to failure in retrieving installed packages.")
            # If we can't even get installed packages, consider it a critical issue
            has_missing_packages = True 
        else:
            for req_base_name, req_info in required_packages.items():
                original_req_line = req_info.get('original_req', req_base_name)
                
                if req_base_name in installed_packages:
                    installed_version = installed_packages[req_base_name]
                    comparison_table_data.append((req_base_name, original_req_line, f"{req_base_name}=={installed_version}"))
                else:
                    error_missing_list.append(original_req_line)
                    comparison_table_data.append((req_base_name, original_req_line, "Not Found"))
                    has_missing_packages = True # Set flag if any package is missing
            
            # Identify extra packages
            for inst_name, inst_version in installed_packages.items():
                if inst_name not in required_packages:
                    extra_packages_list.append(f"{inst_name}=={inst_version}")

        # --- Printing the new report format ---
        print("\n  --- Package Compliance Report ---")

        # Only print "Error Installing / Missing" if there are actual missing packages
        if error_missing_list:
            print("\n  --- Error Installing / Missing Packages (from requirements.txt) ---")
            for pkg_line in error_missing_list:
                print(f"    - {pkg_line}")
        
        # Comparison Table (always printed if data is available)
        print("\n  --- Comparison ---")
        if comparison_table_data:
            # Determine dynamic column widths for clean formatting
            max_pkg_name_len = len("Package Name")
            max_req_line_len = len("Line from requirements.txt")
            max_freeze_line_len = len("Line from pip freeze output")

            for pkg_name, req_line, freeze_line in comparison_table_data:
                max_pkg_name_len = max(max_pkg_name_len, len(pkg_name))
                max_req_line_len = max(max_req_line_len, len(req_line))
                max_freeze_line_len = max(max_freeze_line_len, len(freeze_line))
            
            # Add some padding for readability
            col_padding = 4
            max_pkg_name_len += col_padding
            max_req_line_len += col_padding
            max_freeze_line_len += col_padding

            header_format = f"  {{:<{max_pkg_name_len}}}{{:<{max_req_line_len}}}{{:<{max_freeze_line_len}}}"
            divider_format = f"  {{:-<{max_pkg_name_len}}}{{:-<{max_req_line_len}}}{{:-<{max_freeze_line_len}}}"

            print(header_format.format("Package Name", "Line from requirements.txt", "Line from pip freeze output"))
            print(divider_format.format("", "", "")) # Print a separator line

            for pkg_name, req_line, freeze_line in comparison_table_data:
                print(header_format.format(pkg_name, req_line, freeze_line))
        else:
            print("    No package data to compare.")

        # Extra Packages (always printed if any are found)
        if extra_packages_list:
            print("\n  [!] EXTRA PACKAGES (installed but not explicitly in requirements.txt):")
            for pkg in extra_packages_list:
                print(f"    - {pkg}")
        else:
            print("\n  [OK] No unexpected extra packages found.")

# --- Conditional Final Message ---
if has_missing_packages:
    print("\n--- JanusGraph Python environment setup complete, but with MISSING DEPENDENCIES ---")
    print("Please review the 'Error Installing / Missing Packages' section above.")
else:
    print("\n--- JanusGraph Python environment setup complete ---")
    if venv_created_this_run:
        print("A new virtual environment was created and all dependencies were installed.")
    else:
        print("Existing virtual environment used. All dependencies were checked and updated.")


print("\nVirtual environment setup and status report complete.")
print(f"To activate the virtual environment, run: {venv_dir}\\Scripts\\activate.bat")
print(f"Then you can run your Python scripts using: python your_script_name.py")