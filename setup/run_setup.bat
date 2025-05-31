@echo off
REM run_setup.bat
REM This batch file executes the Python script to set up the JanusGraph environment.

REM %0: This refers to the batch file itself. If you just used %0,
REM it would give you the full path and name of the batch file
REM (e.g., D:\JanusGraph\learning\setup\run_setup.bat).
REM ~: This tilde symbol removes any surrounding quotes from the expanded parameter.
REM d: This flag extracts the drive letter of the path. (e.g., D:)
REM p: This flag extracts the path of the file. (e.g., \JanusGraph\learning\setup\)
REM %~dp0, you get the drive and path of the batch file itself, with a trailing backslash (\).
REM Here the output will be, %~dp0 evaluate to: D:\JanusGraph\learning\setup\
REM %~dp0 expands to the drive letter and path of the batch file itself.
SET "SCRIPT_DIR=%~dp0"

REM Define the name of your Python setup script.
SET "SETUP_SCRIPT_NAME=setup_janusgraph_env.py"

REM Define the name for the log file. It will be created in the same directory.
SET "LOG_FILE=%SCRIPT_DIR%setup_log.txt"

REM --- Dynamically determine BASE_DIR and VENV_ACTIVATE_SCRIPT ---
REM The Python script calculates base_dir as two levels up from its own location.
REM If setup.py is in D:\JanusGraph\learning\setup\, then base_dir is D:\JanusGraph\learning\.
REM We need to replicate that logic here for the batch file to find activate.bat.
FOR %%I IN ("%SCRIPT_DIR%") DO SET "PARENT_DIR=%%~dpI"
FOR %%I IN ("%PARENT_DIR%") DO SET "BASE_DIR=%%~dpI"
SET "BASE_DIR=%BASE_DIR:~0,-1%" REM Remove trailing slash for cleaner path building

SET "VENV_ACTIVATE_SCRIPT=%BASE_DIR%\.venv\Scripts\activate.bat"

REM --- Parse Arguments for Batch File ---
REM This loop checks for --activate (-a) and --force (-f) flags.
REM --activate is handled by the batch file itself for environment activation.
REM --force is passed to the Python script for venv recreation.
SET "ACTIVATE_FLAG_PRESENT="
SET "PYTHON_ARGS="
FOR %%A IN (%*) DO (
    IF /I "%%A"=="--activate" (
        SET "ACTIVATE_FLAG_PRESENT=1"
    ) ELSE IF /I "%%A"=="-a" (
        SET "ACTIVATE_FLAG_PRESENT=1"
    ) ELSE IF /I "%%A"=="-f" (
        SET "PYTHON_ARGS=%PYTHON_ARGS% %%A"
    ) ELSE IF /I "%%A"=="--force" (
        SET "PYTHON_ARGS=%PYTHON_ARGS% %%A"
    ) ELSE (
        REM Pass any other unrecognized arguments directly to the Python script
        SET "PYTHON_ARGS=%PYTHON_ARGS% %%A"
    )
)

REM --- Redirect all subsequent output to the log file ---
> "%LOG_FILE%" (
    echo [START] Script execution started: %DATE% %TIME%
    echo Navigating to %SCRIPT_DIR%...
    cd /d "%SCRIPT_DIR%"
    IF %ERRORLEVEL% NEQ 0 (
        echo ERROR: Could not change directory to %SCRIPT_DIR%. Make sure the path is correct.
        echo [END] Script execution finished with errors.
        EXIT /B %ERRORLEVEL%
    )

    echo.
    echo Running the Python setup script: %SETUP_SCRIPT_NAME% %PYTHON_ARGS%
    echo This may take a few minutes as it creates/updates the virtual environment and installs/updates dependencies.
    echo.

    REM Execute the Python script and redirect its output to the log file.
    REM %PYTHON_ARGS% passes the filtered arguments to the Python script.
    python "%SETUP_SCRIPT_NAME%" %PYTHON_ARGS%

    REM --- Check for script completion within the log ---
    REM The Python script sets ERRORLEVEL based on success/failure.
    IF %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: The Python script encountered an error. Please check the output above for details.
        echo [END] Script execution finished with errors.
        SET "SCRIPT_SUCCESS=0"
    ) ELSE (
        echo.
        echo Python environment setup process completed successfully.
        echo [END] Script execution finished successfully.
        SET "SCRIPT_SUCCESS=1"
    )
)

REM --- Final Console Output and Activation ---
echo.
IF "%SCRIPT_SUCCESS%"=="1" (
    echo --- Setup Process Status: SUCCESS ---
    echo Setup finished. Check "%LOG_FILE%" for detailed output.
    IF "%ACTIVATE_FLAG_PRESENT%"=="1" (
        echo.
        echo Attempting to activate virtual environment...
        REM Ensure the activate script path is correct
        IF NOT EXIST "%VENV_ACTIVATE_SCRIPT%" (
            echo ERROR: Activation script not found at "%VENV_ACTIVATE_SCRIPT%".
            echo Virtual environment might not have been created or path is wrong.
        ) ELSE (
            REM Call the activate script. 'call' is important so the batch file resumes.
            call "%VENV_ACTIVATE_SCRIPT%"
            IF %ERRORLEVEL% NEQ 0 (
                echo WARNING: Activation script ran, but returned an error. You may need to activate it manually.
                echo Current ERRORLEVEL from activate.bat: %ERRORLEVEL%
            ) ELSE (
                echo Virtual environment activated.
            )
        )
    )
) ELSE (
    echo --- Setup Process Status: FAILED ---
    echo An error occurred during setup. Please check "%LOG_FILE%" for details.
)