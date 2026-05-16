import pandas as pd
from bs4 import BeautifulSoup
import argparse
import sys
import os

def parse_krecorder(file_path):
    """Parses a Katalon Recorder (.krecorder) file and returns a list of dictionaries."""
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    data = []
    
    # Each test case is wrapped in a <table>
    for table in soup.find_all('table'):
        # Extract Test Case Name
        tc_name = ""
        thead = table.find('thead')
        if thead:
            tc_name_td = thead.find('td')
            if tc_name_td:
                tc_name = tc_name_td.get_text(strip=True)
        
        # Extract Test Steps
        tbody = table.find('tbody')
        if tbody:
            for row_idx, row in enumerate(tbody.find_all('tr'), start=1):
                cols = row.find_all('td')
                if len(cols) >= 3:
                    command = cols[0].get_text(strip=True)
                    
                    # Target usually contains a <datalist> with alternative locators.
                    # We want to remove the datalist to just get the primary target.
                    target_td = cols[1]
                    if target_td.find('datalist'):
                        target_td.datalist.decompose()
                    target = target_td.get_text(strip=True)
                    
                    value = cols[2].get_text(strip=True)
                    
                    data.append({
                        'Test Case': tc_name,
                        'Step #': row_idx,
                        'Command': command,
                        'Target': target,
                        'Value': value
                    })
    return data

def main():
    parser = argparse.ArgumentParser(description="Convert Katalon Recorder (.krecorder) files to CSV, XLSX, or JSON.")
    parser.add_argument("input_file", help="Path to the .krecorder file")
    parser.add_argument("--format", choices=["csv", "xlsx", "json"], default="xlsx", 
                        help="Output format (default: xlsx)")
    parser.add_argument("--output", help="Optional: Specify custom output filename")
    
    args = parser.parse_args()
    
    print(f"Parsing '{args.input_file}'...")
    data = parse_krecorder(args.input_file)
    
    if not data:
        print("No test cases found. Ensure the file is a valid .krecorder XML/HTML document.")
        sys.exit(1)
        
    df = pd.DataFrame(data)
    print(f"Successfully extracted {len(data)} steps across {df['Test Case'].nunique()} test cases.")

    # Determine output filename if not provided
    base_name = os.path.splitext(args.input_file)[0]
    out_file = args.output if args.output else f"{base_name}_converted.{args.format}"

    # Export to the chosen format
    if args.format == "csv":
        df.to_csv(out_file, index=False, encoding='utf-8')
    elif args.format == "xlsx":
        df.to_excel(out_file, sheet_name="Test Cases", index=False)
    elif args.format == "json":
        df.to_json(out_file, orient="records", indent=4, force_ascii=False)
        
    print(f"File successfully saved to: {out_file}")

if __name__ == "__main__":
    main()