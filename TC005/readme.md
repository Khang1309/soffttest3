# TC005 Test Automation Guide

This directory contains the automated test scripts for the TC005 test case (Moodle Quiz Question Creation), utilizing Selenium and Python.

## Prerequisites

Before running the tests, ensure you have the required dependencies installed. You can install them using the `requirements.txt` file located in the root project folder.

### Using standard Python/Pip
Open a terminal in this `TC005` directory and run:
```powershell
pip install -r ..\requirements.txt
```

### Using `uv` (Alternative)
If you prefer using the `uv` package manager:
```powershell
pip install uv
```

## Running the Tests

There are two levels of tests available. Both tests will open a browser using Selenium, read data from their respective CSV files, and run the automation automatically.

### Run Level 1 Test
Runs the automation using `test_data_level1.csv`.
```powershell
# If using standard python
python tc005_level1.py

# If using uv
uv run python tc005_level1.py
```

### Run Level 2 Test
Runs the automation using `test_data_level2.csv` and the JSON `locators.json`.
```powershell
# If using standard python
python tc005_level2.py

# If using uv
uv run python tc005_level2.py
```

## How the Output Works
- The scripts use data-driven testing. They read test cases row-by-row from the CSV files.
- Each test attempts to log into the Moodle demo site and create a True/False question based on the test data.
- The scripts will output `[PASS]`, `[FAIL]`, or `[ERROR]` to the console in real-time for each `TC_ID` evaluated.
- If any test cases fail, a `========== SUMMARY OF FAILURES ==========` section will be printed at the very end of the script execution to help you debug.

## Important Notes
- **Webdriver Path:** The scripts hardcode the path to `msedgedriver.exe` inside the `TC002` folder. Make sure this executable exists there.
- **Moodle Reset:** The Moodle demo site resets itself automatically on the hour. Tests may fail if the quiz ID (`cmid=1160`) is missing due to a reset.
- **False Positives:** The verification checks if the expected result is anywhere within the page text. Be aware that short numeric expected results (like "4" or "7") might occasionally trigger a false pass if those numbers naturally appear on the site interface.
