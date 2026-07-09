#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 12 22:47:20 2025
@author: NAFENG26

Description:
This script backtests a day-trading strategy using the KDJ technical indicator 
across 1-minute, 3-minute, and 5-minute timeframes. It simulates buying and 
selling a financial asset, tracking account equity, and ensuring all positions 
are closed before the market ends.
"""

# Import necessary libraries for data manipulation, math operations, plotting, and time management
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import time
import logging

# Set up matplotlib fonts to avoid warnings when generating charts
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False # Ensures minus signs display correctly in plots
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR) # Suppress font manager warnings

# ---------------------------------------------------------
# 1. DATA LOADING & PREPARATION
# ---------------------------------------------------------
# Load historical price and KDJ data from three different Excel files (1m, 3m, 5m intervals)
df_1min = pd.read_excel('RIOT_1m_data_with_KDJ.xlsx', sheet_name='Data')
df_3min = pd.read_excel('RIOT_3m_data_with_KDJ.xlsx', sheet_name='Data')
df_5min = pd.read_excel('RIOT_5m_data_with_KDJ.xlsx', sheet_name='Data')

# Convert the 'Time' column in the 1-minute dataframe to actual datetime objects
df_1min['Time'] = pd.to_datetime(df_1min['Time'])
# Set the 'Time' column as the index of the dataframe to make time-based lookups easier
df_1min.set_index('Time', inplace=True)

# Extract just the date (without the time) into a new column for daily grouping
df_1min['Date'] = df_1min.index.date

# ---------------------------------------------------------
# 2. INITIALIZE BACKTEST PARAMETERS
# ---------------------------------------------------------
initial_capital = 10000      # Starting money in dollars
commission = 0.15            # Flat fee charged per trade
position = 0                 # Trading state: 0 means we hold no shares (flat), 1 means we hold shares (long)
cash = initial_capital       # Available cash on hand
shares = 0                   # Number of shares currently held

# List to store our total account value at the end of each day
daily_equity = []

# KDJ Strategy Parameters
overbought_threshold = 80    # If the J-line goes above this, the asset might be overpriced (sell signal)
oversold_threshold = 20      # If the J-line goes below this, the asset might be underpriced (buy signal)

# Variables to track trade history and daily progress
trades = []                  # Will store a log of every trade made
current_date = None          # Keeps track of the day we are currently looping through
day_start_cash = initial_capital 
day_trades = 0               # Counter for trades made on a specific day

# Market hours constraints
market_open_time = time(9, 30)   # Market opens at 9:30 AM
market_close_time = time(16, 0)  # Market closes at 4:00 PM
force_close_time = time(15, 30)  # Strategy rule: sell all shares by 3:30 PM (no overnight holds)

# ---------------------------------------------------------
# 3. MAIN BACKTEST LOOP
# ---------------------------------------------------------
# Loop through every single row in the 1-minute dataset, starting from the second row (index 1)
# We start at 1 instead of 0 so we can compare current values to the previous minute's values
for i in range(1, len(df_1min)):
    # Get the timestamp, closing price, and KDJ values for the current minute
    current_time = df_1min.index[i]
    current_close = df_1min['Close'].iloc[i]
    current_k = df_1min['K'].iloc[i]
    current_d = df_1min['D'].iloc[i]
    current_j = df_1min['J'].iloc[i]
    
    # Get the KDJ values from exactly one minute ago
    prev_k = df_1min['K'].iloc[i-1]
    prev_d = df_1min['D'].iloc[i-1]
    prev_j = df_1min['J'].iloc[i-1]
    
    # Extract the corresponding 3-minute KDJ data
    alpha = int(i // 3) # Map the 1-min index to the 3-min timeframe
    if alpha < len(df_3min) and alpha > 0:
        min3_current_k = df_3min['K'].iloc[alpha-1]
        min3_current_d = df_3min['D'].iloc[alpha-1]
        min3_current_j = df_3min['J'].iloc[alpha-1]
        
        min3_prev_k = df_3min['K'].iloc[alpha-2]
        min3_prev_d = df_3min['D'].iloc[alpha-2]
        min3_prev_j = df_3min['J'].iloc[alpha-2]
    else:
        # Default neutral values if 3-minute data isn't available yet
        min3_current_k = min3_current_d = min3_current_j = 50
        min3_prev_k = min3_prev_d = min3_prev_j = 50
    
    # Extract the corresponding 5-minute KDJ data (Currently unused in signals, but available)
    beta = int(i // 5) # Map the 1-min index to the 5-min timeframe
    if beta < len(df_5min) and beta > 0:
        min5_current_k = df_5min['K'].iloc[beta-1]
        min5_current_d = df_5min['D'].iloc[beta-1]
        min5_current_j = df_5min['J'].iloc[beta-1]
        
        min5_prev_k = df_5min['K'].iloc[beta-2]
        min5_prev_d = df_5min['D'].iloc[beta-2]
        min5_prev_j = df_5min['J'].iloc[beta-2]
    else:
        # Default neutral values if 5-minute data isn't available yet
        min5_current_k = min5_current_d = min5_current_j = 50
        min5_prev_k = min5_prev_d = min5_prev_j = 50
    
    # Check if the date has changed (i.e., it's a new trading day)
    if current_date != current_time.date():
        # If it's not the very first day, record the results from the day that just ended
        if current_date is not None:
            # Failsafe: Ensure we are not holding any positions at the end of the day
            if position == 1:
                # Force sell at the last known price of the previous day
                close_price = df_1min['Close'].iloc[i-1] if i > 0 else current_close
                cash += shares * close_price - commission
                day_trades += 1
                trades.append(('FORCE_CLOSE_EOD', df_1min.index[i-1] if i > 0 else current_time, 
                              close_price, shares, cash))
                shares = 0
                position = 0
            
            # Log the daily summary
            daily_equity.append({
                'Date': current_date,
                'Equity': cash,
                'Trades': day_trades,
                'Cash': cash,
                'Shares': 0,  # Ensured empty at start of day
                'Position_Value': 0
            })
        
        # Reset counters for the new day
        current_date = current_time.date()
        day_start_cash = cash
        day_trades = 0
        print(f"New Trading Day: {current_date}, Starting Capital: ${cash:.2f}")
    
    # Calculate the total value of the account right now (cash + value of held shares)
    current_equity = cash + shares * current_close
    
    # Reset signals for this specific minute
    buy_signal = False
    sell_signal = False
    
    # ---------------------------------------------------------
    # 4. TRADE LOGIC (Signals)
    # ---------------------------------------------------------
    # BUY CONDITIONS: Only check if we are flat (position == 0) AND within allowed trading hours
    if position == 0 and market_open_time <= current_time.time() < force_close_time:
        # Condition 1: 1m J-line crosses up from oversold AND 3m J-line is rising
        if (prev_j < oversold_threshold and current_j >= oversold_threshold and min3_prev_j < min3_current_j) or \
           (prev_k < prev_d and current_k > current_d and current_k < 50 and current_d < 50 and min3_prev_j < min3_current_j) or \
           (current_j < oversold_threshold and current_j > prev_j and min3_prev_j < min3_current_j):
            # Condition 2: 1m K-line crosses over D-line in the lower half (<50) AND 3m J-line is rising
            # Condition 3: 1m J-line is oversold but starts turning up AND 3m J-line is rising
            buy_signal = True
    
    # SELL CONDITIONS: Only check if we are currently holding shares (position == 1)
    if position == 1:
        # Condition 1: J-line falls back down below overbought threshold
        if (prev_j > overbought_threshold and current_j <= overbought_threshold) or \
           (prev_k > prev_d and current_k < current_d and current_k > 50 and current_d > 50) or \
           (current_j > overbought_threshold and current_j < prev_j):
            # Condition 2: K-line crosses under D-line in the upper half (>50)
            # Condition 3: J-line is overbought and starts turning down
            sell_signal = True
    
    # ---------------------------------------------------------
    # 5. TRADE EXECUTION
    # ---------------------------------------------------------
    # If we got a buy signal and have no position, execute a BUY
    if position == 0 and buy_signal:
        # Go "All In" - calculate maximum shares we can afford minus the commission fee
        max_shares = (cash - commission) // current_close
        if max_shares > 0:
            shares = max_shares
            cash -= shares * current_close + commission # Deduct money
            position = 1                                # Update state to 'holding'
            day_trades += 1
            trades.append(('BUY', current_time, current_close, shares, current_equity))
            print(f"BUY: {current_time}, Price: ${current_close:.2f}, Shares: {shares}, Equity: ${current_equity:.2f}")
    
    # If we got a sell signal and we hold shares, execute a SELL
    elif position == 1 and sell_signal:
        # Sell all held shares
        cash += shares * current_close - commission     # Add money back
        day_trades += 1
        trades.append(('SELL', current_time, current_close, shares, current_equity))
        print(f"SELL: {current_time}, Price: ${current_close:.2f}, Shares: {shares}, Equity: ${current_equity:.2f}")
        shares = 0                                      # Reset shares
        position = 0                                    # Update state to 'flat'
    
    # Intraday Forced Close: If it's 3:30 PM or later and we still hold shares, sell immediately
    if position == 1 and current_time.time() >= force_close_time:
        cash += shares * current_close - commission
        day_trades += 1
        trades.append(('FORCE_CLOSE', current_time, current_close, shares, current_equity))
        print(f"FORCE CLOSE: {current_time}, Price: ${current_close:.2f}, Shares: {shares}, Equity: ${current_equity:.2f}")
        shares = 0
        position = 0

# ---------------------------------------------------------
# 6. POST-LOOP CLEANUP
# ---------------------------------------------------------
# The backtest loop is finished. Check if we are still holding shares on the very last minute.
if position == 1:
    cash += shares * df_1min['Close'].iloc[-1] - commission
    day_trades += 1
    trades.append(('FINAL_CLOSE', df_1min.index[-1], df_1min['Close'].iloc[-1], shares, cash))
    shares = 0
    position = 0

# Log the very last day into our daily equity tracker
daily_equity.append({
    'Date': current_date,
    'Equity': cash,
    'Trades': day_trades,
    'Cash': cash,
    'Shares': 0,
    'Position_Value': 0
})

# Convert the daily logs into a pandas DataFrame for easy analysis
daily_df = pd.DataFrame(daily_equity)
daily_df.set_index('Date', inplace=True)

# ---------------------------------------------------------
# 7. PERFORMANCE METRICS & STATISTICS
# ---------------------------------------------------------
# Calculate total return percentage
final_equity = daily_df['Equity'].iloc[-1]
total_return = (final_equity - initial_capital) / initial_capital * 100

# Calculate annualized return (how much you'd make if this continued for a year)
days = (daily_df.index[-1] - daily_df.index[0]).days
annual_return = (1 + total_return/100) ** (365/days) - 1 if days > 0 else 0

# Tally up trade statistics
total_trades = len(trades)
buy_trades = len([t for t in trades if t[0] == 'BUY'])
sell_trades = len([t for t in trades if t[0] in ['SELL', 'FORCE_CLOSE', 'FINAL_CLOSE', 'FORCE_CLOSE_EOD']])

# ---------------------------------------------------------
# 8. CONSOLE OUTPUT (Reporting)
# ---------------------------------------------------------
print(f"\n" + "="*80)
print("BACKTEST RESULTS SUMMARY")
print("="*80)
print(f"Initial Capital: ${initial_capital:,.2f}")
print(f"Final Equity: ${final_equity:,.2f}")
print(f"Total Return: {total_return:.2f}%")
print(f"Annualized Return: {annual_return*100:.2f}%")
print(f"Trading Days: {len(daily_df)}")
print(f"Total Trades: {total_trades}")
print(f"Buy Trades: {buy_trades}")
print(f"Sell Trades: {sell_trades}")
print(f"Trade Pairing Check: {'Passed' if buy_trades == sell_trades else 'Failed'}")
print(f"Average Trades per Day: {total_trades/len(daily_df):.2f}")

# Print the day-by-day breakdown
print("\n" + "="*80)
print("DAILY ACCOUNT EQUITY AND TRADE COUNT REPORT")
print("="*80)
for index, row in daily_df.iterrows():
    print(f"Date: {index}, Account Equity: ${row['Equity']:,.2f}, Trades: {row['Trades']}, "
          f"Cash: ${row['Cash']:,.2f}, Shares Held: {row['Shares']}, Position Value: ${row['Position_Value']:,.2f}")

# Check that every buy trade has a corresponding sell trade
print("\n" + "="*80)
print("TRADE PAIRING VERIFICATION")
print("="*80)
trade_pairs = []
current_buy = None
for trade in trades:
    if trade[0] == 'BUY':
        current_buy = trade
    elif trade[0] in ['SELL', 'FORCE_CLOSE', 'FINAL_CLOSE', 'FORCE_CLOSE_EOD'] and current_buy:
        trade_pairs.append((current_buy, trade))
        current_buy = None

print(f"Total Completed Trade Pairs: {len(trade_pairs)}")
if len(trade_pairs) * 2 != total_trades:
    print("WARNING: Unpaired trades detected!")
    # Locate where the pairing broke
    for i, trade in enumerate(trades):
        if i < len(trades) - 1 and trades[i][0] == 'BUY' and trades[i+1][0] not in ['SELL', 'FORCE_CLOSE', 'FINAL_CLOSE', 'FORCE_CLOSE_EOD']:
            print(f"Unpaired Buy Trade: {trade}")
        elif i == len(trades) - 1 and trade[0] == 'BUY':
            print(f"Final Unclosed Buy Trade: {trade}")

# ---------------------------------------------------------
# 9. VISUALIZATION (Charts)
# ---------------------------------------------------------
plt.figure(figsize=(12, 8))

# Subplot 1: The Equity Curve (How account balance grows/shrinks over time)
plt.subplot(2, 1, 1)
plt.plot(daily_df.index, daily_df['Equity'], linewidth=2)
plt.title('Daily Equity Curve', fontsize=14)
plt.xlabel('Date')
plt.ylabel('Equity ($)')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

# Subplot 2: Bar chart showing number of trades executed per day
plt.subplot(2, 1, 2)
plt.bar(daily_df.index, daily_df['Trades'], alpha=0.7)
plt.title('Daily Number of Trades', fontsize=14)
plt.xlabel('Date')
plt.ylabel('Number of Trades')
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)

plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# 10. FINAL DEBUGGING PRINTOUTS
# ---------------------------------------------------------
# Convert trade list to a DataFrame to print a neat table of the final 20 trades
trades_df = pd.DataFrame(trades, columns=['Action', 'Time', 'Price', 'Shares', 'Equity'])
print("\nLast 20 Trades:")
print(trades_df.tail(20))

# Display statistical description of daily trade frequency
print("\nDaily Trade Statistics:")
print(daily_df['Trades'].describe())

# Final system integrity check
print("\n" + "="*80)
print("FINAL VALIDATION")
print("="*80)
print(f"Final Cash: ${cash:,.2f}")
print(f"Final Shares Held: {shares}")
print(f"Final Position State: {'Holding' if position == 1 else 'Flat/Empty'}")
print(f"Is total trade count an even number?: {'Yes' if total_trades % 2 == 0 else 'No'}")
print(f"Are Buys and Sells balanced?: {'Yes' if buy_trades == sell_trades else 'No'}")