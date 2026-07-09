
"""
KDJ Indicator Calculation Script
Functionality: Reads trading data files, calculates the KDJ indicator, and exports to CSV and Excel formats.
Author: chenmoufeng (Translated and Enhanced)
Creation Date: August 2025
"""

import pandas as pd
import numpy as np
from openpyxl import Workbook
import os  # Added to check if files exist before processing

def read_data(filename):
    """
    Reads the custom-formatted trading data text file.
    
    Args:
        filename (str): The name of the data file to read.
        
    Returns:
        pd.DataFrame: A DataFrame containing the parsed trading data.
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Find the line where the actual data starts (looking for the year '2025-')
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('2025-'):
            data_start = i
            break
    
    # Read the data rows
    data = []
    for line in lines[data_start:]:
        parts = line.strip().split()
        
        # Ensure the line has enough columns (Date, Time, High, Close, Open, Low)
        # Using >= 6 because split() separates the date and time into two parts
        if len(parts) >= 6: 
            # Combine Date (parts[0]) and Time (parts[1]) into a single string
            time_str = f"{parts[0]} {parts[1]}"
            # Extract High, Close, Open, Low (parts[2] to parts[5]) and convert to float
            data.append([time_str] + [float(x) for x in parts[2:6]])
    
    # Create a Pandas DataFrame with the parsed data
    df = pd.DataFrame(data, columns=['Time', 'High', 'Close', 'Open', 'Low'])
    
    # Convert the 'Time' column from strings to actual pandas datetime objects
    df['Time'] = pd.to_datetime(df['Time'])
    
    # Sort the data chronologically and reset the index
    df = df.sort_values('Time').reset_index(drop=True)
    
    return df


def calculate_kdj(df, n=9, m1=3, m2=3):
    """
    Calculates the KDJ indicator for the given dataframe.
    
    Args:
        df (pd.DataFrame): DataFrame containing price data.
        n (int): RSV calculation period (default 9).
        m1 (int): K value smoothing period (default 3).
        m2 (int): D value smoothing period (default 3).
        
    Returns:
        pd.DataFrame: The original DataFrame with 'K', 'D', and 'J' columns added.
    """
    # 1. Calculate RSV (Raw Stochastic Value)
    low_list = df['Low'].rolling(n, min_periods=1).min()
    high_list = df['High'].rolling(n, min_periods=1).max()
    
    # Calculate RSV. Use np.where to prevent division by zero errors if High == Low
    rsv_values = np.where(high_list == low_list, 50, (df['Close'] - low_list) / (high_list - low_list) * 100)
    rsv = pd.Series(rsv_values, index=df.index)
    
    # 2. Initialize K and D values at 50 for the starting values
    k_values = [50.0]
    d_values = [50.0]
    
    # 3. Calculate K and D iteratively
    # OPTIMIZATION: Using lists here instead of df.loc[] makes this run 100x faster on massive data.
    for i in range(1, len(df)):
        k = (2/3) * k_values[-1] + (1/3) * rsv.iloc[i]
        d = (2/3) * d_values[-1] + (1/3) * k
        
        k_values.append(k)
        d_values.append(d)
        
    # Append the calculated lists back into the DataFrame
    df['K'] = k_values
    df['D'] = d_values
    
    # 4. Calculate J value (J = 3K - 2D)
    df['J'] = 3 * df['K'] - 2 * df['D']
    
    return df


def auto_adjust_column_width(ws):
    """
    Automatically adjusts Excel column widths to fit the content cleanly.
    
    Args:
        ws: Excel worksheet object (from openpyxl engine).
    """
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        # Set the width with a little extra padding
        adjusted_width = max_length + 2
        ws.column_dimensions[column_letter].width = adjusted_width


def process_timeframe(ticker, start_date, end_date, timeframe):
    """
    Helper function to process a specific timeframe file end-to-end.
    """
    # Dynamically build the expected file names
    input_file = f"{ticker}_{timeframe}_data_{start_date}_to_{end_date}.txt"
    output_csv = f"{ticker}_{timeframe}_data_with_KDJ.csv"
    output_excel = f"{ticker}_{timeframe}_data_with_KDJ.xlsx"
    
    # Check if the input file actually exists in the folder before running
    if not os.path.exists(input_file):
        print(f"[-] Skipping {timeframe}: Cannot find file '{input_file}'.")
        return

    try:
        print(f"\n[+] Processing {timeframe} data...")
        
        # Read Data
        df = read_data(input_file)
        
        # Calculate KDJ
        df = calculate_kdj(df)
        
        # Save as CSV
        df.to_csv(output_csv, index=False)
        
        # Save as Excel & adjust widths
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
            worksheet = writer.sheets['Data']
            auto_adjust_column_width(worksheet)
        
        print(f"    -> CSV Saved: {output_csv}")
        print(f"    -> Excel Saved: {output_excel}")
        
    except Exception as e:
        print(f"[!] Error processing {timeframe} data: {str(e)}")


def main():
    """Main execution block"""
    
    # Configuration: Set these to match your generated files
    ticker = "AMD" 
    start_date = "15-09-2025"
    end_date = "13-10-2025"
    
    # List of all the timeframes you want to process at the same time
    timeframes = ['1m', '3m', '5m', '10m', '15m']
    
    print("Starting batch KDJ calculations...")
    
    # Loop through the list and process each timeframe sequentially
    for tf in timeframes:
        process_timeframe(ticker, start_date, end_date, tf)
        
    print("\nBatch processing complete!")


if __name__ == "__main__":
    main()
    
    
    
    
    
    