#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 15:54:41 2026

@author: chenmoufeng
"""

import requests          # Used to make the HTTP call to the Polygon.io API
import pandas as pd      # Used for data manipulation, specifically resampling timeframes
from datetime import datetime  # Used to format the dates cleanly for the text file

def round_to_nearest_half_cent(val):
    """
    Takes a price (float) and rounds it to the nearest 0.005.
    This ensures the 3rd decimal place is always exactly a 0 or a 5.
    
    How the math works:
    If val = 159.102:
    1. 159.102 * 200 = 31820.4
    2. round(31820.4) = 31820
    3. 31820 / 200.0 = 159.100 (Ends in 0)
    """
    return round(val * 200) / 200.0

def save_formatted_txt(df, ticker, start_date, end_date, timeframe_label):
    """
    Takes a processed Pandas DataFrame and saves it as a .txt file.
    It perfectly mimics the custom header and tab-separated format requested.
    """
    # Safety check: If the dataframe has no data, skip saving to prevent errors
    if df.empty:
        print(f"Skipping {timeframe_label} - no data available.")
        return
        
    # Make a copy of the data so we don't accidentally modify the original 1m data 
    # when applying our rounding rules.
    df_out = df.copy()
    
    # Loop through the price columns and apply our 0-or-5 rounding rule to every row
    for col in ['High', 'Close', 'Open', 'Low']:
        df_out[col] = df_out[col].apply(round_to_nearest_half_cent)
        
    # Extract the very first and very last timestamp to show the *actual* data range
    actual_start = df_out['Time'].iloc[0].strftime('%Y-%m-%d %H:%M:%S')
    actual_end = df_out['Time'].iloc[-1].strftime('%Y-%m-%d %H:%M:%S')
    
    # Count how many rows (data points) we are about to save
    data_points = len(df_out)
    
    # Re-format the user's input dates (YYYY-MM-DD) into the header's requested format (DD/MM/YYYY)
    start_fmt = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
    end_fmt = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
    
    # Construct the final file name dynamically based on the inputs
    output_filename = f"{ticker}_{timeframe_label}_data_{start_date}_to_{end_date}.txt"
    print(f" -> Saving {output_filename} ({data_points} rows)")
    
    # Open the file in "w" (write) mode. This will create the file or overwrite it if it exists.
    with open(output_filename, "w") as f:
        
        # 1. Write the custom header block
        f.write(f"# Stock Data: {ticker}\n")
        f.write(f"# Time Interval: {timeframe_label}\n")
        f.write(f"# Date Range: {start_fmt} to {end_fmt}\n")
        f.write(f"# Actual Data Range: {actual_start} to {actual_end}\n")
        f.write(f"# Data Points: {data_points}\n")
        f.write(f"# Columns: Time, High, Close, Open, Low\n")
        f.write(f"# Precision: Prices adjusted to 3 decimal places with last digit 0 or 5\n")
        f.write(f"#============================================================\n\n")
        
        # 2. Write the column headers using \t (tabs) for spacing
        f.write("Time\t\t\tHigh\t\tClose\t\tOpen\t\tLow\n")
        f.write("-" * 80 + "\n") # Prints a divider line 80 characters long
        
        # 3. Loop through every row in the dataframe and write it to the file
        for _, row in df_out.iterrows():
            # Format time as a string
            time_str = row['Time'].strftime('%Y-%m-%d %H:%M:%S')
            
            # Format prices to strictly show 3 decimal places (e.g., 159.100 instead of just 159.1)
            high_str = f"{row['High']:.3f}"
            close_str = f"{row['Close']:.3f}"
            open_str = f"{row['Open']:.3f}"
            low_str = f"{row['Low']:.3f}"
            
            # Write the row data separated by tabs (\t) and end with a newline (\n)
            f.write(f"{time_str}\t{high_str}\t{close_str}\t{open_str}\t{low_str}\n")


def fetch_and_generate_multiple_timeframes(ticker, start_date, end_date, api_key):
    """
    Main function that fetches 1-minute data from Polygon.io,
    then mathematically converts that 1m data into 3m, 5m, 10m, and 15m intervals.
    """
    print(f"Fetching base 1m data for {ticker} from Polygon.io...")
    
    # 1. Build the Polygon API URL to request 1-minute aggregate bars
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/{start_date}/{end_date}"
    params = {
        "adjusted": "true", # Adjust for stock splits
        "sort": "asc",      # Sort oldest to newest
        "limit": 50000,     # Max data points allowed per call
        "apiKey": api_key
    }
    
    # Send the request and convert the response to a JSON dictionary
    response = requests.get(url, params=params)
    data = response.json()
    
    # Check if the API actually returned data
    if "results" not in data:
        print("Error fetching data:", data.get("error", "No results found."))
        return
        
    # 2. Load the raw JSON results into a Pandas DataFrame for easy manipulation
    df = pd.DataFrame(data["results"])
    
    # Polygon returns timestamps in milliseconds under the column 't'.
    # Convert this to standard human-readable Date/Time objects.
    df['Time'] = pd.to_datetime(df['t'], unit='ms')
    
    # Rename Polygon's shorthand columns to full names
    df = df.rename(columns={'h': 'High', 'c': 'Close', 'o': 'Open', 'l': 'Low'})
    
    # Set the 'Time' column as the index. 
    # Pandas requires the Time to be the index in order to use the .resample() grouping function later.
    df.set_index('Time', inplace=True)
    
    # Keep only the columns we actually care about
    df = df[['High', 'Close', 'Open', 'Low']]
    
    # ---------------------------------------------------------
    # Generate 1-minute file
    # ---------------------------------------------------------
    # Reset index to pull 'Time' back out into a normal column, then save it.
    df_1m = df.reset_index()
    save_formatted_txt(df_1m, ticker, start_date, end_date, "1m")
    
    # ---------------------------------------------------------
    # Generate Higher Timeframe Files
    # ---------------------------------------------------------
    # A dictionary mapping the file label (e.g., "3m") to Pandas time rules (e.g., "3min")
    timeframes = {
        "3m": "3min",
        "5m": "5min",
        "10m": "10min",
        "15m": "15min"
    }
    
    # Loop through the dictionary to generate each file dynamically
    for label, rule in timeframes.items():
        
        # .resample(rule) groups the 1-minute rows into larger chunks (e.g., 5-minute blocks).
        # .agg() tells Pandas *how* to combine the rows in that chunk:
        #   - The highest price in the 5 mins becomes the new High.
        #   - The final price in the 5 mins becomes the new Close.
        #   - The first price in the 5 mins becomes the new Open.
        #   - The lowest price in the 5 mins becomes the new Low.
        df_resampled = df.resample(rule).agg({
            'High': 'max',
            'Close': 'last',
            'Open': 'first',
            'Low': 'min'
        }).dropna() # .dropna() removes empty periods (like outside market hours)
        
        # Pull 'Time' out of the index so we can save it normally
        df_resampled = df_resampled.reset_index()
        
        # Save the file using the label (e.g., "5m")
        save_formatted_txt(df_resampled, ticker, start_date, end_date, label)
        
    print("\nAll files successfully generated!")

# This block ensures the code only runs if you execute this file directly.
if __name__ == "__main__":
    YOUR_API_KEY = "YOUR_API_KEY_HERE"
    fetch_and_generate_multiple_timeframes(
        ticker="AMD", 
        start_date="2025-09-15", 
        end_date="2025-10-13", 
        api_key=YOUR_API_KEY
    )
    
    
    
    
    
    
    
    
    
    
    
    