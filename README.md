## 📈 Quantitative Crypto Trading Systems

This repository contains a suite of Python-based quantitative tools for cryptocurrency market analysis, algorithmic backtesting, and portfolio management. The project is modularized to separate indicator logic, strategy simulation, and portfolio rebalancing.

### 🗂️ Repository Structure

* **`BMSB.py` & `BMSB_conf.py`**: Core logic and configuration parameters for calculating the Bull Market Support Band, a key macroeconomic indicator for market cycle analysis.
* **`backtest_long_only_trailing.py`**: Event-driven backtesting engine focused on long-only strategies utilizing trailing stop-loss mechanisms to maximize upside while protecting capital.
* **`backtest_market_structure.py`**: Advanced backtesting framework designed to execute trades based on shifts in underlying market structure and support/resistance confluences.
* **`rebalance.py`**: Object-Oriented simulator for multi-asset portfolio rebalancing, evaluating algorithmic risk mitigation against traditional Buy & Hold strategies.
* **`figures/`**: Directory containing generated visualization outputs of the backtesting results.

### 🔌 Data Acquisition & API Management

Market data is retrieved utilizing the **Binance API**. To ensure robust, secure, and uninterrupted execution, the framework implements the following protocols:

* **Credential Security:** API keys and sensitive environment variables are strictly managed locally via `.env` files and are explicitly excluded from version control (`.gitignore`).
* **Rate Limit Handling:** Built-in request pacing and sleep functions are integrated to strictly adhere to Binance's API rate limits. This prevents IP bans and ensures data pipeline stability during extensive historical data extraction and live backtesting sessions.


### 📊 Performance Analysis & Stress Testing

The strategies have been rigorously backtested across the top 3 highest-capitalization assets (excluding stablecoins): **Bitcoin (BTC), Ethereum (ETH), and Solana (SOL)** against USDT.

To ensure the robustness of the algorithms across different market conditions, the data pipeline extracts and analyzes historical data across three strategic timeframes:
* **4000 Days (Macro Long-Term):** Evaluates the strategy's compounding efficiency and overall performance across multiple complete macroeconomic cycles (halving cycles).
* **1000 Days (Post-Bear Recovery):** Measures the algorithm's ability to identify accumulation zones and capitalize on the transition from a bear market bottom into a new expansionary phase.
* **300 Days (Bear Market Stress-Test):** A localized stress-test designed to evaluate the strategy's capital preservation and risk mitigation during a strict bearish or consolidatory cycle.

Visual performance metrics for each asset and timeframe can be reviewed in the `figures/` directory.
