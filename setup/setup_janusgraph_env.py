import subprocess
import sys
from pathlib import Path
import re 
import shutil 

def _get_paths(script_path: Path):

    # script is in D:\JanusGraph\learning\setup\setup_janusgraph_env.py
    # base_dir should be D:\JanusGraph\learning
    base_dir = script_path.parent.parent.resolve()
    venv_dir = base_dir / ".venv"
    requirements_file = script_path.parent / "requirements.txt" 

    # Determine Python and Pip executables within the virtual environment
    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    return base_dir, venv_dir, requirements_file, python_exe, pip_exe

def _manage_virtual_environment(venv_dir: Path, python_exe: Path, requirements_file: Path, force_recreate: bool):

    venv_created_this_run = False
    installation_successful = False

    print(f"Checking virtual environment at: {venv_dir}")

    # Check if venv already exists and if it should be recreated
    if venv_dir.exists() and not force_recreate:
        print("Virtual environment already exists. Checking for updates...")
        if not (python_exe.exists() and requirements_file.exists()):
            print("WARNING: Existing venv might be corrupt or requirements.txt is missing. Attempting recreation.")
            # Force recreation if essential files are missing
            force_recreate = True 
    
    if force_recreate:
        print("Force recreation initiated. Removing existing virtual environment...")
        try:
            if venv_dir.exists():
                shutil.rmtree(venv_dir)
            print("Existing virtual environment removed.")
        except OSError as e:
            print(f"ERROR: Could not remove existing virtual environment: {e}")
            print("Please ensure no files in the .venv folder are open and try again.")
            # Indicate failure
            return False, False 

    # Create the virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating new virtual environment...")
        try:
            # Use the system's default python to create the venv
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            venv_created_this_run = True
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to create virtual environment: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False, False 
        except Exception as e:
            print(f"An unexpected error occurred during venv creation: {e}")
            return False, False

    # Ensure python and pip exist in the newly created or existing venv
    if not python_exe.exists():
        print(f"ERROR: python.exe not found in venv at {python_exe}. Venv might be corrupt.")
        return False, False

    # Check for pip.exe in the same directory as python.exe
    if not (python_exe.parent / "pip.exe").exists():
        print(f"ERROR: pip.exe not found in venv. Venv might be corrupt.")
        return False, False

    # Install/update dependencies
    if requirements_file.exists():
        print(f"Installing/updating dependencies from {requirements_file.name}...")
        try:
            # Use the venv's python to run pip install
            # Added `encoding='utf-8', errors='replace'` for broader compatibility
            result = subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(requirements_file)],
                                    check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            print("All dependencies from requirements.txt installed successfully.")
            installation_successful = True
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install dependencies: {e}")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            print("Please check the error output above for details.")
        except Exception as e:
            print(f"An unexpected error occurred during pip installation: {e}")
    else:
        print(f"WARNING: {requirements_file.name} not found. Skipping dependency installation.")
        installation_successful = True 

    return venv_created_this_run, installation_successful

def parse_requirements_file(req_file_path: Path):
    required_packages = {}
    if not req_file_path.exists():
        return required_packages
    with open(req_file_path, 'r', encoding='utf-8') as f: 
        for line in f:
            line = line.strip()
            if line and not line.startswith(('#', '-e', '-f', '--')): 
                original_req_line = line #

                name_part = line
                version = None
                specifier = None

                # Split off version specifier first 
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

                # Step 2: Strip off the [extras] part from the name_part to get the base package name
                base_name = name_part.split('[', 1)[0].strip() if '[' in name_part else name_part.strip()
                
                required_packages[base_name] = {
                    'specifier': specifier,
                    'version': version,
                    'original_req': original_req_line
                }
    return required_packages

