# Stock-Indicators-backtesting
A Python framework for backtesting and optimizing quantitative trading strategies. It utilizes technical indicators like MACD and KDJ to generate actionable buy/sell signals, allowing users to evaluate historical profitability and refine their algorithms.
# KDJ Strategy Backtester

This repository contains a set of Python scripts designed to download historical stock data, calculate KDJ indicators, and run a backtest on the trading strategy. 

## Setup and Usage Instructions

Follow these steps in order to fetch the data and run the backtest successfully.

### Step 1: Obtain the Data (`DATA_OBTAIN_TXT.py`)
1. Go to [massive.com](https://massive.com) and create an account to get your API key.
2. Open `DATA_OBTAIN_TXT.py` and paste your API key into the variable labeled `"YOUR_API_KEY_HERE"`.
3. Change the dates in the script to match your desired timeframe.
4. Set the stock code for the company you want to analyze (for example, use `AMD` for AMD or `NVDA` for Nvidia).
5. Run the script. It will download the historical data as a few `.txt` files directly into the same folder where the script is located.

### Step 2: Add KDJ Indicators (`KDJ_Additional.py`)
1. Once the raw `.txt` files are downloaded, run `KDJ_Additional.py`.
2. This script processes the raw data, applies the KDJ calculations, and generates new `.csv` and `.xlsx` files in your directory.

### Step 3: Run the Backtest (`GH_KDJ_Backtesting.py`)
1. Open `GH_KDJ_Backtesting.py` and ensure it is set up to read the `.csv` or `.xlsx` files generated in Step 2.
2. Customize your trading parameters in the script:
   - **Initial Cost:** Set your starting capital.
   - **Commission Fees:** Adjust this to match your broker's rates.
   - **KDJ Strategy:** Tweak the specific KDJ parameters to test different variations.
3. Run the script to execute the backtest and view the performance of the strategy!