def get_installed_packages_from_venv(pip_exe: Path):

    installed_packages = {}
    if not pip_exe.exists():
        print(f"ERROR: pip executable not found at {pip_exe}. Cannot check installed packages.")
        return None
    try:
        # Use the venv's pip to freeze
        result = subprocess.run([str(pip_exe), "freeze"], check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.startswith(('#', '-e', '-f')): 
                # Regex to match 'package==version' format
                match = re.match(r"^([a-zA-Z0-9._-]+)==([0-9a-zA-Z._-]+)", line)
                if match:
                    package_name = match.group(1).strip()
                    package_version = match.group(2).strip()
                    installed_packages[package_name] = package_version
        return installed_packages
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to run 'pip freeze': {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during 'pip freeze': {e}")
        return None

def _check_package_compliance(requirements_file: Path, pip_exe: Path):

    error_missing_list = []
    comparison_table_data = []
    extra_packages_list = []
    has_missing_packages = False

    if not requirements_file.exists():
        print(f"  WARNING: {requirements_file.name} not found. Skipping detailed package compliance check.")
        # No requirements file, so no missing packages to report.
        return error_missing_list, comparison_table_data, extra_packages_list, False
    
    required_packages = parse_requirements_file(requirements_file)
    installed_packages = get_installed_packages_from_venv(pip_exe)

    if installed_packages is None: 
        print("  [ERROR] Cannot perform package compliance check due to failure in retrieving installed packages.")
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
                # Set flag if any package is missing
                has_missing_packages = True 
        
        # Identify extra packages
        for inst_name, inst_version in installed_packages.items():
            if inst_name not in required_packages:
                extra_packages_list.append(f"{inst_name}=={inst_version}")

    return error_missing_list, comparison_table_data, extra_packages_list, has_missing_packages

def _print_status_report(venv_dir: Path, base_dir: Path, python_exe: Path, pip_exe: Path, requirements_file: Path,
                         venv_created_this_run: bool,
                         error_missing_list: list, comparison_table_data: list, extra_packages_list: list,
                         has_missing_packages: bool):

    print("\n--- Automated Virtual Environment Status Report ---")

    # Overall Virtual Environment health check
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
        print("\n  --- Package Compliance Report ---")

        # Print "Error Installing / Missing" 
        if error_missing_list:
            print("\n  --- Error Installing / Missing Packages (from requirements.txt) ---")
            for pkg_line in error_missing_list:
                print(f"    - {pkg_line}")
        
        # Comparison Table 
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
            # Print a separator line
            print(divider_format.format("", "", "")) 

            for pkg_name, req_line, freeze_line in comparison_table_data:
                print(header_format.format(pkg_name, req_line, freeze_line))
        else:
            print("    No package data to compare.")

        # Extra Packages 
        if extra_packages_list:
            print("\n  [!] EXTRA PACKAGES (installed but not explicitly in requirements.txt):")
            for pkg in extra_packages_list:
                print(f"    - {pkg}")
        else:
            print("\n  [OK] No unexpected extra packages found.")

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

# --- Main execution block ---
def main():
     # Get the absolute path of the current script
    script_path = Path(__file__).resolve()

    # Parse command-line arguments (e.g., --force, --activate)
    force_recreate = "--force" in sys.argv or "-f" in sys.argv
    activate_env = "--activate" in sys.argv or "-a" in sys.argv

    # 1. Get essential paths for the project and virtual environment
    base_dir, venv_dir, requirements_file, python_exe, pip_exe = _get_paths(script_path)

    # 2. Manage the Virtual Environment (create/recreate/install packages)
    venv_created_this_run, installation_successful = _manage_virtual_environment(
        venv_dir, python_exe, requirements_file, force_recreate
    )

    # 3. Perform Package Compliance Check (collects data for reporting)
    error_missing_list, comparison_table_data, extra_packages_list, has_missing_packages = \
        _check_package_compliance(requirements_file, pip_exe)

    # 4. Print the comprehensive Status Report based on all collected data
    _print_status_report(
        venv_dir, base_dir, python_exe, pip_exe, requirements_file,
        venv_created_this_run,
        error_missing_list, comparison_table_data, extra_packages_list,
        has_missing_packages
    )

if __name__ == "__main__":
    main()